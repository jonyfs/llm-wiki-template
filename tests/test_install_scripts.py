"""The guided installers: syntax, lint, and end-to-end runs of the starter scripts against a local copy of the template."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
BASH_FILES = [SCRIPTS / "install-macos.command", SCRIPTS / "install-linux.sh", SCRIPTS / "new-llm-wiki.sh"]
POWERSHELL_FILES = [SCRIPTS / "install-windows.ps1", SCRIPTS / "new-llm-wiki.ps1"]
GIT_ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def make_local_template(dest: Path) -> Path:
    """A git repository holding the current working tree, so the starter scripts can clone it offline."""
    shutil.copytree(
        ROOT,
        dest,
        ignore=shutil.ignore_patterns(".git", "node_modules", "__pycache__", ".opencode"),
        symlinks=True,
    )
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=dest, check=True, env=GIT_ENV)
    subprocess.run(["git", "add", "-A"], cwd=dest, check=True, env=GIT_ENV)
    subprocess.run(["git", "commit", "-qm", "template"], cwd=dest, check=True, env=GIT_ENV)
    return dest


class InstallerSyntaxTest(unittest.TestCase):
    def test_bash_installers_parse(self):
        bash = shutil.which("bash")
        if not bash:
            self.skipTest("bash not installed")
        for path in BASH_FILES:
            with self.subTest(path=path.name):
                self.assertTrue(path.stat().st_mode & 0o111, f"{path.name} must be executable")
                self.assertEqual(subprocess.run([bash, "-n", str(path)]).returncode, 0)

    def test_bash_installers_pass_shellcheck(self):
        shellcheck = shutil.which("shellcheck")
        if not shellcheck:
            self.skipTest("shellcheck not installed")
        result = subprocess.run([shellcheck, *map(str, BASH_FILES)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_powershell_installers_parse(self):
        pwsh = shutil.which("pwsh")
        if not pwsh:
            self.skipTest("pwsh not installed")
        for path in POWERSHELL_FILES:
            with self.subTest(path=path.name):
                script = (
                    "$t=$null; $e=$null; "
                    f"[void][System.Management.Automation.Language.Parser]::ParseFile('{path}', [ref]$t, [ref]$e); "
                    "if ($e.Count) { $e | ForEach-Object { $_.Message }; exit 1 }"
                )
                result = subprocess.run([pwsh, "-NoProfile", "-Command", script], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_windows_launcher_bypasses_policy_only_for_this_script(self):
        text = (SCRIPTS / "install-windows.cmd").read_text(encoding="utf-8")
        self.assertIn("-ExecutionPolicy Bypass", text)
        self.assertIn("install-windows.ps1", text)


@unittest.skipUnless(shutil.which("git") and shutil.which("bash"), "needs git and bash")
class StarterScriptEndToEndTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.template = make_local_template(self.tmp / "template")
        self.env = {**GIT_ENV, "TEMPLATE_URL": f"file://{self.template}", "TEMPLATE_BRANCH": "main"}

    def assert_clean_notebook(self, notebook: Path, name: str):
        self.assertTrue((notebook / "AGENTS.md").is_file())
        self.assertFalse((notebook / "github-pages").exists(), "the template's site must be removed")
        self.assertFalse((notebook / ".github/workflows/pages.yml").exists())
        self.assertIn(f"# {name}", (notebook / "README.md").read_text(encoding="utf-8"))
        log = (notebook / "wiki/log.md").read_text(encoding="utf-8")
        self.assertIn("bootstrap | Start", log)
        self.assertNotIn("## [2026-04-02] ingest", log, "the template's history must be reset")
        self.assertIn("template=file://", (notebook / ".agents/template.lock").read_text(encoding="utf-8"))
        log_out = subprocess.run(["git", "log", "--oneline"], cwd=notebook, capture_output=True, text=True, env=GIT_ENV)
        self.assertEqual(log_out.returncode, 0)
        self.assertEqual(len(log_out.stdout.strip().splitlines()), 1, "a fresh history with one commit")

    def test_bash_starter_creates_a_clean_notebook(self):
        result = subprocess.run(
            ["bash", str(ROOT / "scripts" / "new-llm-wiki.sh"), "demo", "--no-check"],
            cwd=self.tmp, capture_output=True, text=True, env=self.env,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_clean_notebook(self.tmp / "demo", "demo")

    def test_bash_starter_refuses_a_folder_that_exists(self):
        (self.tmp / "taken").mkdir()
        (self.tmp / "taken" / "keep.txt").write_text("mine", encoding="utf-8")
        result = subprocess.run(
            ["bash", str(ROOT / "scripts" / "new-llm-wiki.sh"), "taken", "--no-check"],
            cwd=self.tmp, capture_output=True, text=True, env=self.env,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.tmp / "taken" / "keep.txt").read_text(encoding="utf-8"), "mine")

    def test_powershell_starter_matches_the_bash_result(self):
        pwsh = shutil.which("pwsh")
        if not pwsh:
            self.skipTest("pwsh not installed")
        result = subprocess.run(
            [pwsh, "-NoProfile", "-File", str(ROOT / "scripts" / "new-llm-wiki.ps1"), "-Name", "demo-ps", "-NoCheck"],
            cwd=self.tmp, capture_output=True, text=True, env=self.env,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_clean_notebook(self.tmp / "demo-ps", "demo-ps")


if __name__ == "__main__":
    unittest.main()

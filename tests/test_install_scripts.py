"""The guided installers: syntax, lint, and end-to-end runs of the starter scripts against a local copy of the template."""
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
BASH_FILES = [
    SCRIPTS / "bootstrap.sh",
    SCRIPTS / "install-macos.command",
    SCRIPTS / "install-linux.sh",
    SCRIPTS / "new-llm-wiki.sh",
]
POWERSHELL_FILES = [SCRIPTS / "bootstrap.ps1", SCRIPTS / "install-windows.ps1", SCRIPTS / "new-llm-wiki.ps1"]
GIT_ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def require_tool(name: str) -> str:
    """Return the tool's path. Skip locally when it is missing; fail in CI, where a silent skip would hide a broken check."""
    path = shutil.which(name)
    if path:
        return path
    if os.environ.get("CI"):
        raise AssertionError(f"{name} is required in CI but is not installed")
    raise unittest.SkipTest(f"{name} not installed")


def tree_files(root: Path) -> dict[str, bytes]:
    """Every file under root except .git, mapped to its bytes, for comparing two generated notebooks."""
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file() and ".git" not in p.relative_to(root).parts
    }


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
        shellcheck = require_tool("shellcheck")
        result = subprocess.run([shellcheck, *map(str, BASH_FILES)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_powershell_installers_parse(self):
        pwsh = require_tool("pwsh")
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
        self.assertEqual(len(re.findall(r"^## \[", log, re.M)), 1, "the template's history must be reset to one entry")
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

    def test_powershell_starter_produces_the_same_tree_as_bash(self):
        pwsh = require_tool("pwsh")
        # Same name in two separate parent folders, so the README (which names the folder) matches byte for byte.
        bash_parent, ps_parent = self.tmp / "bash-side", self.tmp / "ps-side"
        bash_parent.mkdir()
        ps_parent.mkdir()
        bash_run = subprocess.run(
            ["bash", str(ROOT / "scripts" / "new-llm-wiki.sh"), "same", "--no-check"],
            cwd=bash_parent, capture_output=True, text=True, env=self.env,
        )
        self.assertEqual(bash_run.returncode, 0, bash_run.stdout + bash_run.stderr)
        ps_run = subprocess.run(
            [pwsh, "-NoProfile", "-File", str(ROOT / "scripts" / "new-llm-wiki.ps1"), "-Name", "same", "-NoCheck"],
            cwd=ps_parent, capture_output=True, text=True, env=self.env,
        )
        self.assertEqual(ps_run.returncode, 0, ps_run.stdout + ps_run.stderr)
        self.assert_clean_notebook(ps_parent / "same", "same")
        self.assertEqual(tree_files(bash_parent / "same"), tree_files(ps_parent / "same"))

    def test_bash_starter_rejects_dot_names(self):
        for name in (".", ".."):
            with self.subTest(name=name):
                result = subprocess.run(
                    ["bash", str(ROOT / "scripts" / "new-llm-wiki.sh"), name, "--no-check"],
                    cwd=self.tmp, capture_output=True, text=True, env=self.env,
                )
                self.assertNotEqual(result.returncode, 0)


@unittest.skipUnless(shutil.which("bash") and shutil.which("git") and shutil.which("python3"), "needs bash, git and python3")
class LinuxInstallerTest(unittest.TestCase):
    def test_refuses_a_name_with_spaces_and_creates_nothing(self):
        home = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, home, True)
        result = subprocess.run(
            ["bash", str(SCRIPTS / "install-linux.sh")],
            input="bad name\n", capture_output=True, text=True,
            env={**os.environ, "HOME": str(home)}, cwd=home,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("use only letters", result.stdout + result.stderr)
        self.assertFalse((home / "Documents").exists(), "nothing is created before the name is accepted")


if __name__ == "__main__":
    unittest.main()

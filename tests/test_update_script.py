"""scripts/update-llm-wiki.sh against throwaway repositories: a two-commit template and an outdated copy with customizations."""
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "update-llm-wiki.sh"
MANIFEST = ROOT / ".agents" / "template-manifest"
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, env=ENV, capture_output=True, text=True, check=True).stdout.strip()


def write(base: Path, rel: str, text: str, mode=None):
    p = base / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    if mode:
        p.chmod(mode)


def template_v1(base: Path):
    (base / ".agents").mkdir(parents=True, exist_ok=True)
    shutil.copy(MANIFEST, base / ".agents" / "template-manifest")
    write(base, "AGENTS.md", "# Rules\nA1\nB\nC\nD\nE\nF1\n")
    write(base, ".agents/skills/wiki-a/SKILL.md", "skill a v1\n")
    write(base, ".agents/skills/wiki-b/SKILL.md", "skill b v1\n")
    write(base, ".agents/skills/wiki-old/SKILL.md", "old skill\n")
    write(base, "scripts/lint.py", "print('lint v1')\n")
    write(base, "scripts/tool.sh", "#!/bin/sh\necho v1\n", 0o755)
    write(base, ".github/workflows/test.yml", "name: v1\n")
    write(base, "wiki/log.md", "# Log\n\nHeader.\n")
    write(base, "wiki/index.md", "template index\n")


def template_v2(base: Path):
    write(base, "AGENTS.md", "# Rules\nA2\nB\nC\nD\nE\nF1\n")
    write(base, ".agents/skills/wiki-a/SKILL.md", "skill a v2\n")
    write(base, ".agents/skills/wiki-b/SKILL.md", "skill b v2\n")
    shutil.rmtree(base / ".agents/skills/wiki-old")
    write(base, ".agents/skills/wiki-new/SKILL.md", "new skill\n")
    write(base, "scripts/lint.py", "print('lint v2')\n")
    write(base, ".github/workflows/test.yml", "name: v2\n")
    write(base, "wiki/index.md", "template index changed\n")
    write(base, "README.md", "template readme\n")


@unittest.skipUnless(shutil.which("bash") and shutil.which("git"), "needs bash and git")
class UpdateScriptTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.tpl = self.tmp / "template"
        self.tpl.mkdir()
        git(self.tpl, "init", "-q", "-b", "main")
        template_v1(self.tpl)
        git(self.tpl, "add", "-A")
        git(self.tpl, "commit", "-qm", "v1")
        self.c1 = git(self.tpl, "rev-parse", "HEAD")
        template_v2(self.tpl)
        git(self.tpl, "add", "-A")
        git(self.tpl, "commit", "-qm", "v2: new skill, newer scripts")
        self.c2 = git(self.tpl, "rev-parse", "HEAD")

    def downstream(self, with_lock=True):
        d = self.tmp / "notebook"
        d.mkdir()
        git(d, "init", "-q", "-b", "main")
        git(self.tpl, "archive", "--format=tar", "-o", str(self.tmp / "v1.tar"), self.c1)
        subprocess.run(["tar", "-xf", str(self.tmp / "v1.tar"), "-C", str(d)], check=True)
        write(d, "AGENTS.md", "# Rules\nA1\nB\nC\nD\nE\nF-custom\n")            # edited at the bottom: merges with the template's top edit
        write(d, ".agents/skills/wiki-b/SKILL.md", "skill b custom\n")          # same line as the template: conflict
        write(d, "README.md", "my readme\n")
        write(d, "raw/mine.md", "my source\n")
        write(d, "wiki/page.md", "my page\n")
        if with_lock:
            write(d, ".agents/template.lock", f"template=x\nref={self.c1}\nupdated=2026-01-01\n")
        git(d, "add", "-A")
        git(d, "commit", "-qm", "my notebook")
        return d

    def run_script(self, d, *args):
        env = {**ENV, "TEMPLATE_URL": f"file://{self.tpl}", "TEMPLATE_BRANCH": "main"}
        return subprocess.run(["bash", str(SCRIPT), *args], cwd=d, env=env, capture_output=True, text=True)

    def test_dry_run_changes_nothing(self):
        d = self.downstream()
        r = self.run_script(d, "--no-check")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(git(d, "status", "--porcelain"), "")
        self.assertRegex(r.stdout, r"ADD: 1")
        self.assertIn("wiki-new/SKILL.md", r.stdout)
        self.assertRegex(r.stdout, r"CONFLICT: 1")
        self.assertIn("Nothing was changed", r.stdout)
        self.assertIn("v2: new skill, newer scripts", r.stdout)

    def test_apply_with_a_lock_uses_three_way_logic(self):
        d = self.downstream()
        r = self.run_script(d, "--apply", "--no-check")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)  # one conflict left to resolve
        self.assertEqual((d / "scripts/lint.py").read_text(), "print('lint v2')\n")            # untouched here: updated
        self.assertEqual((d / ".agents/skills/wiki-a/SKILL.md").read_text(), "skill a v2\n")
        self.assertEqual((d / ".agents/skills/wiki-new/SKILL.md").read_text(), "new skill\n")  # added
        merged = (d / "AGENTS.md").read_text()
        self.assertIn("A2", merged)                                                              # template's change
        self.assertIn("F-custom", merged)                                                        # your change
        self.assertEqual((d / ".agents/skills/wiki-b/SKILL.md").read_text(), "skill b custom\n")  # conflict: yours is kept
        self.assertEqual((d / ".agents/skills/wiki-b/SKILL.md.template-new").read_text(), "skill b v2\n")
        self.assertEqual((d / ".agents/skills/wiki-b/SKILL.md.template-base").read_text(), "skill b v1\n")
        self.assertEqual((d / ".github/workflows/test.yml").read_text(), "name: v1\n")          # once: never overwritten
        self.assertTrue((d / ".agents/skills/wiki-old/SKILL.md").exists())                       # no --prune
        self.assertTrue(os.access(d / "scripts/tool.sh", os.X_OK))
        # Never touched: the notebook's own files and everything under raw/ and wiki/ except the log.
        self.assertEqual((d / "README.md").read_text(), "my readme\n")
        self.assertEqual((d / "raw/mine.md").read_text(), "my source\n")
        self.assertEqual((d / "wiki/page.md").read_text(), "my page\n")
        self.assertEqual((d / "wiki/index.md").read_text(), "template index\n")
        self.assertIn("maintenance | Update template files to " + self.c2[:7], (d / "wiki/log.md").read_text())
        # The base is not advanced while a conflict is open.
        self.assertIn(self.c1, (d / ".agents/template.lock").read_text())
        self.assertIn(self.c2, (d / ".agents/template.pending").read_text())

    def test_finish_waits_for_resolution_then_records_the_new_base(self):
        d = self.downstream()
        self.run_script(d, "--apply", "--no-check")
        early = self.run_script(d, "--finish")
        self.assertEqual(early.returncode, 2)
        self.assertIn("wiki-b/SKILL.md.template-new", early.stdout)
        write(d, ".agents/skills/wiki-b/SKILL.md", "skill b custom on top of v2\n")
        (d / ".agents/skills/wiki-b/SKILL.md.template-new").unlink()
        (d / ".agents/skills/wiki-b/SKILL.md.template-base").unlink()
        done = self.run_script(d, "--finish")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn(self.c2, (d / ".agents/template.lock").read_text())
        self.assertFalse((d / ".agents/template.pending").exists())
        again = self.run_script(d, "--no-check")
        self.assertIn("Already up to date", again.stdout)

    def test_without_a_lock_old_versions_are_recognized_from_history(self):
        d = self.downstream(with_lock=False)
        r = self.run_script(d, "--apply", "--no-check")
        self.assertEqual(r.returncode, 2)
        self.assertEqual((d / "scripts/lint.py").read_text(), "print('lint v2')\n")             # equals a past template version: safe
        self.assertEqual((d / ".agents/skills/wiki-a/SKILL.md").read_text(), "skill a v2\n")
        self.assertEqual((d / ".agents/skills/wiki-b/SKILL.md").read_text(), "skill b custom\n")  # customized: kept
        self.assertTrue((d / ".agents/skills/wiki-b/SKILL.md.template-new").exists())
        self.assertFalse((d / ".agents/skills/wiki-b/SKILL.md.template-base").exists())          # base unknown
        self.assertTrue((d / "AGENTS.md.template-new").exists())                                 # no base, so no automatic merge
        self.assertEqual((d / "AGENTS.md").read_text(), "# Rules\nA1\nB\nC\nD\nE\nF-custom\n")

    def test_prune_removes_only_untouched_dropped_files(self):
        d = self.downstream()
        write(d, ".agents/skills/wiki-old/SKILL.md", "old skill\n")  # same as the template's old version
        self.run_script(d, "--apply", "--prune", "--no-check")
        self.assertFalse((d / ".agents/skills/wiki-old/SKILL.md").exists())
        d2 = self.tmp / "other"
        shutil.copytree(d, d2, symlinks=True)
        write(d2, ".agents/skills/wiki-old/SKILL.md", "my edits\n")
        out = self.run_script(d2, "--apply", "--prune", "--allow-dirty", "--no-check")
        self.assertIn("DROPPED_EDITED", out.stdout)
        self.assertTrue((d2 / ".agents/skills/wiki-old/SKILL.md").exists())

    def test_apply_refuses_a_dirty_tree_and_branch_flag_switches(self):
        d = self.downstream()
        write(d, "wiki/page.md", "uncommitted\n")
        r = self.run_script(d, "--apply", "--no-check")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("uncommitted changes", r.stderr)
        git(d, "checkout", "--", "wiki/page.md")
        self.run_script(d, "--apply", "--branch", "update-llm-wiki", "--no-check")
        self.assertEqual(git(d, "branch", "--show-current"), "update-llm-wiki")

    def test_missing_symlinks_are_added_and_real_files_are_left_alone(self):
        d = self.downstream()
        write(d, "CLAUDE.md", "a real file\n")
        git(d, "add", "-A")
        git(d, "commit", "-qm", "real CLAUDE.md")
        r = self.run_script(d, "--apply", "--no-check")
        self.assertTrue((d / ".cursorrules").is_symlink())
        self.assertEqual(os.readlink(d / ".cursorrules"), "AGENTS.md")
        self.assertFalse((d / "CLAUDE.md").is_symlink())
        self.assertIn("LINK_BLOCKED", r.stdout)

    def test_refuses_to_run_outside_a_notebook(self):
        empty = self.tmp / "empty"
        empty.mkdir()
        git(empty, "init", "-q")
        r = self.run_script(empty)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("does not look like an LLM wiki notebook", r.stderr)


class ManifestTest(unittest.TestCase):
    def policy(self, path):
        for line in MANIFEST.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#"):
                continue
            pol, pat, *_ = line.split("\t")
            if re.fullmatch(re.escape(pat).replace(r"\*", ".*"), path):
                return pol
        return "none"

    def test_notebook_owned_files_are_never_updated(self):
        for path in ("raw/a.md", "wiki/index.md", "wiki/sources/x.md", "README.md", "LICENSE", "github-pages/index.html", "tests/test_readme.py", "tests/test_github_pages.py", "scripts/new-llm-wiki.sh"):
            self.assertEqual(self.policy(path), "never", path)

    def test_template_owned_files_are_managed(self):
        self.assertEqual(self.policy("AGENTS.md"), "merge")
        for path in (".agents/skills/wiki-update/SKILL.md", ".agents/commands/wiki-update.md", "scripts/lint.py", "scripts/update-llm-wiki.sh", "tests/test_lint.py", "docs/migration.md"):
            self.assertEqual(self.policy(path), "managed", path)
        self.assertEqual(self.policy(".github/workflows/test.yml"), "once")

    def test_every_link_in_the_manifest_exists_with_that_target(self):
        for line in MANIFEST.read_text(encoding="utf-8").splitlines():
            if line.startswith("link\t"):
                _, path, target = line.split("\t")
                self.assertTrue((ROOT / path).is_symlink(), path)
                self.assertEqual(os.readlink(ROOT / path), target, path)


if __name__ == "__main__":
    unittest.main()

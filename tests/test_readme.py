"""Keep the README honest: images exist, the scripts are linked, not pasted, intro anchors resolve."""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
SCRIPT = ROOT / "scripts" / "new-llm-wiki.sh"


def slug(heading: str) -> str:
    s = re.sub(r"[^\w\s-]", "", heading.lower().strip())
    return re.sub(r"\s", "-", s)


class ReadmeTest(unittest.TestCase):
    def test_every_local_image_exists(self):
        refs = set(re.findall(r'(?:src|srcset)="(docs/images/[^"]+)"', README)) | set(re.findall(r"!\[[^\]]*\]\((docs/images/[^)]+)\)", README))
        for ref in refs:
            self.assertTrue((ROOT / ref).is_file(), ref)

    def test_internal_anchors_point_at_headings(self):
        headings = {slug(h) for h in re.findall(r"^#{1,6} (.+)$", README, re.M)}
        for anchor in set(re.findall(r"\]\(#([^)]+)\)", README)):
            self.assertIn(anchor, headings, anchor)

    def test_no_em_dashes(self):
        self.assertNotIn("—", README)


@unittest.skipUnless(SCRIPT.is_file(), "starter script not present in this copy")
class StarterScriptTest(unittest.TestCase):
    def test_readme_links_the_scripts_instead_of_pasting_them(self):
        self.assertNotIn("````bash", README, "link to the scripts instead of pasting them")
        for name in ("new-llm-wiki.sh", "update-llm-wiki.sh"):
            if (ROOT / "scripts" / name).is_file():
                self.assertIn(f"blob/main/scripts/{name}", README, name)

    def test_script_is_executable_and_parses(self):
        bash = shutil.which("bash")
        for path in (SCRIPT, ROOT / "scripts" / "update-llm-wiki.sh"):
            if not path.is_file():
                continue
            self.assertTrue(path.stat().st_mode & 0o111, f"{path.name} must be executable")
            if bash:
                self.assertEqual(subprocess.run([bash, "-n", str(path)]).returncode, 0, path.name)

    def test_script_refuses_unknown_options(self):
        bash = shutil.which("bash")
        if not bash:
            self.skipTest("bash not available")
        result = subprocess.run([bash, str(SCRIPT), "x", "--bogus"], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown option", result.stderr)


if __name__ == "__main__":
    unittest.main()

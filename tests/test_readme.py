"""Keep the README honest: images exist, the pasted starter script matches the real one, intro anchors resolve."""
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
    def test_readme_pastes_the_real_script(self):
        if "## The starter script" not in README:
            self.skipTest("README does not paste the script")
        block = re.search(r"## The starter script.*?````bash\n(.*?)\n````", README, re.S).group(1)
        self.assertEqual(block.strip(), SCRIPT.read_text(encoding="utf-8").strip())

    def test_script_is_executable_and_parses(self):
        self.assertTrue(SCRIPT.stat().st_mode & 0o111, "script must be executable")
        bash = shutil.which("bash")
        if bash:
            self.assertEqual(subprocess.run([bash, "-n", str(SCRIPT)]).returncode, 0)

    def test_script_refuses_unknown_options(self):
        bash = shutil.which("bash")
        if not bash:
            self.skipTest("bash not available")
        result = subprocess.run([bash, str(SCRIPT), "x", "--bogus"], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown option", result.stderr)


if __name__ == "__main__":
    unittest.main()

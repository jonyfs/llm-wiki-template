from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "extract_outline.py"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import extract_outline  # noqa: E402


SECTION_TEXT = "# {title}\n" + "x" * 71 + "\n"


class ExtractOutlineTests(unittest.TestCase):
    def write_doc(self, text: str) -> Path:
        handle = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
        handle.write(text)
        handle.close()
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))
        return Path(handle.name)

    def run_outline(self, path: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), str(path), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_outline_lists_level_line_number_and_title_for_each_heading(self) -> None:
        path = self.write_doc("# Top\n\nLead.\n\n## Child\nBody.\n\n### Deep\nMore.\n")

        result = self.run_outline(path)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        lines = result.stdout.splitlines()
        self.assertTrue(lines[0].startswith("L1 h1 Top"), msg=lines[0])
        self.assertTrue(lines[1].startswith("L5 h2 Child"), msg=lines[1])
        self.assertTrue(lines[2].startswith("L8 h3 Deep"), msg=lines[2])

    def test_headings_inside_fenced_code_are_ignored(self) -> None:
        path = self.write_doc("# Real\n\n```\n# Not a heading\n```\n")

        outline = extract_outline.outline(path.read_text(encoding="utf-8"))

        self.assertEqual([section.title for section in outline], ["Real"])

    def test_budget_groups_consecutive_sections_into_chunks(self) -> None:
        text = "".join(SECTION_TEXT.format(title=f"S{index}") for index in range(3))
        path = self.write_doc(text)

        result = self.run_outline(path, "--budget", "40")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        chunk_lines = [line for line in result.stdout.splitlines() if line.startswith("chunk ")]
        self.assertEqual(len(chunk_lines), 2)
        self.assertTrue(chunk_lines[0].startswith("chunk 1: lines 1-"), msg=chunk_lines[0])

    def test_oversized_section_gets_its_own_chunk(self) -> None:
        text = "# Big\n" + "y" * 800 + "\n# Small\nz\n"

        chunks = extract_outline.plan_chunks(text, budget_tokens=50)

        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0].start, 1)

    def test_file_without_headings_is_one_chunk(self) -> None:
        path = self.write_doc("plain text only\nsecond line\n")

        result = self.run_outline(path, "--budget", "1000")

        self.assertIn("no headings", result.stdout)
        self.assertIn("chunk 1: lines 1-2", result.stdout)


if __name__ == "__main__":
    unittest.main()

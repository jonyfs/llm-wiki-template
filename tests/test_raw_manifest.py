from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "raw_manifest.py"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import raw_manifest  # noqa: E402


class RawManifestTests(unittest.TestCase):
    def make_root(self) -> Path:
        root = Path(tempfile.mkdtemp(prefix="manifest-"))
        self.addCleanup(lambda: shutil.rmtree(root, ignore_errors=True))
        (root / "raw" / "assets").mkdir(parents=True)
        (root / "wiki").mkdir()
        (root / "raw" / "alpha.md").write_text("# Alpha Title\n\nBody text about Alpha.\n", encoding="utf-8")
        (root / "raw" / "assets" / "chart.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00binary")
        return root

    def run_manifest(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--root", str(root), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_manifest_lists_each_raw_file_with_digest_size_and_first_heading(self) -> None:
        root = self.make_root()

        entries = {entry["path"]: entry for entry in raw_manifest.build_manifest(root)}

        alpha = entries["raw/alpha.md"]
        self.assertEqual(alpha["first_heading"], "Alpha Title")
        self.assertEqual(alpha["size"], (root / "raw" / "alpha.md").stat().st_size)
        self.assertEqual(len(alpha["sha256"]), 64)
        self.assertIsNone(entries["raw/assets/chart.png"]["first_heading"])

    def test_manifest_is_written_under_wiki_and_raw_is_untouched(self) -> None:
        root = self.make_root()
        before = sorted((path.relative_to(root).as_posix(), path.read_bytes()) for path in (root / "raw").rglob("*") if path.is_file())

        result = self.run_manifest(root)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("manifest ok: 2 raw files", result.stdout)
        payload = json.loads((root / "wiki" / ".manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(payload["files"]), 2)
        after = sorted((path.relative_to(root).as_posix(), path.read_bytes()) for path in (root / "raw").rglob("*") if path.is_file())
        self.assertEqual(before, after)

    def test_normalized_digest_ignores_case_and_whitespace(self) -> None:
        first = raw_manifest.normalized_digest(b"Alpha   Title\n\nBody")
        second = raw_manifest.normalized_digest(b"  alpha title body  ")

        self.assertEqual(first, second)

    def test_check_reports_duplicate_of_existing_raw_file(self) -> None:
        root = self.make_root()
        self.run_manifest(root)
        candidate = root / "candidate.md"
        candidate.write_text("# ALPHA   title\nbody TEXT about alpha.\n", encoding="utf-8")

        result = self.run_manifest(root, "--check", str(candidate))

        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate of raw/alpha.md", result.stdout)

    def test_check_passes_for_new_content(self) -> None:
        root = self.make_root()
        candidate = root / "candidate.md"
        candidate.write_text("Something else entirely.\n", encoding="utf-8")

        result = self.run_manifest(root, "--check", str(candidate))

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("no duplicate", result.stdout)

    def test_check_ignores_stale_manifest_when_raw_changed(self) -> None:
        root = self.make_root()
        self.run_manifest(root)
        (root / "raw" / "alpha.md").write_text("Changed after manifest.\n", encoding="utf-8")
        candidate = root / "candidate.md"
        candidate.write_text("# Alpha Title\n\nBody text about Alpha.\n", encoding="utf-8")

        result = self.run_manifest(root, "--check", str(candidate))

        self.assertEqual(result.returncode, 0, msg=result.stdout)
        self.assertIn("no duplicate", result.stdout)


if __name__ == "__main__":
    unittest.main()

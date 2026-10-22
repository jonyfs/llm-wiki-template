import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "lint.py"
FIXTURES_ROOT = REPO_ROOT / "tests" / "fixtures"

LEDGER = """
## Claims ledger
- C1: Alpha source reports no comparative deployment measurements. [[raw/alpha.md]]
- C2: The fixture is a primary research evidence page. [[raw/alpha.md]]
"""


class ClaimsLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        temp_dir = Path(tempfile.mkdtemp(prefix="claims-ledger-"))
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))
        shutil.copytree(FIXTURES_ROOT / "lint_valid_research", temp_dir, dirs_exist_ok=True)
        self.root = temp_dir
        self.source = self.root / "wiki" / "sources" / "alpha-source.md"

    def add_ledger(self, block: str) -> None:
        text = self.source.read_text(encoding="utf-8")
        self.source.write_text(text.rstrip("\n") + "\n" + block, encoding="utf-8")

    def run_lint(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--root", str(self.root), "--format", "json"],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_valid_claims_ledger_passes(self) -> None:
        self.add_ledger(LEDGER)

        result = self.run_lint()

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(json.loads(result.stdout)["violations"], [])

    def test_malformed_ledger_entry_fails(self) -> None:
        self.add_ledger("\n## Claims ledger\n- C1 no colon and no raw link\n")

        result = self.run_lint()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("claims ledger entries must read", result.stdout + result.stderr)

    def test_duplicate_claim_id_fails(self) -> None:
        self.add_ledger(LEDGER.replace("- C2:", "- C1:"))

        result = self.run_lint()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("claim id C1 is duplicated", result.stdout + result.stderr)

    def test_claim_citing_non_canonical_raw_file_fails(self) -> None:
        self.add_ledger(LEDGER.replace("[[raw/alpha.md]]", "[[raw/other.md]]", 1))

        result = self.run_lint()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must cite the canonical raw file", result.stdout + result.stderr)

    def test_empty_claims_ledger_fails(self) -> None:
        self.add_ledger("\n## Claims ledger\n")

        result = self.run_lint()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("claims ledger must contain at least one claim", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import re
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

    def violations(self, result: subprocess.CompletedProcess[str]) -> list[str]:
        return json.loads(result.stdout)["violations"]

    def rewrite_source_frontmatter(self, old: str, new: str) -> None:
        text = self.source.read_text(encoding="utf-8")
        self.assertIn(old, text)
        self.source.write_text(text.replace(old, new, 1), encoding="utf-8")

    def ledger_violations(self, result: subprocess.CompletedProcess[str]) -> list[str]:
        return [
            item
            for item in self.violations(result)
            if "claims ledger" in item or "must cite the canonical" in item or "claim id" in item
        ]

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

    # CR-2: link_target() returns None for "[[#x]]"; the old comprehension called
    # .startswith on None and aborted the whole run with a traceback.
    def test_empty_link_target_in_sources_does_not_crash_lint(self) -> None:
        self.rewrite_source_frontmatter('  - "[[raw/alpha.md]]"\n', '  - "[[raw/alpha.md]] [[#x]]"\n')
        self.add_ledger(LEDGER)

        result = self.run_lint()

        self.assertNotIn("Traceback", result.stderr)
        self.assertNotIn("AttributeError", result.stderr)
        items = self.violations(result)
        self.assertTrue(any("must be a wiki link" in item for item in items), msg=str(items))
        self.assertTrue(any("claims ledger" in item for item in items), msg=str(items))

    # CR-1: duplicate heading — the old filter stripped every copy from the schema
    # check and find_section_ranges kept only the last range, so a malformed first
    # block was never scanned and the page linted clean.
    def test_duplicate_claims_ledger_heading_is_violation(self) -> None:
        self.add_ledger("\n## Claims ledger\n- C1 totally malformed line no colon\n")
        self.add_ledger("\n## Claims ledger\n- C2: The fixture is a primary research evidence page. [[raw/alpha.md]]\n")

        result = self.run_lint()

        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(
            any("more than one `## Claims ledger`" in item for item in self.violations(result)),
            msg=result.stdout + result.stderr,
        )

    # CR-1(b) / WR-5: the ledger must be the last level-2 section.
    def test_claims_ledger_followed_by_another_h2_is_violation(self) -> None:
        self.add_ledger(LEDGER)
        self.add_ledger("\n## Additional detail\nTrailing section.\n")

        result = self.run_lint()

        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(
            any("must be the last" in item and "Claims ledger" in item for item in self.violations(result)),
            msg=result.stdout + result.stderr,
        )

    # WR-1: the lazy claim text group admitted a second wikilink before the anchor link.
    def test_claim_line_with_extra_wikilink_is_malformed(self) -> None:
        self.add_ledger("\n## Claims ledger\n- C1: text [[raw/beta.md]] extra [[raw/alpha.md]]\n")

        result = self.run_lint()

        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(
            any(
                "claims ledger entries must read" in item
                for item in self.ledger_violations(result)
            ),
            msg=result.stdout + result.stderr,
        )

    # WR-8: whitespace-only claim text matched the old (.+?) group.
    def test_whitespace_only_claim_text_is_malformed(self) -> None:
        self.add_ledger("\n## Claims ledger\n- C1:   [[raw/alpha.md]]\n")

        result = self.run_lint()

        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(
            any("claims ledger entries must read" in item for item in self.violations(result)),
            msg=result.stdout + result.stderr,
        )

    # WR-8: strip-then-match admitted an indented sub-bullet as a claim.
    def test_indented_claim_sub_bullet_is_malformed(self) -> None:
        self.add_ledger(
            "\n## Claims ledger\n- C1: Alpha source reports no comparative deployment measurements. [[raw/alpha.md]]\n"
            "  - C2: indented sub-bullet. [[raw/alpha.md]]\n"
        )

        result = self.run_lint()

        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(
            any("claims ledger entries must read" in item for item in self.violations(result)),
            msg=result.stdout + result.stderr,
        )

    # WR-7: per-line ledger messages must carry the line number used elsewhere.
    def test_malformed_claim_violation_includes_line_number(self) -> None:
        self.add_ledger("\n## Claims ledger\n- C1 no colon and no raw link\n")

        result = self.run_lint()

        malformed = [item for item in self.violations(result) if "claims ledger entries must read" in item]
        self.assertTrue(malformed, msg=result.stdout + result.stderr)
        for item in malformed:
            self.assertRegex(item, r": line \d+: claims ledger entries must read")

    # NT-1: with canonical=None every well-formed claim used to get a misleading
    # per-claim error; now exactly one page-level violation replaces the cascade.
    def test_multiple_raw_sources_reports_one_ledger_violation(self) -> None:
        self.rewrite_source_frontmatter(
            '  - "[[raw/alpha.md]]"\n', '  - "[[raw/alpha.md]]"\n  - "[[raw/beta.md]]"\n'
        )
        self.add_ledger(LEDGER)

        result = self.run_lint()

        self.assertNotEqual(result.returncode, 0)
        items = self.violations(result)
        self.assertFalse(any("must cite the canonical" in item for item in items), msg=str(items))
        page_level = [item for item in items if "claims ledger requires exactly one canonical" in item]
        self.assertEqual(len(page_level), 1, msg=str(items))

    # NT-2: an all-malformed ledger must not also claim the section is empty.
    def test_all_malformed_ledger_does_not_report_empty(self) -> None:
        self.add_ledger("\n## Claims ledger\n- C1 no colon and no raw link\n")

        result = self.run_lint()

        items = self.violations(result)
        self.assertTrue(any("claims ledger entries must read" in item for item in items), msg=str(items))
        self.assertFalse(any("at least one claim" in item for item in items), msg=str(items))

    # WR-6: id boundary cases (regex is C[1-9][0-9]*).
    def test_zero_prefixed_claim_id_is_malformed(self) -> None:
        self.add_ledger("\n## Claims ledger\n- C0: Zero is not a valid claim id. [[raw/alpha.md]]\n")

        result = self.run_lint()

        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(
            any("claims ledger entries must read" in item for item in self.violations(result)),
            msg=result.stdout + result.stderr,
        )

    def test_lowercase_claim_id_is_malformed(self) -> None:
        self.add_ledger("\n## Claims ledger\n- c1: Lowercase is not a valid claim id. [[raw/alpha.md]]\n")

        result = self.run_lint()

        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(
            any("claims ledger entries must read" in item for item in self.violations(result)),
            msg=result.stdout + result.stderr,
        )

    # WR-6: the source-page type guard — a non-source page must not get ledger
    # validation, only the schema heading error.
    def test_entity_page_with_ledger_gets_heading_error_not_ledger_validation(self) -> None:
        entity = self.root / "wiki" / "entities" / "wireguard.md"
        text = entity.read_text(encoding="utf-8")
        entity.write_text(text.rstrip("\n") + "\n\n## Claims ledger\n- C1 no colon\n", encoding="utf-8")

        result = self.run_lint()

        items = self.violations(result)
        self.assertTrue(any("level-2 headings must be exactly" in item for item in items), msg=str(items))
        self.assertFalse(any("claims ledger entries must read" in item for item in items), msg=str(items))


if __name__ == "__main__":
    unittest.main()

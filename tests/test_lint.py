from __future__ import annotations

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


class LintScriptTests(unittest.TestCase):
    def copy_fixture(self, name: str) -> Path:
        temp_dir = Path(tempfile.mkdtemp(prefix="lint-fixture-"))
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))
        shutil.copytree(FIXTURES_ROOT / name, temp_dir, dirs_exist_ok=True)
        return temp_dir

    def run_lint(self, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--root", str(root)],
            capture_output=True,
            text=True,
            check=False,
        )

    def load_report(self, result: subprocess.CompletedProcess[str]) -> dict[str, object]:
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        return json.loads(result.stdout)

    def replace_in_file(self, path: Path, old: str, new: str) -> None:
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new), encoding="utf-8")

    def replace_everywhere(self, root: Path, old: str, new: str) -> None:
        for path in root.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            if old in text:
                path.write_text(text.replace(old, new), encoding="utf-8")

    def test_lint_passes_on_valid_research_fixture(self) -> None:
        root = self.copy_fixture("lint_valid_research")

        report = self.load_report(self.run_lint(root))

        self.assertEqual(report["page_count"], 4)
        self.assertEqual(report["violations"], [])

    def test_lint_fails_when_source_role_is_missing(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "sources" / "alpha-source.md"
        self.replace_in_file(path, 'source_role: "primary"\n', "")

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must include `source_role`", result.stderr)

    def test_lint_fails_when_source_format_is_invalid(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "sources" / "alpha-source.md"
        self.replace_in_file(path, 'source_format: "paper"', 'source_format: "memo"')

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("`source_format` must be one of", result.stderr)

    def test_lint_fails_when_authors_is_not_a_list(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "sources" / "alpha-source.md"
        self.replace_in_file(
            path,
            'authors:\n  - "Researcher One"\n  - "Researcher Two"\n',
            'authors: "Researcher One"\n',
        )

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("`authors` must be a YAML list of non-empty strings", result.stderr)

    def test_lint_fails_when_published_at_is_invalid(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "sources" / "alpha-source.md"
        self.replace_in_file(path, 'published_at: "2026-04-08"', 'published_at: "2026-4-8"')

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("`published_at` must use YYYY-MM-DD", result.stderr)

    def test_lint_fails_when_canonical_url_is_invalid(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "sources" / "alpha-source.md"
        self.replace_in_file(path, 'canonical_url: "https://example.com/alpha"', 'canonical_url: "example.com/alpha"')

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("`canonical_url` must be an absolute http(s) URL", result.stderr)

    def test_lint_fails_when_required_heading_is_missing(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "sources" / "alpha-source.md"
        self.replace_in_file(
            path,
            '## Open questions\nAlpha question about what the source still leaves unmeasured.\n',
            "",
        )

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("level-2 headings must be exactly", result.stderr)

    def test_lint_fails_when_filename_is_not_kebab_case(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        old_path = root / "wiki" / "concepts" / "key-rotation.md"
        new_path = root / "wiki" / "concepts" / "Key_Rotation.md"
        old_path.rename(new_path)
        self.replace_everywhere(root, "[[key-rotation]]", "[[Key_Rotation]]")

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("filename must use lowercase kebab-case", result.stderr)

    def test_lint_fails_when_title_is_duplicated_across_page_types(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "entities" / "wireguard.md"
        self.replace_in_file(path, 'title: "WireGuard"', 'title: "Alpha Source"')

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("`title` must be unique across page types", result.stderr)

    def test_lint_fails_when_old_synthesis_heading_is_used(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "syntheses" / "research-overview.md"
        self.replace_in_file(path, "## Evidence base", "## Citations or supporting pages")

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("use `## Evidence base` instead of `## Citations or supporting pages`", result.stderr)

    def test_lint_fails_when_evidence_subheading_is_invalid(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "syntheses" / "research-overview.md"
        self.replace_in_file(path, "### Supports", "### Mixed evidence")

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("`## Evidence base` only allows", result.stderr)

    def test_lint_fails_when_evidence_bullet_is_not_claim_led(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "syntheses" / "research-overview.md"
        self.replace_in_file(
            path,
            "- Key rotation is central to the current explanation: [[key-rotation]] [[alpha-source]]",
            "- [[key-rotation]] [[alpha-source]]",
        )

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("evidence bullets must begin with a short claim fragment", result.stderr)

    def test_lint_fails_when_index_entry_is_missing(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "index.md"
        self.replace_in_file(
            path,
            "- [[wireguard]] - Entity page for WireGuard as a stable protocol object in the corpus.\n",
            "",
        )

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing `entity` index entry for `[[wireguard]]`", result.stderr)

    def test_lint_fails_when_related_pages_are_missing(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "concepts" / "key-rotation.md"
        self.replace_in_file(
            path,
            "## Related pages\n- [[research-overview]]\n",
            "## Related pages\nNo linked pages yet.\n",
        )

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("`## Related pages` must include at least one wiki-page link", result.stderr)

    def test_lint_fails_when_unheaded_lead_is_missing(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "syntheses" / "research-overview.md"
        self.replace_in_file(
            path,
            "Research overview lead. This synthesis is bounded to the current fixture corpus and does not claim broader empirical coverage beyond these example pages.\n\n## Question or thesis",
            "## Question or thesis",
        )

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("page body must begin with an unheaded lead", result.stderr)


if __name__ == "__main__":
    unittest.main()

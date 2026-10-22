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

    def run_lint(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--root", str(root), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def load_report(self, result: subprocess.CompletedProcess[str]) -> dict[str, object]:
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        return json.loads(result.stdout)

    def add_index_entry(self, root: Path, section: str, line: str) -> None:
        index = root / "wiki" / "index.md"
        text = index.read_text(encoding="utf-8")
        if section == "Concepts":
            text = text.replace("## Syntheses", f"{line}\n\n## Syntheses")
        else:
            text = text.rstrip("\n") + f"\n{line}\n"
        index.write_text(text, encoding="utf-8")

    def add_concept(self, root: Path, slug: str, title: str, body_extra: str = "") -> None:
        text = (
            "---\n"
            f'title: "{title}"\n'
            'type: "concept"\n'
            "sources:\n"
            '  - "[[alpha-source]]"\n'
            'created_at: "2026-04-08"\n'
            'updated_at: "2026-04-08"\n'
            "---\n\n"
            f"Lead for {title}.\n\n"
            "## Summary\nSummary text.\n\n"
            "## Why it matters\nIt matters here.\n\n"
            "## Current understanding\nCurrent view.\n"
            f"{body_extra}"
            "\n## Related pages\n- [[research-overview]]\n\n"
            "## Open questions or tensions\nNone yet.\n"
        )
        (root / "wiki" / "concepts" / f"{slug}.md").write_text(text, encoding="utf-8")

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

        report = self.load_report(self.run_lint(root, "--format", "json"))

        self.assertEqual(report["page_count"], 4)
        self.assertEqual(report["violations"], [])
        self.assertEqual(report["warnings"], [])

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

    def test_lint_fails_when_created_at_is_after_updated_at(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "sources" / "alpha-source.md"
        self.replace_in_file(path, 'created_at: "2026-04-08"', 'created_at: "2026-04-09"')

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("`created_at` must not be later than `updated_at`", result.stderr)

    def test_lint_fails_when_published_at_is_not_a_real_date(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "sources" / "alpha-source.md"
        self.replace_in_file(path, 'published_at: "2026-04-08"', 'published_at: "2026-02-30"')

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("`published_at` must be a real calendar date", result.stderr)

    def test_lint_fails_when_canonical_url_embeds_credentials(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "sources" / "alpha-source.md"
        self.replace_in_file(
            path,
            'canonical_url: "https://example.com/alpha"',
            'canonical_url: "https://user:secret@example.com/alpha"',
        )

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("`canonical_url` must not embed credentials", result.stderr)

    def test_lint_fails_when_raw_sha256_is_not_64_lowercase_hex(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "sources" / "alpha-source.md"
        self.replace_in_file(path, "0123456789abcdef" * 4, "0123456789ABCDEF" * 4)

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("`raw_sha256` must be 64 lowercase hex characters", result.stderr)

    def test_lint_fails_when_source_page_cites_another_source_page(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        alpha = root / "wiki" / "sources" / "alpha-source.md"
        gamma_text = alpha.read_text(encoding="utf-8").replace("Alpha Source", "Gamma Source")
        gamma_text = gamma_text.replace(
            '  - "[[raw/alpha.md]]"\n', '  - "[[raw/alpha.md]]"\n  - "[[alpha-source]]"\n'
        )
        (root / "wiki" / "sources" / "gamma-source.md").write_text(gamma_text, encoding="utf-8")

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source pages must not cite other source pages", result.stderr)

    def test_lint_fails_when_page_cites_itself(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "sources" / "alpha-source.md"
        self.replace_in_file(path, '  - "[[raw/alpha.md]]"\n', '  - "[[raw/alpha.md]]"\n  - "[[alpha-source]]"\n')

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("`sources` must not reference the page itself", result.stderr)

    def test_lint_fails_on_dependency_cycle_in_sources(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "concepts" / "key-rotation.md"
        self.replace_in_file(path, '  - "[[wireguard]]"\n', '  - "[[wireguard]]"\n  - "[[research-overview]]"\n')

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dependency cycle detected in `sources`", result.stderr)

    def test_lint_fails_on_broken_body_wikilink(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "concepts" / "key-rotation.md"
        self.replace_in_file(path, "Key rotation tension.", "Key rotation tension. See [[does-not-exist]].")

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("broken wikilink `[[does-not-exist]]`", result.stderr)

    def test_lint_fails_when_raw_file_of_indexed_source_is_deleted(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        (root / "raw" / "alpha.md").unlink()

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("`sources` references missing raw file `raw/alpha.md`", result.stderr)

    def test_lint_fails_when_body_raw_link_points_outside_raw(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "concepts" / "key-rotation.md"
        self.replace_in_file(path, "Key rotation tension.", "Key rotation tension. See [[raw/../wiki/index.md]].")

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must point inside `raw/`", result.stderr)

    def test_lint_fails_when_body_raw_link_target_is_missing(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "concepts" / "key-rotation.md"
        self.replace_in_file(path, "Key rotation tension.", "Key rotation tension. See [[raw/missing.md]].")

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("raw link `[[raw/missing.md]]` points to a missing file", result.stderr)

    def test_lint_fails_when_embedded_raw_asset_is_missing(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "concepts" / "key-rotation.md"
        self.replace_in_file(path, "Key rotation tension.", "Key rotation tension.\n\n![[raw/assets/none.png]]")

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("embed references missing asset `[[raw/assets/none.png]]`", result.stderr)

    def test_lint_fails_when_footnote_cites_raw_file_missing_from_sources(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        (root / "raw" / "other.md").write_text("Other raw text.\n", encoding="utf-8")
        path = root / "wiki" / "sources" / "alpha-source.md"
        self.replace_in_file(path, "[^1]: [[raw/alpha.md]], general discussion.", "[^1]: [[raw/alpha.md]], general discussion.\n[^2]: [[raw/other.md]], drift.")

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("footnote cites raw file not listed in `sources`: `[[raw/other.md]]`", result.stderr)

    def test_lint_fails_when_wiki_has_unexpected_file(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        (root / "wiki" / "notes.md").write_text("# Notes\n", encoding="utf-8")

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unexpected file under wiki/", result.stderr)

    def test_lint_fails_when_log_heading_format_is_wrong(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "log.md"
        self.replace_in_file(path, "## [2026-04-08] ingest | Alpha source", "## 2026-04-08 ingest | Alpha source")

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("log heading must use `## [YYYY-MM-DD] operation | title`", result.stderr)

    def test_lint_fails_when_log_entry_is_in_the_future(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "log.md"
        path.write_text(path.read_text(encoding="utf-8") + "\n## [2999-01-01] ingest | Later\n", encoding="utf-8")

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("entry dated 2999-01-01 is in the future", result.stderr)

    def test_lint_fails_when_log_entries_are_out_of_order(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "log.md"
        path.write_text(path.read_text(encoding="utf-8") + "\n## [2026-04-01] ingest | Earlier\n", encoding="utf-8")

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("out of chronological order", result.stderr)

    def test_lint_fails_when_log_file_is_missing(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        (root / "wiki" / "log.md").unlink()

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing required log file", result.stderr)

    def test_lint_fails_when_learning_path_references_missing_page(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "index.md"
        self.replace_in_file(path, "[[research-overview]]\n", "[[research-overview]] -> [[missing-page]]\n")

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("learning path references missing wiki page `[[missing-page]]`", result.stderr)

    def test_lint_reports_unparseable_page_as_violation_not_traceback(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "concepts" / "key-rotation.md"
        self.replace_in_file(path, 'title: "Key Rotation"', 'title: "Key Rotation"\ntitle: "Again"')

        result = self.run_lint(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("wiki/concepts/key-rotation.md\n  - duplicate frontmatter key `title`", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_lint_warns_on_orphan_page_without_failing(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        self.add_concept(root, "lonely-idea", "Lonely Idea")
        self.add_index_entry(root, "Concepts", "- [[lonely-idea]] - Concept with no inbound links.")

        report = self.load_report(self.run_lint(root, "--format", "json"))

        warnings = report["warnings"]
        self.assertTrue(any(w.startswith("wiki/concepts/lonely-idea.md: orphan page") for w in warnings), msg=warnings)

    def test_lint_warns_when_h1_differs_from_title(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "concepts" / "key-rotation.md"
        self.replace_in_file(path, "Key rotation tension.", "Key rotation tension.\n\n# Some Other Title")

        report = self.load_report(self.run_lint(root, "--format", "json"))

        self.assertTrue(
            any("wiki/concepts/key-rotation.md: `# ` heading differs from `title`" in w for w in report["warnings"]),
            msg=report["warnings"],
        )

    def test_lint_warns_on_overlong_sentence(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "concepts" / "key-rotation.md"
        long_sentence = " ".join(["word"] * 70) + "."
        self.replace_in_file(path, "Key rotation tension.", f"Key rotation tension. {long_sentence}")

        report = self.load_report(self.run_lint(root, "--format", "json"))

        self.assertTrue(
            any("sentence has 70 words (over 60)" in w for w in report["warnings"]),
            msg=report["warnings"],
        )

    def test_lint_warns_when_related_pages_duplicate_another_synthesis(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        original = root / "wiki" / "syntheses" / "research-overview.md"
        copy_text = original.read_text(encoding="utf-8").replace('title: "Research Overview"', 'title: "Research Overview Copy"')
        (root / "wiki" / "syntheses" / "research-overview-copy.md").write_text(copy_text, encoding="utf-8")
        self.add_index_entry(root, "Syntheses", "- [[research-overview-copy]] - Copy used to test duplicate related lists.")

        report = self.load_report(self.run_lint(root, "--format", "json"))

        self.assertTrue(any("`## Related pages` duplicates" in w for w in report["warnings"]), msg=report["warnings"])

    def test_lint_warns_on_near_duplicate_normalized_titles(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        self.replace_in_file(root / "wiki" / "entities" / "wireguard.md", 'title: "WireGuard"', 'title: "Wire-Guard!"')
        self.replace_in_file(root / "wiki" / "concepts" / "key-rotation.md", 'title: "Key Rotation"', 'title: "WIRE GUARD"')

        report = self.load_report(self.run_lint(root, "--format", "json"))

        self.assertTrue(any("near-duplicate title" in w for w in report["warnings"]), msg=report["warnings"])

    def test_lint_warns_on_slug_drift_from_title(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        self.replace_in_file(root / "wiki" / "concepts" / "key-rotation.md", 'title: "Key Rotation"', 'title: "Quantum Entanglement Surveys"')

        report = self.load_report(self.run_lint(root, "--format", "json"))

        self.assertTrue(any("wiki/concepts/key-rotation.md: file name differs from title" in w for w in report["warnings"]))

    def test_lint_warns_on_raw_file_without_source_page(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        (root / "raw" / "loose.md").write_text("Loose raw text.\n", encoding="utf-8")

        report = self.load_report(self.run_lint(root, "--format", "json"))

        self.assertTrue(any(w.startswith("raw/loose.md: raw file is not backed by any source page") for w in report["warnings"]))

    def test_lint_default_success_output_is_one_line(self) -> None:
        root = self.copy_fixture("lint_valid_research")

        result = self.run_lint(root)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout, "lint ok: 4 pages, 0 violations\n")

    def test_lint_verbose_prints_json_report_on_success(self) -> None:
        root = self.copy_fixture("lint_valid_research")

        result = self.run_lint(root, "--verbose")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn('"page_count": 4', result.stdout)

    def test_lint_json_format_is_compact(self) -> None:
        root = self.copy_fixture("lint_valid_research")

        result = self.run_lint(root, "--format", "json")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout.count("\n"), 1)
        self.assertNotIn('": ', result.stdout)

    def test_lint_limit_truncates_violation_list_with_count(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "sources" / "alpha-source.md"
        self.replace_in_file(path, 'source_role: "primary"\n', "")
        self.replace_in_file(path, 'source_format: "paper"', 'source_format: "memo"')

        report_result = self.run_lint(root, "--format", "json", "--limit", "1")

        self.assertEqual(report_result.returncode, 1)
        report = json.loads(report_result.stdout)
        self.assertEqual(len(report["violations"]), 1)
        self.assertGreater(report["violation_count"], 1)

    def test_lint_groups_violations_by_file(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "sources" / "alpha-source.md"
        self.replace_in_file(path, 'source_role: "primary"\n', "")
        self.replace_in_file(path, 'source_format: "paper"', 'source_format: "memo"')

        result = self.run_lint(root)

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr.count("wiki/sources/alpha-source.md"), 1)
        self.assertIn("must include `source_role`", result.stderr)

    def test_lint_quiet_prints_nothing_and_sets_exit_status(self) -> None:
        valid = self.copy_fixture("lint_valid_research")
        valid_result = self.run_lint(valid, "--quiet")
        self.assertEqual((valid_result.returncode, valid_result.stdout, valid_result.stderr), (0, "", ""))

        broken = self.copy_fixture("lint_valid_research")
        self.replace_in_file(broken / "wiki" / "sources" / "alpha-source.md", 'source_role: "primary"\n', "")
        broken_result = self.run_lint(broken, "--quiet")
        self.assertEqual((broken_result.returncode, broken_result.stdout, broken_result.stderr), (1, "", ""))

    def test_lint_summary_counts_violation_kinds(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        self.replace_in_file(root / "wiki" / "sources" / "alpha-source.md", 'source_role: "primary"\n', "")

        result = self.run_lint(root, "--summary")

        self.assertEqual(result.returncode, 1)
        self.assertIn("1 source pages must include `…`", result.stderr)
        self.assertNotIn("alpha-source.md", result.stderr)

    def test_lint_output_is_deterministic(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        self.replace_in_file(root / "wiki" / "sources" / "alpha-source.md", 'source_role: "primary"\n', "")

        first = self.run_lint(root)
        second = self.run_lint(root)

        self.assertEqual(first.stderr, second.stderr)

    def test_lint_changed_only_checks_only_git_changed_pages(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        self.add_concept(root, "committed-broken", "Committed Broken")
        path = root / "wiki" / "concepts" / "committed-broken.md"
        self.replace_in_file(path, 'created_at: "2026-04-08"\n', "")
        self.add_index_entry(root, "Concepts", "- [[committed-broken]] - Broken on purpose.")
        git = ["git", "-c", "user.email=test@example.com", "-c", "user.name=test"]
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "add", "wiki", "raw"], cwd=root, check=True)
        subprocess.run([*git, "commit", "-qm", "init"], cwd=root, check=True)
        self.replace_in_file(root / "wiki" / "sources" / "alpha-source.md", 'source_role: "primary"\n', "")

        result = self.run_lint(root, "--changed-only")

        self.assertEqual(result.returncode, 1)
        self.assertIn("must include `source_role`", result.stderr)
        self.assertNotIn("wiki/concepts/committed-broken.md:", result.stderr)

    def test_lint_cache_is_written_under_dot_cache_and_invalidated_on_change(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        self.assertEqual(self.run_lint(root).returncode, 0)
        self.assertTrue((root / ".cache" / "wiki-scripts.json").is_file())

        self.replace_in_file(root / "wiki" / "sources" / "alpha-source.md", 'source_role: "primary"\n', "")
        result = self.run_lint(root)

        self.assertEqual(result.returncode, 1)
        self.assertIn("must include `source_role`", result.stderr)

    def test_lint_no_cache_writes_no_cache_directory(self) -> None:
        root = self.copy_fixture("lint_valid_research")

        self.assertEqual(self.run_lint(root, "--no-cache").returncode, 0)

        self.assertFalse((root / ".cache").exists())

    def test_lint_import_has_no_side_effects(self) -> None:
        code = (
            "import sys; sys.path.insert(0, sys.argv[1]); "
            "import lint, refresh, wiki_schema"
        )
        result = subprocess.run(
            [sys.executable, "-c", code, str(REPO_ROOT / "scripts")],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout, "")


class LintModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import lint

        cls.lint = lint

    def test_find_section_ranges_is_linear_and_bounds_each_level_two_section(self) -> None:
        lines = ["lead", "## A", "x", "### sub", "y", "## B", "z", "", ""]
        headings = [(2, "A", 2), (3, "sub", 4), (2, "B", 6)]

        ranges = self.lint.find_section_ranges(lines, headings)

        self.assertEqual(ranges, {"A": (2, 6), "B": (6, len(lines) + 1)})

    def test_learning_path_findings_warn_when_missing_on_large_wiki(self) -> None:
        errors, warnings = self.lint.learning_path_findings("# Index\n\n## Sources\n", {"a"}, page_count=12)

        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("no `## Learning paths` section", warnings[0])

    def test_learning_path_findings_silent_on_small_wiki(self) -> None:
        errors, warnings = self.lint.learning_path_findings("# Index\n", {"a"}, page_count=4)

        self.assertEqual((errors, warnings), ([], []))

    def test_normalize_title_strips_case_punctuation_and_spaces(self) -> None:
        self.assertEqual(self.lint.normalize_title("Wire-Guard!"), self.lint.normalize_title("WIRE GUARD"))


if __name__ == "__main__":
    unittest.main()

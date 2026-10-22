from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "refresh.py"
FIXTURES_ROOT = REPO_ROOT / "tests" / "fixtures"


class RefreshScriptTests(unittest.TestCase):
    def copy_fixture(self, name: str) -> Path:
        temp_dir = Path(tempfile.mkdtemp(prefix="refresh-fixture-"))
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))
        shutil.copytree(FIXTURES_ROOT / name, temp_dir, dirs_exist_ok=True)
        return temp_dir

    def run_refresh(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--root", str(root), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def run_refresh_json(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return self.run_refresh(root, "--json", *args)

    def load_report(self, result: subprocess.CompletedProcess[str]) -> dict[str, object]:
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        return json.loads(result.stdout)

    def test_bootstrap_initializes_hashes_and_marks_sources_for_refresh(self) -> None:
        root = self.copy_fixture("refresh_valid")

        report = self.load_report(self.run_refresh_json(root))

        self.assertEqual(report["mode"], "changed-only")
        self.assertEqual(
            [item["source_slug"] for item in report["changed_raw_files"]],
            ["alpha-source", "beta-source"],
        )
        self.assertEqual(
            [item["slug"] for item in report["refresh_order"]],
            [
                "alpha-source",
                "beta-source",
                "mesh-vpn",
                "coordination",
                "overview",
                "unrelated",
            ],
        )
        alpha_source = (root / "wiki" / "sources" / "alpha-source.md").read_text(encoding="utf-8")
        self.assertIn("raw_sha256:", alpha_source)
        self.assertIn('source_role: "primary"', alpha_source)
        self.assertIn('source_format: "report"', alpha_source)
        self.assertIn('canonical_url: "https://example.com/alpha"', alpha_source)

    def test_unchanged_raw_files_produce_no_changed_only_targets_after_bootstrap(self) -> None:
        root = self.copy_fixture("refresh_valid")

        first = self.run_refresh_json(root)
        self.load_report(first)

        second_report = self.load_report(self.run_refresh_json(root))
        self.assertEqual(second_report["changed_raw_files"], [])
        self.assertEqual(second_report["refresh_order"], [])
        self.assertEqual(second_report["refresh_roots"], [])

    def test_changed_raw_file_updates_hash_and_reports_transitive_dependents(self) -> None:
        root = self.copy_fixture("refresh_valid")
        self.load_report(self.run_refresh_json(root))

        raw_file = root / "raw" / "alpha.md"
        raw_file.write_text(raw_file.read_text(encoding="utf-8") + "\nNew material.\n", encoding="utf-8")

        report = self.load_report(self.run_refresh_json(root))

        self.assertEqual(
            [item["source_slug"] for item in report["changed_raw_files"]],
            ["alpha-source"],
        )
        self.assertEqual(
            [item["slug"] for item in report["refresh_order"]],
            ["alpha-source", "mesh-vpn", "coordination", "overview"],
        )
        alpha_source = (root / "wiki" / "sources" / "alpha-source.md").read_text(encoding="utf-8")
        self.assertIn(report["changed_raw_files"][0]["new_sha256"], alpha_source)

    def test_refresh_preserves_new_source_metadata_fields(self) -> None:
        root = self.copy_fixture("refresh_valid")

        self.load_report(self.run_refresh_json(root))

        beta_source = (root / "wiki" / "sources" / "beta-source.md").read_text(encoding="utf-8")
        self.assertIn('source_role: "secondary"', beta_source)
        self.assertIn('source_format: "article"', beta_source)

    def test_full_rebuild_reports_all_pages_even_without_drift(self) -> None:
        root = self.copy_fixture("refresh_valid")
        self.load_report(self.run_refresh_json(root))

        report = self.load_report(self.run_refresh_json(root, "--full-rebuild"))

        self.assertEqual(report["mode"], "full-rebuild")
        self.assertEqual(
            [item["slug"] for item in report["refresh_order"]],
            [
                "alpha-source",
                "beta-source",
                "mesh-vpn",
                "coordination",
                "overview",
                "unrelated",
            ],
        )

    def test_refresh_fails_when_non_source_page_has_raw_sha256(self) -> None:
        root = self.copy_fixture("invalid_non_source_hash")

        result = self.run_refresh_json(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("`raw_sha256` is only valid on source pages", result.stderr)

    def test_refresh_fails_when_source_page_has_multiple_raw_refs(self) -> None:
        root = self.copy_fixture("invalid_multiple_raw_refs")

        result = self.run_refresh_json(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exactly one canonical", result.stderr)

    def test_refresh_fails_when_sources_reference_missing_wiki_slug(self) -> None:
        root = self.copy_fixture("invalid_missing_wiki_slug")

        result = self.run_refresh_json(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("references missing wiki page", result.stderr)

    def test_refresh_fails_when_raw_file_is_missing(self) -> None:
        root = self.copy_fixture("refresh_valid")
        (root / "raw" / "alpha.md").unlink()

        result = self.run_refresh_json(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("referenced raw file does not exist", result.stderr)

    def test_refresh_round_trips_non_ascii_source_metadata(self) -> None:
        root = self.copy_fixture("refresh_valid")
        path = root / "wiki" / "sources" / "alpha-source.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace('title: "Alpha Source"', 'title: "Coordenação de Ação — café"'),
            encoding="utf-8",
        )

        self.load_report(self.run_refresh_json(root))

        self.assertIn('title: "Coordenação de Ação — café"', path.read_text(encoding="utf-8"))

    def test_refresh_default_output_is_one_compact_line_per_section(self) -> None:
        root = self.copy_fixture("refresh_valid")

        result = self.run_refresh(root)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertNotIn("{", result.stdout)
        self.assertTrue(result.stdout.startswith("refresh changed-only: 2 changed raw file(s), 6 page(s) to refresh\n"))

    def test_refresh_json_is_compact(self) -> None:
        root = self.copy_fixture("refresh_valid")

        result = self.run_refresh_json(root)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout.count("\n"), 1)
        self.assertNotIn('": ', result.stdout)

    def test_refresh_order_rows_hold_only_slug_and_path_by_default(self) -> None:
        root = self.copy_fixture("refresh_valid")

        report = self.load_report(self.run_refresh_json(root))

        self.assertEqual(set(report["refresh_order"][0]), {"slug", "path"})

    def test_refresh_verbose_adds_reasons_and_dependencies(self) -> None:
        root = self.copy_fixture("refresh_valid")

        report = self.load_report(self.run_refresh_json(root, "--verbose"))

        self.assertIn("reasons", report["refresh_order"][0])
        self.assertIn("depends_on", report["refresh_order"][0])

    def test_refresh_atomic_write_keeps_mode_and_leaves_no_temp_files(self) -> None:
        root = self.copy_fixture("refresh_valid")
        alpha = root / "wiki" / "sources" / "alpha-source.md"
        alpha.chmod(0o644)

        self.load_report(self.run_refresh_json(root))

        self.assertEqual(alpha.stat().st_mode & 0o777, 0o644)
        self.assertEqual([p for p in (root / "wiki").rglob("*") if p.name.endswith(".tmp")], [])

    def test_refresh_fails_on_dependency_cycle(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "concepts" / "key-rotation.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace('  - "[[wireguard]]"\n', '  - "[[wireguard]]"\n  - "[[research-overview]]"\n'),
            encoding="utf-8",
        )

        result = self.run_refresh(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dependency cycle detected", result.stderr)

    def test_write_page_if_changed_is_noop_when_rendering_matches_disk(self) -> None:
        original_path = list(sys.path)
        self.addCleanup(lambda: sys.path.__setitem__(slice(None), original_path))
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import refresh

        root = self.copy_fixture("refresh_valid")
        path = root / "wiki" / "sources" / "alpha-source.md"
        before = path.read_text(encoding="utf-8")
        page = refresh.discover_pages(root)[0]

        self.assertFalse(refresh.write_page_if_changed(page))
        self.assertEqual(path.read_text(encoding="utf-8"), before)


if __name__ == "__main__":
    unittest.main()

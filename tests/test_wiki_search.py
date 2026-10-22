from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "wiki_search.py"
INDEX_SCRIPT_PATH = REPO_ROOT / "scripts" / "wiki_index.py"
FIXTURES_ROOT = REPO_ROOT / "tests" / "fixtures"
BENCHMARK_PATH = FIXTURES_ROOT / "search_benchmark.json"


class WikiSearchTests(unittest.TestCase):
    def copy_fixture(self, name: str = "lint_valid_research") -> Path:
        temp_dir = Path(tempfile.mkdtemp(prefix="search-fixture-"))
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))
        shutil.copytree(FIXTURES_ROOT / name, temp_dir, dirs_exist_ok=True)
        return temp_dir

    def run_search(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--root", str(root), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def build_index(self, root: Path) -> None:
        result = subprocess.run(
            [sys.executable, str(INDEX_SCRIPT_PATH), "--root", str(root)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_search_prints_slug_type_and_summary_only(self) -> None:
        root = self.copy_fixture()

        result = self.run_search(root, "rotation")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout.strip(), "key-rotation [concept] Key rotation summary.")

    def test_search_type_filter_excludes_other_types(self) -> None:
        root = self.copy_fixture()

        result = self.run_search(root, "alpha", "--type", "entity")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertNotIn("alpha-source", result.stdout)

    def test_search_limit_caps_number_of_hits(self) -> None:
        root = self.copy_fixture()

        result = self.run_search(root, "summary", "--limit", "1")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(len([line for line in result.stdout.splitlines() if line]), 1)

    def test_search_snippet_is_bounded_to_200_characters(self) -> None:
        root = self.copy_fixture()
        path = root / "wiki" / "concepts" / "key-rotation.md"
        path.write_text(path.read_text(encoding="utf-8").replace("Key rotation summary.", "rotation " * 60), encoding="utf-8")

        result = self.run_search(root, "rotation")

        line = result.stdout.strip()
        self.assertLessEqual(len(line.split(" [concept] ", 1)[1]), 200)

    def test_query_without_searchable_terms_is_rejected(self) -> None:
        root = self.copy_fixture()

        result = self.run_search(root, "!!!")

        self.assertEqual(result.returncode, 2)
        self.assertIn("no searchable terms", result.stderr)

    def test_backlinks_lists_pages_that_link_to_slug(self) -> None:
        root = self.copy_fixture()

        result = self.run_search(root, "--backlinks", "wireguard")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("alpha-source", result.stdout.split())

    def test_backlinks_unknown_slug_fails(self) -> None:
        root = self.copy_fixture()

        result = self.run_search(root, "--backlinks", "no-such-page")

        self.assertEqual(result.returncode, 1)
        self.assertIn("unknown slug", result.stderr)

    def test_path_finds_shortest_wiki_link_chain(self) -> None:
        root = self.copy_fixture()

        result = self.run_search(root, "--path", "alpha-source", "key-rotation")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout.strip(), "alpha-source -> wireguard -> key-rotation")

    def test_path_reports_when_no_chain_exists(self) -> None:
        root = self.copy_fixture()
        (root / "wiki" / "concepts" / "island.md").write_text(
            '---\ntitle: "Island"\ntype: "concept"\nsources:\n  - "[[raw/alpha.md]]"\n'
            'created_at: "2026-04-08"\nupdated_at: "2026-04-08"\n---\n\nIsolated lead.\n\n'
            "## Summary\nIsolated summary.\n",
            encoding="utf-8",
        )

        result = self.run_search(root, "--path", "island", "alpha-source")

        self.assertEqual(result.returncode, 1)
        self.assertIn("no path", result.stdout)

    def test_search_uses_built_index_and_warns_when_it_goes_stale(self) -> None:
        root = self.copy_fixture()
        self.build_index(root)
        path = root / "wiki" / "concepts" / "key-rotation.md"
        path.write_text(path.read_text(encoding="utf-8").replace("Key rotation summary.", "Rotation changed."), encoding="utf-8")
        stat = path.stat()
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 10_000_000_000))

        result = self.run_search(root, "changed")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("key-rotation [concept] Rotation changed.", result.stdout)
        self.assertIn("index is stale", result.stderr)

    def test_wiki_works_without_any_index_and_creates_none(self) -> None:
        root = self.copy_fixture()

        result = self.run_search(root, "rotation")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("key-rotation", result.stdout)
        self.assertFalse((root / "wiki" / ".index.json").exists())
        self.assertFalse((root / "wiki" / ".index.sqlite").exists())

    def test_rebuild_flag_writes_fresh_index(self) -> None:
        root = self.copy_fixture()

        result = self.run_search(root, "rotation", "--rebuild")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue((root / "wiki" / ".index.json").is_file())
        self.assertTrue((root / "wiki" / ".index.sqlite").is_file())

    def test_rebuild_aborts_without_writing_when_a_page_is_unparseable(self) -> None:
        root = self.copy_fixture()
        (root / "wiki" / "concepts" / "broken.md").write_text("no frontmatter here\n", encoding="utf-8")

        result = self.run_search(root, "rotation", "--rebuild")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("broken.md", result.stderr)
        self.assertFalse((root / "wiki" / ".index.json").exists())
        self.assertFalse((root / "wiki" / ".index.sqlite").exists())

    def test_benchmark_fixture_has_ten_questions_with_expected_slugs(self) -> None:
        payload = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))

        questions = payload["questions"]
        self.assertEqual(len(questions), 10)
        for item in questions:
            self.assertTrue(item["question"].strip())
            self.assertTrue(item["expected"])

    def test_benchmark_rejects_malformed_questions_with_exit_two(self) -> None:
        root = self.copy_fixture()
        benchmark = root / "benchmark.json"
        benchmark.write_text(json.dumps({"questions": [{"question": "rotation"}]}), encoding="utf-8")

        result = self.run_search(root, "--benchmark", str(benchmark))

        self.assertEqual(result.returncode, 2)
        self.assertIn("benchmark", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_benchmark_scores_hits_at_limit(self) -> None:
        root = self.copy_fixture()
        benchmark = root / "benchmark.json"
        benchmark.write_text(
            json.dumps(
                {
                    "questions": [
                        {"question": "rotation", "expected": ["key-rotation"]},
                        {"question": "overview", "expected": ["alpha-source"]},
                    ]
                }
            ),
            encoding="utf-8",
        )

        result = self.run_search(root, "--benchmark", str(benchmark), "--limit", "5")

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("hit@5: 1/2", result.stdout)


if __name__ == "__main__":
    unittest.main()

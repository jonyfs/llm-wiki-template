from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "wiki_index.py"
FIXTURES_ROOT = REPO_ROOT / "tests" / "fixtures"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import wiki_index  # noqa: E402
import wiki_schema  # noqa: E402


class WikiIndexTests(unittest.TestCase):
    def copy_fixture(self, name: str) -> Path:
        temp_dir = Path(tempfile.mkdtemp(prefix="index-fixture-"))
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))
        shutil.copytree(FIXTURES_ROOT / name, temp_dir, dirs_exist_ok=True)
        return temp_dir

    def run_index(self, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--root", str(root)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_index_writes_json_graph_and_fts_artifacts_under_wiki_root(self) -> None:
        root = self.copy_fixture("lint_valid_research")

        result = self.run_index(root)

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("index ok: 4 pages", result.stdout)
        for name in (".index.json", ".graph.json", ".index.sqlite"):
            self.assertTrue((root / "wiki" / name).is_file(), msg=name)

        payload = json.loads((root / "wiki" / ".index.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(page["slug"] for page in payload["pages"]), [
            "alpha-source",
            "key-rotation",
            "research-overview",
            "wireguard",
        ])
        connection = sqlite3.connect(root / "wiki" / ".index.sqlite")
        self.addCleanup(connection.close)
        tables = {row[0] for row in connection.execute("select name from sqlite_master")}
        self.assertIn("pages_fts", tables)

    def test_graph_records_wiki_links_but_not_raw_links(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        data = wiki_index.build_index(root).edges

        self.assertIn("wireguard", data["alpha-source"])
        self.assertIn("key-rotation", data["wireguard"])
        self.assertNotIn("raw", "".join(data["alpha-source"]))
        self.assertNotIn("alpha-source", data["alpha-source"])

    def test_summary_is_first_line_under_type_heading_and_capped_at_200_chars(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        long_line = "word " * 80
        path = root / "wiki" / "concepts" / "key-rotation.md"
        path.write_text(path.read_text(encoding="utf-8").replace("Key rotation summary.", long_line.strip()), encoding="utf-8")

        records = {record["slug"]: record for record in wiki_index.build_index(root).records}

        self.assertEqual(records["alpha-source"]["summary"], "Alpha source summary.")
        self.assertLessEqual(len(records["key-rotation"]["summary"]), 200)
        self.assertTrue(records["key-rotation"]["summary"].endswith("..."))

    def test_fresh_index_loads_and_edited_page_marks_it_stale(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        wiki_index.write_index(root, wiki_index.build_index(root))
        self.assertIsNotNone(wiki_index.load_index(root))

        path = root / "wiki" / "entities" / "wireguard.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nExtra line.\n", encoding="utf-8")
        stat = path.stat()
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 10_000_000_000))

        self.assertIsNone(wiki_index.load_index(root))

    def test_edit_that_preserves_mtime_and_size_still_marks_index_stale(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        wiki_index.write_index(root, wiki_index.build_index(root))
        path = root / "wiki" / "entities" / "wireguard.md"
        stat = path.stat()
        text = path.read_text(encoding="utf-8")
        replaced = text.replace("WireGuard", "WireGuarX", 1)
        self.assertEqual(len(replaced), len(text))
        path.write_text(replaced, encoding="utf-8")
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))

        self.assertIsNone(wiki_index.load_index(root))

    def test_index_is_not_a_content_page_and_is_not_listed_as_one(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        self.run_index(root)

        slugs = set(wiki_schema.iter_page_slugs(root))

        self.assertNotIn(".index", slugs)
        self.assertEqual(list((root / "wiki" / "sources").glob(".*")), [])

    def test_index_never_writes_under_raw(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        before = sorted(path.relative_to(root).as_posix() for path in (root / "raw").rglob("*"))

        self.run_index(root)

        after = sorted(path.relative_to(root).as_posix() for path in (root / "raw").rglob("*"))
        self.assertEqual(before, after)

    def test_index_refuses_to_write_when_a_page_fails_to_parse(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        (root / "wiki" / "concepts" / "broken.md").write_text("no frontmatter\n", encoding="utf-8")

        result = self.run_index(root)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing YAML frontmatter", result.stderr)
        self.assertFalse((root / "wiki" / ".index.json").exists())

    def test_index_md_summaries_parses_catalog_entries_only(self) -> None:
        root = self.copy_fixture("lint_valid_research")

        catalog = wiki_index.index_md_summaries(root)

        self.assertEqual(set(catalog), {"alpha-source", "wireguard", "key-rotation", "research-overview"})
        self.assertEqual(
            catalog["alpha-source"], "Source page for the alpha research artifact and its main claims."
        )

    def test_from_index_sources_summaries_from_catalog_but_keeps_record_keys(self) -> None:
        root = self.copy_fixture("lint_valid_research")

        records = {record["slug"]: record for record in wiki_index.build_index(root, from_index=True).records}

        self.assertEqual(
            records["key-rotation"]["summary"], "Concept page for key rotation as a recurring mechanism and concern."
        )
        self.assertEqual(records["key-rotation"]["type"], "concept")
        self.assertEqual(sorted(records["key-rotation"]), ["path", "slug", "summary", "title", "type"])

    def test_from_index_falls_back_to_page_summary_when_entry_missing(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        path = root / "wiki" / "index.md"
        path.write_text(
            "\n".join(line for line in path.read_text(encoding="utf-8").splitlines() if "[[key-rotation]]" not in line)
            + "\n",
            encoding="utf-8",
        )

        records = {record["slug"]: record for record in wiki_index.build_index(root, from_index=True).records}

        self.assertEqual(records["key-rotation"]["summary"], "Key rotation summary.")

    def test_cli_from_index_writes_catalog_summaries_with_compact_json(self) -> None:
        root = self.copy_fixture("lint_valid_research")

        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--root", str(root), "--from-index"],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        raw = (root / "wiki" / ".index.json").read_text(encoding="utf-8")
        self.assertTrue(raw.startswith('{"fingerprint":'), msg=raw[:40])
        payload = json.loads(raw)
        by_slug = {page["slug"]: page for page in payload["pages"]}
        self.assertEqual(
            by_slug["wireguard"]["summary"], "Entity page for WireGuard as a stable protocol object in the corpus."
        )

    def test_index_md_edit_marks_built_index_stale(self) -> None:
        root = self.copy_fixture("lint_valid_research")
        wiki_index.write_index(root, wiki_index.build_index(root))
        self.assertIsNotNone(wiki_index.load_index(root))

        path = root / "wiki" / "index.md"
        path.write_text(path.read_text(encoding="utf-8").replace("main claims.", "main claims, revised."), encoding="utf-8")

        self.assertIsNone(wiki_index.load_index(root))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import inspect
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_ROOT = REPO_ROOT / "tests" / "fixtures"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import wiki_schema  # noqa: E402
from wiki_schema import MarkdownPage, WikiSchemaError  # noqa: E402


ROUND_TRIP_TEXT = """---
title: "Coordenação de Ação — café \\"quoted\\" back\\\\slash"
type: "source"
source_role: "primary"
source_format: "paper"
authors:
  - "Ação Autora"
published_at: 2026-04-08
canonical_url: "https://example.com/alpha"
sources:
  - "[[raw/alpha.md]]"
raw_sha256: "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
created_at: "2026-04-08"
updated_at: "2026-04-08"
---

Lead text for the round-trip page.

## Summary
Summary text.
"""


def page_from_text(text: str, label: str = "wiki/sources/round-trip.md") -> MarkdownPage:
    frontmatter, raw, body = wiki_schema.parse_frontmatter_with_raw(text, label)
    return MarkdownPage(
        path=Path(label),
        rel_path=label,
        slug="round-trip",
        page_type=str(frontmatter.get("type", "")),
        frontmatter=frontmatter,
        body=body,
        raw_frontmatter=raw,
    )


class ParseScalarTests(unittest.TestCase):
    def test_non_ascii_value_survives_quote_and_parse(self) -> None:
        value = "Coordenação de Ação — café"

        parsed = wiki_schema.parse_scalar(wiki_schema.quote_scalar(value))

        self.assertEqual(parsed, value)

    def test_only_backslash_and_quote_escapes_are_unescaped(self) -> None:
        self.assertEqual(wiki_schema.parse_scalar(r'"a \"b\" c\\d"'), 'a "b" c\\d')
        self.assertEqual(wiki_schema.parse_scalar(r'"tab\tx"'), r"tab\tx")

    def test_unescaped_quote_inside_quoted_scalar_is_rejected(self) -> None:
        with self.assertRaisesRegex(WikiSchemaError, "unescaped"):
            wiki_schema.parse_scalar('"a "b" c"')


class RoundTripTests(unittest.TestCase):
    def test_round_trip_is_byte_equal_for_representative_frontmatter(self) -> None:
        page = page_from_text(ROUND_TRIP_TEXT)

        self.assertEqual(wiki_schema.serialize_page(page), ROUND_TRIP_TEXT)

    def test_round_trip_keeps_original_key_order_and_unquoted_values(self) -> None:
        text = (
            "---\n"
            "updated_at: 2026-04-08\n"
            "created_at: 2026-04-08\n"
            "title: \"Odd Order\"\n"
            "type: \"concept\"\n"
            "sources:\n"
            "  - \"[[wireguard]]\"\n"
            "---\n\n"
            "Lead.\n"
        )
        page = page_from_text(text, label="wiki/concepts/odd-order.md")

        self.assertEqual(wiki_schema.serialize_page(page), text)

    def test_set_raw_sha256_inserts_key_before_created_at(self) -> None:
        text = ROUND_TRIP_TEXT.replace(
            'raw_sha256: "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"\n', ""
        )
        page = page_from_text(text)

        wiki_schema.set_raw_sha256(page, "f" * 64)
        rendered = wiki_schema.serialize_page(page)

        self.assertLess(rendered.index("raw_sha256:"), rendered.index("created_at:"))
        self.assertIn(f'raw_sha256: "{"f" * 64}"', rendered)

    def test_duplicate_frontmatter_key_is_rejected(self) -> None:
        text = '---\ntitle: "A"\ntitle: "B"\ntype: "concept"\n---\n\nLead.\n'

        with self.assertRaisesRegex(WikiSchemaError, "duplicate frontmatter key `title`"):
            wiki_schema.parse_frontmatter_with_raw(text, "wiki/concepts/dup.md")

    def test_parse_errors_use_relative_label_not_absolute_path(self) -> None:
        with self.assertRaisesRegex(WikiSchemaError, "^wiki/concepts/x.md: missing YAML frontmatter"):
            wiki_schema.parse_frontmatter_with_raw("no frontmatter\n", "wiki/concepts/x.md")


class RawTargetContainmentTests(unittest.TestCase):
    def test_raw_target_rejects_path_escaping_raw_directory(self) -> None:
        self.assertIsNone(wiki_schema.raw_target("[[raw/../../../../etc/hosts]]"))
        self.assertIsNone(wiki_schema.raw_target("[[raw/../wiki/index.md]]"))

    def test_raw_target_accepts_nested_file_inside_raw(self) -> None:
        self.assertEqual(wiki_schema.raw_target("[[raw/assets/a.png]]"), "raw/assets/a.png")


class CanonicalUrlNormalizationTests(unittest.TestCase):
    def test_utm_parameters_are_stripped_and_other_parameters_kept(self) -> None:
        url = "https://example.com/a?id=7&utm_source=news&UTM_medium=x&page=2&utm_campaign=y"
        self.assertEqual(wiki_schema.normalize_canonical_url(url), "https://example.com/a?id=7&page=2")

    def test_url_without_remaining_query_drops_question_mark(self) -> None:
        url = "https://example.com/a?utm_source=news"
        self.assertEqual(wiki_schema.normalize_canonical_url(url), "https://example.com/a")

    def test_url_without_tracking_parameters_is_unchanged(self) -> None:
        url = "https://example.com/a?id=7#top"
        self.assertEqual(wiki_schema.normalize_canonical_url(url), url)

    def test_empty_query_parts_are_not_treated_as_tracking(self) -> None:
        url = "https://example.com/a?x=1&"
        self.assertEqual(wiki_schema.normalize_canonical_url(url), url)


class ValidationHelperTests(unittest.TestCase):
    def test_date_problem_distinguishes_format_from_calendar_validity(self) -> None:
        self.assertIsNone(wiki_schema.date_problem("2026-02-28"))
        self.assertIn("YYYY-MM-DD", wiki_schema.date_problem("2026-4-8"))
        self.assertIn("real calendar date", wiki_schema.date_problem("2026-02-30"))

    def test_canonical_url_problem_rejects_credentials_and_missing_host(self) -> None:
        self.assertIsNone(wiki_schema.canonical_url_problem("https://example.com/alpha"))
        self.assertIn("credentials", wiki_schema.canonical_url_problem("https://user:pw@example.com/a"))
        self.assertIn("host", wiki_schema.canonical_url_problem("https://:80/a"))
        self.assertIn("absolute", wiki_schema.canonical_url_problem("example.com/a"))

    def test_find_dependency_cycle_reports_cycle_and_ignores_self_loops(self) -> None:
        cycle = wiki_schema.find_dependency_cycle({"a": {"b"}, "b": {"a"}, "c": set()})
        self.assertIsNotNone(cycle)
        self.assertEqual(set(cycle), {"a", "b"})

        self.assertIsNone(wiki_schema.find_dependency_cycle({"a": {"b"}, "b": set()}))
        self.assertIsNone(wiki_schema.find_dependency_cycle({"a": {"a"}}))

    def test_build_slug_map_reports_duplicates_without_raising_when_collecting(self) -> None:
        first = page_from_text(ROUND_TRIP_TEXT, label="wiki/sources/dup.md")
        first.slug = "dup"
        second = page_from_text(ROUND_TRIP_TEXT, label="wiki/concepts/dup.md")
        second.slug = "dup"
        errors: list[str] = []

        slug_map = wiki_schema.build_slug_map([first, second], errors)

        self.assertEqual(set(slug_map), {"dup"})
        self.assertEqual(len(errors), 1)
        self.assertIn("duplicate slug `dup`", errors[0])
        with self.assertRaisesRegex(WikiSchemaError, "duplicate slug"):
            wiki_schema.build_slug_map([first, second])


class PageLoadingTests(unittest.TestCase):
    def test_pages_are_slotted_dataclasses(self) -> None:
        page = page_from_text(ROUND_TRIP_TEXT)

        self.assertFalse(hasattr(page, "__dict__"))
        with self.assertRaises(AttributeError):
            page.unexpected_attribute = 1  # type: ignore[attr-defined]

    def test_discover_pages_parses_each_page_once(self) -> None:
        root = FIXTURES_ROOT / "lint_valid_research"
        original = wiki_schema.parse_frontmatter_with_raw

        with mock.patch.object(wiki_schema, "parse_frontmatter_with_raw", wraps=original) as spy:
            pages = wiki_schema.discover_pages(root)

        self.assertEqual(len(pages), 4)
        self.assertEqual(spy.call_count, 4)

    def test_iter_page_slugs_is_lazy_generator(self) -> None:
        result = wiki_schema.iter_page_slugs(FIXTURES_ROOT / "lint_valid_research")

        self.assertTrue(inspect.isgenerator(result))
        self.assertIn("wireguard", set(result))


class AtomicWriteTests(unittest.TestCase):
    def test_atomic_write_replaces_content_and_keeps_mode(self) -> None:
        temp_dir = Path(tempfile.mkdtemp(prefix="atomic-"))
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))
        target = temp_dir / "page.md"
        target.write_text("old\n", encoding="utf-8")
        target.chmod(0o644)

        wiki_schema.atomic_write_text(target, "new text é\n")

        self.assertEqual(target.read_text(encoding="utf-8"), "new text é\n")
        self.assertEqual(target.stat().st_mode & 0o777, 0o644)
        self.assertEqual(sorted(p.name for p in temp_dir.iterdir()), ["page.md"])


class ScriptCacheTests(unittest.TestCase):
    def make_root(self) -> Path:
        temp_dir = Path(tempfile.mkdtemp(prefix="cache-"))
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))
        return temp_dir

    def test_digest_cache_is_saved_under_dot_cache(self) -> None:
        root = self.make_root()
        (root / "raw").mkdir()
        (root / "raw" / "a.md").write_text("alpha\n", encoding="utf-8")

        cache = wiki_schema.ScriptCache(root)
        digest = cache.digest(root / "raw" / "a.md", "raw/a.md")
        cache.save()

        saved = json.loads((root / ".cache" / "wiki-scripts.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["digests"]["raw/a.md"]["sha256"], digest)

    def test_digest_is_recomputed_when_file_changes(self) -> None:
        root = self.make_root()
        (root / "raw").mkdir()
        raw_file = root / "raw" / "a.md"
        raw_file.write_text("alpha\n", encoding="utf-8")
        first = wiki_schema.ScriptCache(root)
        first_digest = first.digest(raw_file, "raw/a.md")
        first.save()

        raw_file.write_text("alpha, now longer\n", encoding="utf-8")
        second = wiki_schema.ScriptCache(root)

        self.assertNotEqual(second.digest(raw_file, "raw/a.md"), first_digest)
        self.assertEqual(second.digest(raw_file, "raw/a.md"), wiki_schema.sha256_file(raw_file))

    def test_disabled_cache_writes_nothing(self) -> None:
        root = self.make_root()
        (root / "raw").mkdir()
        raw_file = root / "raw" / "a.md"
        raw_file.write_text("alpha\n", encoding="utf-8")

        cache = wiki_schema.ScriptCache(root, enabled=False)
        cache.digest(raw_file, "raw/a.md")
        cache.save()

        self.assertFalse((root / ".cache").exists())


if __name__ == "__main__":
    unittest.main()

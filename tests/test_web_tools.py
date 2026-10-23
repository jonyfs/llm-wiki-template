from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import web_tools  # noqa: E402


PAGE = """<html><head><style>p {color: red}</style><script>var x = 1;</script></head>
<body>
<nav><a href="/">Home</a> <a href="/about">About</a></nav>
<div class="cookie-banner">Accept cookies</div>
<article>
<h1>Coordination Notes</h1>
<p>First   paragraph about   WireGuard.</p>
<h2>Details</h2>
<p>Second paragraph.</p>
<aside>Related links</aside>
</article>
<footer>Copyright 2026</footer>
</body></html>"""


class HtmlToMarkdownTests(unittest.TestCase):
    def test_keeps_headings_and_paragraph_text_in_order(self) -> None:
        text = web_tools.html_to_markdown(PAGE)

        self.assertIn("# Coordination Notes", text)
        self.assertIn("## Details", text)
        self.assertIn("First paragraph about WireGuard.", text)
        self.assertLess(text.index("# Coordination Notes"), text.index("## Details"))

    def test_strips_navigation_scripts_styles_ads_and_footer(self) -> None:
        text = web_tools.html_to_markdown(PAGE)

        for boilerplate in ("var x", "color: red", "Home", "Accept cookies", "Related links", "Copyright"):
            self.assertNotIn(boilerplate, text)

    def test_unmatched_end_tag_does_not_reopen_skipped_content(self) -> None:
        text = web_tools.html_to_markdown("<header><em>Menu</i> more</em></header><p>Body</p>")

        self.assertNotIn("more", text)
        self.assertIn("Body", text)

    def test_output_has_no_runs_of_blank_lines(self) -> None:
        text = web_tools.html_to_markdown(PAGE)

        self.assertNotIn("\n\n\n", text)


class RetryTests(unittest.TestCase):
    def test_rate_limited_fetch_is_retried_with_backoff_then_succeeds(self) -> None:
        calls: list[str] = []
        delays: list[float] = []

        def fake_fetch(url: str) -> str:
            calls.append(url)
            if len(calls) < 3:
                raise web_tools.RateLimitError()
            return "<html></html>"

        result = web_tools.fetch_with_retry(fake_fetch, "https://example.com/a", base_delay=1.0, sleep=delays.append)

        self.assertEqual(result.html, "<html></html>")
        self.assertEqual(len(calls), 3)
        self.assertEqual(delays, [1.0, 2.0])

    def test_retry_after_hint_overrides_backoff(self) -> None:
        delays: list[float] = []
        state = {"calls": 0}

        def fake_fetch(url: str) -> str:
            state["calls"] += 1
            if state["calls"] == 1:
                raise web_tools.RateLimitError(retry_after=7.5)
            return "ok"

        web_tools.fetch_with_retry(fake_fetch, "https://example.com/a", sleep=delays.append)

        self.assertEqual(delays, [7.5])

    def test_exhausted_retries_raise_the_last_rate_limit_error(self) -> None:
        def always_limited(url: str) -> str:
            raise web_tools.RateLimitError()

        with self.assertRaises(web_tools.RateLimitError):
            web_tools.fetch_with_retry(always_limited, "https://example.com/a", attempts=2, sleep=lambda _: None)

    def test_other_errors_are_not_retried(self) -> None:
        calls: list[str] = []

        def broken(url: str) -> str:
            calls.append(url)
            raise OSError("boom")

        with self.assertRaises(OSError):
            web_tools.fetch_with_retry(broken, "https://example.com/a", sleep=lambda _: None)
        self.assertEqual(len(calls), 1)


class FetchResultTests(unittest.TestCase):
    def test_plain_string_return_is_stamped_with_utc_fetch_date(self) -> None:
        result = web_tools.fetch_with_retry(lambda url: "<p>hi</p>", "https://example.com/a", sleep=lambda _: None)

        self.assertIsInstance(result, web_tools.FetchResult)
        self.assertEqual(result.html, "<p>hi</p>")
        self.assertIsNone(result.http_status)
        self.assertEqual(result.fetched_at, web_tools.utc_fetch_date())

    def test_fetch_result_status_and_date_pass_through_unchanged(self) -> None:
        sent = web_tools.FetchResult(html="ok", http_status=418, fetched_at="2026-01-02")

        result = web_tools.fetch_with_retry(lambda url: sent, "https://example.com/a", sleep=lambda _: None)

        self.assertEqual(result, sent)

    def test_fetch_result_without_date_gets_stamped(self) -> None:
        result = web_tools.fetch_with_retry(lambda url: web_tools.FetchResult(html="ok", http_status=200), "https://example.com/a", sleep=lambda _: None)

        self.assertEqual(result.http_status, 200)
        self.assertEqual(result.fetched_at, web_tools.utc_fetch_date())

    def test_utc_fetch_date_matches_lint_fetched_at_format(self) -> None:
        self.assertRegex(web_tools.utc_fetch_date(), r"^\d{4}-\d{2}-\d{2}$")


class CacheTests(unittest.TestCase):
    def make_root(self) -> Path:
        root = Path(tempfile.mkdtemp(prefix="web-cache-"))
        self.addCleanup(lambda: shutil.rmtree(root, ignore_errors=True))
        (root / "raw").mkdir()
        return root

    def test_cache_path_is_under_dot_cache_and_never_under_raw(self) -> None:
        root = self.make_root()

        path = web_tools.web_cache_path(root, "https://example.com/a")

        self.assertEqual(path.parent, root / ".cache" / "web")
        self.assertNotIn("raw", path.relative_to(root).parts)

    def test_identical_url_is_fetched_once_and_then_read_from_cache(self) -> None:
        root = self.make_root()
        calls: list[str] = []

        def fake_fetch(url: str) -> str:
            calls.append(url)
            return "<p>cached body</p>"

        first = web_tools.cached_fetch(root, "https://example.com/a", fake_fetch)
        second = web_tools.cached_fetch(root, "https://example.com/a", fake_fetch)

        self.assertEqual(first, second)
        self.assertEqual(calls, ["https://example.com/a"])

    def test_cache_hit_replays_stored_status_and_original_fetch_date(self) -> None:
        root = self.make_root()
        calls: list[str] = []

        def fake_fetch(url: str) -> web_tools.FetchResult:
            calls.append(url)
            return web_tools.FetchResult(html="<p>body</p>", http_status=429, fetched_at="2026-03-04")

        first = web_tools.cached_fetch(root, "https://example.com/a", fake_fetch)
        second = web_tools.cached_fetch(root, "https://example.com/a", fake_fetch)

        self.assertEqual(first.http_status, 429)
        self.assertEqual(web_tools.web_cache_meta_path(root, "https://example.com/a").parent, root / ".cache" / "web")
        self.assertEqual(second.http_status, 429)
        self.assertEqual(second.fetched_at, "2026-03-04")
        self.assertEqual(calls, ["https://example.com/a"])

    def test_cache_hit_without_sidecar_yields_unknown_provenance(self) -> None:
        root = self.make_root()
        web_tools.web_cache_path(root, "https://example.com/a").parent.mkdir(parents=True, exist_ok=True)
        web_tools.web_cache_path(root, "https://example.com/a").write_text("<p>legacy</p>", encoding="utf-8")

        result = web_tools.cached_fetch(root, "https://example.com/a", lambda url: "unused")

        self.assertEqual(result.html, "<p>legacy</p>")
        self.assertIsNone(result.http_status)
        self.assertIsNone(result.fetched_at)

    def test_raw_directory_is_left_empty_by_caching(self) -> None:
        root = self.make_root()

        web_tools.cached_fetch(root, "https://example.com/a", lambda url: "<p>x</p>")

        self.assertEqual(list((root / "raw").iterdir()), [])


if __name__ == "__main__":
    unittest.main()

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

        self.assertEqual(result, "<html></html>")
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

    def test_raw_directory_is_left_empty_by_caching(self) -> None:
        root = self.make_root()

        web_tools.cached_fetch(root, "https://example.com/a", lambda url: "<p>x</p>")

        self.assertEqual(list((root / "raw").iterdir()), [])


if __name__ == "__main__":
    unittest.main()

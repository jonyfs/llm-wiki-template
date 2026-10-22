"""Offline helpers for web material: HTML clean-up, rate-limit-aware retry, and a `.cache/` fetch cache.

Nothing here performs network access. Callers inject `fetch` (a callable taking a URL and returning
HTML text), so the retry and cache logic can be tested with fakes. Cleaned output is meant to be
written into raw/ only when the operator explicitly asks to add that material (see AGENTS.md).
"""
from __future__ import annotations

import hashlib
import re
import time
from collections.abc import Callable
from html.parser import HTMLParser
from pathlib import Path

from wiki_schema import atomic_write_text


SKIPPED_TAGS = frozenset({"script", "style", "noscript", "template", "svg", "iframe", "nav", "header", "footer", "aside", "form"})
VOID_TAGS = frozenset({"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "wbr"})
BOILERPLATE_ATTR_RE = re.compile(r"(^|[\s_-])(ad|ads|advert|banner|cookie|sidebar|share|social|promo)([\s_-]|$)", re.I)
HEADING_MARKS = {"h1": "#", "h2": "##", "h3": "###", "h4": "####", "h5": "#####", "h6": "######"}
BLOCK_TAGS = frozenset({"p", "div", "li", "tr", "section", "article", "main", "blockquote"})
BLANK_RUN_RE = re.compile(r"\n{3,}")
SPACE_RUN_RE = re.compile(r"[ \t]+")
RETRY_ATTEMPTS = 3
RETRY_BASE_DELAY = 1.0


class RateLimitError(Exception):
    """Raised by a fetch callable when the remote side answers with a rate limit."""

    def __init__(self, retry_after: float | None = None) -> None:
        super().__init__("rate limited")
        self.retry_after = retry_after


class _MarkdownExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.stack: list[tuple[str, bool]] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in VOID_TAGS:
            if tag == "br" and not self.skip_depth:
                self.parts.append("\n")
            return
        attributes = " ".join(value or "" for name, value in attrs if name in {"class", "id"})
        skip = tag in SKIPPED_TAGS or BOILERPLATE_ATTR_RE.search(attributes) is not None
        self.stack.append((tag, skip))
        if skip:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag in HEADING_MARKS:
            self.parts.append(f"\n\n{HEADING_MARKS[tag]} ")
        elif tag in BLOCK_TAGS:
            self.parts.append("\n\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID_TAGS or tag not in {open_tag for open_tag, _ in self.stack}:
            return
        while self.stack:
            open_tag, skip = self.stack.pop()
            if skip:
                self.skip_depth -= 1
            if open_tag == tag:
                break
        if self.skip_depth:
            return
        if tag in HEADING_MARKS or tag in BLOCK_TAGS:
            self.parts.append("\n\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)


def html_to_markdown(html: str) -> str:
    """Strip scripts, styles, navigation, footers, asides, forms, and ad-like blocks; keep headings and text."""
    extractor = _MarkdownExtractor()
    extractor.feed(html)
    extractor.close()
    lines = [SPACE_RUN_RE.sub(" ", line).strip() for line in "".join(extractor.parts).split("\n")]
    return BLANK_RUN_RE.sub("\n\n", "\n".join(lines)).strip() + "\n"


def fetch_with_retry(
    fetch: Callable[[str], str],
    url: str,
    attempts: int = RETRY_ATTEMPTS,
    base_delay: float = RETRY_BASE_DELAY,
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    """Call `fetch(url)`, retrying only on RateLimitError with exponential backoff or the server's hint."""
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    for attempt in range(attempts):
        try:
            return fetch(url)
        except RateLimitError as exc:
            if attempt == attempts - 1:
                raise
            delay = exc.retry_after if exc.retry_after is not None else base_delay * (2**attempt)
            sleep(delay)
    raise AssertionError("unreachable")


def web_cache_path(root: Path, url: str) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return root / ".cache" / "web" / f"{digest}.html"


def cached_fetch(
    root: Path,
    url: str,
    fetch: Callable[[str], str],
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    """Return cached HTML for `url`, fetching (with retry) and caching it on the first call."""
    path = web_cache_path(root, url)
    if path.is_file():
        return path.read_text(encoding="utf-8")
    text = fetch_with_retry(fetch, url, sleep=sleep)
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(path, text)
    return text

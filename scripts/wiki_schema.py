from __future__ import annotations

import contextlib
import copy
import hashlib
import json
import os
import re
import stat
import tempfile
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path, PurePosixPath
from typing import NamedTuple
from urllib.parse import urlparse, urlunparse


CONTENT_DIRS = ("sources", "entities", "concepts", "syntheses")
REQUIRED_WIKI_FILES = ("index.md", "log.md")
PAGE_TYPE_DIRS = {
    "source": "sources",
    "entity": "entities",
    "concept": "concepts",
    "synthesis": "syntheses",
}
SOURCE_ROLE_VALUES = ("primary", "secondary", "reference", "operational", "informal")
SOURCE_FORMAT_VALUES = (
    "paper",
    "article",
    "book",
    "report",
    "spec",
    "documentation",
    "dataset",
    "benchmark",
    "transcript",
    "notes",
    "other",
)
PAGE_HEADINGS = {
    "source": [
        "Summary",
        "Key takeaways",
        "Evidence or notable details",
        "Related pages",
        "Open questions",
    ],
    "entity": [
        "Summary",
        "Role or significance",
        "Current understanding",
        "Related pages",
        "Open questions or tensions",
    ],
    "concept": [
        "Summary",
        "Why it matters",
        "Current understanding",
        "Related pages",
        "Open questions or tensions",
    ],
    "synthesis": [
        "Question or thesis",
        "Synthesized answer",
        "Evidence base",
        "Unresolved points",
        "Related pages",
    ],
}
SYNTHESIS_EVIDENCE_SUBHEADINGS = (
    "Supports",
    "Conflicts or tensions",
    "Gaps or missing evidence",
)
REQUIRED_FRONTMATTER_KEYS = {
    "source": ("title", "type", "source_role", "sources", "created_at", "updated_at"),
    "entity": ("title", "type", "sources", "created_at", "updated_at"),
    "concept": ("title", "type", "sources", "created_at", "updated_at"),
    "synthesis": ("title", "type", "sources", "created_at", "updated_at"),
}
WIKILINK_RE = re.compile(r"^\[\[([^\]]+)\]\]$")
WIKILINK_ANY_RE = re.compile(r"(!?)\[\[([^\]]+)\]\]")
KEY_RE = re.compile(r"^([A-Za-z0-9_]+):(?:\s+(.*))?$")
LIST_RE = re.compile(r"^\s*-\s+(.*)$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RAW_SHA256_RE = re.compile(r"[0-9a-f]{64}")
HEADING_RE = re.compile(r"^(#{2,6})\s+(.+?)\s*$")
FOOTNOTE_DEF_RE = re.compile(r"^\[\^[^\]]+\]:")
CLAIM_LED_EVIDENCE_RE = re.compile(r"^\s*-\s+[^:\n]+:\s+.*\[\[[^\]]+\]\].*$")
CACHE_VERSION = 1
CACHE_DIR_NAME = ".cache"
CACHE_FILE_NAME = "wiki-scripts.json"


class WikiSchemaError(Exception):
    """Raised when the wiki does not satisfy the schema contract."""


class BodyLink(NamedTuple):
    line_no: int
    embed: bool
    target: str
    footnote: bool


@dataclass(slots=True)
class MarkdownPage:
    path: Path
    rel_path: str
    slug: str
    page_type: str
    frontmatter: dict[str, object]
    body: str
    raw_frontmatter: dict[str, object] = field(default_factory=dict)
    source_text: str | None = None


@dataclass(slots=True)
class Heading:
    level: int
    title: str
    line_no: int


def parse_scalar(raw: str) -> str:
    value = raw.strip()
    if not value:
        return ""
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return unescape_double_quoted(value[1:-1])
    return value


def unescape_double_quoted(inner: str) -> str:
    """Unescape only `\\\\` and `\\"`; any other backslash is kept literally."""
    if "\\" not in inner and '"' not in inner:
        return inner
    out: list[str] = []
    index = 0
    while index < len(inner):
        char = inner[index]
        if char == "\\" and index + 1 < len(inner) and inner[index + 1] in ('\\', '"'):
            out.append(inner[index + 1])
            index += 2
            continue
        if char == '"':
            raise WikiSchemaError("unescaped `\"` inside quoted scalar")
        out.append(char)
        index += 1
    return "".join(out)


def quote_scalar(value: object) -> str:
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def parse_frontmatter_with_raw(text: str, label: str | Path) -> tuple[dict[str, object], dict[str, object], str]:
    """Return (values, raw inline text per key, body). Raw text lets serialize keep original quoting."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise WikiSchemaError(f"{label}: missing YAML frontmatter")

    end_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break
    if end_index is None:
        raise WikiSchemaError(f"{label}: unterminated YAML frontmatter")

    frontmatter_lines = lines[1:end_index]
    body = "".join(lines[end_index + 1 :])
    frontmatter: dict[str, object] = {}
    raw_values: dict[str, object] = {}
    index = 0
    while index < len(frontmatter_lines):
        raw_line = frontmatter_lines[index].rstrip("\n")
        if not raw_line.strip():
            index += 1
            continue

        key_match = KEY_RE.match(raw_line)
        if not key_match:
            raise WikiSchemaError(f"{label}: unsupported frontmatter line: {raw_line}")

        key = key_match.group(1)
        if key in frontmatter:
            raise WikiSchemaError(f"{label}: duplicate frontmatter key `{key}`")
        inline_value = key_match.group(2)
        if inline_value is None:
            inline_value = ""

        if inline_value == "":
            items: list[str] = []
            raw_items: list[str] = []
            index += 1
            while index < len(frontmatter_lines):
                list_line = frontmatter_lines[index].rstrip("\n")
                if not list_line.strip():
                    index += 1
                    continue
                list_match = LIST_RE.match(list_line)
                if not list_match:
                    break
                raw_items.append(list_match.group(1).strip())
                items.append(_scalar(raw_items[-1], label))
                index += 1
            frontmatter[key] = items
            raw_values[key] = raw_items
            continue

        frontmatter[key] = _scalar(inline_value, label)
        raw_values[key] = inline_value.strip()
        index += 1

    return frontmatter, raw_values, body


def _scalar(raw: str, label: str | Path) -> str:
    try:
        return parse_scalar(raw)
    except WikiSchemaError as exc:
        raise WikiSchemaError(f"{label}: {exc}") from None


def parse_frontmatter(text: str, label: str | Path) -> tuple[dict[str, object], str]:
    frontmatter, _, body = parse_frontmatter_with_raw(text, label)
    return frontmatter, body


def serialize_page(page: MarkdownPage) -> str:
    """Render frontmatter in its existing key order, reusing original quoting when the value is unchanged."""
    lines = ["---\n"]
    for key, value in page.frontmatter.items():
        raw = page.raw_frontmatter.get(key)
        if isinstance(value, list):
            lines.append(f"{key}:\n")
            raw_items = raw if isinstance(raw, list) and len(raw) == len(value) else None
            for index, item in enumerate(value):
                if raw_items is not None and parse_scalar(str(raw_items[index])) == str(item):
                    text = str(raw_items[index])
                else:
                    text = quote_scalar(item)
                lines.append(f"  - {text}\n")
        else:
            if isinstance(raw, str) and parse_scalar(raw) == str(value):
                text = raw
            else:
                text = quote_scalar(value)
            lines.append(f"{key}: {text}\n")
    lines.append("---\n")
    return "".join(lines) + page.body


def load_page(path: Path, root: Path, cache: ScriptCache | None = None) -> MarkdownPage:
    rel_path = path.relative_to(root).as_posix()
    slug = path.stem
    stamp = None
    if cache is not None:
        file_stat = path.stat()
        stamp = (file_stat.st_mtime_ns, file_stat.st_size)
        cached = cache.get_page(rel_path, stamp)
        if cached is not None:
            frontmatter, raw, body = cached
            return MarkdownPage(
                path=path,
                rel_path=rel_path,
                slug=slug,
                page_type=str(frontmatter.get("type", "")),
                frontmatter=frontmatter,
                body=body,
                raw_frontmatter=raw,
            )

    text = path.read_text(encoding="utf-8")
    frontmatter, raw, body = parse_frontmatter_with_raw(text, rel_path)
    if cache is not None and stamp is not None:
        cache.put_page(rel_path, stamp, frontmatter, raw, body)
    return MarkdownPage(
        path=path,
        rel_path=rel_path,
        slug=slug,
        page_type=str(frontmatter.get("type", "")),
        frontmatter=frontmatter,
        body=body,
        raw_frontmatter=raw,
        source_text=text,
    )


def read_page(path: Path, root: Path) -> MarkdownPage:
    return load_page(path, root)


def iter_page_paths(root: Path) -> Iterator[Path]:
    for directory in CONTENT_DIRS:
        content_dir = root / "wiki" / directory
        if not content_dir.is_dir():
            continue
        with os.scandir(content_dir) as entries:
            names = sorted(
                entry.name
                for entry in entries
                if entry.is_file() and entry.name.endswith(".md") and not entry.name.startswith(".")
            )
        for name in names:
            yield content_dir / name


def iter_page_slugs(root: Path) -> Iterator[str]:
    for path in iter_page_paths(root):
        yield path.stem


def discover_pages(
    root: Path,
    errors: list[str] | None = None,
    cache: ScriptCache | None = None,
) -> list[MarkdownPage]:
    """Parse every content page once. With `errors`, unparseable pages are collected instead of raised."""
    pages: list[MarkdownPage] = []
    for path in iter_page_paths(root):
        try:
            pages.append(load_page(path, root, cache))
        except WikiSchemaError as exc:
            if errors is None:
                raise
            errors.append(str(exc))
    return pages


def link_target(inner: str) -> str | None:
    target = inner.split("|", 1)[0].split("#", 1)[0].strip()
    return target or None


def split_wikilink(link: str) -> str | None:
    match = WIKILINK_RE.match(link.strip())
    if not match:
        return None
    return link_target(match.group(1))


def raw_target(link: str) -> str | None:
    target = split_wikilink(link)
    if not target or not target.startswith("raw/"):
        return None
    if ".." in PurePosixPath(target).parts:
        return None
    return target


def wiki_target(link: str) -> str | None:
    target = split_wikilink(link)
    if target and not target.startswith("raw/"):
        return target
    return None


def iter_body_lines(body: str) -> Iterator[tuple[int, str]]:
    """Yield (line number, line) for body lines outside fenced code blocks."""
    in_fence = False
    for line_no, line in enumerate(body.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield line_no, line


def iter_body_links(body: str) -> Iterator[BodyLink]:
    for line_no, line in iter_body_lines(body):
        in_footnote = FOOTNOTE_DEF_RE.match(line) is not None
        for match in WIKILINK_ANY_RE.finditer(line):
            target = link_target(match.group(2))
            if target:
                yield BodyLink(line_no, match.group(1) == "!", target, in_footnote)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stamp(path: Path) -> tuple[int, int]:
    file_stat = path.stat()
    return file_stat.st_mtime_ns, file_stat.st_size


class ScriptCache:
    """Digest and parsed-page cache under a git-ignored `.cache/` directory.

    Entries are keyed by relative path and valid only while (mtime_ns, size) match.
    A rewrite that keeps both values identical goes undetected; `--no-cache` bypasses it.
    """

    def __init__(self, root: Path, enabled: bool = True) -> None:
        self.enabled = enabled
        self.path = root / CACHE_DIR_NAME / CACHE_FILE_NAME
        self.digests: dict[str, dict[str, object]] = {}
        self.pages: dict[str, dict[str, object]] = {}
        self._seen_digests: set[str] = set()
        self._seen_pages: set[str] = set()
        if enabled:
            self._load()

    def _load(self) -> None:
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if not isinstance(loaded, dict) or loaded.get("version") != CACHE_VERSION:
            return
        if isinstance(loaded.get("digests"), dict):
            self.digests = loaded["digests"]
        if isinstance(loaded.get("pages"), dict):
            self.pages = loaded["pages"]

    def digest(self, path: Path, rel_path: str) -> str:
        mtime_ns, size = _stamp(path)
        self._seen_digests.add(rel_path)
        entry = self.digests.get(rel_path)
        if (
            self.enabled
            and isinstance(entry, dict)
            and entry.get("mtime_ns") == mtime_ns
            and entry.get("size") == size
            and isinstance(entry.get("sha256"), str)
        ):
            return entry["sha256"]
        digest = sha256_file(path)
        self.digests[rel_path] = {"mtime_ns": mtime_ns, "size": size, "sha256": digest}
        return digest

    def get_page(
        self, rel_path: str, stamp: tuple[int, int]
    ) -> tuple[dict[str, object], dict[str, object], str] | None:
        self._seen_pages.add(rel_path)
        entry = self.pages.get(rel_path)
        if not self.enabled or not isinstance(entry, dict):
            return None
        if entry.get("mtime_ns") != stamp[0] or entry.get("size") != stamp[1]:
            return None
        frontmatter, raw, body = entry.get("frontmatter"), entry.get("raw"), entry.get("body")
        if not (isinstance(frontmatter, dict) and isinstance(raw, dict) and isinstance(body, str)):
            return None
        return copy.deepcopy(frontmatter), copy.deepcopy(raw), body

    def put_page(
        self,
        rel_path: str,
        stamp: tuple[int, int],
        frontmatter: dict[str, object],
        raw: dict[str, object],
        body: str,
    ) -> None:
        self._seen_pages.add(rel_path)
        if not self.enabled:
            return
        self.pages[rel_path] = {
            "mtime_ns": stamp[0],
            "size": stamp[1],
            "frontmatter": copy.deepcopy(frontmatter),
            "raw": copy.deepcopy(raw),
            "body": body,
        }

    def save(self) -> None:
        if not self.enabled:
            return
        payload = {
            "version": CACHE_VERSION,
            "digests": {key: value for key, value in self.digests.items() if key in self._seen_digests},
            "pages": {key: value for key, value in self.pages.items() if key in self._seen_pages},
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(self.path, json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n")


def atomic_write_text(path: Path, text: str) -> None:
    """Write via a temp file in the same directory, then `os.replace`, keeping the target's mode."""
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.chmod(temp_name, mode)
        os.replace(temp_name, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(temp_name)
        raise


def ensure_list(path: str, key: str, value: object) -> list[str]:
    if not isinstance(value, list):
        raise WikiSchemaError(f"{path}: `{key}` must be a YAML list")
    return [str(item) for item in value]


def set_raw_sha256(page: MarkdownPage, digest: str) -> None:
    if "raw_sha256" in page.frontmatter:
        page.frontmatter["raw_sha256"] = digest
        return
    items = list(page.frontmatter.items())
    index = next((position for position, (key, _) in enumerate(items) if key == "created_at"), len(items))
    items.insert(index, ("raw_sha256", digest))
    page.frontmatter.clear()
    page.frontmatter.update(items)


def date_problem(value: object) -> str | None:
    text = str(value)
    if not DATE_RE.match(text):
        return "must use YYYY-MM-DD"
    try:
        date.fromisoformat(text)
    except ValueError:
        return "must be a real calendar date"
    return None


def canonical_url_problem(value: str) -> str | None:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return "must be an absolute http(s) URL"
    if "@" in parsed.netloc:
        return "must not embed credentials"
    if not parsed.hostname:
        return "must include a host name"
    return None


def normalize_canonical_url(value: str) -> str:
    """Drop `utm_*` tracking parameters (case-insensitive) so duplicate URLs compare equal."""
    parsed = urlparse(value)
    if not parsed.query:
        return value
    kept = [
        part
        for part in parsed.query.split("&")
        if not part.split("=", 1)[0].lower().startswith("utm_")
    ]
    return urlunparse(parsed._replace(query="&".join(kept)))


def find_dependency_cycle(dependencies: dict[str, set[str]]) -> list[str] | None:
    """Return one cycle as a closed path, ignoring self-loops (reported separately)."""
    state: dict[str, int] = {}
    for start in sorted(dependencies):
        if state.get(start):
            continue
        state[start] = 1
        path = [start]
        stack = [iter(sorted(dependencies.get(start, set())))]
        while stack:
            for child in stack[-1]:
                if child == path[-1]:
                    continue
                if state.get(child) == 1:
                    return path[path.index(child) :] + [child]
                if not state.get(child):
                    state[child] = 1
                    path.append(child)
                    stack.append(iter(sorted(dependencies.get(child, set()))))
                    break
            else:
                finished = path.pop()
                stack.pop()
                state[finished] = 2
    return None


def build_slug_map(pages: list[MarkdownPage], errors: list[str] | None = None) -> dict[str, MarkdownPage]:
    slug_map: dict[str, MarkdownPage] = {}
    for page in pages:
        if page.slug in slug_map:
            message = (
                f"{page.rel_path}: duplicate slug `{page.slug}` also exists at {slug_map[page.slug].rel_path}"
            )
            if errors is None:
                raise WikiSchemaError(message)
            errors.append(message)
            continue
        slug_map[page.slug] = page
    return slug_map


def validate_refresh_pages(
    pages: list[MarkdownPage], root: Path
) -> tuple[
    dict[str, MarkdownPage],
    dict[str, str],
    dict[str, str],
    dict[str, set[str]],
    dict[str, set[str]],
]:
    slug_map = build_slug_map(pages)
    raw_refs: dict[str, str] = {}
    raw_paths: dict[str, str] = {}
    dependencies: dict[str, set[str]] = {}
    reverse_dependencies: dict[str, set[str]] = {}

    for page in pages:
        dependencies[page.slug] = set()
        reverse_dependencies.setdefault(page.slug, set())

        if "raw_sha256" in page.frontmatter and page.page_type != "source":
            raise WikiSchemaError(f"{page.rel_path}: `raw_sha256` is only valid on source pages")

        sources = ensure_list(page.rel_path, "sources", page.frontmatter.get("sources", []))
        page.frontmatter["sources"] = sources

        raw_links = [target for target in (raw_target(item) for item in sources) if target]
        if page.page_type == "source":
            if len(raw_links) != 1:
                raise WikiSchemaError(
                    f"{page.rel_path}: source pages must contain exactly one canonical `[[raw/...]]` reference"
                )
            raw_ref = raw_links[0]
            raw_path = root / raw_ref
            if not raw_path.is_file():
                raise WikiSchemaError(f"{page.rel_path}: referenced raw file does not exist: {raw_ref}")
            raw_refs[page.slug] = raw_ref
            raw_paths[page.slug] = raw_path.as_posix()

        for item in sources:
            target = wiki_target(item)
            if not target:
                continue
            if target not in slug_map:
                raise WikiSchemaError(
                    f"{page.rel_path}: `sources` references missing wiki page `[[{target}]]`"
                )
            dependencies[page.slug].add(target)
            reverse_dependencies.setdefault(target, set()).add(page.slug)

    return slug_map, raw_refs, raw_paths, dependencies, reverse_dependencies


def parse_headings(body: str) -> list[Heading]:
    headings: list[Heading] = []
    for line_no, line in iter_body_lines(body):
        match = HEADING_RE.match(line)
        if not match:
            continue
        headings.append(Heading(level=len(match.group(1)), title=match.group(2).strip(), line_no=line_no))
    return headings


def first_nonempty_body_line(body: str) -> tuple[int, str] | None:
    for index, line in enumerate(body.splitlines(), start=1):
        if line.strip():
            return index, line
    return None


def is_absolute_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

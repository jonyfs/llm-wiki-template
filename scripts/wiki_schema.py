from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


CONTENT_DIRS = ("sources", "entities", "concepts", "syntheses")
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
KEY_RE = re.compile(r"^([A-Za-z0-9_]+):(?:\s+(.*))?$")
LIST_RE = re.compile(r"^\s*-\s+(.*)$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HEADING_RE = re.compile(r"^(#{2,6})\s+(.+?)\s*$")
CLAIM_LED_EVIDENCE_RE = re.compile(r"^\s*-\s+[^:\n]+:\s+.*\[\[[^\]]+\]\].*$")


class WikiSchemaError(Exception):
    """Raised when the wiki does not satisfy the schema contract."""


@dataclass
class MarkdownPage:
    path: Path
    rel_path: str
    slug: str
    page_type: str
    frontmatter: dict[str, object]
    body: str


@dataclass
class Heading:
    level: int
    title: str
    line_no: int


def parse_scalar(raw: str) -> str:
    value = raw.strip()
    if not value:
        return ""
    if value[0] == value[-1] == '"':
        return bytes(value[1:-1], "utf-8").decode("unicode_escape")
    return value


def quote_scalar(value: object) -> str:
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def parse_frontmatter(text: str, path: Path) -> tuple[dict[str, object], str]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise WikiSchemaError(f"{path}: missing YAML frontmatter")

    end_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break
    if end_index is None:
        raise WikiSchemaError(f"{path}: unterminated YAML frontmatter")

    frontmatter_lines = lines[1:end_index]
    body = "".join(lines[end_index + 1 :])
    frontmatter: dict[str, object] = {}
    index = 0
    while index < len(frontmatter_lines):
        raw_line = frontmatter_lines[index].rstrip("\n")
        if not raw_line.strip():
            index += 1
            continue

        key_match = KEY_RE.match(raw_line)
        if not key_match:
            raise WikiSchemaError(f"{path}: unsupported frontmatter line: {raw_line}")

        key = key_match.group(1)
        inline_value = key_match.group(2)
        if inline_value is None:
            inline_value = ""

        if inline_value == "":
            items: list[str] = []
            index += 1
            while index < len(frontmatter_lines):
                list_line = frontmatter_lines[index].rstrip("\n")
                if not list_line.strip():
                    index += 1
                    continue
                list_match = LIST_RE.match(list_line)
                if not list_match:
                    break
                items.append(parse_scalar(list_match.group(1)))
                index += 1
            frontmatter[key] = items
            continue

        frontmatter[key] = parse_scalar(inline_value)
        index += 1

    return frontmatter, body


def serialize_page(page: MarkdownPage) -> str:
    frontmatter = page.frontmatter
    ordered_keys = [
        "title",
        "type",
        "source_role",
        "source_format",
        "authors",
        "published_at",
        "canonical_url",
        "sources",
        "raw_sha256",
        "created_at",
        "updated_at",
    ]
    emitted = [key for key in ordered_keys if key in frontmatter]
    emitted.extend(key for key in frontmatter if key not in emitted)

    lines = ["---\n"]
    for key in emitted:
        value = frontmatter[key]
        if isinstance(value, list):
            lines.append(f"{key}:\n")
            for item in value:
                lines.append(f"  - {quote_scalar(item)}\n")
        else:
            lines.append(f"{key}: {quote_scalar(value)}\n")
    lines.append("---\n")
    return "".join(lines) + page.body


def read_page(path: Path, root: Path) -> MarkdownPage:
    text = path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(text, path)
    slug = path.stem
    page_type = str(frontmatter.get("type", ""))
    rel_path = path.relative_to(root).as_posix()
    return MarkdownPage(path=path, rel_path=rel_path, slug=slug, page_type=page_type, frontmatter=frontmatter, body=body)


def discover_pages(root: Path) -> list[MarkdownPage]:
    pages: list[MarkdownPage] = []
    wiki_root = root / "wiki"
    for directory in CONTENT_DIRS:
        content_dir = wiki_root / directory
        if not content_dir.exists():
            continue
        for path in sorted(content_dir.glob("*.md")):
            if path.name == ".gitkeep":
                continue
            pages.append(read_page(path, root))
    return pages


def split_wikilink(link: str) -> str | None:
    match = WIKILINK_RE.match(link.strip())
    if not match:
        return None
    target = match.group(1).split("|", 1)[0].split("#", 1)[0].strip()
    return target or None


def raw_target(link: str) -> str | None:
    target = split_wikilink(link)
    if target and target.startswith("raw/"):
        return target
    return None


def wiki_target(link: str) -> str | None:
    target = split_wikilink(link)
    if target and not target.startswith("raw/"):
        return target
    return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_list(path: str, key: str, value: object) -> list[str]:
    if not isinstance(value, list):
        raise WikiSchemaError(f"{path}: `{key}` must be a YAML list")
    return [str(item) for item in value]


def set_raw_sha256(page: MarkdownPage, digest: str) -> None:
    page.frontmatter["raw_sha256"] = digest


def validate_refresh_pages(
    pages: list[MarkdownPage], root: Path
) -> tuple[
    dict[str, MarkdownPage],
    dict[str, str],
    dict[str, str],
    dict[str, set[str]],
    dict[str, set[str]],
]:
    slug_map: dict[str, MarkdownPage] = {}
    raw_refs: dict[str, str] = {}
    raw_paths: dict[str, str] = {}
    dependencies: dict[str, set[str]] = {}
    reverse_dependencies: dict[str, set[str]] = {}

    for page in pages:
        if page.slug in slug_map:
            raise WikiSchemaError(
                f"duplicate slug `{page.slug}` at {slug_map[page.slug].rel_path} and {page.rel_path}"
            )
        slug_map[page.slug] = page

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
    for index, line in enumerate(body.splitlines(), start=1):
        match = HEADING_RE.match(line)
        if not match:
            continue
        headings.append(Heading(level=len(match.group(1)), title=match.group(2).strip(), line_no=index))
    return headings


def first_nonempty_body_line(body: str) -> tuple[int, str] | None:
    for index, line in enumerate(body.splitlines(), start=1):
        if line.strip():
            return index, line
    return None


def is_absolute_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

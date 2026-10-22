#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

from wiki_schema import (
    CLAIM_LED_EVIDENCE_RE,
    CONTENT_DIRS,
    FOOTNOTE_DEF_RE,
    PAGE_HEADINGS,
    PAGE_TYPE_DIRS,
    RAW_SHA256_RE,
    REQUIRED_FRONTMATTER_KEYS,
    REQUIRED_WIKI_FILES,
    SOURCE_FORMAT_VALUES,
    SOURCE_ROLE_VALUES,
    SYNTHESIS_EVIDENCE_SUBHEADINGS,
    WIKILINK_ANY_RE,
    ScriptCache,
    WikiSchemaError,
    build_slug_map,
    canonical_url_problem,
    date_problem,
    normalize_canonical_url,
    discover_pages,
    ensure_list,
    find_dependency_cycle,
    first_nonempty_body_line,
    iter_body_lines,
    iter_body_links,
    link_target,
    parse_headings,
    raw_target,
    split_wikilink,
    wiki_target,
)


KEBAB_CASE_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HTTP_STATUS_RE = re.compile(r"[0-9]{3}")
INDEX_ENTRY_RE = re.compile(r"^\s*-\s+\[\[([^\]]+)\]\]\s+-\s+(.+?)\s*$")
INDEX_SECTIONS = {
    "Sources": "source",
    "Entities": "entity",
    "Concepts": "concept",
    "Syntheses": "synthesis",
}
LOG_HEADING_RE = re.compile(r"^## \[(\d{4}-\d{2}-\d{2})\] ([a-z][a-z-]*) \| (\S.*?)\s*$")
RELATED_LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
CLAIM_LINE_RE = re.compile(r"^- (C[1-9][0-9]*): (.+?) \[\[(raw/[^\]|#]+)\]\]$")
CLAIMS_LEDGER_HEADING = "Claims ledger"
H1_RE = re.compile(r"^#\s+(.+?)\s*$")
NON_WORD_RE = re.compile(r"[\W_]+")
BACKTICK_SPAN_RE = re.compile(r"`[^`]*`")
BRACKET_LINK_RE = re.compile(r"\[\[[^\]]*\]\]")
DIGITS_RE = re.compile(r"\d+")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
LIST_MARKER_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+")
LEARNING_PATHS_HEADING = "Learning paths"
LEARNING_PATH_MIN_PAGES = 10
MAX_SENTENCE_WORDS = 60
SLUG_DRIFT_MIN_SIMILARITY = 0.5
DEFAULT_LIMIT = 50
INDEX_PATH = "wiki/index.md"


def add_error(errors: list[str], page_path: str, message: str) -> None:
    errors.append(f"{page_path}: {message}")


def normalize_title(text: str) -> str:
    return NON_WORD_RE.sub("", text.casefold())


def source_items(page) -> list[str]:
    value = page.frontmatter.get("sources")
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def find_section_ranges(lines: list[str], headings: list[tuple[int, str, int]]) -> dict[str, tuple[int, int]]:
    ranges: dict[str, tuple[int, int]] = {}
    open_title: str | None = None
    open_start = 0
    for level, title, line_no in headings:
        if level != 2:
            continue
        if open_title is not None:
            ranges[open_title] = (open_start, line_no)
        open_title, open_start = title, line_no
    if open_title is not None:
        ranges[open_title] = (open_start, len(lines) + 1)
    return ranges


def validate_frontmatter(page, slug_map, root: Path, errors: list[str]) -> None:
    if page.page_type not in PAGE_TYPE_DIRS:
        add_error(errors, page.rel_path, f"`type` must be one of {', '.join(sorted(PAGE_TYPE_DIRS))}")
        return

    if not KEBAB_CASE_RE.match(page.slug):
        add_error(errors, page.rel_path, "filename must use lowercase kebab-case")

    expected_dir = PAGE_TYPE_DIRS[page.page_type]
    if page.path.parent.name != expected_dir:
        add_error(errors, page.rel_path, f"`{page.page_type}` pages must live in `wiki/{expected_dir}/`")

    for key in REQUIRED_FRONTMATTER_KEYS[page.page_type]:
        if key not in page.frontmatter:
            add_error(errors, page.rel_path, f"missing required frontmatter field `{key}`")

    dates: dict[str, date] = {}
    for date_key in ("created_at", "updated_at"):
        value = page.frontmatter.get(date_key)
        if value is None:
            continue
        problem = date_problem(value)
        if problem:
            add_error(errors, page.rel_path, f"`{date_key}` {problem}")
        else:
            dates[date_key] = date.fromisoformat(str(value))
    if "created_at" in dates and "updated_at" in dates and dates["created_at"] > dates["updated_at"]:
        add_error(errors, page.rel_path, "`created_at` must not be later than `updated_at`")

    try:
        sources = ensure_list(page.rel_path, "sources", page.frontmatter.get("sources", []))
    except WikiSchemaError as exc:
        add_error(errors, page.rel_path, str(exc).split(": ", 1)[1])
        return

    raw_links = []
    for item in sources:
        target = split_wikilink(item)
        if not target:
            add_error(errors, page.rel_path, f"`sources` item must be a wiki link: {item}")
            continue
        raw_ref = raw_target(item)
        wiki_ref = wiki_target(item)
        if raw_ref:
            if not (root / raw_ref).is_file():
                add_error(errors, page.rel_path, f"`sources` references missing raw file `{raw_ref}`")
            raw_links.append(raw_ref)
            continue
        if wiki_ref is None:
            continue
        if wiki_ref not in slug_map:
            add_error(errors, page.rel_path, f"`sources` references missing wiki page `[[{wiki_ref}]]`")
        elif wiki_ref == page.slug:
            add_error(errors, page.rel_path, "`sources` must not reference the page itself")
        elif page.page_type == "source" and slug_map[wiki_ref].page_type == "source":
            add_error(errors, page.rel_path, "source pages must not cite other source pages in `sources`")

    if page.page_type == "source":
        if "raw_sha256" not in page.frontmatter:
            add_error(errors, page.rel_path, "source pages must include `raw_sha256`")
        elif not RAW_SHA256_RE.fullmatch(str(page.frontmatter["raw_sha256"])):
            add_error(errors, page.rel_path, "`raw_sha256` must be 64 lowercase hex characters")
        if len(raw_links) != 1:
            add_error(errors, page.rel_path, "source pages must contain exactly one canonical `[[raw/...]]` reference")
        source_role = page.frontmatter.get("source_role")
        if source_role is None:
            add_error(errors, page.rel_path, "source pages must include `source_role`")
        elif str(source_role) not in SOURCE_ROLE_VALUES:
            add_error(errors, page.rel_path, f"`source_role` must be one of {', '.join(SOURCE_ROLE_VALUES)}")

        source_format = page.frontmatter.get("source_format")
        if source_format is not None and str(source_format) not in SOURCE_FORMAT_VALUES:
            add_error(errors, page.rel_path, f"`source_format` must be one of {', '.join(SOURCE_FORMAT_VALUES)}")

        authors = page.frontmatter.get("authors")
        if authors is not None:
            if not isinstance(authors, list) or not all(isinstance(item, str) and item.strip() for item in authors):
                add_error(errors, page.rel_path, "`authors` must be a YAML list of non-empty strings")

        published_at = page.frontmatter.get("published_at")
        if published_at is not None:
            problem = date_problem(published_at)
            if problem:
                add_error(errors, page.rel_path, f"`published_at` {problem}")

        canonical_url = page.frontmatter.get("canonical_url")
        if canonical_url is not None:
            problem = canonical_url_problem(str(canonical_url))
            if problem:
                add_error(errors, page.rel_path, f"`canonical_url` {problem}")
            elif normalize_canonical_url(str(canonical_url)) != str(canonical_url):
                add_error(errors, page.rel_path, "`canonical_url` must not carry utm_* tracking parameters")

        fetched_at = page.frontmatter.get("fetched_at")
        if fetched_at is not None:
            problem = date_problem(fetched_at)
            if problem:
                add_error(errors, page.rel_path, f"`fetched_at` {problem}")

        http_status = page.frontmatter.get("http_status")
        if http_status is not None and not (
            HTTP_STATUS_RE.fullmatch(str(http_status)) and 100 <= int(str(http_status)) <= 599
        ):
            add_error(errors, page.rel_path, "`http_status` must be an integer from 100 to 599")
    else:
        for key in (
            "raw_sha256",
            "source_role",
            "source_format",
            "authors",
            "published_at",
            "canonical_url",
            "fetched_at",
            "http_status",
        ):
            if key in page.frontmatter:
                add_error(errors, page.rel_path, f"`{key}` is only valid on source pages")


def stale_source_findings(
    entries: list[tuple[str, object]], today: date, max_age_years: int | None
) -> list[str]:
    """Warn for each (rel_path, published_at) older than `max_age_years`; disabled when None."""
    if max_age_years is None:
        return []
    cutoff = today - timedelta(days=round(365.25 * max_age_years))
    findings: list[str] = []
    for rel_path, published_at in entries:
        if published_at is None or date_problem(published_at) is not None:
            continue
        if date.fromisoformat(str(published_at)) < cutoff:
            findings.append(
                f"{rel_path}: source is older than {max_age_years} year(s) by `published_at` {published_at}"
            )
    return findings


def validate_headings(page, errors: list[str]) -> tuple[str, ...]:
    """Check heading layout once and return the page's `## Related pages` wiki links."""
    lines = page.body.splitlines()
    first_line = first_nonempty_body_line(page.body)
    if first_line is None:
        add_error(errors, page.rel_path, "page body must include an unheaded lead before section headings")
        return ()
    _, line = first_line
    if line.lstrip().startswith("#"):
        add_error(errors, page.rel_path, "page body must begin with an unheaded lead before the first section heading")

    heading_objs = parse_headings(page.body)
    headings = [(heading.level, heading.title, heading.line_no) for heading in heading_objs]
    h2_titles = [title for level, title, _ in headings if level == 2]
    if page.page_type == "source":
        h2_titles = [title for title in h2_titles if title != CLAIMS_LEDGER_HEADING]
    expected_titles = PAGE_HEADINGS.get(page.page_type, [])

    if page.page_type == "synthesis" and "Citations or supporting pages" in h2_titles:
        add_error(errors, page.rel_path, "use `## Evidence base` instead of `## Citations or supporting pages`")

    if h2_titles != expected_titles:
        add_error(
            errors,
            page.rel_path,
            f"level-2 headings must be exactly: {', '.join(f'`## {title}`' for title in expected_titles)}",
        )

    section_ranges = find_section_ranges(lines, headings)
    related = validate_related_pages(page, lines, section_ranges, errors)
    if page.page_type == "synthesis":
        validate_evidence_base(page, lines, headings, section_ranges, errors)
    if page.page_type == "source":
        validate_claims_ledger(page, lines, section_ranges, errors)
    return related


def validate_claims_ledger(page, lines: list[str], section_ranges, errors: list[str]) -> None:
    """Check the optional `## Claims ledger` section of a source page."""
    ledger_range = section_ranges.get(CLAIMS_LEDGER_HEADING)
    if ledger_range is None:
        return

    start, end = ledger_range
    raw_refs = {
        link_target(match.group(1))
        for item in source_items(page)
        for match in RELATED_LINK_RE.finditer(item)
        if link_target(match.group(1)).startswith("raw/")
    }
    canonical = next(iter(raw_refs)) if len(raw_refs) == 1 else None
    claim_ids: set[str] = set()
    claim_count = 0
    for line_no in range(start + 1, end):
        line = lines[line_no - 1].strip()
        if not line:
            continue
        match = CLAIM_LINE_RE.match(line)
        if not match:
            add_error(errors, page.rel_path, "claims ledger entries must read `- C<n>: <claim> [[raw/...]]`")
            continue
        claim_id, raw_target = match.group(1), match.group(3)
        claim_count += 1
        if claim_id in claim_ids:
            add_error(errors, page.rel_path, f"claim id {claim_id} is duplicated")
        claim_ids.add(claim_id)
        if raw_target != canonical:
            add_error(errors, page.rel_path, f"claim {claim_id} must cite the canonical raw file in `sources`")
    if claim_count == 0:
        add_error(errors, page.rel_path, "claims ledger must contain at least one claim")


def validate_related_pages(page, lines: list[str], section_ranges, errors: list[str]) -> tuple[str, ...]:
    related_range = section_ranges.get("Related pages")
    if related_range is None:
        return ()

    start, end = related_range
    related_links: set[str] = set()
    for line_no in range(start + 1, end):
        line = lines[line_no - 1].strip()
        if not line or not line.startswith("- "):
            continue
        match = RELATED_LINK_RE.search(line)
        if not match:
            continue
        target = link_target(match.group(1))
        if target and not target.startswith("raw/"):
            related_links.add(target)

    if not related_links:
        add_error(errors, page.rel_path, "`## Related pages` must include at least one wiki-page link")
    return tuple(sorted(related_links))


def validate_evidence_base(page, lines: list[str], headings, section_ranges, errors: list[str]) -> None:
    evidence_range = section_ranges.get("Evidence base")
    if evidence_range is None:
        return

    evidence_start, evidence_end = evidence_range
    current_h2 = None
    current_h3 = None
    for level, title, line_no in headings:
        if line_no < evidence_start or line_no >= evidence_end:
            continue
        if level == 2:
            current_h2 = title
            current_h3 = None
            continue
        if level == 3:
            if current_h2 != "Evidence base":
                add_error(errors, page.rel_path, f"`### {title}` is only allowed under `## Evidence base`")
                continue
            if title not in SYNTHESIS_EVIDENCE_SUBHEADINGS:
                add_error(
                    errors,
                    page.rel_path,
                    f"`## Evidence base` only allows {', '.join(f'`### {item}`' for item in SYNTHESIS_EVIDENCE_SUBHEADINGS)}",
                )
                continue
            current_h3 = title
            continue
        if level > 3 and current_h2 == "Evidence base":
            add_error(errors, page.rel_path, "`## Evidence base` only allows the fixed level-3 subgroup headings")

    for line_no in range(evidence_start + 1, evidence_end):
        line = lines[line_no - 1]
        if not line.strip():
            continue
        if line.startswith("### "):
            current_h3 = line[4:].strip()
            continue
        if line.startswith("## "):
            current_h3 = None
            continue
        if line.lstrip().startswith("- "):
            if current_h3 not in SYNTHESIS_EVIDENCE_SUBHEADINGS:
                add_error(errors, page.rel_path, "evidence bullets must appear under an allowed `## Evidence base` subgroup heading")
                continue
            if not CLAIM_LED_EVIDENCE_RE.match(line):
                add_error(errors, page.rel_path, "evidence bullets must begin with a short claim fragment followed by `:` and at least one wikilink")


def check_body_links(page, slug_map, root: Path, errors: list[str], links, source_raw: set[str]) -> None:
    raw_root = (root / "raw").resolve()
    for link in links:
        if not link.target.startswith("raw/"):
            if link.target not in slug_map:
                add_error(errors, page.rel_path, f"broken wikilink `[[{link.target}]]`")
            continue
        resolved = (root / link.target).resolve()
        if not resolved.is_relative_to(raw_root):
            add_error(errors, page.rel_path, f"raw link `[[{link.target}]]` must point inside `raw/`")
            continue
        if not resolved.is_file():
            if link.embed:
                add_error(errors, page.rel_path, f"embed references missing asset `[[{link.target}]]`")
            else:
                add_error(errors, page.rel_path, f"raw link `[[{link.target}]]` points to a missing file")
        if link.footnote and link.target not in source_raw:
            add_error(errors, page.rel_path, f"footnote cites raw file not listed in `sources`: `[[{link.target}]]`")


def check_prose_density(page, warnings: list[str]) -> None:
    for _, line in iter_body_lines(page.body):
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "|")) or FOOTNOTE_DEF_RE.match(stripped):
            continue
        text = LIST_MARKER_RE.sub("", stripped)
        for sentence in SENTENCE_SPLIT_RE.split(text):
            words = len(sentence.split())
            if words > MAX_SENTENCE_WORDS:
                warnings.append(
                    f"{page.rel_path}: sentence has {words} words (over {MAX_SENTENCE_WORDS}); consider splitting"
                )


def check_title_heading(page, warnings: list[str]) -> None:
    title = str(page.frontmatter.get("title", "")).strip()
    for _, line in iter_body_lines(page.body):
        match = H1_RE.match(line)
        if match and match.group(1).strip() != title:
            warnings.append(f"{page.rel_path}: `# ` heading differs from `title`")
            return


def check_slug_drift(page, warnings: list[str]) -> None:
    title = str(page.frontmatter.get("title", "")).strip()
    if not title:
        return
    similarity = difflib.SequenceMatcher(None, normalize_title(page.slug), normalize_title(title)).ratio()
    if similarity < SLUG_DRIFT_MIN_SIMILARITY:
        warnings.append(f"{page.rel_path}: file name differs from title (similarity {similarity:.2f})")


def inbound_links(pages, links_by_slug) -> dict[str, set[str]]:
    inbound: dict[str, set[str]] = defaultdict(set)
    for page in pages:
        targets = {link.target for link in links_by_slug[page.slug] if not link.target.startswith("raw/")}
        targets.update(target for target in (wiki_target(item) for item in source_items(page)) if target)
        for target in targets:
            if target != page.slug:
                inbound[target].add(page.slug)
    return inbound


def warn_near_duplicate_titles(pages, warnings: list[str]) -> None:
    groups: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for page in pages:
        title = str(page.frontmatter.get("title", "")).strip()
        normalized = normalize_title(title)
        if normalized:
            groups[normalized][title.casefold()].append(page.rel_path)
    for by_exact in groups.values():
        if len(by_exact) < 2:
            continue
        all_paths = sorted(path for paths in by_exact.values() for path in paths)
        for path in all_paths:
            others = ", ".join(other for other in all_paths if other != path)
            warnings.append(f"{path}: near-duplicate title; normalized form also used by {others}")


def validate_duplicate_titles(pages, errors: list[str]) -> None:
    titles: dict[str, list[str]] = {}
    for page in pages:
        title = str(page.frontmatter.get("title", "")).strip()
        if not title:
            continue
        titles.setdefault(title.casefold(), []).append(page.rel_path)
    for paths in titles.values():
        if len(paths) > 1:
            joined = ", ".join(sorted(paths))
            for path in paths:
                add_error(errors, path, f"`title` must be unique across page types; duplicate set: {joined}")


def warn_synthesis_related_duplicates(scope, related_by_slug: dict[str, tuple[str, ...]], warnings: list[str]) -> None:
    groups: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for page in scope:
        if page.page_type == "synthesis" and related_by_slug.get(page.slug):
            groups[related_by_slug[page.slug]].append(page.slug)
    for slugs in groups.values():
        if len(slugs) < 2:
            continue
        for slug in slugs:
            others = ", ".join(f"[[{other}]]" for other in slugs if other != slug)
            warnings.append(f"{slug}: `## Related pages` duplicates {others}")


def read_index(root: Path) -> str | None:
    index_path = root / "wiki" / "index.md"
    if not index_path.is_file():
        return None
    return index_path.read_text(encoding="utf-8")


def parse_index(index_text: str) -> dict[str, dict[str, str]]:
    sections = {page_type: {} for page_type in INDEX_SECTIONS.values()}
    current_type = None
    for raw_line in index_text.splitlines():
        line = raw_line.rstrip()
        if line.startswith("## "):
            current_type = INDEX_SECTIONS.get(line[3:].strip())
            continue
        if current_type is None:
            continue
        match = INDEX_ENTRY_RE.match(line)
        if not match:
            continue
        slug = match.group(1).split("|", 1)[0].split("#", 1)[0].strip()
        summary = match.group(2).strip()
        sections[current_type][slug] = summary

    return sections


def validate_index(index_text: str, pages, slug_map, errors: list[str]) -> None:
    sections = parse_index(index_text)

    for page in pages:
        summary = sections.get(page.page_type, {}).get(page.slug)
        if summary is None:
            add_error(errors, INDEX_PATH, f"missing `{page.page_type}` index entry for `[[{page.slug}]]`")
        elif not summary.strip():
            add_error(errors, INDEX_PATH, f"`[[{page.slug}]]` index entry must include a one-line summary")

    for page_type, entries in sections.items():
        for slug, summary in entries.items():
            if slug not in slug_map:
                add_error(errors, INDEX_PATH, f"index entry references missing wiki page `[[{slug}]]`")
                continue
            if slug_map[slug].page_type != page_type:
                add_error(errors, INDEX_PATH, f"`[[{slug}]]` is listed under the wrong index section")
            if not summary.strip():
                add_error(errors, INDEX_PATH, f"`[[{slug}]]` index entry must include a one-line summary")


def learning_path_findings(index_text: str | None, slugs: set[str], page_count: int) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if index_text is None:
        return errors, warnings

    in_section = False
    found = False
    for line in index_text.splitlines():
        if line.startswith("## "):
            in_section = line[3:].strip() == LEARNING_PATHS_HEADING
            found = found or in_section
            continue
        if not in_section or "->" not in line:
            continue
        for match in WIKILINK_ANY_RE.finditer(line):
            target = link_target(match.group(2))
            if target and target not in slugs:
                add_error(errors, INDEX_PATH, f"learning path references missing wiki page `[[{target}]]`")

    if page_count >= LEARNING_PATH_MIN_PAGES and not found:
        warnings.append(f"{INDEX_PATH}: no `## {LEARNING_PATHS_HEADING}` section for {page_count} pages")
    return errors, warnings


def validate_dependency_cycles(pages, slug_map, errors: list[str]) -> None:
    dependencies = {
        page.slug: {
            target
            for target in (wiki_target(item) for item in source_items(page))
            if target and target in slug_map and target != page.slug
        }
        for page in pages
    }
    cycle = find_dependency_cycle(dependencies)
    if cycle:
        first = slug_map[cycle[0]].rel_path
        add_error(errors, first, f"dependency cycle detected in `sources`: {' -> '.join(cycle)}")


def validate_log(root: Path, errors: list[str], today: date) -> None:
    log_path = root / "wiki" / "log.md"
    if not log_path.is_file():
        add_error(errors, "wiki/log.md", "missing required log file")
        return

    previous: date | None = None
    for line_no, line in enumerate(log_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.startswith("## "):
            continue
        match = LOG_HEADING_RE.match(line)
        if not match:
            add_error(errors, "wiki/log.md", f"line {line_no}: log heading must use `## [YYYY-MM-DD] operation | title`")
            continue
        day_text = match.group(1)
        problem = date_problem(day_text)
        if problem:
            add_error(errors, "wiki/log.md", f"line {line_no}: `{day_text}` {problem}")
            continue
        day = date.fromisoformat(day_text)
        if day > today:
            add_error(errors, "wiki/log.md", f"line {line_no}: entry dated {day_text} is in the future")
        if previous is not None and day < previous:
            add_error(errors, "wiki/log.md", f"line {line_no}: entry dated {day_text} is out of chronological order")
        previous = day


def validate_wiki_layout(root: Path, errors: list[str]) -> None:
    wiki = root / "wiki"
    if not wiki.is_dir():
        return
    for entry in sorted(wiki.iterdir(), key=lambda path: path.name):
        if entry.name.startswith("."):
            continue
        if entry.is_dir():
            if entry.name not in CONTENT_DIRS:
                add_error(errors, f"wiki/{entry.name}", "unexpected directory under wiki/")
                continue
            for child in sorted(entry.iterdir(), key=lambda path: path.name):
                if child.name.startswith("."):
                    continue
                if child.is_dir():
                    add_error(errors, f"wiki/{entry.name}/{child.name}", "nested directories are not allowed")
                elif child.suffix != ".md":
                    add_error(errors, f"wiki/{entry.name}/{child.name}", "only `.md` pages belong here")
        elif entry.name not in REQUIRED_WIKI_FILES:
            add_error(errors, f"wiki/{entry.name}", "unexpected file under wiki/")


def validate_raw_coverage(root: Path, pages, warnings: list[str]) -> None:
    raw_dir = root / "raw"
    if not raw_dir.is_dir():
        return
    covered = {
        target
        for page in pages
        if page.page_type == "source"
        for target in (raw_target(item) for item in source_items(page))
        if target
    }
    for path in sorted(raw_dir.rglob("*")):
        if not path.is_file():
            continue
        parts = path.relative_to(raw_dir).parts
        if parts[0] == "assets" or any(part.startswith(".") for part in parts):
            continue
        rel_path = path.relative_to(root).as_posix()
        if rel_path not in covered:
            warnings.append(f"{rel_path}: raw file is not backed by any source page")


def git_changed_paths(root: Path) -> set[str]:
    def git(*args: str) -> list[str]:
        result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise WikiSchemaError("--changed-only requires a git repository")
        return [line for line in result.stdout.splitlines() if line]

    has_head = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--verify", "-q", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    ).returncode == 0
    tracked = git("diff", "--name-only", "--relative", "HEAD") if has_head else git("ls-files")
    untracked = git("ls-files", "--others", "--exclude-standard")
    return set(tracked) | set(untracked)


def run(
    root: Path,
    changed_only: bool = False,
    use_cache: bool = True,
    today: date | None = None,
    max_source_age_years: int | None = None,
) -> dict[str, object]:
    today = today or date.today()
    cache = ScriptCache(root, enabled=use_cache)
    errors: list[str] = []
    warnings: list[str] = []

    pages = discover_pages(root, errors=errors, cache=cache)
    slug_map = build_slug_map(pages, errors)
    changed = git_changed_paths(root) if changed_only else None
    scope = [page for page in pages if changed is None or page.rel_path in changed]

    links_by_slug = {page.slug: list(iter_body_links(page.body)) for page in pages}
    inbound = inbound_links(pages, links_by_slug)
    related_by_slug: dict[str, tuple[str, ...]] = {}
    for page in scope:
        validate_frontmatter(page, slug_map, root, errors)
        related_by_slug[page.slug] = validate_headings(page, errors)
        source_raw = {target for target in (raw_target(item) for item in source_items(page)) if target}
        check_body_links(page, slug_map, root, errors, links_by_slug[page.slug], source_raw)
        check_prose_density(page, warnings)
        check_title_heading(page, warnings)
        check_slug_drift(page, warnings)
        if not inbound.get(page.slug):
            warnings.append(f"{page.rel_path}: orphan page: no inbound links from other pages")
    validate_duplicate_titles(pages, errors)
    warn_near_duplicate_titles(pages, warnings)
    warn_synthesis_related_duplicates(scope, related_by_slug, warnings)

    index_text = read_index(root)
    if index_text is None:
        add_error(errors, INDEX_PATH, "missing required index file")
    else:
        validate_index(index_text, pages, slug_map, errors)
    path_errors, path_warnings = learning_path_findings(index_text, set(slug_map), len(pages))
    errors.extend(path_errors)
    warnings.extend(path_warnings)

    stale_entries = [
        (page.rel_path, page.frontmatter.get("published_at"))
        for page in scope
        if page.page_type == "source"
    ]
    warnings.extend(stale_source_findings(stale_entries, today, max_source_age_years))
    validate_dependency_cycles(pages, slug_map, errors)
    validate_log(root, errors, today)
    validate_wiki_layout(root, errors)
    validate_raw_coverage(root, pages, warnings)
    cache.save()

    errors.sort()
    warnings.sort()
    return {
        "page_count": len(pages),
        "violation_count": len(errors),
        "violations": errors,
        "warning_count": len(warnings),
        "warnings": warnings,
    }


def summary_kind(item: str) -> str:
    _, _, message = item.partition(": ")
    message = BACKTICK_SPAN_RE.sub("`…`", message)
    message = BRACKET_LINK_RE.sub("[[…]]", message)
    return DIGITS_RE.sub("N", message)


def render_items(items: list[str], limit: int, summary: bool) -> list[str]:
    if summary:
        counts = Counter(summary_kind(item) for item in items)
        return [f"{count:>4} {kind}" for kind, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))]
    shown = items if limit == 0 else items[:limit]
    lines: list[str] = []
    current = None
    for item in shown:
        path, _, message = item.partition(": ")
        if path != current:
            lines.append(path)
            current = path
        lines.append(f"  - {message}")
    hidden = len(items) - len(shown)
    if hidden:
        lines.append(f"... {hidden} more (use --limit 0 to show all)")
    return lines


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lint wiki structure and page schema.")
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root to scan. Defaults to the current working directory.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format; json is one compact object.")
    parser.add_argument("--verbose", action="store_true", help="On success, also print the full JSON report.")
    parser.add_argument("--quiet", action="store_true", help="Print nothing; set the exit status only.")
    parser.add_argument("--summary", action="store_true", help="Print counts per violation kind instead of each message.")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Maximum messages per section; 0 shows all.")
    parser.add_argument("--changed-only", action="store_true", help="Check only pages changed in git.")
    parser.add_argument("--no-cache", action="store_true", help="Do not read or write the .cache/ parse cache.")
    parser.add_argument(
        "--max-source-age-years",
        type=int,
        default=None,
        help="Warn about source pages whose published_at is older than N years. Off by default.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        report = run(
            Path(args.root).resolve(),
            changed_only=args.changed_only,
            use_cache=not args.no_cache,
            max_source_age_years=args.max_source_age_years,
        )
    except WikiSchemaError as exc:
        if not args.quiet:
            print(f"lint failed: {exc}", file=sys.stderr)
        return 1

    failed = report["violation_count"] > 0
    if args.quiet:
        return 1 if failed else 0

    if args.format == "json":
        payload = dict(report)
        payload["violations"] = render_limit(report["violations"], args.limit)
        payload["warnings"] = render_limit(report["warnings"], args.limit)
        print(json.dumps(payload, separators=(",", ":")))
        return 1 if failed else 0

    if failed:
        print(f"lint failed: {report['violation_count']} violation(s)", file=sys.stderr)
        for line in render_items(report["violations"], args.limit, args.summary):
            print(line, file=sys.stderr)
        if report["warnings"]:
            print(f"lint warnings: {report['warning_count']}", file=sys.stderr)
            for line in render_items(report["warnings"], args.limit, args.summary):
                print(line, file=sys.stderr)
        return 1

    note = f", {report['warning_count']} warning(s)" if report["warning_count"] else ""
    print(f"lint ok: {report['page_count']} pages, 0 violations{note}")
    if args.verbose:
        print(json.dumps(report, indent=2))
    if report["warnings"]:
        print(f"lint warnings: {report['warning_count']}", file=sys.stderr)
        for line in render_items(report["warnings"], args.limit, args.summary):
            print(line, file=sys.stderr)
    return 0


def render_limit(items: list[str], limit: int) -> list[str]:
    return items if limit == 0 else items[:limit]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

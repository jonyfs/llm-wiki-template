#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from wiki_schema import (
    CLAIM_LED_EVIDENCE_RE,
    DATE_RE,
    PAGE_HEADINGS,
    PAGE_TYPE_DIRS,
    REQUIRED_FRONTMATTER_KEYS,
    SOURCE_FORMAT_VALUES,
    SOURCE_ROLE_VALUES,
    SYNTHESIS_EVIDENCE_SUBHEADINGS,
    WikiSchemaError,
    discover_pages,
    ensure_list,
    first_nonempty_body_line,
    parse_headings,
    raw_target,
    split_wikilink,
    wiki_target,
)

KEBAB_CASE_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
INDEX_ENTRY_RE = re.compile(r"^\s*-\s+\[\[([^\]]+)\]\]\s+-\s+(.+?)\s*$")
INDEX_SECTIONS = {
    "Sources": "source",
    "Entities": "entity",
    "Concepts": "concept",
    "Syntheses": "synthesis",
}


def add_error(errors: list[str], page_path: str, message: str) -> None:
    errors.append(f"{page_path}: {message}")


def find_section_ranges(lines: list[str], headings: list[tuple[int, str, int]]) -> dict[str, tuple[int, int]]:
    ranges: dict[str, tuple[int, int]] = {}
    for index, (level, title, line_no) in enumerate(headings):
        if level != 2:
            continue
        start = line_no
        end = len(lines) + 1
        for next_level, _, next_line in headings[index + 1 :]:
            if next_level == 2:
                end = next_line
                break
        ranges[title] = (start, end)
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

    for date_key in ("created_at", "updated_at"):
        value = page.frontmatter.get(date_key)
        if value is not None and not DATE_RE.match(str(value)):
            add_error(errors, page.rel_path, f"`{date_key}` must use YYYY-MM-DD")

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
        if wiki_ref and wiki_ref not in slug_map:
            add_error(errors, page.rel_path, f"`sources` references missing wiki page `[[{wiki_ref}]]`")

    if page.page_type == "source":
        if "raw_sha256" not in page.frontmatter:
            add_error(errors, page.rel_path, "source pages must include `raw_sha256`")
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
        if published_at is not None and not DATE_RE.match(str(published_at)):
            add_error(errors, page.rel_path, "`published_at` must use YYYY-MM-DD")

        canonical_url = page.frontmatter.get("canonical_url")
        if canonical_url is not None:
            from wiki_schema import is_absolute_url

            if not is_absolute_url(str(canonical_url)):
                add_error(errors, page.rel_path, "`canonical_url` must be an absolute http(s) URL")
    else:
        for key in ("raw_sha256", "source_role", "source_format", "authors", "published_at", "canonical_url"):
            if key in page.frontmatter:
                add_error(errors, page.rel_path, f"`{key}` is only valid on source pages")


def validate_headings(page, errors: list[str]) -> None:
    lines = page.body.splitlines()
    first_line = first_nonempty_body_line(page.body)
    if first_line is None:
        add_error(errors, page.rel_path, "page body must include an unheaded lead before section headings")
        return
    _, line = first_line
    if line.lstrip().startswith("#"):
        add_error(errors, page.rel_path, "page body must begin with an unheaded lead before the first section heading")

    heading_objs = parse_headings(page.body)
    headings = [(heading.level, heading.title, heading.line_no) for heading in heading_objs]
    h2_titles = [title for level, title, _ in headings if level == 2]
    expected_titles = PAGE_HEADINGS.get(page.page_type, [])

    if page.page_type == "synthesis" and "Citations or supporting pages" in h2_titles:
        add_error(errors, page.rel_path, "use `## Evidence base` instead of `## Citations or supporting pages`")

    if h2_titles != expected_titles:
        add_error(
            errors,
            page.rel_path,
            f"level-2 headings must be exactly: {', '.join(f'`## {title}`' for title in expected_titles)}",
        )

    if page.page_type != "synthesis":
        validate_related_pages(page, lines, headings, errors)
        return

    validate_related_pages(page, lines, headings, errors)
    section_ranges = find_section_ranges(lines, headings)
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


def validate_related_pages(page, lines: list[str], headings: list[tuple[int, str, int]], errors: list[str]) -> None:
    section_ranges = find_section_ranges(lines, headings)
    related_range = section_ranges.get("Related pages")
    if related_range is None:
        return

    start, end = related_range
    related_links: set[str] = set()
    for line_no in range(start + 1, end):
        line = lines[line_no - 1].strip()
        if not line or not line.startswith("- "):
            continue
        match = re.search(r"\[\[([^\]]+)\]\]", line)
        if not match:
            continue
        target = match.group(1).split("|", 1)[0].split("#", 1)[0].strip()
        if target and not target.startswith("raw/"):
            related_links.add(target)

    if not related_links:
        add_error(errors, page.rel_path, "`## Related pages` must include at least one wiki-page link")


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


def parse_index(root: Path, errors: list[str]) -> dict[str, dict[str, str]]:
    index_path = root / "wiki" / "index.md"
    if not index_path.is_file():
        add_error(errors, "wiki/index.md", "missing required index file")
        return {}

    sections = {page_type: {} for page_type in INDEX_SECTIONS.values()}
    current_type = None
    for raw_line in index_path.read_text(encoding="utf-8").splitlines():
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


def validate_index(root: Path, pages, slug_map, errors: list[str]) -> None:
    sections = parse_index(root, errors)
    if not sections:
        return

    for page in pages:
        summary = sections.get(page.page_type, {}).get(page.slug)
        if summary is None:
            add_error(errors, "wiki/index.md", f"missing `{page.page_type}` index entry for `[[{page.slug}]]`")
        elif not summary.strip():
            add_error(errors, "wiki/index.md", f"`[[{page.slug}]]` index entry must include a one-line summary")

    for page_type, entries in sections.items():
        for slug, summary in entries.items():
            if slug not in slug_map:
                add_error(errors, "wiki/index.md", f"index entry references missing wiki page `[[{slug}]]`")
                continue
            if slug_map[slug].page_type != page_type:
                add_error(errors, "wiki/index.md", f"`[[{slug}]]` is listed under the wrong index section")
            if not summary.strip():
                add_error(errors, "wiki/index.md", f"`[[{slug}]]` index entry must include a one-line summary")


def run(root: Path) -> dict[str, object]:
    pages = discover_pages(root)
    slug_map = {}
    errors: list[str] = []
    for page in pages:
        if page.slug in slug_map:
            add_error(errors, page.rel_path, f"duplicate slug `{page.slug}` also exists at {slug_map[page.slug].rel_path}")
            continue
        slug_map[page.slug] = page

    for page in pages:
        validate_frontmatter(page, slug_map, root, errors)
        validate_headings(page, errors)
    validate_duplicate_titles(pages, errors)
    validate_index(root, pages, slug_map, errors)

    return {
        "repo_root": root.as_posix(),
        "page_count": len(pages),
        "violations": errors,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lint wiki structure and page schema.")
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root to scan. Defaults to the current working directory.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    report = run(Path(args.root).resolve())
    if report["violations"]:
        print("lint failed:", file=sys.stderr)
        for violation in report["violations"]:
            print(f"- {violation}", file=sys.stderr)
        return 1

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

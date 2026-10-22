#!/usr/bin/env python3
"""Build generated search artifacts under wiki/: .index.json, .graph.json, .index.sqlite (FTS5).

The artifacts are derived from content pages, are git-ignored, and are optional: wiki_search
falls back to an in-memory build when they are absent or stale.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

from wiki_schema import (
    PAGE_HEADINGS,
    MarkdownPage,
    WikiSchemaError,
    discover_pages,
    iter_body_links,
    iter_page_paths,
    parse_headings,
    wiki_target,
)


INDEX_VERSION = 1
SUMMARY_MAX_CHARS = 200
# One catalog entry per line: "- [[slug]] - one-line summary" (wiki/index.md convention).
INDEX_ENTRY_RE = re.compile(r"^- \[\[([^\]\[]+)\]\][ \t]*[-\u2013\u2014][ \t]*(.+)$", re.MULTILINE)
INDEX_JSON_NAME = ".index.json"
GRAPH_JSON_NAME = ".graph.json"
INDEX_DB_NAME = ".index.sqlite"


@dataclass
class IndexData:
    records: list[dict[str, str]]
    edges: dict[str, list[str]]
    fingerprint: dict[str, object]


def artifact_paths(root: Path) -> dict[str, Path]:
    wiki = root / "wiki"
    return {
        "index": wiki / INDEX_JSON_NAME,
        "graph": wiki / GRAPH_JSON_NAME,
        "db": wiki / INDEX_DB_NAME,
    }


def _cap(text: str) -> str:
    text = " ".join(text.split())
    if len(text) > SUMMARY_MAX_CHARS:
        text = text[: SUMMARY_MAX_CHARS - 3].rstrip() + "..."
    return text


def summarize(page: MarkdownPage) -> str:
    """First non-empty line under the page's first required heading, else the first body line."""
    lines = page.body.splitlines()
    required = PAGE_HEADINGS.get(page.page_type, [""])[0]
    anchor = next((heading for heading in parse_headings(page.body) if heading.title == required), None)
    text = ""
    if anchor is not None:
        for line in lines[anchor.line_no :]:
            if line.lstrip().startswith("#"):
                break
            if line.strip():
                text = line.strip()
                break
    else:
        text = next((line.strip() for line in lines if line.strip()), "")
    return _cap(text)


def index_md_summaries(root: Path) -> dict[str, str]:
    """Catalog one-line summaries from wiki/index.md entries, keyed by slug (item 74)."""
    try:
        text = (root / "wiki" / "index.md").read_text(encoding="utf-8")
    except OSError:
        return {}
    return {slug: _cap(summary) for slug, summary in INDEX_ENTRY_RE.findall(text)}


def fingerprint(root: Path) -> dict[str, object]:
    """Freshness key: a digest over wiki/index.md plus each content page's path, mtime, size, and content.

    index.md is covered because --from-index sources summaries from it; a catalog edit must mark
    the artifacts stale. In the default mode the extra input only risks a harmless false-stale.
    """
    digest = hashlib.sha256()
    index_md = root / "wiki" / "index.md"
    if index_md.is_file():
        digest.update(f"index.md\0{index_md.stat().st_size}\0".encode("utf-8"))
        digest.update(hashlib.sha256(index_md.read_bytes()).digest())
    paths = sorted(iter_page_paths(root))
    for path in paths:
        stat = path.stat()
        digest.update(f"{path.relative_to(root).as_posix()}\0{stat.st_mtime_ns}\0{stat.st_size}\0".encode("utf-8"))
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return {"pages": len(paths), "sha256": digest.hexdigest()}


def build_index(root: Path, errors: list[str] | None = None, from_index: bool = False) -> IndexData:
    """Build records and edges. With from_index, summaries come from wiki/index.md catalog
    entries when present, falling back to the page-derived summary (item 74)."""
    pages = discover_pages(root, errors=errors if errors is not None else [])
    catalog = index_md_summaries(root) if from_index else {}
    slugs = {page.slug for page in pages}
    records: list[dict[str, str]] = []
    edges: dict[str, list[str]] = {}
    for page in sorted(pages, key=lambda item: item.slug):
        records.append(
            {
                "slug": page.slug,
                "type": page.page_type,
                "title": str(page.frontmatter.get("title", page.slug)),
                "summary": catalog.get(page.slug) or summarize(page),
                "path": page.rel_path,
            }
        )
        targets: set[str] = set()
        for link in iter_body_links(page.body):
            if not link.embed and not link.footnote and not link.target.startswith("raw/"):
                targets.add(link.target)
        for item in page.frontmatter.get("sources", []) or []:
            target = wiki_target(str(item))
            if target:
                targets.add(target)
        edges[page.slug] = sorted(target for target in targets if target in slugs and target != page.slug)
    return IndexData(records=records, edges=edges, fingerprint=fingerprint(root))


def materialize(connection: sqlite3.Connection, data: IndexData) -> None:
    connection.execute("CREATE TABLE pages (slug TEXT PRIMARY KEY, type TEXT, title TEXT, summary TEXT, path TEXT)")
    connection.execute("CREATE VIRTUAL TABLE pages_fts USING fts5(slug UNINDEXED, title, summary)")
    connection.executemany(
        "INSERT INTO pages VALUES (:slug, :type, :title, :summary, :path)",
        data.records,
    )
    connection.executemany(
        "INSERT INTO pages_fts (slug, title, summary) VALUES (:slug, :title, :summary)",
        data.records,
    )
    connection.commit()


def write_index(root: Path, data: IndexData) -> dict[str, Path]:
    paths = artifact_paths(root)
    paths["index"].parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": INDEX_VERSION, "fingerprint": data.fingerprint, "pages": data.records}
    _replace_text(paths["index"], json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n")
    graph = {"version": INDEX_VERSION, "fingerprint": data.fingerprint, "edges": data.edges}
    _replace_text(paths["graph"], json.dumps(graph, separators=(",", ":"), sort_keys=True) + "\n")

    temp_db = paths["db"].with_name(paths["db"].name + ".tmp")
    if temp_db.exists():
        temp_db.unlink()
    connection = sqlite3.connect(temp_db)
    try:
        materialize(connection, data)
    finally:
        connection.close()
    os.replace(temp_db, paths["db"])
    return paths


def _replace_text(path: Path, text: str) -> None:
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(text, encoding="utf-8")
    os.replace(temp, path)


def load_index(root: Path) -> IndexData | None:
    """Return the on-disk index only when its fingerprint matches the current content pages."""
    paths = artifact_paths(root)
    try:
        index = json.loads(paths["index"].read_text(encoding="utf-8"))
        graph = json.loads(paths["graph"].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not (isinstance(index, dict) and isinstance(graph, dict)):
        return None
    if index.get("version") != INDEX_VERSION or graph.get("version") != INDEX_VERSION:
        return None
    if index.get("fingerprint") != fingerprint(root):
        return None
    return IndexData(records=index["pages"], edges=graph["edges"], fingerprint=index["fingerprint"])


def artifacts_exist(root: Path) -> bool:
    return any(path.exists() for path in artifact_paths(root).values())


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the generated wiki search index.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to the current directory.")
    parser.add_argument(
        "--from-index",
        action="store_true",
        help="Source summaries from wiki/index.md catalog entries when present, else from the page.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    errors: list[str] = []
    try:
        data = build_index(root, errors, from_index=args.from_index)
    except (WikiSchemaError, OSError) as exc:
        print(f"index failed: {exc}", file=sys.stderr)
        return 1
    if errors:
        print("index failed: unparseable pages; nothing written", file=sys.stderr)
        for line in errors:
            print(line, file=sys.stderr)
        return 1
    write_index(root, data)
    links = sum(len(targets) for targets in data.edges.values())
    print(f"index ok: {len(data.records)} pages, {links} links")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

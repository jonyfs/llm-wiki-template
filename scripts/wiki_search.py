#!/usr/bin/env python3
"""Search wiki pages by title and summary, follow backlinks, and find link paths.

Uses wiki/.index.sqlite (FTS5) when fresh. Without a fresh index it builds one in memory, so the
wiki works with no generated artifacts at all.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import deque
from pathlib import Path

from wiki_index import (
    IndexData,
    artifact_paths,
    artifacts_exist,
    build_index,
    load_index,
    materialize,
    write_index,
)
from wiki_schema import PAGE_TYPE_DIRS, WikiSchemaError


SNIPPET_MAX_CHARS = 200
TOKEN_RE = re.compile(r"\w+")


def open_database(root: Path, data: IndexData, from_disk: bool) -> sqlite3.Connection:
    db_path = artifact_paths(root)["db"]
    if from_disk and db_path.is_file():
        return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    connection = sqlite3.connect(":memory:")
    materialize(connection, data)
    return connection


def load_state(root: Path, rebuild: bool) -> tuple[IndexData, sqlite3.Connection]:
    if rebuild:
        errors: list[str] = []
        data = build_index(root, errors)
        if errors:
            raise WikiSchemaError("unparseable pages; nothing written:\n" + "\n".join(errors))
        write_index(root, data)
        return data, open_database(root, data, from_disk=True)
    data = load_index(root)
    if data is not None:
        return data, open_database(root, data, from_disk=True)
    if artifacts_exist(root):
        print("warning: search index is stale; run wiki_index.py or pass --rebuild", file=sys.stderr)
    data = build_index(root)
    return data, open_database(root, data, from_disk=False)


def fts_query(query: str) -> str | None:
    tokens = TOKEN_RE.findall(query)
    if not tokens:
        return None
    return " ".join(f'"{token}"*' for token in tokens)


def search(
    connection: sqlite3.Connection, query: str, limit: int, page_type: str | None
) -> list[tuple[str, str, str]]:
    match = fts_query(query)
    if match is None:
        raise ValueError("no searchable terms in query")
    sql = (
        "SELECT p.slug, p.type, p.summary FROM pages_fts "
        "JOIN pages p ON p.slug = pages_fts.slug "
        "WHERE pages_fts MATCH ?"
    )
    params: list[object] = [match]
    if page_type:
        sql += " AND p.type = ?"
        params.append(page_type)
    sql += " ORDER BY bm25(pages_fts, 0.0, 5.0, 1.0) LIMIT ?"
    params.append(limit)
    rows = connection.execute(sql, params).fetchall()
    return [(slug, kind, summary[:SNIPPET_MAX_CHARS]) for slug, kind, summary in rows]


def backlinks(edges: dict[str, list[str]], slug: str) -> list[str]:
    return sorted(source for source, targets in edges.items() if slug in targets)


def shortest_path(edges: dict[str, list[str]], start: str, goal: str) -> list[str] | None:
    """Breadth-first search over outbound wiki links, so the first path found is a shortest one."""
    parents: dict[str, str | None] = {start: None}
    queue: deque[str] = deque([start])
    while queue:
        node = queue.popleft()
        if node == goal:
            path: list[str] = []
            current: str | None = node
            while current is not None:
                path.append(current)
                current = parents[current]
            return list(reversed(path))
        for target in edges.get(node, []):
            if target not in parents:
                parents[target] = node
                queue.append(target)
    return None


def run_benchmark(connection: sqlite3.Connection, benchmark: Path, limit: int) -> int:
    payload = json.loads(benchmark.read_text(encoding="utf-8"))
    questions = payload.get("questions") if isinstance(payload, dict) else None
    if not isinstance(questions, list) or not all(
        isinstance(item, dict)
        and isinstance(item.get("question"), str)
        and isinstance(item.get("expected"), list)
        for item in questions
    ):
        raise WikiSchemaError(f"benchmark file must hold a `questions` list of question/expected objects: {benchmark}")
    hits = 0
    for item in questions:
        slugs = {slug for slug, _, _ in search(connection, item["question"], limit, None)}
        if slugs & set(item["expected"]):
            hits += 1
        else:
            print(f"miss: {item['question']}")
    print(f"hit@{limit}: {hits}/{len(questions)}")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search and navigate wiki pages without reading every page.")
    parser.add_argument("query", nargs="?", help="Words to search in page titles and summaries.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to the current directory.")
    parser.add_argument("--limit", type=int, default=5, help="Maximum hits to print.")
    parser.add_argument("--type", choices=sorted(PAGE_TYPE_DIRS), help="Only return pages of this type.")
    parser.add_argument("--backlinks", metavar="SLUG", help="List pages that link to SLUG.")
    parser.add_argument("--path", nargs=2, metavar=("FROM", "TO"), help="Shortest wiki-link chain from FROM to TO.")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild wiki/.index.* artifacts before searching.")
    parser.add_argument("--benchmark", metavar="FILE", help="Score hit@LIMIT over a benchmark JSON file.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if not any((args.query, args.backlinks, args.path, args.benchmark, args.rebuild)):
        print("give a query, --backlinks, --path, --benchmark, or --rebuild", file=sys.stderr)
        return 2
    try:
        data, connection = load_state(root, args.rebuild)
    except (WikiSchemaError, OSError) as exc:
        print(f"search failed: {exc}", file=sys.stderr)
        return 1

    try:
        if args.benchmark:
            try:
                return run_benchmark(connection, Path(args.benchmark), args.limit)
            except (WikiSchemaError, OSError, json.JSONDecodeError) as exc:
                print(f"benchmark failed: {exc}", file=sys.stderr)
                return 2
        if args.backlinks:
            if args.backlinks not in data.edges:
                print(f"unknown slug: {args.backlinks}", file=sys.stderr)
                return 1
            for slug in backlinks(data.edges, args.backlinks):
                print(slug)
            return 0
        if args.path:
            start, goal = args.path
            unknown = [slug for slug in (start, goal) if slug not in data.edges]
            if unknown:
                print(f"unknown slug: {unknown[0]}", file=sys.stderr)
                return 1
            chain = shortest_path(data.edges, start, goal)
            if chain is None:
                print(f"no path: {start} -> {goal}")
                return 1
            print(" -> ".join(chain))
            return 0
        if args.query:
            try:
                hits = search(connection, args.query, args.limit, args.type)
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return 2
            for slug, kind, summary in hits:
                print(f"{slug} [{kind}] {summary}")
            return 0
        return 0
    finally:
        connection.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

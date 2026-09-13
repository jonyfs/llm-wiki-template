#!/usr/bin/env python3
from __future__ import annotations

import argparse
import heapq
import json
import sys
from collections import deque
from pathlib import Path

from wiki_schema import (
    MarkdownPage,
    WikiSchemaError,
    discover_pages,
    serialize_page,
    set_raw_sha256,
    sha256_file,
    validate_refresh_pages,
)


def write_page_if_changed(page: MarkdownPage) -> bool:
    new_text = page.path.read_text(encoding="utf-8")
    rendered = serialize_page(page)
    if rendered == new_text:
        return False
    page.path.write_text(rendered, encoding="utf-8")
    return True


def topo_sort(
    targets: set[str],
    dependencies: dict[str, set[str]],
    reverse_dependencies: dict[str, set[str]],
) -> list[str]:
    indegree = {
        slug: len([dep for dep in dependencies.get(slug, set()) if dep in targets])
        for slug in targets
    }
    ready = [slug for slug, count in indegree.items() if count == 0]
    heapq.heapify(ready)
    order: list[str] = []

    while ready:
        slug = heapq.heappop(ready)
        order.append(slug)
        for dependent in sorted(reverse_dependencies.get(slug, set())):
            if dependent not in indegree:
                continue
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                heapq.heappush(ready, dependent)

    if len(order) != len(targets):
        remaining = sorted(targets - set(order))
        raise WikiSchemaError(
            "dependency cycle detected in `sources` frontmatter: " + ", ".join(remaining)
        )

    return order


def build_report(
    mode: str,
    root: Path,
    pages_by_slug: dict[str, MarkdownPage],
    dependencies: dict[str, set[str]],
    reverse_dependencies: dict[str, set[str]],
    roots: dict[str, list[str]],
    changed_files: list[dict[str, object]],
) -> dict[str, object]:
    if mode == "full-rebuild":
        targets = set(pages_by_slug)
    else:
        targets = set(roots)
        queue = deque(sorted(roots))
        while queue:
            slug = queue.popleft()
            for dependent in sorted(reverse_dependencies.get(slug, set())):
                if dependent in targets:
                    continue
                targets.add(dependent)
                queue.append(dependent)

    refresh_order = topo_sort(targets, dependencies, reverse_dependencies) if targets else []
    refresh_rows = []
    for slug in refresh_order:
        page = pages_by_slug[slug]
        if slug in roots:
            reasons = roots[slug]
        else:
            reasons = sorted(
                f"depends_on:{dep}"
                for dep in dependencies.get(slug, set())
                if dep in targets
            )
        refresh_rows.append(
            {
                "slug": slug,
                "type": page.page_type,
                "path": page.rel_path,
                "depends_on": sorted(dep for dep in dependencies.get(slug, set()) if dep in targets),
                "reasons": reasons,
            }
        )

    return {
        "mode": mode,
        "repo_root": root.as_posix(),
        "changed_raw_files": changed_files,
        "refresh_roots": [
            {
                "slug": slug,
                "path": pages_by_slug[slug].rel_path,
                "type": pages_by_slug[slug].page_type,
                "reasons": roots[slug],
            }
            for slug in sorted(roots)
        ],
        "refresh_order": refresh_rows,
    }


def run(root: Path, full_rebuild: bool) -> dict[str, object]:
    pages = discover_pages(root)
    slug_map, raw_refs, raw_paths, dependencies, reverse_dependencies = validate_refresh_pages(pages, root)

    mode = "full-rebuild" if full_rebuild else "changed-only"
    roots: dict[str, list[str]] = {}
    changed_files: list[dict[str, object]] = []

    for slug in sorted(raw_refs):
        page = slug_map[slug]
        old_digest = str(page.frontmatter.get("raw_sha256", "")).strip() or None
        new_digest = sha256_file(Path(raw_paths[slug]))

        reasons: list[str] = []
        if old_digest is None:
            reasons.append("missing_hash")
        elif old_digest != new_digest:
            reasons.append("hash_changed")
        if full_rebuild:
            reasons.append("full_rebuild")

        if old_digest != new_digest:
            set_raw_sha256(page, new_digest)
            write_page_if_changed(page)

        if old_digest != new_digest:
            changed_files.append(
                {
                    "raw_path": raw_refs[slug],
                    "source_slug": slug,
                    "source_path": page.rel_path,
                    "old_sha256": old_digest,
                    "new_sha256": new_digest,
                }
            )

        if reasons:
            roots[slug] = sorted(set(reasons))

    return build_report(mode, root, slug_map, dependencies, reverse_dependencies, roots, changed_files)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan wiki page refresh work from raw-source drift."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root to scan. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--full-rebuild",
        action="store_true",
        help="Report the full wiki dependency graph regardless of hash drift.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    try:
        report = run(root=root, full_rebuild=args.full_rebuild)
    except WikiSchemaError as exc:
        print(f"refresh failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import heapq
import json
import sys
from pathlib import Path

from wiki_schema import (
    MarkdownPage,
    ScriptCache,
    WikiSchemaError,
    atomic_write_text,
    discover_pages,
    parse_frontmatter,
    serialize_page,
    set_raw_sha256,
    validate_refresh_pages,
)


def write_page_if_changed(page: MarkdownPage) -> bool:
    original = page.source_text if page.source_text is not None else page.path.read_text(encoding="utf-8")
    rendered = serialize_page(page)
    if rendered == original:
        return False
    if parse_frontmatter(rendered, page.rel_path) == parse_frontmatter(original, page.rel_path):
        return False
    atomic_write_text(page.path, rendered)
    page.source_text = rendered
    return True


def topo_sort(
    targets: set[str],
    dependencies: dict[str, set[str]],
    reverse_sorted: dict[str, list[str]],
) -> list[str]:
    indegree = {
        slug: len([dep for dep in dependencies.get(slug, set()) if dep in targets])
        for slug in targets
    }
    # The ready set is a heap so the smallest slug is emitted first. The order must be deterministic:
    # completion order would follow set iteration and make refresh_order differ between runs.
    ready = [slug for slug, count in indegree.items() if count == 0]
    heapq.heapify(ready)
    order: list[str] = []

    while ready:
        slug = heapq.heappop(ready)
        order.append(slug)
        for dependent in reverse_sorted.get(slug, []):
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


def dependent_closure(roots: set[str], reverse_sorted: dict[str, list[str]]) -> set[str]:
    targets = set(roots)
    pending = list(roots)
    while pending:
        slug = pending.pop()
        for dependent in reverse_sorted.get(slug, []):
            if dependent not in targets:
                targets.add(dependent)
                pending.append(dependent)
    return targets


def build_report(
    mode: str,
    pages_by_slug: dict[str, MarkdownPage],
    dependencies: dict[str, set[str]],
    reverse_sorted: dict[str, list[str]],
    roots: dict[str, list[str]],
    changed_files: list[dict[str, object]],
    verbose: bool,
) -> dict[str, object]:
    if mode == "full-rebuild":
        targets = set(pages_by_slug)
    else:
        targets = dependent_closure(set(roots), reverse_sorted)

    refresh_order = topo_sort(targets, dependencies, reverse_sorted) if targets else []
    refresh_rows = []
    for slug in refresh_order:
        row: dict[str, object] = {"slug": slug, "path": pages_by_slug[slug].rel_path}
        if verbose:
            depends_on = sorted(dep for dep in dependencies.get(slug, set()) if dep in targets)
            reasons = roots[slug] if slug in roots else [f"depends_on:{dep}" for dep in depends_on]
            row.update({"type": pages_by_slug[slug].page_type, "depends_on": depends_on, "reasons": reasons})
        refresh_rows.append(row)

    return {
        "mode": mode,
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


def run(root: Path, full_rebuild: bool, verbose: bool = False, use_cache: bool = True) -> dict[str, object]:
    cache = ScriptCache(root, enabled=use_cache)
    pages = discover_pages(root, cache=cache)
    slug_map, raw_refs, raw_paths, dependencies, reverse_dependencies = validate_refresh_pages(pages, root)
    reverse_sorted = {slug: sorted(deps) for slug, deps in reverse_dependencies.items()}

    mode = "full-rebuild" if full_rebuild else "changed-only"
    roots: dict[str, list[str]] = {}
    changed_files: list[dict[str, object]] = []

    for slug in sorted(raw_refs):
        page = slug_map[slug]
        old_digest = str(page.frontmatter.get("raw_sha256", "")).strip() or None
        new_digest = cache.digest(Path(raw_paths[slug]), raw_refs[slug])

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

    cache.save()
    return build_report(mode, slug_map, dependencies, reverse_sorted, roots, changed_files, verbose)


def render_text(report: dict[str, object], verbose: bool) -> list[str]:
    rows = report["refresh_order"]
    changed = report["changed_raw_files"]
    changed_total = report.get("changed_raw_files_total", len(changed))
    rows_total = report.get("refresh_order_total", len(rows))
    lines = [f"refresh {report['mode']}: {changed_total} changed raw file(s), {rows_total} page(s) to refresh"]
    for change in changed:
        lines.append(f"  changed: {change['raw_path']} -> {change['source_slug']}")
    if rows:
        lines.append("order: " + ", ".join(row["slug"] for row in rows))
    if verbose:
        for row in rows:
            lines.append(f"  {row['slug']}: {', '.join(row['reasons'])}")
    return lines


def render_summary(report: dict[str, object]) -> list[str]:
    """One count line per reason kind instead of every per-page row."""
    counts: dict[str, int] = {}
    for row in report["refresh_roots"]:
        for reason in row["reasons"]:
            counts[reason] = counts.get(reason, 0) + 1
    lines = [
        f"refresh {report['mode']}: {len(report['changed_raw_files'])} changed raw file(s), "
        f"{len(report['refresh_order'])} page(s) to refresh"
    ]
    lines.extend(f"  {reason}: {counts[reason]}" for reason in sorted(counts))
    return lines


LIMITED_REPORT_KEYS = ("changed_raw_files", "refresh_roots", "refresh_order")


def limit_report(report: dict[str, object], limit: int) -> dict[str, object]:
    """Cap each listed row set at `limit` rows; full size moves to `<key>_total`. 0 means no cap."""
    if limit > 0:
        for key in LIMITED_REPORT_KEYS:
            rows = report[key]
            if len(rows) > limit:
                report[f"{key}_total"] = len(rows)
                report[key] = rows[:limit]
    return report


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
    parser.add_argument("--json", action="store_true", help="Print the report as one compact JSON object.")
    parser.add_argument("--verbose", action="store_true", help="Include reasons, types, and dependencies per page.")
    parser.add_argument("--quiet", action="store_true", help="Print nothing; set the exit status only.")
    parser.add_argument("--summary", action="store_true", help="Print counts per reason kind instead of per-page rows.")
    parser.add_argument("--limit", type=int, default=0, help="Cap rows per listed section (0 = no cap).")
    parser.add_argument("--no-cache", action="store_true", help="Do not read or write the .cache/ digest cache.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    try:
        report = run(root=root, full_rebuild=args.full_rebuild, verbose=args.verbose, use_cache=not args.no_cache)
    except WikiSchemaError as exc:
        print(f"refresh failed: {exc}", file=sys.stderr)
        return 1

    if args.quiet:
        return 0
    if args.json:
        print(json.dumps(limit_report(report, args.limit), separators=(",", ":")))
        return 0
    lines = render_summary(limit_report(report, args.limit)) if args.summary else render_text(limit_report(report, args.limit), args.verbose)
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

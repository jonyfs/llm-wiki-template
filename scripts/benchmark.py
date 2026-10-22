#!/usr/bin/env python3
"""Time lint and refresh on a generated wiki. Usage: benchmark.py [--pages N] [--profile]."""
from __future__ import annotations

import argparse
import cProfile
import hashlib
import io
import pstats
import sys
import tempfile
import time
from pathlib import Path

import lint
import refresh


def source_text(index: int, concept: int, digest: str) -> str:
    return f"""---
title: "Source {index}"
type: "source"
source_role: "primary"
sources:
  - "[[raw/src-{index}.md]]"
raw_sha256: "{digest}"
created_at: "2026-04-08"
updated_at: "2026-04-08"
---

Lead for source {index}.

## Summary
Summary for source {index}.

## Key takeaways
Takeaway for source {index}.

## Evidence or notable details
Evidence for source {index}.

## Related pages
- [[concept-{concept}]]

## Open questions
Open question for source {index}.
"""


def concept_text(index: int, source_count: int) -> str:
    source = index % source_count
    chain = f'  - "[[concept-{index - 1}]]"\n' if index > 0 else ""
    return f"""---
title: "Concept {index}"
type: "concept"
sources:
  - "[[src-{source}]]"
{chain}created_at: "2026-04-08"
updated_at: "2026-04-08"
---

Lead for concept {index}.

## Summary
Summary for concept {index}.

## Why it matters
Why concept {index} matters.

## Current understanding
Current understanding of concept {index}.

## Related pages
- [[src-{source}]]

## Open questions or tensions
Open question for concept {index}.
"""


def write_wiki(root: Path, pages: int) -> None:
    source_count = max(1, pages // 2)
    concept_count = max(1, pages - source_count)
    for name in ("sources", "entities", "concepts", "syntheses"):
        (root / "wiki" / name).mkdir(parents=True)
    (root / "raw").mkdir()

    index_lines = ["# Index", "", "## Learning paths", "", "- Bench path: [[src-0]] -> [[concept-0]]", ""]
    index_lines += ["## Sources", ""]
    for index in range(source_count):
        text = f"Raw text for source {index}.\n"
        (root / "raw" / f"src-{index}.md").write_text(text, encoding="utf-8")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        (root / "wiki" / "sources" / f"src-{index}.md").write_text(
            source_text(index, index % concept_count, digest), encoding="utf-8"
        )
        index_lines.append(f"- [[src-{index}]] - Synthetic source {index}.")
    index_lines += ["", "## Concepts", ""]
    for index in range(concept_count):
        (root / "wiki" / "concepts" / f"concept-{index}.md").write_text(
            concept_text(index, source_count), encoding="utf-8"
        )
        index_lines.append(f"- [[concept-{index}]] - Synthetic concept {index}.")
    (root / "wiki" / "index.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    (root / "wiki" / "log.md").write_text(
        "# Log\n\n## [2026-04-08] ingest | Benchmark wiki\n\nSynthetic entry for timing.\n",
        encoding="utf-8",
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Time lint and refresh on a synthetic wiki.")
    parser.add_argument("--pages", type=int, default=1000, help="Number of content pages to generate (min 2).")
    parser.add_argument("--profile", action="store_true", help="Print the top cumulative cProfile hotspots.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="wiki-bench-") as temp_dir:
        root = Path(temp_dir)
        write_wiki(root, max(2, args.pages))

        profiler = cProfile.Profile() if args.profile else None
        if profiler:
            profiler.enable()
        started = time.perf_counter()
        lint_report = lint.run(root, use_cache=False)
        lint_seconds = time.perf_counter() - started

        started = time.perf_counter()
        refresh.run(root, full_rebuild=True, use_cache=False)
        refresh_seconds = time.perf_counter() - started
        if profiler:
            profiler.disable()

    print(f"pages: {args.pages}")
    print(f"lint: {lint_seconds:.3f}s")
    print(f"lint violations: {lint_report['violation_count']}")
    print(f"refresh: {refresh_seconds:.3f}s (full rebuild)")
    if profiler:
        stream = io.StringIO()
        pstats.Stats(profiler, stream=stream).sort_stats("cumulative").print_stats(15)
        print(stream.getvalue())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

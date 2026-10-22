#!/usr/bin/env python3
"""Print a markdown heading outline and an optional token-budget chunk plan.

Agents read the outline first, then read only the needed line ranges with offset and limit.
Token counts are estimates (characters / 4), not tokenizer output.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from wiki_schema import iter_body_lines


HEADING_ANY_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
CHARS_PER_TOKEN = 4


@dataclass(frozen=True)
class Section:
    level: int
    title: str
    line: int


@dataclass
class Chunk:
    start: int
    end: int
    tokens: int


def estimate_tokens(char_count: int) -> int:
    return -(-char_count // CHARS_PER_TOKEN)


def outline(text: str) -> list[Section]:
    sections: list[Section] = []
    for line_no, line in iter_body_lines(text):
        match = HEADING_ANY_RE.match(line)
        if match:
            sections.append(Section(level=len(match.group(1)), title=match.group(2), line=line_no))
    return sections


def _line_tokens(lines: list[str], start: int, end: int) -> int:
    return estimate_tokens(sum(len(lines[index - 1]) + 1 for index in range(start, end + 1)))


def plan_chunks(text: str, budget_tokens: int) -> list[Chunk]:
    """Group consecutive heading-delimited units into chunks of at most `budget_tokens` where possible.

    A unit larger than the budget becomes its own chunk; it is never split mid-section.
    """
    lines = text.splitlines()
    if not lines:
        return []
    starts = [section.line for section in outline(text)]
    if not starts or starts[0] != 1:
        starts.insert(0, 1)
    units: list[tuple[int, int]] = []
    for index, start in enumerate(starts):
        end = starts[index + 1] - 1 if index + 1 < len(starts) else len(lines)
        if end >= start:
            units.append((start, end))

    chunks: list[Chunk] = []
    current: Chunk | None = None
    for start, end in units:
        tokens = _line_tokens(lines, start, end)
        if current is not None and current.tokens + tokens <= budget_tokens:
            current.end = end
            current.tokens += tokens
            continue
        if current is not None:
            chunks.append(current)
        current = Chunk(start=start, end=end, tokens=tokens)
    if current is not None:
        chunks.append(current)
    return chunks


def render_outline(text: str) -> list[str]:
    lines = text.splitlines()
    sections = outline(text)
    if not sections:
        return ["no headings"]
    rendered: list[str] = []
    for index, section in enumerate(sections):
        end = sections[index + 1].line - 1 if index + 1 < len(sections) else len(lines)
        tokens = _line_tokens(lines, section.line, end)
        rendered.append(
            f"L{section.line} h{section.level} {section.title} (lines {section.line}-{end}, ~{tokens} tokens)"
        )
    return rendered


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print a markdown heading outline with line numbers.")
    parser.add_argument("path", help="Markdown file to outline.")
    parser.add_argument(
        "--budget",
        type=int,
        metavar="TOKENS",
        help="Also print a chunk plan where each chunk is about TOKENS tokens (estimated).",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        text = Path(args.path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"cannot read {args.path}: {exc}", file=sys.stderr)
        return 1
    for line in render_outline(text):
        print(line)
    if args.budget is not None:
        if args.budget <= 0:
            print("--budget must be positive", file=sys.stderr)
            return 2
        for number, chunk in enumerate(plan_chunks(text, args.budget), start=1):
            print(f"chunk {number}: lines {chunk.start}-{chunk.end} (~{chunk.tokens} tokens)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Keep the agent entry points as real copies of their sources.

Every `mirror` line in .agents/template-manifest names a path (`CLAUDE.md`, `.claude/skills`, ...) and the source it must copy (`AGENTS.md`, `.agents/skills`, ...). The copies are real files and folders, not symlinks: Git on Windows often checks symlinks out as plain text files, which hides the skills and commands from Claude Code.

Usage:
  python3 scripts/sync_agent_files.py           copy every source over its mirror
  python3 scripts/sync_agent_files.py --check   fail if any mirror differs from its source (writes nothing)

Standard library only, so it runs wherever Python 3.9+ runs.
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def mirror_pairs(root: Path) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for line in (root / ".agents" / "template-manifest").read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) == 3 and parts[0] == "mirror":
            pairs.append((parts[1], parts[2]))
    return pairs


# Conflict leftovers written by scripts/update-llm-wiki.sh next to a file it could not merge. They are not template content.
CONFLICT_SUFFIXES = (".template-new", ".template-base")


def is_conflict_leftover(path: Path) -> bool:
    return path.name.endswith(CONFLICT_SUFFIXES)


def files_under(folder: Path) -> list[Path]:
    return sorted(p.relative_to(folder) for p in folder.rglob("*") if (p.is_file() or p.is_symlink()) and not is_conflict_leftover(p))


def same_tree(target: Path, source: Path) -> bool:
    if target.is_symlink() or not target.exists():
        return False
    if source.is_dir():
        if not target.is_dir():
            return False
        source_files = files_under(source)
        target_files = files_under(target)
        if source_files != target_files:
            return False
        return all(
            not (target / rel).is_symlink() and filecmp.cmp(source / rel, target / rel, shallow=False)
            for rel in source_files
        )
    return target.is_file() and not target.is_symlink() and filecmp.cmp(source, target, shallow=False)


def remove(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def copy_source(source: Path, target: Path) -> None:
    remove(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target, symlinks=False, ignore=shutil.ignore_patterns("*" + CONFLICT_SUFFIXES[0], "*" + CONFLICT_SUFFIXES[1]))
    else:
        shutil.copyfile(source, target)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="report drift and exit 1 instead of copying")
    parser.add_argument("--root", type=Path, default=repo_root(), help="repository root (default: this repo)")
    args = parser.parse_args(argv)
    root = args.root.resolve()

    pairs = mirror_pairs(root)
    if not pairs:
        print("no mirror lines in .agents/template-manifest", file=sys.stderr)
        return 1

    drift = []
    for target_rel, source_rel in pairs:
        target, source = root / target_rel, root / source_rel
        if not source.exists():
            print(f"missing source: {source_rel}", file=sys.stderr)
            return 1
        if args.check:
            if not same_tree(target, source):
                drift.append(target_rel)
        elif not same_tree(target, source):
            copy_source(source, target)
            print(f"synced {target_rel} <- {source_rel}")

    if args.check:
        for rel in drift:
            print(f"out of sync: {rel}", file=sys.stderr)
        if drift:
            print("run: python3 scripts/sync_agent_files.py", file=sys.stderr)
            return 1
        print(f"{len(pairs)} mirrors in sync")
    return 0


if __name__ == "__main__":
    sys.exit(main())

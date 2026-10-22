#!/usr/bin/env python3
"""List raw/ files with digests and first headings, and check candidates for duplicates.

The manifest is written to wiki/.manifest.json (generated, git-ignored). raw/ is only ever read.
Duplicate detection compares normalized text (casefolded, whitespace collapsed), so the same article
under two URLs with different formatting is still caught.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from wiki_schema import atomic_write_text


MANIFEST_VERSION = 1
MANIFEST_NAME = ".manifest.json"


def normalize_text(text: str) -> str:
    return " ".join(text.casefold().split())


def normalized_digest(data: bytes) -> str:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return hashlib.sha256(data).hexdigest()
    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()


def first_heading(data: bytes) -> str | None:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def manifest_entry(path: Path, rel_path: str) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": rel_path,
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "normalized_sha256": normalized_digest(data),
        "first_heading": first_heading(data),
    }


def build_manifest(root: Path) -> list[dict[str, object]]:
    raw_root = root / "raw"
    entries = [
        manifest_entry(path, path.relative_to(root).as_posix())
        for path in sorted(raw_root.rglob("*"))
        if path.is_file() and not any(part.startswith(".") for part in path.relative_to(raw_root).parts)
    ]
    return entries


def write_manifest(root: Path, entries: list[dict[str, object]]) -> Path:
    path = root / "wiki" / MANIFEST_NAME
    payload = {"version": MANIFEST_VERSION, "files": entries}
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(path, json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n")
    return path


def load_manifest(root: Path) -> list[dict[str, object]] | None:
    try:
        payload = json.loads((root / "wiki" / MANIFEST_NAME).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(payload, dict) or payload.get("version") != MANIFEST_VERSION:
        return None
    files = payload.get("files")
    return files if isinstance(files, list) else None


def find_duplicates(entries: list[dict[str, object]], candidate: bytes) -> list[str]:
    exact = hashlib.sha256(candidate).hexdigest()
    normal = normalized_digest(candidate)
    return [
        str(entry["path"])
        for entry in entries
        if entry.get("sha256") == exact or entry.get("normalized_sha256") == normal
    ]


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manifest of raw/ files and duplicate check for candidates.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to the current directory.")
    parser.add_argument("--check", metavar="FILE", help="Report raw/ files that duplicate FILE; exit 1 on a match.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if args.check:
        entries = load_manifest(root)
        if entries is None:
            entries = build_manifest(root)
        duplicates = find_duplicates(entries, Path(args.check).read_bytes())
        if duplicates:
            for path in duplicates:
                print(f"duplicate of {path}")
            return 1
        print("no duplicate in raw/")
        return 0

    entries = build_manifest(root)
    write_manifest(root, entries)
    print(f"manifest ok: {len(entries)} raw files")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

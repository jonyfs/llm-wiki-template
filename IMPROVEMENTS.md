# LLM Wiki: Improvement Catalog

This document lists 100 candidate improvements for this repository. It began as a proposal; the operator selects which items to implement. Items marked `Resolved:` record work already merged, verified against the code at the time of the note.

## Scope and method

The repository is a three-layer LLM Wiki: `raw/` (curated sources), `wiki/` (LLM-maintained markdown), and `AGENTS.md` plus `.agents/skills/` (the operating contract). At baseline it had three stdlib-only Python scripts (`scripts/lint.py`, `scripts/refresh.py`, `scripts/wiki_schema.py`) and 24 unit tests; later batches add more, named in the item notes.

Baseline at HEAD `72d80b0`: `python3 -m unittest discover -s tests -t .` passes all 24 tests.

Token footprint measured on the current files:

- `AGENTS.md`: 32,736 bytes, loaded on every session.
- Skills: `wiki-writing` 14,734 B, `wiki-query` 8,877 B, `wiki` 7,987 B, `wiki-ingest` 7,745 B, `wiki-maintenance` 5,743 B.
- `README.md`: 4,167 bytes.
- `wiki/index.md`: placeholder text only (no real entries yet).

The largest recurring token cost is the always-loaded `AGENTS.md`, followed by whichever skill is loaded for a task. Scripts are cheap in tokens but produce verbose JSON that the agent must read.

## Verified defect (highest priority)

> Resolved: `parse_scalar` unescapes only `\\` and `\"` via `unescape_double_quoted`; see item 1.

`scripts/wiki_schema.py` `parse_scalar` decodes quoted values with `bytes(value, "utf-8").decode("unicode_escape")`. This corrupts non-ASCII text. Reproduced: the string `Coordenação de Ação — café` does not survive a round-trip; it comes back as mojibake (`CoordenaÃ§Ã£o...`). The corruption is reachable through `refresh.py`, because `serialize_page` rewrites the full frontmatter from parsed values whenever a source hash changes. An accented title, author, or publisher on a source page is silently damaged on refresh. Fix by unescaping only backslash and double-quote sequences, or by using a real YAML parser.

## 1. Correctness and data integrity

1. Fix `parse_scalar` so non-ASCII frontmatter values survive a refresh round-trip. Add a regression test with accented titles. Resolved: `parse_scalar` now unescapes only `\\` and `\"` (`unescape_double_quoted`); regression tests cover accented titles and the refresh round-trip.
2. Add a round-trip test: parse then serialize a page and assert byte-equal frontmatter for representative values. Resolved: `test_round_trip_is_byte_equal_for_representative_frontmatter` in `tests/test_wiki_schema.py`.
3. Make `serialize_page` preserve original key order and quoting style, so refresh produces minimal diffs.
4. Make `refresh.py` write atomically (write to a temp file in the same directory, then `os.replace`) to avoid truncated pages on crash.
5. Check for duplicate frontmatter keys during parse and report them as errors instead of silently overwriting.
6. Reject frontmatter values that contain an unescaped `"` in quoted scalars before parsing, with a clear message.
7. Validate `raw_sha256` is exactly 64 lowercase hex characters in lint, not only present.
8. Validate that `created_at` is not later than `updated_at`.
9. Validate that `published_at` is a real calendar date (for example reject `2026-02-30`), not only a regex match.
10. Validate `canonical_url` host and reject URLs with embedded credentials.
11. Detect a `source` page that cites another `source` page as its only supporting link, since the raw reference is the only valid backing.
12. Detect a `source` page whose raw file has been deleted but whose page is still listed in `wiki/index.md` (lint, not only refresh).
13. Detect dependency cycles in lint, not only in refresh.
14. Detect self-referencing `sources` entries.
15. Warn when `title` in frontmatter differs from the first `#` heading or the index summary anchor.

## 2. Lint coverage gaps against AGENTS.md

16. Implement lint item 3: orphan page detection (pages with no inbound wiki links from other pages or the index).
17. Implement lint item 4: broken wikilinks inside the body text (currently only frontmatter and index are checked).
18. Implement lint item 15: missing or stale learning-path detection in `wiki/index.md`.
19. Implement lint item 16: prose-density heuristic (flag sentences over a word threshold) as an advisory warning.
20. Detect `[[raw/...]]` body links that point to files outside `raw/` or to files that do not exist.
21. Detect `![[raw/assets/...]]` embeds whose asset file is missing.
22. Detect markdown footnotes that reference raw files not listed in `sources` (drift between prose and frontmatter).
23. Detect `synthesis` pages whose `## Related pages` list is identical to another synthesis page (near-duplicate detection).
24. Add a near-duplicate check using normalized titles (casefolded, punctuation stripped) across all pages.
25. Detect slug drift: a file name that differs from `title` by more than a threshold, as a warning.
26. Lint `wiki/log.md` headings against the `## [YYYY-MM-DD] operation | title` format.
27. Detect `wiki/log.md` entries with dates later than today or not in chronological order.
28. Detect files under `wiki/` that are neither index-listed content pages nor the two required files.
29. Detect files inside `raw/` that changed without a corresponding source page (report only, never write).
30. Add `--format text|json` so humans get a short report and agents get structured output.

## 3. Output and token efficiency of the scripts

31. Print the JSON success report only with `--verbose`. Default success output should be one line, such as `lint ok: 4 pages, 0 violations`. Resolved: default prints the one-line summary; `--verbose` adds the JSON report.
32. Make `refresh.py` default to a compact report, with the full JSON behind `--json`. Resolved: `render_text` is the default output; `--json` prints the compact report.
33. Emit only slugs and paths in `refresh_order` by default; move `reasons` and `depends_on` behind `--verbose`.
34. Use compact JSON separators (`separators=(",", ":")`) in machine mode. This is a real byte reduction for agents that parse the output. Resolved: all machine-mode output uses the compact separators.
35. Truncate long violation lists with a count and a `--limit N` flag, so a broken wiki does not flood the context window.
36. Group violations by file in the error output so each file name is printed once.
37. Add a `--quiet` flag that prints exit status only, for hook and CI use.
38. Make error messages shorter and stable, so repeated runs can be compared by diff.
39. Add a `--changed-only` lint mode that checks only files changed in git, reducing work and output on large wikis.
40. Add a `--summary` mode that prints counts per violation kind instead of every message.

## 4. Performance of the Python scripts

41. Parse each page once per run. `discover_pages` is called separately by each script, and every script reads and parses every page again. Resolved: `discover_pages` accepts a `ScriptCache`; each run parses each page at most once.
42. Cache parsed pages keyed by `(path, mtime_ns, size)` in a small JSON file under a git-ignored `.cache/` directory. Resolved: `ScriptCache` under `.cache/`, with `--no-cache` opt-out.
43. Cache SHA-256 digests of raw files keyed by `(path, mtime_ns, size)`. Today every raw file is re-hashed on every refresh. Resolved: the same `ScriptCache` stores digests keyed by path and validated by the `(mtime_ns, size)` stamp.
44. Use `os.scandir` or a single `Path.rglob` pass instead of several `glob` calls per content directory.
45. Compile regular expressions once at module level (mostly done; audit the remaining inline calls).
46. Remove the function-local `from wiki_schema import is_absolute_url` inside the `validate_frontmatter` loop; import at module top.
47. In `lint.py`, call `validate_related_pages` once per page instead of twice for synthesis pages.
48. Compute `find_section_ranges` once per page and reuse it for both the related-pages check and the evidence-base check.
49. Replace the nested scan in `find_section_ranges` (quadratic in the number of headings in the worst case) with a single linear pass.
50. Avoid reading a raw file fully when only its hash is needed: stream it in 64 KiB chunks (already done) and skip the re-hash when the cache is valid.
51. In `refresh.write_page_if_changed`, compare the rendered string with the in-memory original instead of re-reading the file from disk.
52. Avoid rewriting a page when only key order changed, by comparing parsed frontmatter dictionaries before writing.
53. Build the reverse-dependency graph once and reuse it for both closure computation and reporting.
54. Replace the deque BFS plus list rebuild in `build_report` with a set-based traversal that avoids repeated `sorted` calls inside the loop.
55. Precompute `sorted(reverse_dependencies[slug])` once instead of inside the BFS loop.
56. Use `heapq` only where the ordering matters; document why `topo_sort` needs deterministic order.
57. Add a benchmark script that generates a synthetic wiki of 1,000 pages and times lint and refresh, so performance claims are measured.
58. Profile the scripts with `cProfile` on the synthetic wiki and record the top hotspots in the PR description.
59. Consider PyYAML's C-accelerated loader only if an optional dependency is acceptable; the current zero-dependency rule should be kept by default. Resolved as not adopted: the zero-dependency rule is kept (decision 2026-10-22).
60. Evaluate `python-frontmatter` as an optional dependency only; it would replace the custom parser but breaks the stdlib-only property. Resolved as not adopted: same decision as item 59.
61. Add `__slots__` to the `MarkdownPage` and `Heading` dataclasses to reduce per-page memory on large wikis.
62. Make `discover_pages` lazy (generator) when the caller only needs slugs.
63. Avoid building `slug_map` twice (once in `lint.run` and once inside `validate_refresh_pages`).
64. Keep the scripts importable without executing `main` (already true; preserve it).

## 5. Search and retrieval (internal wiki)

65. Add a `scripts/wiki_index.py` that builds a compact machine-readable index (slug, type, title, one-line summary, outbound links) as JSON. Agents read this instead of scanning every page. Resolved: `scripts/wiki_index.py` writes `wiki/.index.json` (git-ignored).
66. Store the index as SQLite with an FTS5 table for full-text search over titles and summaries. Stdlib `sqlite3` supports FTS5 in most CPython builds, so no new dependency is needed. Resolved: `wiki/.index.sqlite` with a `pages_fts` FTS5 table; stdlib only.
67. Add `scripts/wiki_search.py "<query>" --limit 5` that returns slug, type, and the matching summary line only, not full pages. Resolved: `wiki_search.py` with `--limit` defaulting to 5 and snippets capped at 200 characters.
68. Return a snippet of at most 200 characters per hit, so one query costs a bounded number of tokens.
69. Add a `--type` filter (source, entity, concept, synthesis) to search.
70. Add a `--backlinks <slug>` query that lists pages linking to a slug, which replaces repeated grep work in `wiki-query`.
71. Add a `--path <a> <b>` query that returns the shortest link path between two pages (BFS over wiki links).
72. Maintain a precomputed `wiki/.graph.json` adjacency list so backlink and path queries do not reparse pages.
73. Make the search script the single entry point in `wiki-query`: run it first, then read only the returned pages.
74. Keep `wiki/index.md` as the human catalog, and generate a second, compact `wiki/.index.json` from it for agents. Do not hand-edit the JSON.
75. Add a freshness check: the search index stores the max `mtime` of its inputs and warns when stale.
76. Add a `--rebuild` flag and make the index optional; the wiki must still work without it (degradation path).
77. Measure retrieval quality with a set of 10 benchmark questions and their expected slugs, so changes to the index can be scored.

## 6. External search and source ingestion

78. Add a deduplication step before ingest: hash the normalized text of a candidate source and reject it if the hash already exists in `raw/` (prevents double ingest of the same article under two URLs).
79. Normalize `canonical_url` (strip tracking parameters such as `utm_*`) before storing it, so duplicate detection works.
80. Add a `scripts/raw_manifest.py` that lists every `raw/` file with its SHA-256, size, and first heading, so ingest decisions are made from a manifest instead of opening files.
81. Store that manifest outside `raw/` (for example `wiki/.manifest.json`), because `raw/` is protected corpus that must not be written by tooling.
82. Add a per-source token budget: when a raw file is over N tokens, ingest reads it in chunks guided by its headings instead of loading it whole.
83. Extract a heading outline per raw file with a script, so the agent reads the outline and only the needed sections.
84. Add a "claims ledger" format for each source page, so later queries can cite a claim without re-reading the raw text. Resolved: optional `## Claims ledger` section on source pages, one `- C<n>: <claim> [[raw/...]]` line per claim; `lint.py` validates ids and the canonical raw file.
85. Add `scripts/extract_outline.py` that prints heading levels and line numbers for a markdown file; agents then read with offset and limit.
86. For web material, add a conversion step that strips navigation, ads, and boilerplate before the file enters `raw/` (only when the user explicitly asks to add raw material, per AGENTS.md).
87. Record the fetch date and HTTP status in source frontmatter when a source came from the web, so staleness can be detected by lint.
88. Add a staleness rule: flag `source` pages whose `published_at` is older than a configurable number of years for fast-moving topics.
89. Add a rate-limit-aware retry helper for any future network fetch script, with a cache directory outside `raw/`.
90. Keep fetched web content cached under a git-ignored `.cache/` so repeated research does not refetch identical pages.

## 7. Skills, AGENTS.md, and repository gaps (token footprint of the harness)

91. Split `AGENTS.md` into a short always-loaded core (rules that apply to every turn) and load-on-demand sections (page templates, lint checklist, migration notes). Target: reduce the always-loaded file to under 8 KB. Resolved: `AGENTS.md` is under 8 KB; migration notes moved to `docs/migration.md`, templates and checklists to skill references.
92. Move the page body templates out of `AGENTS.md` into `wiki-writing`, which is loaded only when writing prose. Keep only the frontmatter schema in the core. Resolved: body templates live in `wiki-writing/references/body-templates.md`; only the frontmatter schema stays in `AGENTS.md`.
93. Move the "Migration for derived wikis" section into a separate skill or doc, since most sessions do not need it. Resolved: moved to `docs/migration.md`.
94. Move the "Pitfalls" and "Completion checklist" sections into `wiki-maintenance` and reference them by a one-line pointer from the core. Resolved: both live in `wiki-maintenance/references/checklists.md`.
95. Deduplicate repeated rules across `AGENTS.md` and the five skills (for example the `raw/` protection rule and the `[[raw/...]]` citation rule appear in more than one place). Keep one canonical statement and link to it.
96. Trim `wiki-writing` (14.7 KB, the largest skill) by moving examples into a `references/` subfolder that is read only on demand.
97. Add a `wiki-router` skill that maps a request to exactly one playbook, so the agent loads one skill instead of reading several.
98. Add a test that every skill folder under `.agents/skills/` has a `SKILL.md` with `name` and `description` frontmatter, and that `.claude/skills` and `.opencode/skills` resolve to it; also check that `CLAUDE.md`, `.cursorrules`, and `.github/copilot-instructions.md` resolve to `AGENTS.md`.
99. Add a CI workflow under `.github/workflows/` that runs the unit tests on every push and pull request. No workflow exists today.
100. Add `scripts/review-cycle.sh` and `scripts/push-guard.sh`, or remove the references to them. The `pr-reviewer` and `pr-fixer` skills reference both, but neither exists in this repository. Resolved: references removed; scripts live only in external skill directories.

## Recommended first batch

If the operator wants a small first step, the highest value items are:

- Items 1 and 2 (fix the verified non-ASCII corruption and add a regression test). This is a correctness defect, not an optimization.
- Items 31, 32, and 34 (compact script output, a direct token saving on every run).
- Items 41 to 43 (single parse and digest cache, a measurable speedup on larger wikis).
- Item 91 (shrink the always-loaded `AGENTS.md`, the largest recurring token cost).
- Items 65 to 67 (a compact search index, the main lever for reducing query-time token use).
- Item 99 (CI, so the test suite runs on every pull request).

## Open questions

- ~~Should the zero-dependency rule be kept?~~ Decided 2026-10-22: keep it. Items 59 and 60 are resolved as not adopted; SQLite FTS5 (items 65 to 67) is stdlib and unaffected.
- ~~Should the wiki search index (items 65 to 77) be committed to git or treated as a generated artifact?~~ Decided 2026-10-22: generated artifact. `.gitignore` excludes `wiki/.index.*`, `wiki/.graph.json*` and `wiki/.manifest.json*`. This decides artifact placement only; items 68 to 77 stay open unless marked.
- ~~Should `AGENTS.md` be split (item 91), given that every agent reads the whole file through its symlink?~~ Decided 2026-10-22: split done; the symlinks still resolve to `AGENTS.md`, now under 8 KB.
- Which benchmark questions (item 77) best represent the operator's real use?

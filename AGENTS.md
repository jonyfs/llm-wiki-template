# AGENTS.md

This repository follows an LLM wiki pattern inspired by Andrej Karpathy's `llm-wiki` gist. It keeps a persistent, compounding markdown wiki between the human and curated sources. This always-loaded file holds structure, schema, and routing. Playbooks live in `.agents/skills/`; long references are listed under "On-demand references".

Source of truth: [jonyfs/llm-wiki-template](https://github.com/jonyfs/llm-wiki-template). This file tracks that template plus the multi-agent configuration below.

## Purpose

1. `raw/` is curated source material. Read and cite it. Never add, modify, rename, rewrite, or reorganize files in `raw/` (including `raw/assets/`) unless the user explicitly asks.
2. `wiki/` is the persistent markdown wiki, maintained by the LLM.
3. `AGENTS.md` plus `.agents/skills/` define how the LLM operates on the wiki.

## Multi-agent configuration

Every agent reads this file through a symlink. Edit `AGENTS.md` only.

| File | Agent | Points to |
|------|-------|-----------|
| `CLAUDE.md` | Claude Code | `AGENTS.md` |
| `.cursorrules` | Cursor / OpenCode | `AGENTS.md` |
| `.github/copilot-instructions.md` | Copilot / Codex | `../AGENTS.md` |

`.agents/skills/` (and `.agents/commands/`) is the single source of truth. Each skill is a folder with a `SKILL.md` whose frontmatter has `name` and `description`.

| Path | Agent | Type |
|------|-------|------|
| `.claude/skills`, `.claude/commands` | Claude Code | symlink to `.agents/` |
| `.opencode/skills`, `.opencode/commands` | OpenCode | symlink to `.agents/` |
| `.agents/skills`, `.agents/commands` | Codex, Cursor, Copilot | native |

## Required repo-local skills

Load the relevant skill before substantive work, or `wiki-router` if unsure.

- `wiki-writing/`: before creating or materially revising wiki prose.
- `wiki-ingest/`: before ingesting new source material.
- `wiki-query/`: before answering wiki-grounded questions or filing a durable answer.
- `wiki/`: before a read-only wiki answer, when no file may be written.
- `wiki-maintenance/`: before refresh, lint, drift, or health-check work.
- `wiki-delete/`: before removing a page, link, footnote, or index entry about a subject that should not be in the wiki.
- `wiki-router/`: maps any request to exactly one of the skills above.

## Core principles

- Prefer updating existing pages over creating near-duplicates.
- Treat `wiki/index.md` as the first navigation surface.
- Record meaningful operations in `wiki/log.md`.
- Write in plain language with a professional tone. Define non-obvious terms.
- Teach the smallest useful model first, then add evidence, distinctions, examples, limits, and open questions.
- Preserve contradictions and open questions instead of forcing premature reconciliation.
- Keep the structure narrow. Do not add content directories, required metadata, or page types unless the user asks.

## Session orientation

Before substantive work on an existing wiki: read this file, load the relevant skill, read `wiki/index.md`, scan recent `wiki/log.md` entries, read the most relevant pages, and search `wiki/` for existing slugs before creating anything. Use `python3 scripts/wiki_search.py "<terms>"` when the wiki is large.

## Repository layout

Required files: `AGENTS.md`, `wiki/index.md`, `wiki/log.md`, and `.agents/skills/`.

Content pages live in `wiki/sources/`, `wiki/entities/`, `wiki/concepts/`, and `wiki/syntheses/`. One optional subject subfolder is allowed beneath each type directory (for example `wiki/sources/<subject>/<slug>.md`) to keep large wikis from accumulating hundreds of files in a single flat folder. No deeper nesting is allowed. Raw files may likewise be grouped into subject subfolders under `raw/`.

## Markdown conventions

- Write each prose paragraph as one logical line. No hard wraps, trailing spaces, or backslash breaks.
- Preserve structural layout: frontmatter, headings, lists, tables, and fenced code.

## Frontmatter schema

Every content page begins with YAML frontmatter:

```yaml
---
title: "Page Title"
type: "source|entity|concept|synthesis"
sources:
  - "[[raw/source-file.md]]"
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
---
```

Rules:

- `title` is the canonical human title. `type` is `source`, `entity`, `concept`, or `synthesis`.
- `sources` lists wiki-link strings: `[[raw/...]]` for raw files (including `[[raw/assets/...]]`), bare `[[slug]]` for supporting wiki pages. A `source` page cites exactly one canonical `[[raw/...]]` file.
- `created_at` (creation date) and `updated_at` (last material edit) are `YYYY-MM-DD`. All types require all five fields.
- `source` pages require `source_role`: `primary` (main evidence or specification), `secondary` (interprets primary material), `reference` (definitions, background), `operational` (live procedures, runbooks), or `informal` (notes, threads, chats). Classify by research use, not prestige.
- `source` pages may add `source_format` (`paper`, `article`, `book`, `report`, `spec`, `documentation`, `dataset`, `benchmark`, `transcript`, `notes`, `other`), `authors` (non-empty strings), `published_at` (`YYYY-MM-DD`), and `canonical_url` (absolute `http` or `https`).
- `source` pages require `raw_sha256`: the SHA-256 of the single canonical raw file, set by the creator at creation. `refresh` reconciles or bootstraps it.
- Keep the single-file source model. Appendices, dataset cards, and changelogs become separate `source` pages.
- `raw_sha256`, `source_role`, `source_format`, `authors`, `published_at`, and `canonical_url` must not appear on `entity`, `concept`, or `synthesis` pages.

Filenames are lowercase `kebab-case`, `<slug>.md`. Slugs are unique across all four content directories. On collision, append a short stable qualifier, and prefer updating an existing slug over an alternate spelling.

Create-vs-update and entity-vs-concept rules: `wiki-writing/references/page-decisions.md`.

## Writing and citations

- Every content page starts with a short unheaded lead, then the required sections for its type (`wiki-writing/references/body-templates.md`).
- Cite wiki pages inline with bare `[[slug]]` links. Cite direct raw support with a Markdown footnote whose first item is the `[[raw/...]]` link, then a short locator.
- Source pages may keep an optional `## Claims ledger` as their last section; cite a claim from other pages as `[[slug]] C<n>` (mechanics: `wiki-writing/references/citations.md`).
- Embed raw images only with `![[raw/assets/...]]`, never a website URL or relative path.
- Frontmatter `sources`, `Related pages`, and index entries use normal wiki links, not footnotes.
- Link new or materially updated pages to their most relevant related pages. Avoid isolated pages.
- Footnote mechanics: `wiki-writing/references/citations.md`.

## Operations

- Ingest (`wiki-ingest`): the source must already be in `raw/`. If a URL, PDF, or pasted text is not in `raw/`, ask before adding it. Update the `source` page first, then touched pages, then `wiki/index.md` and `wiki/log.md`.
- Query (`wiki-query` read-write, or `wiki` read-only): answer from the wiki first; `raw/` only for verification or gaps. Durable answers become `synthesis` pages only through `wiki-query`.
- Refresh and lint (`wiki-maintenance`): refresh reports raw drift and never rewrites pages merely because a source changed. Dependencies come only from `sources` frontmatter; body wikilinks are never dependencies. Lint is a health check.

## Index and log

- `wiki/index.md` is the category catalog with `Sources`, `Entities`, `Concepts`, and `Syntheses` sections. Each content page has one entry: a link and a one-line summary.
- Add a `## Learning paths` section before the catalogs once there are enough pages. Keep each path to three to seven pages, in learning order.
- `wiki/log.md` is chronological and append-only. Each entry starts with `## [YYYY-MM-DD] operation | title`.

## GitHub Pages synchronization

- The project publishes a static site from `index.html` via `.github/workflows/pages.yml`, which rebuilds on every push to `main`.
- **Rule:** any change to documentation (`README.md`, `docs/`, `DISCOVERABILITY.md`, `PAGES_IMPROVEMENTS.md`, `DESIGN_SYSTEM.md`, `AGENTS.md` sections, or `wiki/` content surfaced on the site) MUST be evaluated for inclusion in the published site. If the change affects what visitors should see, update `index.html` (or add the file to the workflow's `_site` copy list) in the same change, so documentation and GitHub Pages never drift.
- The workflow copies `README.md`, `docs/`, `assets/`, `llms.txt`, `llms-full.txt`, `robots.txt`, and `sitemap.xml` into `_site`. Add new documentation files to that copy list when they should be publicly readable.
- After editing docs, verify the site still builds (workflow green) and that the live URL reflects the change. A doc change that is not reflected on the site is an incomplete change.
- Derived wikis: if you fork this template, keep the same sync rule so your published docs stay current.

## On-demand references

- Body templates, section headings, example frontmatter: `.agents/skills/wiki-writing/references/body-templates.md`
- Citation mechanics: `.agents/skills/wiki-writing/references/citations.md`
- Create-vs-update and entity-vs-concept: `.agents/skills/wiki-writing/references/page-decisions.md`
- Lint checklist, pitfalls, completion checklist (run before finishing any wiki-changing task): `.agents/skills/wiki-maintenance/references/checklists.md`
- Migration for derived wikis: `docs/migration.md`

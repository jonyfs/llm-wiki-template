# LLM Wiki

An LLM wiki template that turns curated `raw/` sources into a persistent markdown knowledge base. It follows the LLM wiki pattern from Andrej Karpathy's [gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

## What is an LLM wiki?

Most tools that work with documents use retrieval. You upload files, and at query time the model pulls the relevant chunks and writes an answer from them. This works, but the model rebuilds its knowledge on every question. Nothing accumulates, and a subtle question that spans several documents means reassembling the same fragments each time.

An LLM wiki works the other way. The model reads each source once and writes what it learned into a folder of interlinked markdown pages. It updates entity pages, revises summaries, flags where new material contradicts old claims, and keeps a running synthesis. Knowledge gets compiled once and then kept current, instead of being re-derived on every query.

The result is a persistent, compounding artifact. Cross-references already exist, contradictions are already flagged, and each source you add or question you ask makes the wiki richer.

You rarely write the wiki yourself. You curate sources, explore, and ask questions; the model does the summarizing, cross-referencing, filing, and bookkeeping. Many people keep the agent open on one side and Obsidian on the other, browsing the updated pages as the model edits.

```mermaid
flowchart LR
    S[New source] -->|ingest| W[Wiki pages]
    Q[Questions] -->|query| W
    W -->|answers| Q
    Q -->|durable answers filed back| W
```

## How it works

The basic model is `raw/ -> wiki/`.

Three layers sit between you and the sources:

- `raw/` holds curated source documents: articles, papers, images, and data files. These are immutable. The model reads them but never modifies them.
- `wiki/` holds the markdown pages the model owns: source summaries, entity pages, concept pages, and syntheses.
- `AGENTS.md` is the schema. It tells the model how the wiki is structured, what the conventions are, and what to do when ingesting, answering, or maintaining.

```mermaid
flowchart TD
    YOU[You] -->|curate| RAW[raw/ - immutable sources]
    RAW -->|read| LLM[LLM]
    SCHEMA[AGENTS.md - schema] -->|rules| LLM
    SKILLS[.agents/skills/ - playbooks] -->|procedures| LLM
    LLM -->|writes and maintains| WIKI[wiki/ - markdown pages]
    WIKI -->|you read| YOU
```

The writing model is plain-language, answer-first wiki prose: teach the smallest useful model first, then deepen it with evidence, distinctions, examples, limits, and open questions.

## Repo structure

```
.
├── AGENTS.md                 # root contract: structure, schema, workflows
├── .agents/
│   ├── skills/               # repo-local playbooks (single source of truth)
│   └── commands/             # slash-command wrappers for ingest/query/lint/refresh/wiki
├── raw/                      # curated, immutable source documents
├── wiki/                     # LLM-maintained markdown pages
│   ├── index.md              # category catalog and learning paths
│   ├── log.md                # append-only operation log
│   ├── sources/              # one page per raw source
│   ├── entities/             # people, orgs, products, places
│   ├── concepts/             # ideas, methods, theories
│   └── syntheses/            # comparisons, maps, durable answers
├── scripts/                  # lint, refresh, search, schema helpers
├── tests/                    # unit tests for scripts and structure
└── docs/                     # migration notes for derived wikis
```

Multi-agent entry points (`CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`, `.claude/`, `.opencode/`) are symlinks to the single source of truth above, so one edit reaches every agent.

## Skills

Load the relevant skill before substantive work, or `wiki-router` when unsure. Each skill is a folder under `.agents/skills/` with a `SKILL.md`.

| Skill | Purpose |
|-------|---------|
| `wiki-writing` | Create or revise wiki prose for any page type, with templates and citation rules. |
| `wiki-ingest` | Integrate curated material already in `raw/` into `wiki/` and update related pages, index, and log. |
| `wiki-query` | Answer from the wiki first, then file durable answers back as synthesis pages. |
| `wiki` | Read-only answers from the wiki; never writes, creates, updates, or deletes a file. |
| `wiki-maintenance` | Refresh raw-source drift and run lint/health checks. |
| `wiki-delete` | Remove a subject, page, or reference safely, with impact review and confirmation. |
| `wiki-router` | Map an unclear request to exactly one of the playbooks above. |

```mermaid
flowchart TD
    R[Request] --> ROUTER{wiki-router}
    ROUTER -->|write prose| WW[wiki-writing]
    ROUTER -->|add source| WI[wiki-ingest]
    ROUTER -->|answer + file| WQ[wiki-query]
    ROUTER -->|answer only| W[wiki]
    ROUTER -->|refresh/lint| WM[wiki-maintenance]
    ROUTER -->|remove subject| WD[wiki-delete]
```

## Commands

Slash commands (in `.agents/commands/`) are thin wrappers that invoke the matching skill:

| Command | Skill | Use |
|---------|-------|-----|
| `/wiki-ingest` | `wiki-ingest` | Ingest curated raw material. |
| `/wiki-query` | `wiki-query` | Answer a question and possibly file it. |
| `/wiki` | `wiki` | Read-only answer. |
| `/wiki-refresh` | `wiki-maintenance` | Run a refresh pass. |
| `/wiki-lint` | `wiki-maintenance` | Run a lint/health check. |

## Workflow

1. Add curated source material to `raw/`.
2. Follow `AGENTS.md` for the always-on contract and load the relevant repo-local skills from `.agents/skills/`.
3. Create or update pages in `wiki/sources/`, `wiki/entities/`, `wiki/concepts/`, and `wiki/syntheses/`.
4. Use synthesis pages for reusable questions, comparisons, and topic maps.
5. Keep `wiki/index.md`, learning paths, and `wiki/log.md` up to date.

## Operations

- `ingest` - integrate curated material from `raw/` into `wiki/` and update related pages, the index, and the log.
- `query` - answer from the wiki first, then fold durable answers back into the knowledge base when they deserve a synthesis page.
- `wiki` - answer from the wiki first in read-only mode, never writing or modifying any file.
- `refresh` - detect raw-source drift and report the downstream pages that should be revisited. Run via `python3 scripts/refresh.py`.
- `lint` - check wiki health, including structure, link integrity, stale claims, and integration gaps. Run via `python3 scripts/lint.py`.

```mermaid
flowchart LR
    INGEST[ingest] --> PAGES[wiki pages]
    QUERY[query] --> PAGES
    REFRESH[refresh] --> PAGES
    LINT[lint] --> PAGES
    PAGES --> INDEX[wiki/index.md]
    PAGES --> LOG[wiki/log.md]
```

## Validation

- Run the test suite: `python3 -m unittest discover -s tests -t .`
- Run lint on a wiki: `python3 scripts/lint.py`
- Run refresh on a wiki: `python3 scripts/refresh.py`
- Search a wiki: `python3 scripts/wiki_search.py "<terms>"`

## Credits

This template began from [caelaxie/llm-wiki-template](https://github.com/caelaxie/llm-wiki-template), which laid the foundation for the `raw/ -> wiki/` model this repo builds on. The underlying idea comes from Andrej Karpathy's [LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).
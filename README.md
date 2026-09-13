# LLM Wiki Template

An LLM wiki template based on Andrej Karpathy's `llm-wiki` gist for turning curated `raw/` sources into a persistent markdown knowledge base.

## How it works

The basic model is `raw/ -> wiki/`.

You curate source material in `raw/`, then use the repo contract to turn that material into durable wiki pages under `wiki/`. As the corpus grows, the wiki becomes the main knowledge layer, while `raw/` remains the backing source layer.

The writing model is plain-language, answer-first wiki prose: teach the smallest useful model first, then deepen it with evidence, distinctions, examples, limits, and open questions.

## Repo structure

- `raw/` - curated source documents
- `wiki/` - persistent markdown wiki and navigation surfaces
- `AGENTS.md` - root contract for structure, workflows, and page types
- `.agents/skills/` - repo-local skill playbooks for writing, ingest, query, and maintenance work

## Workflow

1. Add curated source material to `raw/`.
2. Follow `AGENTS.md` for the always-on contract and load the relevant repo-local skills from `.agents/skills/`.
3. Create or update pages in `wiki/sources/`, `wiki/entities/`, `wiki/concepts/`, and `wiki/syntheses/`.
4. Use synthesis pages for reusable questions, comparisons, and topic maps.
5. Keep `wiki/index.md`, learning paths, and `wiki/log.md` up to date.

## Operations

- `ingest` - integrate curated material from `raw/` into `wiki/` and update related pages, the index, and the log.
- `query` - answer from the wiki first, then fold durable answers back into the knowledge base when they deserve a synthesis page.
- `lint` - check wiki health, including structure, link integrity, stale claims, and integration gaps.
- `refresh` - detect raw-source drift and report the downstream pages that should be revisited.

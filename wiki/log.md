# Log

This log is the append-only chronological record of material wiki operations. Each entry should use a heading in the form `## [YYYY-MM-DD] operation | title` so later maintenance work can scan changes quickly.

## [2026-04-07] bootstrap | Initialize LLM wiki template

Created the minimal `llm-wiki` template bootstrap:

- added `AGENTS.md` as the schema and workflow contract
- created `raw/` with a tracked placeholder
- created typed wiki content directories under `wiki/`
- created `wiki/index.md`
- created `wiki/log.md`

## [2026-04-08] maintenance | Refresh index and log for updated repo contract

Updated the wiki navigation and operation surfaces to match the revised instructions in `AGENTS.md` and `STYLE_GUIDE.md`:

- rewrote `wiki/index.md` so it acts as the first navigation surface and states
  the current empty-page status by category
- clarified `wiki/log.md` entry expectations while preserving the append-only
  history

## [2026-04-08] maintenance | Rewrite style guide around ChatGPT-style prose

Replaced the prior writing guide with a full rewrite aligned to the current public OpenAI Model Spec's writing defaults, adapted for persistent wiki pages:

- removed the prior MediaWiki-inspired framing
- rewrote the guide around answer-first, direct, warm, professional, and
  concise prose
- tightened formatting rules for leads, paragraphs, headings, and list usage
- rewrote page-type guidance from scratch
- added anti-patterns and short good/bad examples to make the style operational

## [2026-04-08] maintenance | Make style guide easier for agents to apply

Tightened the rewritten style guide so agents can execute it with less interpretation:

- added a quick-start workflow for drafting and revising pages
- added default decision rules for common writing tradeoffs
- added a default page-writing sequence shared across page types
- expanded the final checks to verify the guide is operational for agents

## [2026-04-22] maintenance | Collapse root guidance into AGENTS plus repo-local skills

Refactored the repo from a two-file guidance model into a single root contract plus repo-local skills:

- rewrote `AGENTS.md` as the sole root contract for structure, schema, workflow, and completion rules
- added `.agents/skills/wiki-writing`, `.agents/skills/wiki-ingest`, `.agents/skills/wiki-query`, and `.agents/skills/wiki-maintenance`
- moved detailed writing and task-playbook guidance out of the root contract and into those repo-local skills
- updated `README.md` to describe the new operating model
- removed `STYLE_GUIDE.md`

## [2026-04-22] maintenance | Shift template prose toward plain-language dual-use writing

Updated the template's writing contract so the wiki style explicitly serves both experienced readers and careful newcomers:

- added plain-language and professional-tone requirements to `AGENTS.md` and `.agents/skills/wiki-writing`
- clarified that pages should define non-obvious terms and add only the minimum orientation needed to follow the page
- tightened anti-patterns to reject expert-only shorthand, inflated prose, and tutorial-style overexplaining
- aligned query, ingest, maintenance, and README wording with the revised style contract
- rewrote the example pages so their leads and first sections model the new style directly

## [2026-04-22] maintenance | Make example pages less repo-internal

Tightened the writing examples so they model explanatory prose more directly and rely less on corpus-internal framing:

- replaced several uses of `current corpus` and `in this wiki` in the examples with plainer explanatory wording
- kept the examples aligned to the same page-type distinctions while reducing meta commentary in the opening sections

## [2026-04-22] maintenance | Make repo-local skills more cost-aware and image-aware

Refined the repo-local wiki skills after comparing them with the external `llm-wiki` skill in `Ar9av/obsidian-wiki`:

- added a more explicit cheap-to-expensive retrieval ladder and retrieval-primitives guidance to `.agents/skills/wiki-query`
- added image-backed source handling and provenance cautions to `.agents/skills/wiki-ingest`
- added a cost-aware structural scan order to `.agents/skills/wiki-maintenance`
- kept the repo's stricter page schema and avoided importing incompatible Obsidian-specific metadata or manifest rules

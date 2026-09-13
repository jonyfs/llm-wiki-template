# AGENTS.md

This repository follows an LLM wiki pattern inspired by Andrej Karpathy's `llm-wiki` gist and related agentic wiki workflows.

The goal is not one-off retrieval over `raw/`. The goal is to maintain a persistent, compounding markdown wiki that sits between the human and a curated collection of source material.

This file is the authoritative root contract for the repository. It defines repo structure, page schema, workflow rules, and completion requirements.

Detailed writing guidance and detailed task playbooks do not live here. They live in repo-local skills under `.agents/skills/`.

## Purpose

There are three layers in this repo:

1. `raw/` contains curated source documents. This is a human-curated source layer by default. The agent may read from it, cite it, and build wiki pages from it, but must not add, modify, rename, rewrite, or reorganize files in `raw/` unless the user explicitly asks. When the user does explicitly ask the agent to add material into `raw/`, any images that are part of that material must be downloaded automatically into `raw/assets/` and embedded with `![[raw/assets/...]]` wiki links. For web material, this includes relevant source images exposed by the page or its image URLs, but excludes obvious site chrome, ads, avatars, tracking pixels, and unrelated decorative assets.
2. `wiki/` contains the persistent markdown wiki. This layer is generated and maintained by the LLM.
3. `AGENTS.md` plus `.agents/skills/` define how the LLM operates on the wiki.

The wiki is a persistent artifact. New sources and valuable answers should be integrated into the wiki so knowledge accumulates over time.

## Required repo-local skills

This repo uses a layered guidance model:

- `AGENTS.md` is the always-on contract.
- `.agents/skills/` contains the detailed behavior agents are expected to load for specific work.

Agents working in this repo should load the relevant repo-local skills before substantive work:

- Load `.agents/skills/wiki-writing/` before creating or materially revising wiki prose.
- Load `.agents/skills/wiki-ingest/` before ingesting new source material into the wiki.
- Load `.agents/skills/wiki-query/` before answering wiki-grounded questions or filing a durable answer back into the wiki.
- Load `.agents/skills/wiki-maintenance/` before refresh, lint, drift, or broader health-check work.

This file intentionally does not duplicate the detailed playbooks from those skills. Agents are expected to use the local skills rather than relying on a hidden prose fallback in `AGENTS.md`.

## Core principles

- Prefer updating existing wiki pages over creating near-duplicate pages.
- Treat `wiki/index.md` as the first navigation surface for queries and maintenance work.
- Use `wiki/index.md` learning paths to show useful reading sequences once the wiki has enough pages.
- Record meaningful wiki operations in `wiki/log.md`.
- Keep wiki content in markdown.
- Write in plain language with a professional tone. Prefer the clearest wording that preserves technical accuracy, and define non-obvious terms rather than assuming field familiarity.
- Optimize pages for serious learning: teach the smallest useful model first, then deepen it with evidence, distinctions, examples, limits, and open questions.
- Preserve contradictions, uncertainty, and open questions instead of forcing premature reconciliation.
- Use bare `[[slug]]` wikilinks for wiki content pages whenever possible.
- Use `[[raw/...]]` wikilinks for raw-source references.
- Use `![[raw/assets/...]]` wiki links when embedding downloaded images stored in the raw corpus.
- Keep the repo structure narrow. Do not introduce extra content directories, extra required metadata, or extra page classes unless the user explicitly asks.

## Session orientation

When working on an existing wiki, orient yourself before doing substantive work. Do this especially before ingest, broad maintenance, or creating new pages.

Minimum orientation pass:

1. Read `AGENTS.md`.
2. Load the relevant repo-local skill or skills from `.agents/skills/` for the task at hand.
3. Read `wiki/index.md`.
4. Scan the most recent relevant entries in `wiki/log.md`.
5. Read the most relevant existing wiki pages before creating anything new.

This prevents duplicate pages, missed cross-references, and edits that fight the current shape of the wiki.

If the wiki has grown enough that `wiki/index.md` is no longer sufficient on its own, run a targeted search across `wiki/` for relevant slugs, entities, concepts, and phrases before creating new pages.

## Repository layout

Required files:

- `AGENTS.md`
- `wiki/index.md`
- `wiki/log.md`

Required repo-local skill root:

- `.agents/skills/`

Required wiki content directories:

- `wiki/sources/`
- `wiki/entities/`
- `wiki/concepts/`
- `wiki/syntheses/`

Content pages must live only in those four typed directories.

## Markdown page conventions

Markdown source formatting is repo-wide by default:

- Store prose paragraphs as single logical lines separated by blank lines.
- Rely on editor soft wrap for reading.
- Do not manually wrap prose for visual width.
- Do not use trailing spaces or end-of-line backslashes for hard line breaks.
- Use explicit `<br>` only when a forced rendered line break is genuinely unavoidable.
- Preserve structural Markdown layout where line shape is part of the syntax or meaning, including YAML frontmatter, headings, lists, blockquotes, tables, and fenced code blocks.
- Apply this rule to repo Markdown by default, including wiki pages and Markdown test fixtures.
- Keep top-level `raw/` as protected corpus material, including `raw/assets/`; do not reformat it unless the user explicitly asks.

### Page types

Use these page types for markdown content pages:

- `source`
- `entity`
- `concept`
- `synthesis`

### Frontmatter

All markdown content pages should begin with YAML frontmatter. This example shows the shared fields common to every page type:

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

- `title` is the canonical human-readable page title.
- `type` must be one of `source`, `entity`, `concept`, or `synthesis`.
- `sources` is a list of wiki-link strings pointing to the raw files and/or wiki pages that materially support the page.
- Use `[[raw/...]]` for raw-source references in `sources`, including `[[raw/assets/...]]` when an image asset is itself supporting source material.
- Use bare `[[slug]]` for wiki-page references in `sources`.
- All page types require `title`, `type`, `sources`, `created_at`, and `updated_at`.
- `created_at` is the page creation date in `YYYY-MM-DD` format.
- `updated_at` is the date of the last material edit in `YYYY-MM-DD` format.
- `source` pages must include `source_role`, which classifies the source by research role.
- `source_role` must be one of `primary`, `secondary`, `reference`, `operational`, or `informal`.
- `source` pages may include `source_format`, which classifies the source by artifact shape.
- `source_format`, when present, must be one of `paper`, `article`, `book`, `report`, `spec`, `documentation`, `dataset`, `benchmark`, `transcript`, `notes`, or `other`.
- `source` pages may include `authors` as a YAML list of non-empty strings.
- `source` pages may include `published_at` in `YYYY-MM-DD` format when an exact date is known.
- `source` pages may include `canonical_url` as an absolute `http` or `https` URL.
- `source` pages must include `raw_sha256`, which stores the SHA-256 digest of the single canonical `[[raw/...]]` file that backs the page.
- Newly created `source` pages must include `raw_sha256` at creation time.
- The creator of a new `source` page must compute and set `raw_sha256`.
- The dedicated `refresh` workflow reconciles `raw_sha256` later and may bootstrap a missing value on an existing page during refresh.
- `raw_sha256` must not appear on `entity`, `concept`, or `synthesis` pages.
- `source_role`, `source_format`, `authors`, `published_at`, and `canonical_url` must not appear on `entity`, `concept`, or `synthesis` pages.
- If an image asset under `raw/assets/` is the single canonical raw backing file for a `source` page, it is still a normal `[[raw/...]]` reference and still requires `raw_sha256`.
- Keep the strict single-file source-page model. If a paper has an appendix, a dataset has a card, or a spec has a changelog, represent those related artifacts as separate pages rather than bundling multiple canonical raw files into one `source` page.

Use `source_role` to describe research use, not prestige:

- `primary` for sources that directly present the main evidence, argument, measurement, or specification under study.
- `secondary` for sources that interpret, summarize, compare, or reframe primary material.
- `reference` for sources mainly used to define terms, normalize facts, or supply stable background context.
- `operational` for sources that describe live procedures, implementation behavior, runbooks, or current system practice.
- `informal` for sources that still matter but are weakly formalized, such as notes, forum posts, chats, or ad hoc writeups.

Examples:

- An original benchmark paper or standards document is usually `primary`.
- A review article or analyst comparison is usually `secondary`.
- A glossary, textbook appendix, or canonical explainer is usually `reference`.
- Internal production docs or incident playbooks are usually `operational`.
- Lab notes, issue threads, or transcript fragments are usually `informal`.

Example non-source page frontmatter:

```yaml
---
title: "How Tailscale Builds a Mesh VPN"
type: "synthesis"
sources:
  - "[[tailscale-how-it-works]]"
  - "[[wireguard]]"
created_at: "2026-04-07"
updated_at: "2026-04-07"
---
```

Canonical `source` page frontmatter:

```yaml
---
title: "WireGuard Whitepaper"
type: "source"
source_role: "primary"
source_format: "paper"
authors:
  - "Jason A. Donenfeld"
published_at: "2016-01-01"
canonical_url: "https://www.wireguard.com/papers/wireguard.pdf"
sources:
  - "[[raw/wireguard-whitepaper.md]]"
raw_sha256: "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
created_at: "2026-04-07"
updated_at: "2026-04-07"
---
```

### Filenames and slugs

- Store source pages under `wiki/sources/`.
- Store entity pages under `wiki/entities/`.
- Store concept pages under `wiki/concepts/`.
- Store synthesis pages under `wiki/syntheses/`.
- Do not create additional content directories under `wiki/`.
- Do not create deeper nesting inside the four typed content directories.
- Use lowercase `kebab-case` filenames with a `.md` suffix.
- The canonical filename shape is `<slug>.md`.
- Keep slugs globally unique across all four typed content directories so bare `[[slug]]` links stay unambiguous.
- If two pages would otherwise share a slug, append a short stable qualifier.
- Prefer updating an existing canonical slug file over creating a near-duplicate alternate spelling.

### Create vs update

Default to updating an existing page when:

- the topic already has a canonical page
- the new source adds detail, evidence, dates, nuance, or contradictions
- the mention is important but not strong enough to justify a standalone page

Create a new page when:

- the topic is central to a source, not just a passing mention
- the topic recurs across sources and would otherwise be awkwardly buried
- a durable synthesis question deserves its own `synthesis` page

Do not create pages for fleeting mentions, weakly evidenced subtopics, or alternate phrasings of an existing page.

Before creating a page, search for likely existing slugs, synonyms, and related pages in the wiki.

### Entity vs concept

Use `entity` for a named, persistent thing in the world or corpus.

Use `concept` for an idea, mechanism, method, distinction, or claim family that can apply across multiple entities or sources.

Tie-break rule:

- If the page is mainly about a named thing that persists as an object of discussion, use `entity`.
- If the page is mainly about an idea that recurs across multiple things, use `concept`.

Gray-zone examples:

- A protocol such as WireGuard is usually an `entity`.
- A mesh-VPN coordination pattern is usually a `concept`.
- A named model such as GPT-4.1 is usually an `entity`.
- A benchmarking methodology is usually a `concept`.
- A benchmark suite with a stable name is usually an `entity`.
- A framework such as PyTorch is usually an `entity`.
- A standard such as OAuth 2.0 is usually an `entity`.
- A named method such as retrieval-augmented generation is usually a `concept`.

### Body templates

Keep pages narrative and minimal. Do not add tags, scoring fields, status fields, or Dataview-specific structure unless the user asks.

Every content page must begin with a short unheaded lead immediately after frontmatter and before the first section heading.

Write pages so both informed readers and careful newcomers can use them. Each page should teach the smallest useful model first, then deepen it with evidence, distinctions, examples, limits, and open questions.

The lead should usually answer three questions quickly:

- What is this page about?
- Why does it matter here?
- What mental model or key distinction helps the reader understand the rest?

Use plain language by default. Specialized terms are allowed when they improve precision, but define or ground non-obvious terms on first use instead of assuming the reader already knows them.

When a page is easy to misread, surface one key distinction or common confusion early. Keep that orientation compact so the page still reads like a durable wiki page rather than a primer.

Use the first required section as the fast-take area. Do not add an extra `## Fast take` heading unless the user explicitly asks, because page headings are part of the schema. Instead, make `## Summary` or `## Synthesized answer` open with the page's compact answer before adding detail.

Prefer concrete examples, contrasts, and boundary statements when they speed understanding. Good pages often say what the topic is not, when it matters, where it breaks down, and what would change the current interpretation.

`source` pages should include:

- summary
- key takeaways
- evidence or notable details
- related pages
- open questions

Recommended sentence-case headings for `source` pages:

- `## Summary`
- `## Key takeaways`
- `## Evidence or notable details`
- `## Related pages`
- `## Open questions`

For `source` pages, use `## Evidence or notable details` and `## Open questions` to make the source's limits explicit. Note scope limits, missing measurements, methodological caveats, outdated assumptions, and notable absences there rather than smoothing them away in summary prose.

In `## Summary`, give a one-paragraph fast take before the section map. The reader should understand the source's main contribution before reading its outline.

`entity` pages should include:

- summary
- role or significance
- current understanding
- related pages
- open questions or tensions

Recommended sentence-case headings for `entity` pages:

- `## Summary`
- `## Role or significance`
- `## Current understanding`
- `## Related pages`
- `## Open questions or tensions`

For `entity` pages, `## Current understanding` should explain the useful model of the entity: what it does or represents, what consequences follow, what it is often confused with, and which limits or edge cases matter.

When a nearby confusion would slow learning, include it inline in the lead, `## Summary`, or `## Current understanding`. Do not add a separate required heading for it.

`concept` pages should include:

- summary
- why it matters
- current understanding
- related pages
- open questions or tensions

Recommended sentence-case headings for `concept` pages:

- `## Summary`
- `## Why it matters`
- `## Current understanding`
- `## Related pages`
- `## Open questions or tensions`

For `concept` pages, `## Current understanding` should make the concept operational. Explain the mechanism, give at least one concrete example or contrast when useful, and name the boundary where the concept stops explaining the topic well.

When a concept is often confused with a nearby concept, entity, method, or claim, state that boundary early. Good concept pages often say `This is not the same as...`, `Do not confuse this with...`, or `This explanation breaks down when...` in normal prose.

`synthesis` pages should include:

- question or thesis
- synthesized answer
- evidence base
- unresolved points
- related pages

Recommended sentence-case headings for `synthesis` pages:

- `## Question or thesis`
- `## Synthesized answer`
- `## Evidence base`
- `## Unresolved points`
- `## Related pages`

For `synthesis` pages, the unheaded lead should usually include a short scope note when the answer is meaningfully bounded by source set, time window, method, or corpus coverage.

In `## Synthesized answer`, be decisive before being exhaustive. State the current answer, the main reason, and the most important caveat before expanding into the evidence map.

Frame synthesis pages around reusable questions whenever possible. A good synthesis page should answer something the wiki is likely to need again, not merely collect notes under a topic label.

Use synthesis pages for comparison and map work without adding new page types:

- Comparison syntheses answer questions such as `How does X differ from Y?`, `When should X be preferred over Y?`, or `Why is X not the same as Y?`.
- Map syntheses orient an area of the wiki, such as `How do these pages fit together?`, `What should a newcomer read first?`, or `Which concepts explain this domain?`.
- Periodically add or refresh map syntheses when a topic area has enough pages that the index alone no longer teaches the shape of the subject.

Optional recall checks may appear inline at the end of `## Current understanding`, `## Synthesized answer`, `## Unresolved points`, or `## Open questions or tensions` when they help retention. Do not add a separate `## Recall prompts` heading unless the user explicitly asks. Keep them short and concrete:

```md
Useful recall checks:
- What distinction keeps X and Y separate?
- What example shows the mechanism?
- What evidence would change this answer?
```

### Citations and cross-links

- Footnotes are allowed on any page type.
- In normal prose, use bare `[[slug]]` links for wiki-page support.
- In normal prose, use Markdown footnotes for direct support from `raw/`.
- When embedding a downloaded image stored in the raw corpus, use a `![[raw/assets/...]]` wiki link rather than leaving a website image URL in place or using a plain relative Markdown path.
- When a sentence is supported by both wiki pages and raw material, prefer an inline bare `[[slug]]` link plus a raw-source footnote.
- Footnotes are for attribution and locator detail only, not for side arguments, caveats, definitions, or overflow explanation.
- In raw-source footnotes, put the direct `[[raw/...]]` link first, then add the shortest useful locator detail.
- These rules apply to normal prose only. They do not change frontmatter `sources`, `Related pages`, `wiki/index.md`, or other structural link areas, which continue using normal wiki links.
- In `synthesis` pages, `## Evidence base` should function as an evidence map rather than a flat bibliography.
- Use the fixed subgroup headings `### Supports`, `### Conflicts or tensions`, and `### Gaps or missing evidence` when they are relevant.
- Each evidence bullet should begin with a short claim fragment or question fragment, then a colon, then the supporting `[[slug]]` and `[[raw/...]]` links.
- `synthesis` pages should cite the supporting wiki pages and source pages they rely on, but the evidence section should make the reasoning traceable rather than merely listing links.
- Use `## Unresolved points` to preserve direct contradictions and evidentiary gaps. If `## Synthesized answer` privileges one interpretation over another, say why and keep the counterevidence explicit rather than deleting it from the page.
- New or materially updated pages should include meaningful links to the most relevant related pages whenever those relationships are known.
- Avoid isolated pages. If a page belongs in the wiki, it should usually connect to existing entities, concepts, or syntheses.

## Operations

### Ingest

When the user asks to ingest a new source:

1. Ingest assumes the source has already been curated into `raw/`.
2. If the user provides a URL, PDF, or pasted text that is not yet in `raw/`, pause normal wiki ingest and ask whether to add that material to the corpus first. Only add it to `raw/` when the user explicitly instructs you to do so.
3. If the user explicitly asks to add new raw material and that material comes from the web, automatically download the relevant source images exposed by that material into `raw/assets/` and replace website image references with `![[raw/assets/<filename>]]` wiki links. Skip obvious site chrome, ads, avatars, tracking pixels, and unrelated decorative assets.
4. Read `wiki/index.md`.
5. Read the source from `raw/`.
6. Check what already exists before creating anything new.
7. Create or update the corresponding `source` page in `wiki/sources/`. If the page is newly created, include `raw_sha256` in its frontmatter immediately.
8. Update the most relevant `entity`, `concept`, and `synthesis` pages when the source materially changes them.
9. Create new supporting pages only when they meet the create-vs-update rules above.
10. Ask what the source changes in the wiki's concept graph: new distinctions, stronger examples, broken assumptions, changed comparisons, or a needed map page.
11. Add or refresh meaningful cross-links between the touched pages.
12. Update `wiki/index.md` so it remains a useful category-organized catalog of wiki pages.
13. Add or update short learning paths in `wiki/index.md` when the touched pages create a useful reading sequence.
14. Ensure each relevant index entry includes at least a link and a one-line summary.
15. Append an entry to `wiki/log.md` describing the ingest.
16. Update `updated_at` on every content page materially changed during ingest.
17. Set `created_at` and `updated_at` when creating a new content page.
18. When creating a new `source` page, compute and include `raw_sha256` in the initial frontmatter instead of relying on a later refresh to add it.

For batch ingest:

1. Read all incoming sources first.
2. Identify overlapping entities, concepts, and syntheses once.
3. Update the affected pages in one pass instead of repeatedly reopening the same topics source by source.
4. Update `wiki/index.md` once after the batch.
5. Consider whether the batch creates a comparison synthesis, a map synthesis, or a learning path that would make the new material easier to learn.
6. Append one batch-oriented log entry unless separate entries are genuinely clearer.

### Query

When the user asks a question:

1. Start from `wiki/index.md` to locate relevant wiki pages.
2. Read the most relevant wiki pages first.
3. Use `raw/` selectively when the wiki lacks needed detail, when a claim needs verification, or when a new source has not yet been integrated.
4. Synthesize the answer from the wiki instead of rediscovering everything from `raw/` by default.
5. Cite supporting wiki pages with inline bare `[[slug]]` links and use raw footnotes in normal prose when the answer depends directly on `raw/` material.
6. If the answer creates durable value for the knowledge base, file it back into the wiki as a reusable-question `synthesis` page in `wiki/syntheses/`, then update `wiki/index.md` and `wiki/log.md`.
7. If the answer is trivial or one-off, answer directly without forcing a new page.

### Refresh

When the user asks for a refresh or raw-drift check:

1. Run the dedicated `refresh` command instead of `lint`.
2. `refresh` scans `source` pages and resolves each page's single canonical `[[raw/...]]` backing file.
3. `refresh` computes the SHA-256 of that raw file and ensures `raw_sha256` is present and current on the `source` page, bootstrapping a missing value when needed.
4. `refresh` identifies changed `source` pages and computes downstream dependency closures using only `sources` frontmatter links.
5. `refresh` prints a deterministic ordered report of the pages that should be refreshed next.
6. `refresh` must not rewrite dependent wiki pages, `wiki/index.md`, or `wiki/log.md`.
7. After `refresh`, the agent may rewrite the reported pages, update `updated_at` only for material content changes, then update `wiki/index.md` and `wiki/log.md` if the wiki changed materially.

For dependency resolution during `refresh`:

- If page `A` lists `[[B]]` in `sources`, `A` depends on `B`.
- Body wikilinks remain navigational and do not create refresh dependencies.
- `source` pages must contain exactly one canonical `[[raw/...]]` reference in `sources`.
- `source` pages must carry `raw_sha256`; `refresh` can backfill a missing hash on an existing page without failing fast.

### Lint

When the user asks for a lint or health check:

1. Inspect the wiki for contradictions between pages.
2. Look for stale claims that newer sources may have superseded.
3. Identify orphan pages or pages with weak integration into the rest of the wiki.
4. Identify broken or ambiguous wikilinks.
5. Identify important concepts or entities that are mentioned but not yet well integrated.
6. Identify research gaps or follow-up questions that would improve the wiki.
7. Identify markdown content pages with missing or malformed frontmatter.
8. Identify `source` pages with missing or malformed `raw_sha256`.
9. Identify `created_at` or `updated_at` values that are not in `YYYY-MM-DD` format.
10. Identify filenames that violate lowercase `kebab-case`.
11. Identify content pages stored outside the four typed content directories.
12. Identify near-duplicate pages caused by slug drift or weak disambiguation.
13. Identify slug collisions that would make bare `[[slug]]` links ambiguous.
14. Identify `wiki/index.md` entries missing category placement, links, or one-line summaries.
15. Identify missing or stale learning paths when a topic area has enough pages to deserve a guided route.
16. Identify pages whose prose is structurally valid but still assumes too much field familiarity or uses avoidably dense language.
17. Identify mature areas that need comparison syntheses or map syntheses to support faster learning.
18. Record the lint pass in `wiki/log.md` if it materially affects the wiki or future work.

`lint` remains a health check. It should not be repurposed to perform raw-drift refresh or cascading page rewrites.

For larger wikis, prefer programmatic scans for link graphs, frontmatter shape, and index completeness instead of relying on manual inspection alone.

## Index and log

- `wiki/index.md` is the content-oriented catalog of the wiki.
- Read `wiki/index.md` first for queries and maintenance work.
- Include a `## Learning paths` section before the typed catalogs once the wiki has enough pages to support guided reading.
- Keep learning paths short, ordered for comprehension, and selective; three to seven pages is usually enough.
- Organize `wiki/index.md` by category using sections for `Sources`, `Entities`, `Concepts`, and `Syntheses`.
- Include one entry per content page, with at least a link and a one-line summary.
- `wiki/log.md` is the chronological, append-only record of wiki activity.
- Start each log entry with a heading in this format: `## [YYYY-MM-DD] operation | title`

Examples:

```md
- [[wireguard]] - Entity page for WireGuard as a minimal, public-key-based VPN design.
```

```md
- VPN design path: [[wireguard]] -> [[cryptographic-minimalism]] -> [[why-minimal-vpn-designs-appeal-to-researchers]]
```

```md
## [2026-04-07] ingest | Tailscale architecture source
```

## Migration for derived wikis

If you are updating an existing wiki derived from an older version of this template:

- Rename `## Citations or supporting pages` to `## Evidence base` on synthesis pages.
- Add required `source_role` to every `source` page.
- Add optional `source_format` only when it adds real retrieval value.
- Keep related artifacts as separate `source` pages instead of bundling multiple canonical raw files into one page.

## Pitfalls

- Never modify files in `raw/` unless the user explicitly asks.
- Do not store downloaded images ad hoc elsewhere in `raw/`; place them under `raw/assets/`.
- Do not leave relevant website image URLs in place when the corresponding raw material is being added to the corpus; download those images into `raw/assets/` unless they are obvious site chrome or unrelated assets.
- Do not skip orientation on an existing wiki before major ingest or synthesis work.
- Do not create pages for passing mentions just because a name appears once.
- Do not create alternate pages when an existing canonical slug already covers the topic.
- Do not update content pages without also considering whether `wiki/index.md` or `wiki/log.md` should change.
- Do not flatten contradictions away when the evidence is mixed or dated.
- Do not leave newly created pages weakly linked or invisible from the rest of the wiki.
- Do not rely on `AGENTS.md` alone for detailed execution guidance when a relevant repo-local skill exists.

## Completion checklist

Before finishing any wiki-changing task, verify that:

- no files in `raw/` were modified unless the user explicitly asked to add or update source material there
- any downloaded images added to the raw corpus were stored under `raw/assets/` rather than elsewhere in `raw/`
- relevant images from web-sourced raw material were downloaded locally into `raw/assets/` instead of being left as website image URLs
- every touched content page lives in the correct typed directory
- every touched content page begins with a short unheaded lead immediately after frontmatter
- every touched content page uses plain language with a professional tone and defines non-obvious terms when needed
- every touched content page teaches the smallest useful model before expanding into details
- every touched page uses concrete examples, contrasts, or boundary statements when they materially speed understanding
- wiki-page links use bare `[[slug]]` wherever possible
- raw-source references use `[[raw/...]]` in frontmatter, footnotes, or other structural citation inventories as appropriate
- downloaded image references use `![[raw/assets/...]]` rather than external URLs or plain relative Markdown paths
- every touched `source` page includes `raw_sha256`, and non-`source` pages do not include it
- no content-page slug collides with another content-page slug
- new pages were created only when they were justified over updating an existing page
- `wiki/index.md` reflects the current page set
- `wiki/index.md` learning paths are added or refreshed when the touched pages create a useful reading sequence
- `wiki/log.md` has a new entry if the wiki changed materially
- reusable answers, comparisons, and area maps are represented as `synthesis` pages rather than new page types
- contradictions, weak evidence, and open questions remain explicit
- the wiki is more useful and navigable than it was before the pass

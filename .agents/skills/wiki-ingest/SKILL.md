---
name: wiki-ingest
description: Use when ingesting curated source material from raw/ into a wiki based on this template. Covers orientation, source extraction, create-vs-update decisions in practice, page-touch strategy, cross-linking, and index/log update discipline.
---

# Wiki Ingest

Use this skill before ingesting new source material into a repository derived from this template.

## Purpose

The goal of ingest is to turn curated corpus material in `raw/` into durable wiki knowledge without creating duplicate pages, weakly linked stubs, or schema drift.

## Preconditions

- Ingest assumes the source already exists in `raw/`.
- If the user supplies a URL, PDF, or pasted text that is not yet in `raw/`, stop normal ingest flow and confirm whether it should be added to the corpus first.
- If the user explicitly asks to add new web-sourced raw material, download relevant source images into `raw/assets/` and replace website image references with `![[raw/assets/...]]`.
- Treat image files in `raw/` and `raw/assets/` as valid source material when the user has curated them into the corpus.
- For image-backed sources, distinguish what is directly visible from what is inferred. Do not present diagram interpretation, OCR guesses, or visual extrapolation as if the image stated them verbatim.
- If the available tools cannot inspect an image-backed source reliably enough for ingest, report that limitation instead of guessing.

## Orientation pass

Before touching wiki content:

1. Read `AGENTS.md`.
2. Load `.agents/skills/wiki-writing/` as well when the ingest will create or materially rewrite prose.
3. Read `wiki/index.md`.
4. Scan the most recent relevant entries in `wiki/log.md`.
5. Read the most relevant existing wiki pages for the source topic.
6. Search for likely existing slugs, synonyms, entities, concepts, and syntheses before creating anything new.

## Ingest workflow

1. Read the raw source fully enough to identify the important claims, entities, concepts, evidence, and unresolved questions.
2. Decide the canonical `source` page slug.
3. Create or update that `source` page first.
4. Update the most relevant `entity`, `concept`, and `synthesis` pages only where the new source materially changes the wiki's current understanding.
5. Create new supporting pages only when the topic is central, recurring, or clearly deserves its own durable synthesis.
6. Ask what the source changes in the wiki's concept graph: new distinctions, stronger examples, broken assumptions, changed comparisons, or a needed map page.
7. Add or refresh meaningful cross-links between all touched pages.
8. Update `wiki/index.md` once the touched page set is stable.
9. Add or refresh learning paths in `wiki/index.md` when the touched pages create a useful reading sequence.
10. Append the ingest entry to `wiki/log.md`.

For image-backed raw sources:

- Describe the artifact shape clearly in the `source` page so later readers know they are looking at an image, scan, diagram, slide, or screenshot rather than ordinary prose.
- Be conservative about extracting claims from dense charts, diagrams, or screenshots. If a conclusion depends on interpretation rather than explicit text, state that limit in the page body.
- When the image is the single canonical backing file for the `source` page, compute `raw_sha256` from that image file exactly as you would for any other canonical `[[raw/...]]` source.

## Create-vs-update in practice

Default to updating an existing page when:

- the topic already has a canonical page
- the new source adds detail, evidence, dates, nuance, or contradictions
- the mention matters but is not strong enough to justify a standalone page

Create a new page when:

- the topic is central to the source, not just a passing mention
- the topic recurs across sources and would otherwise be awkwardly buried
- a durable synthesis question deserves its own page
- a comparison or map synthesis would make an existing cluster of pages easier to learn

Do not create pages for fleeting mentions, weakly evidenced subtopics, or alternate phrasings of an existing page.

## Source-page requirements

- A newly created `source` page must include `source_role`.
- Choose `source_role` for research function rather than prestige: primary evidence, secondary interpretation, reference context, operational practice, or informal but relevant material.
- Add `source_format`, `authors`, `published_at`, or `canonical_url` only when the raw source supports them and they improve retrieval or provenance.
- A newly created `source` page must include `raw_sha256` immediately.
- Compute the hash from the single canonical raw backing file rather than relying on later refresh to backfill it.
- Preserve exactly one canonical `[[raw/...]]` backing reference in `sources`.
- Keep related appendices, errata, benchmark sheets, or companion artifacts as separate pages rather than bundling multiple canonical raw files into one `source` page.
- Make the source's limitations explicit inside `## Evidence or notable details` and `## Open questions`; do not let the source summary imply more certainty or coverage than the raw material supports.

## Page-touch strategy

- Prefer one coordinated pass across all affected pages rather than repeatedly reopening the same concepts source by source.
- Keep the touched set narrow. Update only the pages materially changed by the new evidence.
- If several new sources overlap, read them first, identify shared concepts once, and then update the affected pages in one pass.
- When rewriting prose, keep it in plain language with a professional tone. Define non-obvious terms on first use and add only the minimum orientation needed for a careful newcomer to follow the page.
- Preserve learning speed: add useful examples, nearby confusions, and boundary statements where the new source clarifies them.
- Prefer reusable-question syntheses over broad topic-label syntheses.

## Index and log discipline

- `wiki/index.md` should remain a category-organized catalog with one entry per content page.
- `wiki/index.md` should include short learning paths when a set of pages has a useful reading order.
- Each relevant index entry should include at least a link and a one-line summary.
- `wiki/log.md` should record the ingest after the page set is stable.
- Use one batch-oriented log entry for batch ingest unless separate entries are genuinely clearer.

## Common failure modes

- Creating a new page before checking whether a canonical slug already exists
- Updating prose without also updating `updated_at`
- Rewriting a page in field shorthand that assumes too much background or drifts into tutorial-style exposition
- Touching several pages but forgetting to refresh `wiki/index.md`
- Adding pages but leaving the learning path unclear when the page cluster is now big enough to need one
- Adding a new `source` page without `raw_sha256`
- Treating an image-backed source as if every interpreted relationship in the image were explicit text
- Leaving a newly created page weakly linked or invisible from the rest of the wiki
- Flattening contradictions instead of preserving them

## Final checks

Before finishing an ingest pass, verify:

- no files in `raw/` changed unless the user explicitly asked for raw-corpus changes
- each touched page lives in the correct typed directory
- each touched page still follows the required section families from `AGENTS.md`
- new pages were justified over updating existing ones
- new or materially updated pages have meaningful related-page links
- `wiki/index.md` reflects the current page set
- `wiki/index.md` learning paths are added or refreshed when useful
- `wiki/log.md` records the ingest if the wiki changed materially

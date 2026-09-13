---
name: wiki-maintenance
description: Use when refreshing, linting, or auditing a wiki based on this template. Covers refresh versus lint boundaries, raw-drift interpretation, health-check tactics, and when maintenance should or should not rewrite wiki content.
---

# Wiki Maintenance

Use this skill before refresh, lint, drift, or broader health-check work in a repository derived from this template.

## Purpose

The goal of maintenance work is to keep the wiki internally consistent, well linked, current against its raw corpus, and compliant with the repo contract without collapsing refresh and lint into the same operation.

## Pick the right operation

Use `refresh` for raw-drift work:

- run the dedicated `refresh` command instead of `lint`
- reconcile `raw_sha256` on `source` pages
- identify changed source pages and downstream dependencies from `sources` frontmatter
- produce the deterministic ordered report of pages that should be refreshed next

Use `lint` for health-check work:

- contradictions between pages
- stale claims superseded by newer sources
- orphan pages or weak integration
- broken or ambiguous wikilinks
- missing or malformed frontmatter
- missing `source_role` or invalid `source_format`
- missing or malformed `raw_sha256`
- bad date formats
- bad filename hygiene or duplicate titles
- missing required section headings or missing unheaded leads
- prose that is technically valid but still assumes too much field familiarity or uses avoidably dense wording
- malformed synthesis `## Evidence base` structure
- missing index entries or index summaries
- weak `## Related pages` integration
- filename or directory violations
- index gaps, slug drift, or collision risk
- missing or stale learning paths for mature topic clusters
- mature clusters that need comparison syntheses or map syntheses
- research gaps worth surfacing

## Refresh workflow

1. Run `refresh`.
2. Read the report rather than treating refresh as a content rewrite.
3. Confirm which source pages changed and which downstream pages were identified through `sources` links.
4. Rewrite only the reported pages that materially need revision.
5. Update `updated_at` only where the content changed materially.
6. Update `wiki/index.md` and `wiki/log.md` only if the wiki changed materially after the follow-on edits.

Refresh must not:

- rewrite dependent wiki pages directly
- treat body wikilinks as refresh dependencies
- rewrite `wiki/index.md` or `wiki/log.md` on its own

## Lint workflow

1. Start from `wiki/index.md` and the relevant areas of the wiki.
2. Check whether learning paths still describe useful reading routes through the current page set.
3. Use programmatic scans for link graphs, frontmatter shape, filename hygiene, and index completeness when the wiki is large enough that manual inspection is weak.
4. Inspect the wiki for structural defects, integration gaps, and stale or contradictory claims.
5. Identify page clusters that would be easier to learn from with a comparison synthesis or map synthesis.
6. Record the lint pass in `wiki/log.md` only if it materially affects the wiki or future work.

## Cost-aware scan order

Prefer a cheap structural pass before broad manual reading:

1. `wiki/index.md` for the current catalog and obvious gaps
2. `wiki/index.md` learning paths for stale, missing, or poorly ordered reading routes
3. file lists, slug checks, and filename hygiene across `wiki/`
4. frontmatter validation and `sources`-graph inspection
5. wikilink graph scans and targeted searches for ambiguous, broken, or weakly integrated links
6. section-level reads from pages that the structural pass identified as risky
7. full-page reads only for the pages that still need editorial judgment after the cheaper scans

When the wiki is large, use `rg` or similar targeted scans to narrow the candidate set before opening full pages. Do not treat broad manual reading as the default lint strategy.

## How to interpret issues

- Treat contradictions as signals to preserve, explain, or route for follow-up, not as proof that one page must be flattened into another.
- Treat weak integration as a page-shape problem: missing related links, missing index presence, or missing synthesis context.
- Treat missing learning paths as navigation debt when a cluster has enough pages that a reader needs a route.
- Treat missing comparison or map syntheses as learning-structure gaps, not schema gaps.
- Treat expert-only shorthand or needless density as a writing-quality issue when it blocks a careful newcomer from following an otherwise valid page.
- Treat malformed frontmatter and slug issues as contract violations, not editorial preferences.
- Treat missing `raw_sha256` on a `source` page as refresh-related maintenance, not as a reason to rewrite unrelated content.

## When maintenance should rewrite content

Rewrite pages after maintenance only when:

- the refresh report identifies them as drift-affected
- the lint pass exposes a real contradiction, stale claim, or integration gap that requires a content change
- fixing the issue materially improves correctness or navigability

Do not rewrite pages just because maintenance surfaced a question, a possible future improvement, or an editorial preference.

## Common failure modes

- Using `lint` when the task is really raw drift
- Letting `refresh` rewrite the wiki directly instead of producing the next-work report
- Treating body wikilinks as refresh dependencies
- Opening large numbers of full pages before a cheaper structural scan has identified which pages actually need attention
- Fixing page prose when the actual issue is an index or link-graph problem
- Logging every maintenance scan even when it produced no material effect

# Lint checklist, pitfalls, and completion checklist

Read on demand for lint, pitfall, or completion work. Canonical location for these lists; AGENTS.md links here.

## Lint

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

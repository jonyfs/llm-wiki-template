# Body templates and example frontmatter

Read on demand. Holds the required section families per page type and the example frontmatter moved out of AGENTS.md. AGENTS.md keeps the shared frontmatter schema.

## Example frontmatter

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

## Body templates

Keep pages narrative and minimal. Do not add tags, scoring fields, status fields, or Dataview-specific structure unless the user asks.

Every content page must begin with a short unheaded lead immediately after frontmatter and before the first section heading.

Write pages so both informed readers and careful newcomers can use them. Each page should teach the smallest useful model first, then deepen it with evidence, distinctions, examples, limits, and open questions.

The lead should usually answer three questions quickly:

- What is this page about?
- Why does it matter here?
- What mental model or key distinction helps the reader understand the rest?

Use plain language by default. Specialized terms are allowed when they improve precision, but define or ground non-obvious terms on first use instead of assuming the reader already knows them.

When a page is easy to misread, surface one key distinction or common confusion early. Keep that orientation compact so the page still reads like a durable wiki page rather than a primer.

Use the first required section as the fast-take area. Do not add an extra `## Fast take` heading unless the user explicitly asks, because page headings are part of the schema; the only optional extra section is `## Claims ledger` on `source` pages. Instead, make `## Summary` or `## Synthesized answer` open with the page's compact answer before adding detail.

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
- `## Claims ledger` (optional; when present it must be the last level-2 section, format in `citations.md`)

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


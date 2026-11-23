# Page-type guidance

Read on demand, after choosing the page type. Section families are defined in body-templates.md; this file gives the writing sequence for each type.



For any page type, the default writing sequence is:

1. Lead with the answer, definition, or contribution.
2. Explain why the page matters.
3. Give the smallest useful model, including one contrast or example when helpful.
4. Add supporting detail in descending importance.
5. Preserve uncertainty and tensions.
6. End with related pages and open questions as required by `AGENTS.md`.

### Source pages

- Use the lead to identify the source, its research role, its artifact shape when relevant, and why it matters to this wiki in terms a new reader can follow.
- In `## Summary`, state the source's main contribution early and plainly in one paragraph, then add the required nested section map.
- Keep the section map navigational. Detailed interpretation belongs in `## Key takeaways` and `## Evidence or notable details`.
- Preserve the source's original section numbering when it exists. If the source does not number sections, use titled nested bullets instead.
- Skip boilerplate headings such as acknowledgements, references, and author notes by default. Include appendices only when they add substantive content relevant to the wiki.
- In `## Evidence or notable details`, highlight concrete examples, evidence, scope limits, methodological caveats, and notable absences rather than rewriting the entire source.
- In `## Open questions`, preserve what the source leaves unclear, weakly supports, appears to contradict, or fails to measure directly.

### Entity pages

- Use the lead to say plainly what the entity is, why it matters here, and any one distinction a new reader needs before the page gets more specific.
- In `## Summary`, define the entity before describing debates around it.
- In `## Role or significance`, explain why the entity matters here, not only in the outside world.
- In `## Current understanding`, group related ideas together and move from the useful model to qualifying detail: what the entity does or represents, what follows from that, what it is often confused with, and which limits or edge cases matter.
- If a common confusion would mislead the reader, state it directly in normal prose instead of hiding it in related links.
- In `## Open questions or tensions`, name unresolved issues directly instead of burying them in surrounding explanation.

### Concept pages

- Use the lead to define the concept in plain language before expanding it.
- In `## Summary`, give the core idea in a way a new reader can follow.
- In `## Why it matters`, connect the concept to actual questions the wiki helps answer.
- In `## Current understanding`, make the concept operational. Explain the mechanism, distinguish it from nearby terms when that prevents confusion, give at least one concrete example or contrast when useful, and name the boundary where the concept stops explaining the topic well.
- If useful, end `## Current understanding` with short recall checks that test the core distinction, example, or boundary.
- In `## Open questions or tensions`, state where the concept's boundaries, usefulness, or interpretation remain unsettled.

### Synthesis pages

- Use the lead to restate the question or thesis, signal the kind of answer the page gives, define any non-obvious key term that the reader needs immediately, and add a short scope note when the answer is bounded by source set, time window, method, or corpus coverage.
- In `## Question or thesis`, phrase the question clearly and concretely. Prefer questions a future reader would actually ask over broad topic labels.
- In `## Synthesized answer`, answer first, then justify. State the current answer, the main reason, and the most important caveat before expanding into supporting detail.
- In `## Evidence base`, use the fixed subgroup headings from `AGENTS.md` when they are relevant.
- Make each evidence bullet claim-led: start with a short claim fragment or question fragment, add a colon, then list the supporting `[[slug]]` and `[[raw/...]]` links.
- Treat `## Evidence base` as an evidence map rather than normal prose.
- In `## Unresolved points`, keep the remaining uncertainty explicit and preserve direct contradictions. If you privilege one interpretation in `## Synthesized answer`, say why and keep the competing evidence visible.

Synthesis subpatterns:

- Use comparison syntheses for questions such as `How does X differ from Y?`, `When should X be preferred over Y?`, and `Why is X not the same as Y?`.
- Use map syntheses for questions such as `How do these pages fit together?`, `What should a newcomer read first?`, and `Which concepts explain this domain?`.
- Refresh or add map syntheses when a topic area has enough pages that `wiki/index.md` no longer teaches the shape of the subject by itself.


---
name: wiki-writing
description: Use when creating, editing, reviewing, or planning prose for typed markdown wiki pages in a repo based on this template. Covers leads, answer-first flow, paragraph and list usage, citation readability, uncertainty handling, and page-type writing patterns.
---

# Wiki Writing

Use this skill before creating or materially revising wiki prose in a repository derived from this template.

Gold-standard reference pages live in `examples/` next to this skill. Use them when you need a concrete shape for a strong `source`, `entity`, `concept`, or `synthesis` page, including comparison and map synthesis subpatterns.

## Purpose

The goal is to make pages read like durable wiki pages rather than transient chat replies. Write in plain language with a professional tone. State the main point early, preserve uncertainty honestly, and keep the page easy to scan without making it shallow.

For serious learning, the page should teach the smallest useful model first. Give the reader a compact way to understand the topic, then deepen it with evidence, distinctions, concrete examples, limits, and open questions.

## Default decisions

When a choice is unclear, prefer these defaults:

- Prefer a short paragraph over a bullet list unless the content is clearly list-shaped.
- Prefer a direct claim over a cautious setup sentence unless the evidence is genuinely uncertain.
- Prefer defining the term now over linking away and assuming the reader will click.
- Prefer one concrete example over several abstract sentences.
- Prefer a sharp contrast or boundary statement over another broad paraphrase.
- Prefer a reusable question over a vague synthesis topic when creating synthesis pages.
- Prefer plain wording over field-specific shorthand unless the specialized term is the clearest accurate choice.
- Prefer preserving an open question over implying certainty that the sources do not support.
- Prefer cutting a repeated sentence over keeping it for emphasis.
- Prefer the clearest wording over the most technical wording unless precision requires the technical term.

## Writing model

- Write for dual-use reading. Informed readers should be able to move quickly, and careful newcomers should be able to follow without prior field familiarity.
- Write in plain language. Specialized terms are allowed when they improve precision, but define or ground non-obvious terms on first use instead of assuming the reader already knows them.
- Before writing, identify what the page needs to help the reader do, what the reader likely already knows, and whether the page mainly summarizes a source, explains an entity, explains a concept, or answers a synthesis question.
- Apply the page-type boundary from `AGENTS.md`: named persistent things are usually `entity` pages, while recurring ideas, mechanisms, methods, distinctions, and claim families are usually `concept` pages.
- Add only the minimum orientation needed to follow the page. Do not assume field familiarity, but do not turn a normal wiki page into a step-by-step primer.

## Core style rules

Teach the model first:

- Start with the simplest accurate model that makes the topic usable.
- Explain what the topic is not when that prevents a common confusion.
- Use concrete examples or contrasts when they make an abstract idea faster to grasp.
- After the model is clear, add caveats, edge cases, and evidence limits.
- For entity and concept pages, include one nearby confusion or boundary when it materially improves learning.

Answer early:

- State the main point in the lead or first section, not after several setup paragraphs.
- Use the first required section as the page's fast take; do not add a non-schema `## Fast take` heading unless the user asks.
- On synthesis pages, give the synthesized answer before the supporting reasoning.
- On source pages, summarize the source's contribution before listing details.

Define before nuance:

- Define the main term in plain language before discussing disagreements, implementation detail, or history.
- If two nearby ideas are easy to confuse, distinguish them early.

Use plain language with professional tone:

- Sound precise, calm, direct, and evidence-aware.
- Do not confuse professionalism with stiffness, academic phrasing, or jargon density.
- Simplify expression, not thought. Keep the real distinctions, but say them as clearly as the topic allows.

Be clear and direct:

- Prefer direct claims over throat-clearing such as `it is worth noting` or `the wiki's current answer is`.
- Prefer concrete nouns and verbs over vague abstractions.
- Name the system, source, actor, or concept directly when the referent could be unclear.

Be warm and professional:

- Sound human, calm, and engaged.
- Do not sound casual, promotional, or performatively enthusiastic.
- Do not sound distant, stiff, or bureaucratic.

Be thorough but efficient:

- Include enough context to make the page useful on first read.
- Cut repeated setup, repetitive paraphrase, and low-signal filler.

Express uncertainty honestly:

- State when evidence is mixed, dated, partial, or contested.
- Name assumptions when the page depends on them.
- Preserve contradictions and open questions instead of forcing a cleaner conclusion than the sources support.

## Structure and formatting

- The lead should usually say what the page covers, why it matters, the main takeaway, and any prerequisite context the reader truly needs.
- The first screen should usually answer three questions quickly: what is this, why does it matter, and what mental model or key distinction helps a new reader understand the details.
- Prefer short paragraphs by default. One paragraph should usually carry one main idea.
- Split paragraphs that mix explanation, evidence, and caveat in the same block.
- Use headings to guide the reader, not decorate the page.
- Use sentence-case headings and keep them functional.
- Use lists only when they improve comprehension. Do not convert normal explanation into bullets just to make the page look structured.
- Optional recall checks should stay inline inside an existing required section. Do not add `## Recall prompts`, `### Recall`, or any other non-schema heading unless the user asks.
- Follow `AGENTS.md` for required section families and repo-wide Markdown formatting rules.

## Citations in prose

- In normal prose, cite wiki pages inline with bare `[[slug]]` links.
- In normal prose, cite `raw/` materials with Markdown footnotes when the prose depends directly on them.
- Treat footnotes as attribution and locator detail only, not as a place for side arguments, caveats, definitions, or extra explanation.
- Use a raw footnote when a claim is quoted, dated, numerical, source-specific, potentially disputed, surprising, or otherwise grounded directly in `raw/` material.
- A raw footnote is optional for broad orienting statements that are immediately followed by a cited supporting sentence or paragraph.
- A raw footnote is discouraged for generic setup sentences and repeated restatements of a claim already cited in the same short paragraph.
- When adjacent sentences rely on the same raw source and the same locator or tight locator range, one footnote may cover them both. Split footnotes when the support shifts to a different section, page, source, or evidentiary strength.
- When a sentence is supported by both wiki pages and raw material, prefer an inline `[[slug]]` link plus a raw footnote.
- In raw-source footnotes, put the `[[raw/...]]` link first, then add the shortest useful locator detail.

## Page-type guidance

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

## Anti-patterns

- Avoid academic throat-clearing. Start with the claim or definition rather than several setup sentences.
- Avoid assistant-style filler such as `Sure`, `Let's break this down`, or `Here's the key idea`.
- Avoid expert-only shorthand that assumes the reader already knows the field's key terms, distinctions, or acronyms.
- Avoid “teaching mode” that turns a normal wiki page into a tutorial chapter or primer when one or two orienting sentences would do.
- Avoid repetitive paraphrase across the lead, summary, and first body paragraph.
- Avoid dense multi-idea paragraphs that define, compare, caveat, and historicize at the same time.
- Avoid generic bullets that replace explanation with vague phrases.
- Avoid inflated prose that sounds professional only because it is abstract, formal, or jargon-heavy.
- Avoid vague claims such as `This is important because it affects many things`.
- Avoid adding new schema-like headings for recall checks, comparisons, or maps. Use the existing required sections.

## Practical checks

Before finishing a material writing pass, check:

- the lead exists and states the page's main value early
- the page uses only the required section families from `AGENTS.md` unless the user asked for a different structure
- the page defines the topic before diving into nuance
- the page teaches the smallest useful model before expanding into details
- the first screen contains a real answer or summary, not only setup
- useful examples, contrasts, or boundary statements appear where they speed learning
- synthesis pages are framed as reusable questions when possible
- comparison and map syntheses are considered for mature topic areas
- recall checks, when used, stay inside existing required sections
- a careful newcomer could follow the lead without outside explanation
- paragraphs are short enough to scan comfortably
- bullets are used only where they improve comprehension
- repeated paraphrase has been removed
- the prose sounds human and professional, not stiff, academic, inflated, or chatty
- non-obvious terms are defined or grounded on first use
- uncertainty, assumptions, and evidence limits are explicit where needed
- citation density matches the support instead of becoming mechanical
- footnotes carry attribution and locator detail, not side arguments
- the page still reads like durable wiki prose rather than a transient chat reply

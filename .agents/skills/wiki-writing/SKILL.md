---
name: wiki-writing
description: Use when creating, editing, reviewing, or planning prose for typed markdown wiki pages in a repo based on this template. Covers leads, answer-first flow, paragraph and list usage, citation readability, uncertainty handling, and page-type writing patterns.
---

# Wiki Writing

Use this skill before creating or materially revising wiki prose in a repository derived from this template.

Gold-standard reference pages live in `references/examples/`. Use them when you need a concrete shape for a strong `source`, `entity`, `concept`, or `synthesis` page, including comparison and map synthesis subpatterns.

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
- Apply the page-type boundary in `references/page-decisions.md`: named persistent things are usually `entity` pages, while recurring ideas, mechanisms, methods, distinctions, and claim families are usually `concept` pages.
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
- Use the first required section as the page's fast take; do not add a non-schema `## Fast take` heading unless the user asks. The optional `## Claims ledger` on source pages is schema, not a stray section.
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
- Writing sequence per page type: `references/page-type-guidance.md`.
- Follow `AGENTS.md` for repo-wide Markdown rules and `references/body-templates.md` for required section families.

## Citations

Inline wiki links and raw footnotes follow the core rules in AGENTS.md. Footnote behavior is in references/citations.md.

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

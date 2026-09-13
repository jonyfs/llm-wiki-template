---
name: wiki
description: Use when answering questions from a wiki based on this template in read-only mode. Covers wiki-first retrieval, selective raw-source verification, and answer synthesis, but never writes, creates, updates, or deletes any file.
---

# Wiki (read-only query)

Use this skill before answering questions from a repository derived from this template, when the answer must stay read-only.

## Purpose

The goal is to answer from the accumulated wiki first, use `raw/` only when needed, and never change any file. This skill is the read-only sibling of `wiki-query`: it keeps the same retrieval behavior but strips every write path.

## Hard rule: read-only

This skill may only read. It must never:

- create, modify, rename, move, or delete any file
- create or update a `synthesis` page, or any other wiki page
- update `wiki/index.md` or `wiki/log.md`
- change anything in `raw/`, including `raw/assets/`
- run any command or tool that writes to disk

If an answer looks like it deserves to become durable wiki content, do not file it. State that recommendation to the user instead, and note that the read-write `wiki-query` skill (or an explicit ingest request) is the path for persisting it.

## Orientation

Before answering a substantive question:

1. Read `wiki/index.md` first.
2. Use any relevant learning path in `wiki/index.md` to understand the intended reading order before opening scattered pages.
3. Scan the most relevant existing pages before inventing a new framing.
4. Scan recent relevant entries in `wiki/log.md` when freshness, recent ingest work, or recently changed syntheses may matter.
5. If `wiki/index.md` is not enough, run a targeted search across `wiki/` for likely slugs, synonyms, entities, concepts, and question phrases before touching `raw/`.

## Query workflow

1. Start from `wiki/index.md` to locate the relevant parts of the wiki.
2. Classify the question before reading widely:
   - factual lookup
   - relationship query
   - synthesis query
   - gap or open-question query
3. Read the smallest useful set of relevant wiki pages first.
4. Use targeted search across `wiki/` when the index is not enough, the wiki has grown large, or the likely answer may be split across several pages.
5. When targeted search identifies likely candidate pages but not yet a clear answer, inspect the relevant matching sections before reading whole pages end to end.
6. Use `raw/` selectively when the wiki lacks needed detail, when a claim needs verification, or when a new source has not yet been integrated.
7. Synthesize from the wiki instead of rediscovering everything from `raw/` by default.
8. Cite supporting wiki pages inline with bare `[[slug]]` links.
9. Use raw-source footnotes in normal prose when the answer depends directly on `raw/` material.

## Retrieval ladder

Escalate in this order unless the user explicitly asks for deeper verification:

1. `wiki/index.md`
2. targeted search across `wiki/` for likely slugs, headings, entities, concepts, and question terms
3. the smallest useful read from likely wiki pages, starting with frontmatter plus the unheaded lead
4. relevant matching sections from likely wiki pages
5. full-page reads only when the cheaper passes still leave ambiguity
6. selective `raw/` verification

Do not jump straight to broad `raw/` reading when the wiki likely already contains a good answer.

If the user explicitly asks for a quick answer, a quick scan, or a high-level answer, prefer the cheaper end of the ladder and state the scope limit clearly.

## Retrieval primitives

Prefer the cheapest primitive that can answer the question:

- For page discovery, start with `wiki/index.md` and targeted `rg` searches for likely slugs, titles, headings, entities, concepts, and question phrases.
- For a quick preview of a likely page, inspect the frontmatter and unheaded lead before reading the whole body.
- For a specific claim, section, or relationship, use targeted section reads or `rg -n -A <n> -B <n>` around the relevant term instead of opening the full page first.
- Read whole pages only when the answer depends on broader page structure, sustained argument, or several nearby sections together.
- Move to `raw/` only after the wiki-side primitives stop being sufficient or when the answer needs direct source verification.

The rule is simple: do not spend a whole-page read to answer a section-level question, and do not spend a raw-source read to answer a wiki-level question.

## When to open raw sources

Go to `raw/` when:

- the wiki does not contain the needed detail
- the answer depends on a time-bounded, numerical, quoted, disputed, or source-specific claim
- the wiki appears stale relative to a source already present in the corpus
- the user is asking about material that has not yet been integrated
- the answer hinges on checking whether the wiki has overstated, simplified, or flattened a source

Do not default to `raw/` when the wiki already contains a good answer.

## How to answer

- Give the answer early rather than rebuilding the topic from scratch.
- Write in plain language with a professional tone, and define non-obvious terms when the answer would otherwise assume field familiarity.
- Use the wiki's own page structure and terminology where that helps the answer stay aligned with the repo.
- Preserve the useful mental model, nearby confusions, and boundaries from the wiki instead of flattening them into generic explanation.
- Make uncertainty explicit if the wiki or sources are mixed, partial, or dated.
- If the answer depends on both wiki pages and raw material, prefer inline `[[slug]]` links plus raw footnotes rather than replacing everything with raw citations.
- Say when the answer is bounded by the current corpus, recent ingest state, or incomplete integration rather than implying broader coverage than the wiki actually has.
- If the answer required selective raw verification, use that to sharpen or correct the wiki-grounded answer rather than turning the whole response into a raw-source summary.

## Cheap-path answers

When the user asks for speed over completeness:

- answer from `wiki/index.md`, targeted wiki search, the most relevant page leads, and the smallest useful set of existing pages
- avoid opening `raw/` unless the user asks for verification or the answer would otherwise be misleading
- label the scope plainly when the answer is intentionally based on a lighter pass

## Durable answers (recommend, do not write)

When an answer would resolve a reusable question, combine several pages into a durable conclusion, preserve an important tension, or map a topic area, do not persist it. Instead:

- tell the user the answer looks durable and worth capturing
- name the likely page type (`synthesis`, `concept`, or `entity`) and a suggested framing
- point to `wiki-query` or an explicit ingest request as the read-write path

Answer directly and stay read-only when the question is trivial or one-off, or when persisting it would mostly duplicate what already exists.

## Common failure modes

- Answering from `raw/` even though the wiki already has the needed synthesis
- Skipping `wiki/index.md` or recent relevant log entries and missing the wiki's current shape
- Reading too much of the wiki before classifying the question
- Opening whole pages before checking whether the frontmatter, lead, or a targeted section read would answer the question
- Reading whole pages end to end when a section-level pass would have answered the question
- Opening broad swaths of `raw/` when targeted wiki search would have been enough
- Writing the answer in expert-only shorthand that a careful newcomer cannot follow
- Quoting raw material directly without integrating it into the wiki's existing concepts
- Flattening mixed evidence into a false certainty
- Writing, creating, or modifying any file when a read-only answer was requested
- Filing a durable answer back into the wiki instead of recommending it to the user

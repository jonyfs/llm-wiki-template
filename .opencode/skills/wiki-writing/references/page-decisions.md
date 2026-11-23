# Page decisions: create vs update, entity vs concept

Read on demand before creating a page or choosing its type. Canonical location for these rules; AGENTS.md links here.

## Create vs update

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

## Entity vs concept

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

---
name: wiki-router
description: Use first when a request about this LLM wiki is unclear or when choosing which repo-local wiki skill applies. Maps the request to exactly one playbook skill.
---

# Wiki Router

Use this skill to pick one playbook. It does not do the work itself, and it does not chain several skills.

## Route table

| Request | Load exactly this skill |
|---------|-------------------------|
| Write or revise wiki prose for any page type | `wiki-writing` |
| Add, ingest, or integrate a source already in `raw/` | `wiki-ingest` |
| Answer a question, and possibly file the answer as a page | `wiki-query` |
| Answer a question with no file changes allowed | `wiki` |
| Remove a subject, page, or reference | `wiki-delete` |
| Refresh raw drift, lint, health check, orphan or broken-link audit | `wiki-maintenance` |

If no row fits, ask the user one clarifying question. Do not load several skills to cover the gap.

## Disambiguation

- A question with no write request goes to `wiki-query` by default.
- Read-only wording such as "do not write", "read-only", or "just tell me" overrides every other row and routes to `wiki`.
- A URL, PDF, or pasted text that is not in `raw/` is not an ingest request yet. Ask whether to add it to `raw/` first, and add it only on explicit instruction.
- A request to fix raw drift is `wiki-maintenance`, not `wiki-ingest`.

## Rules

- State the chosen route in one line before loading the skill.
- Each playbook loads its own dependencies. For example, `wiki-ingest` tells you when to also use `wiki-writing`. The router does not chain them.

---
name: wiki-delete
description: Use when removing pages, links, footnotes, or index entries about a subject that should not be in this LLM wiki. Finds every mention, shows impact, requires explicit confirmation, then unwraps links and deletes pages. Never touches raw/.
---

# Wiki Delete

Use this skill to remove a subject from a repository derived from this template. Deletion is irreversible for the page file, so every step before the write is part of the safety contract.

## Hard rules

- Never modify, rename, or delete anything under `raw/`, including `raw/assets/`. Raw files are the corpus, not wiki content (canonical rule: `AGENTS.md` "Purpose").
- Never delete a page or change a file without explicit user confirmation of the exact plan shown in step 4.
- Never delete a page whose removal would silently break another page's `sources` without also resolving those dependents (step 5).
- Write all artifacts and log entries in English.

## Procedure

1. **Orient.** Read `AGENTS.md`, `wiki/index.md`, and the last entries of `wiki/log.md`. Load `wiki-maintenance` if you need lint rules.

2. **Find every mention.** Search `wiki/` (and `wiki/index.md`) for the subject: slug, title, aliases, and phrases. Use `python3 scripts/wiki_search.py "<term>"` when available, and `grep -rn` otherwise. Collect each hit as one of:
   - a page whose main subject is the term (candidate for page deletion);
   - a body wikilink `[[slug]]` to such a page;
   - a footnote citing it;
   - a `sources` frontmatter entry pointing to it;
   - an index entry or a `Related pages` line.

3. **Classify.** For each hit decide:
   - **Page delete**: the page is about the subject and has no independent value. Delete the file.
   - **Reference removal**: the page is valid, but a sentence, link, footnote, or entry mentions the subject. Remove only the reference.
   - **Keep**: the mention is a legitimate contrast, correction, or open question. Do not delete it. Report it.

4. **Show the impact and ask.** Compute and present:
   - backlinks to each page slated for deletion (`python3 scripts/wiki_search.py --backlinks <slug>` or a grep of `[[slug]]`);
   - pages whose `sources` list a slated slug (these are dependents);
   - the exact list of files to change and the exact text removals.
   Ask the user to confirm the plan. Stop until they answer. A confirmation for a different plan does not count.

5. **Resolve dependents.** A page whose `sources` lists a deleted slug must be edited to drop that entry. If it has no remaining wiki-page support, flag it to the user rather than deleting it silently.

6. **Apply.**
   - Unwrap each `[[slug]]` to its plain display text (keep the words, drop the brackets).
   - Remove footnotes that cite the deleted subject, and remove their markers.
   - Remove the matching `wiki/index.md` entry and any learning path step that names a deleted page.
   - Remove `sources` entries that point to deleted pages.
   - Set `updated_at` to today's date on every content page materially changed.
   - Delete the page file for each page-delete item. Never delete a file outside `wiki/sources/`, `wiki/entities/`, `wiki/concepts/`, or `wiki/syntheses/`.

7. **Log.** Append one entry to `wiki/log.md`:

   ```md
   ## [YYYY-MM-DD] delete | <short subject title>
   ```

   List the deleted pages and the reference removals in a few lines.

8. **Verify.** Run `python3 -m unittest discover -s tests -t .` and `python3 scripts/lint.py --root .`. Fix any violation caused by the deletion. Confirm with `git status` that no path under `raw/` changed.

## Done criteria

- Every hit from step 2 is either removed, kept with a reason, or reported.
- No dangling `[[slug]]`, no `sources` entry for a deleted slug, no index entry for a deleted page.
- `wiki/log.md` has the delete entry; `raw/` is unchanged; lint and tests pass.

## Related skills

- `wiki-router` when the request is unclear.
- `wiki-maintenance` for lint and refresh rules.

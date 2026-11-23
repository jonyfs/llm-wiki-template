---
name: wiki-update
description: Use when a notebook made from, or forked from, the LLM Wiki Template should receive the template's newer skills, scripts, tests and rules. Covers the dry run, applying the update on a branch, merging files you customized, migrating existing wiki pages, verifying, and recording the update. Never edits raw/ or rewrites wiki pages as part of the update.
---

# Wiki Update

Use this skill before updating a notebook (a fork, or a copy made with "Use this template") with changes from the template. It does not edit wiki pages. For page fixes after the update, use `wiki-maintenance` and `wiki-writing`.

## What the update touches

The template lists what it owns in `.agents/template-manifest`:

- **managed**: `.agents/skills/`, `.agents/commands/`, `scripts/`, `tests/`, `docs/migration.md`. Replaced when you never changed them, merged when both sides changed.
- **merge**: `AGENTS.md`. Expect customizations; conflicts come to you.
- **once**: the CI workflow. Copied only when missing.
- **link**: the entry points for other agents (`CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`, `.claude/`, `.opencode/`). Recreated when missing.
- **never**: `raw/`, `wiki/`, `README.md`, `LICENSE`, and the template's own site. The update leaves them alone, apart from one line it appends to `wiki/log.md`.

The version your notebook started from is recorded in `.agents/template.lock`. Without it, the script recognizes unmodified old files by comparing them with the template's history.

## Rules

- Never edit anything under `raw/`.
- Never delete or rewrite wiki pages as part of the update. Page fixes come afterwards, only for what `scripts/lint.py` or `docs/migration.md` ask for, and you ask before editing many pages.
- Do not use `--prune`, `--allow-dirty`, a push or a pull request without telling the user first.
- Ask for a go-ahead before `--apply`, unless the user already asked you to apply the update.
- If a step surprises you (a file you did not expect, a failing check you cannot explain), stop and report instead of forcing it.

## Steps

1. **Orient.** Read `AGENTS.md`. Run `git status` (it must be clean) and note whether `.agents/template.lock` exists. If `scripts/update-llm-wiki.sh` is missing, an older copy has no updater yet. Download it and run it from the repository root:
   `curl -fsSL https://raw.githubusercontent.com/jonyfs/llm-wiki-template/main/scripts/update-llm-wiki.sh -o /tmp/update-llm-wiki.sh` then `bash /tmp/update-llm-wiki.sh`.
2. **Dry run.** Run `bash scripts/update-llm-wiki.sh`. It changes nothing. Read the whole report and tell the user, in plain words: which new features arrive (the commit list), which files will be added or updated, which files they customized, and how many conflicts to expect. Ask whether to go on.
3. **Apply on a branch.** Run `bash scripts/update-llm-wiki.sh --apply --branch update-llm-wiki-YYYYMMDD`. Exit code 2 means conflicts are left for you.
4. **Resolve each conflict.** List them with `find . -name '*.template-new' -not -path './.git/*'`. For each `FILE` you have three versions: `FILE` (yours), `FILE.template-new` (the template's current one) and, when the base is known, `FILE.template-base` (what your copy started from).
   - With a base, `git merge-file -p FILE FILE.template-base FILE.template-new` prints a merge with conflict markers. Resolve them.
   - Without a base, read `diff -u FILE FILE.template-new` and decide hunk by hunk.
   - Keep deliberate customizations (project names, domain rules, extra skills you added). Adopt the template's improvements to structure, rules and playbooks.
   - For `AGENTS.md`, keep the project-specific parts and take the template's changes to the schema, the required skills list and the operations. Keep it short. Run the `humanizer` pass on any prose you write.
   - For a skill you customized heavily, tell the user what you kept and what you dropped.
   - When `FILE` is resolved, delete `FILE.template-new` and `FILE.template-base`.
5. **Migrate existing wiki content.** Read the new `docs/migration.md`. Run `python3 scripts/lint.py`. Fix what the migration notes or lint report with `wiki-maintenance` and `wiki-writing`. Never touch `raw/`.
6. **Verify.** Run `python3 -m unittest discover -s tests -t .` and `python3 scripts/lint.py`. Confirm no `*.template-new` or `*.template-base` file is left, `wiki-router` lists the new skills, and `git status` shows only files you expect.
7. **Record the base.** If there were conflicts, run `bash scripts/update-llm-wiki.sh --finish`. It refuses while unresolved files remain, then writes the new base to `.agents/template.lock`. Without conflicts the lock is already written.
8. **Hand over.** The script appended a line to `wiki/log.md`. Check that it reads well. Show `git diff --stat`, commit with "Update template files to <short sha>", and stop there. Push or open a pull request only if the user asks.

## What to tell the user

Keep it short: the version before and after, the features that arrived and how to try them (new skills, commands, scripts), the files you merged by hand and what you kept, any wiki pages that needed migration, the result of the checks, and what is left.

## When the script cannot help

- "This is the template repository itself": there is nothing to update here.
- Not a git repository: ask the user to run `git init` and commit first.
- Offline: the script needs the template URL. `TEMPLATE_URL` may point at a local clone.
- A fork with a long diverged history works the same way: the script compares file content, not history.

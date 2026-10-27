# LLM Wiki

**Let your AI assistant write the wiki you never had time for.**

Add files, links or pasted text. Your assistant reads them with its wiki skills, writes linked markdown pages, and answers your questions from those pages, citing them. The wiki is plain files in git: no database, no API keys. It works with Claude Code, Cursor, GitHub Copilot, OpenCode and Codex.

[Live site](https://jonyfs.github.io/llm-wiki-template/) · [Use this template](https://github.com/jonyfs/llm-wiki-template/generate) · [Start in five minutes](#5-start) · [The original gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/images/graph-dark.jpg">
    <img alt="A made-up wiki shaped like a brain: colored cells for pages, curved lines for links" src="docs/images/graph-light.jpg" width="820">
  </picture>
</p>

<p align="center"><sub>A made-up wiki in the shape of a brain, captured from the live graph on the site. Each cell is a page, each line is a <code>[[wikilink]]</code>, and pages with more links grow bigger. GitHub does not run the animation, so this is a still.</sub></p>

New here? Read the five parts in order, or jump to the one you need: [1 Understand the idea](#1-understand-the-idea) · [2 See it working](#2-see-it-working) · [3 Use it](#3-use-it) · [4 Why it pays off](#4-why-it-pays-off) · [5 Start](#5-start)

---

## 1. Understand the idea

Everything in this part paraphrases [Andrej Karpathy's gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f), using the names this template gives things.

### The problem: asking your documents a question

Most tools that answer from documents work like the first picture. The gist puts NotebookLM, ChatGPT file uploads and most RAG setups in that group.

| Retrieval, the usual way | An LLM wiki |
|---|---|
| <img src="docs/images/retrieval.svg" alt="Retrieval: documents are cut into pieces, the pieces become an answer, and every new question starts the loop again" width="400"> | <img src="docs/images/wiki.svg" alt="LLM wiki: documents are read once into linked pages, and answers draw on those pages and can be added back" width="400"> |
| 1. You upload files.<br>2. When you ask, the tool pulls out the pieces that look relevant.<br>3. The model writes a fresh answer from those pieces.<br>4. The next question starts again at step 2. Nothing is kept. | 1. You add a source.<br>2. The assistant reads it once and writes or updates linked pages.<br>3. Later questions start from those pages, with links and flagged contradictions already there.<br>4. The pages stay, and every new source or answer adds to them. |

Example: you save five papers about sleep. Ask how they disagree and a retrieval tool digs through fragments of all five again, every time. In a wiki, the page on sleep and memory already says where paper 2 and paper 4 disagree, and cites both.

### Who does what

You decide what goes in and what to ask. The assistant does the upkeep.

| You | The assistant |
|---|---|
| Pick the sources. | Summarizes each source. |
| Ask the questions. | Links related pages. |
| Read the pages and decide what it all means. | Files everything in the right place. |
| | Keeps summaries current and flags contradictions. |

Karpathy compares it to programming: Obsidian is the editor, the assistant is the programmer and the wiki is the codebase. Obsidian is optional here. Any markdown editor, or just your file browser, works.

### Three layers

Each layer has one owner. That keeps the sources trustworthy and the pages consistent.

<p align="center"><img src="docs/images/layers.svg" alt="Three layers: instructions on top, linked wiki pages in the middle, read-only source files at the bottom" width="520"></p>

- **The schema** is a short instruction file (here, `AGENTS.md` plus the skills in `.agents/skills/`) that says how the wiki is laid out and what to do for each kind of request. You and the assistant refine it as you learn what works.
- **The wiki** is the markdown pages the assistant writes: summaries, entity and concept pages, comparisons, syntheses. You read them. The assistant owns them and keeps them consistent.
- **Raw sources** are your articles, papers, images and data files. They never change. This is the source of truth.

Example: reading a novel. The chapters you save are the raw layer. The wiki gets a page for each character and theme. The schema can say that every character page lists the chapters where that person appears.

### Three operations

Everything you do with the wiki is one of these.

#### Ingest

<img src="docs/images/ingest.svg" alt="One source on the left fans out to about eight pages: a source page, entity pages, concept pages, a synthesis, the index and the log" width="460" align="right">

You add a source and ask the assistant to process it. It reads the source, talks through the main points with you if you like, writes a summary page, updates the index, updates the entity and concept pages the source touches, and adds a line to the log.

One source can change 10 to 15 pages. The gist prefers ingesting one source at a time and staying involved: reading the summaries and steering what to emphasize. You can also ingest many at once with less supervision. Whichever you pick, write the workflow into the schema so the next session follows it.

Example: you add a transcript of a podcast about sleep. The assistant writes a page for the episode, adds a paragraph to the page on melatonin, creates a page for the guest and links the three. In this template that is the `wiki-ingest` skill.

<br clear="right">

#### Query

<img src="docs/images/query.svg" alt="A question reads wiki pages and produces an answer, and the answer can be filed back as a new page" width="460" align="right">

You ask a question. The assistant searches the wiki, reads the relevant pages and answers with citations. The answer can be a page, a table, a slide deck or a chart, whatever fits the question.

A good answer can also be filed back into the wiki as a new page. A comparison you asked for or a connection you found should not vanish into chat history.

Example: you ask for a comparison of two note apps and like it, so the assistant saves it as a synthesis page. A month later you ask a follow-up and it starts from that page. In this template that is the `wiki-query` skill, or `wiki` when nothing may be written.

<br clear="right">

#### Lint

<img src="docs/images/lint.svg" alt="A wiki graph with one orphan page circled, one stale page drawn dotted and one pair of pages that contradict each other" width="460" align="right">

From time to time, ask the assistant to check the wiki's health. It looks for:

- pages that contradict each other
- claims that newer sources have replaced
- orphan pages that nothing links to
- ideas mentioned often but without a page of their own
- missing cross-references between related pages
- gaps that a web search could fill

It is also good at suggesting what to read or ask next. In this template, lint and refresh live in the `wiki-maintenance` skill.

<br clear="right">

### Index and log

Two plain files help both of you find your way as the wiki grows.

`wiki/index.md` is a catalog of every page: a link, a one-line summary, grouped by category. The assistant updates it on every ingest and reads it first when you ask something. The gist says this works well up to roughly a hundred sources and a few hundred pages, with no search infrastructure.

`wiki/log.md` records what happened and when: ingests, questions, lint passes. It only ever grows. Start every entry with the same prefix and simple tools can read it:

```text
## [2026-04-02] ingest | Sleep podcast transcript
## [2026-04-03] query | How do the sleep papers disagree?
## [2026-04-09] lint | 3 orphan pages found
```

```bash
grep "^## \[" wiki/log.md | tail -5    # the last five entries
```

### The vocabulary

| Term | Meaning |
|---|---|
| Source page | One page per raw file. It summarizes what the source says and numbers its claims so other pages can cite them, like `[[slug]] C1`. |
| Entity page | A person, company, product or place that shows up in more than one source. |
| Concept page | An idea, method or theme. It explains the thing and links to the sources behind it. |
| Synthesis page | The saved answer to a question that needed several pages. |
| Wikilink | A `[[slug]]` link from one page to another. Obsidian reads them too. |
| Frontmatter | A small block of YAML at the top of each page with title, type, sources and dates. The lint script checks it. |
| Skill | A markdown file in `.agents/skills/` that tells the assistant how to do one job, such as ingest, query or lint. |

---

## 2. See it working

The graph at the top of this page is simulated data in the shape of a brain, not a real wiki. On the [live site](https://jonyfs.github.io/llm-wiki-template/) it turns, and three buttons play the operations from part 1: adding a page is an ingest, asking the wiki is a query, and running lint is a lint. Cells have different shapes by page type, so the type reads without the color: pyramidal cells for sources, star-shaped ones for entities, branched ones for concepts and large ones for syntheses.

---

## 3. Use it

### What you can add

Start with what you already have. You choose the sources, and the assistant never edits them.

| Source | How it works |
|---|---|
| Files on your computer | Notes, markdown, text, PDFs, images and data files such as CSV. Copy them into `raw/` and ask the assistant to ingest them. |
| Links from the web | Paste a link and the assistant asks whether to save the page into `raw/` first. If you say yes, it keeps a clean copy and notes the date it was fetched. |
| Text you paste | An email, a chat thread or a transcript. The assistant asks before saving it as a file in `raw/`, then ingests it like any other source. |
| Screenshots and scans | Images count as sources too. The assistant separates what it can read in the image from what it is guessing, and says so when it can't read one reliably. |

Whatever the format, the assistant needs a tool that can read it. If it can't, it tells you instead of guessing.

### Every request goes through a skill

When you ask the assistant to ingest, answer or remove something, `AGENTS.md` tells it to load the matching skill first. That is why every answer is built the same way: it starts from the index, uses your pages, cites them and logs any change it makes. These are instructions the assistant follows, not a lock, so if an answer looks like it skipped the wiki, ask it to use the wiki skill and cite its pages.

| You say | Skill | What happens |
|---|---|---|
| Ingest this file or link | `wiki-ingest` | Reads the source, writes or updates the pages it affects, then updates the index and log. A link or pasted text is saved to `raw/` first, and only after you say yes. |
| What does the wiki say about X? | `wiki-query` | Starts from the index, reads the relevant pages, opens raw files only to verify, and cites what it used. It can save a useful answer as a synthesis page. |
| Just tell me, don't change anything | `wiki` | The same lookup, but it cannot write, create or delete a file. |
| Check the wiki | `wiki-maintenance` | Lint looks for broken links, missing fields and orphan pages. Refresh reports raw files that changed after their page was written. |
| Remove everything about X | `wiki-delete` | Lists every mention, shows what would change and waits for your confirmation. It never touches raw files. |
| Write or fix a page | `wiki-writing` | Sets the page type, headings, frontmatter and citation style before any wiki prose is written. |
| Update this notebook from the template | `wiki-update` | Dry-runs the template's changes, applies them on a branch, merges the files you customized and records the new base. It never touches `raw/` or wiki pages. |
| Not sure what to ask | `wiki-router` | Picks exactly one of the skills above, or asks you one question. |

Shortcut commands in `.agents/commands/` call the same skills: `/wiki-ingest`, `/wiki-query`, `/wiki` (read-only), `/wiki-lint`, `/wiki-refresh` and `/wiki-update`.

```mermaid
flowchart TD
    R[Request] --> ROUTER{wiki-router}
    ROUTER -->|write prose| WW[wiki-writing]
    ROUTER -->|add source| WI[wiki-ingest]
    ROUTER -->|answer and file| WQ[wiki-query]
    ROUTER -->|answer only| W[wiki]
    ROUTER -->|refresh or lint| WM[wiki-maintenance]
    ROUTER -->|remove subject| WD[wiki-delete]
    ROUTER -->|update from template| WU[wiki-update]
```

### Examples from an ordinary week

Made-up situations, but the steps are the real ones.

- **Studying for an exam.** You keep lecture PDFs, your class notes and two articles you found online. You tell the assistant to ingest them, and the links are saved to `raw/` after you approve it. Before the exam you ask: "What did the course say about Keynes, and where does the article disagree?" The answer cites the lecture page and the article page.
- **Running a small business.** You drop in proposals, signed contracts, meeting notes and emails exported as text. Months later: "What did I promise this client about delivery, and did the scope change?" The assistant points to the proposal and to the later email, and says where they differ.
- **Planning a trip.** You save a few blog posts as links, the booking confirmation as a PDF and screenshots of the map. You ask: "We land on Sunday night and the museum closes on Mondays. Which day works?" The answer comes from your saved sources, and each claim links to the page it came from.
- **Keeping a team's decisions.** You add meeting notes, design docs and issue threads over a few months. A new teammate asks: "Why did we pick Postgres?" The assistant answers from the decision pages and can save the answer as a synthesis page, so the next person finds it already written.

In each case, `wiki-query` handles the questions and `wiki-ingest` handles every source you add.

### Folder map

```
.
├── AGENTS.md                 # always-on rules for structure and workflows
├── .agents/
│   ├── skills/               # step-by-step playbooks for each task
│   └── commands/             # short commands that invoke the playbooks
├── raw/                      # your curated, read-only source documents
├── wiki/                     # the assistant-maintained notebook
│   ├── index.md              # catalog of pages and learning paths
│   ├── log.md                # append-only record of operations
│   ├── sources/              # one page per source (optional subject subfolder)
│   ├── entities/             # people, organizations, products, places
│   ├── concepts/             # ideas, methods, theories
│   └── syntheses/            # comparisons, maps, durable answers
├── scripts/                  # lint, refresh, search, the new-llm-wiki.sh starter and the update-llm-wiki.sh updater
├── tests/                    # checks that keep the template healthy
├── docs/                     # migration notes and the README images
└── github-pages/             # the template's own site (the starter script removes it)
```

Multi-agent entry points (`CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`, `.claude/`, `.opencode/`) are links to the same source of truth, so one edit reaches every assistant.

### Keeping the wiki healthy

- **refresh** detects when a source has changed and reports which pages to revisit: `python3 scripts/refresh.py`
- **lint** checks structure, link integrity, stale claims and integration gaps: `python3 scripts/lint.py`
- **search** finds pages by term: `python3 scripts/wiki_search.py "<terms>"`
- **tests** keep the template itself healthy: `python3 -m unittest discover -s tests -t .`

---

## 4. Why it pays off

Plain files, a few scripts and instructions your assistant follows. Nothing runs in the background.

- **Answers you can check.** Claims in wiki pages carry a footnote that points at the raw file. When the assistant answers, it names the pages it used, so you can open them.
- **Your sources stay untouched.** The assistant reads `raw/` but never edits it. Everything it writes goes into `wiki/`, and git keeps the history.
- **A record of every change.** `wiki/index.md` lists every page. `wiki/log.md` records what the assistant did and when.
- **Good answers get reused.** A useful answer can be saved as a synthesis page. The next similar question starts from that page instead of the raw files.
- **Problems show up early.** Lint catches broken links and missing fields. Refresh tells you when a raw file changed after its page was written.
- **Removing things is safe.** Removing a subject lists every mention first and waits for your yes. The raw files stay where they are.

### Why this works

Keeping a knowledge base up to date is mostly bookkeeping: fixing cross-references, rewriting summaries, noticing when new data contradicts old claims. People give up on wikis because that work grows faster than the value they get back. An assistant does not get bored, does not forget a link and can touch 15 files in one pass.

The gist ties this to the Memex, an idea Vannevar Bush described in 1945: a private, curated store of documents with trails of associations between them. What Bush could not solve was who would do the upkeep. That is the part the assistant takes on.

### Who this is for

If one of these sounds like you, it is worth an afternoon.

- **Readers and researchers** who save more papers and articles than they can keep in their heads, and want to ask questions across them.
- **Builders and founders** who keep notes on competitors, customer calls and past decisions, and can never find the one they need.
- **Students and writers** who want to start writing with the citations and cross-references already lined up.
- **Teams** who want one shared notebook in git that stays up to date without someone owning it full time.

Skip it if you need search over millions of documents or a hosted service. This is a folder of markdown on your own machine.

### LLM wiki vs. RAG vs. note apps

The same question, answered three ways. Read the rows as rough generalizations.

| | LLM wiki | RAG | Note apps |
|---|---|---|---|
| Answers get written down | Yes | No, rebuilt each time | Only if you write them |
| Links between ideas exist before you ask | Yes | No | Manual |
| Conflicting claims get flagged | On ingest and lint | Rarely | No |
| Setup | Clone the repo | Embeddings and a vector store | Install an app |
| Where the data lives | Local files | Usually a hosted index | Local or the app's cloud |
| Who writes the notes | The assistant | Nobody, it indexes raw text | You |

### Compatible agents

The instructions live in `AGENTS.md` and `.agents/skills/`. Any agent that reads markdown can follow them.

| Agent | Entry point | Status |
|---|---|---|
| Claude Code | `CLAUDE.md` -> `AGENTS.md` | Supported |
| Cursor / OpenCode | `.cursorrules` -> `AGENTS.md` | Supported |
| GitHub Copilot | `.github/copilot-instructions.md` -> `AGENTS.md` | Supported |
| Codex | `.agents/skills/` | Supported |

Python 3.9+ on macOS, Linux and Windows. Standard library only.

### Common questions

- **Do I need an API key or database?** No. The wiki is plain markdown files in git. You only need an AI coding assistant that can read and write them.
- **How is this different from RAG?** RAG finds the relevant chunks and writes a fresh answer every time you ask. Here the assistant writes the pages ahead of time, so links between ideas and conflicting claims are already on the page when you ask.
- **What can I add to it?** Files you copy into `raw/`: notes, markdown, PDFs, images and data files. Links and pasted text work too, once you agree to save them there. The assistant still needs a tool that can read the format.
- **Do I have to use the skills?** They are how the template works. `AGENTS.md` tells the assistant to load the matching skill before it ingests, answers or removes anything. It's an instruction, not a lock, so if an answer looks like it skipped the wiki, ask it to use the wiki skill and cite its pages.
- **Does it cost a lot of tokens?** `AGENTS.md` is about 10 KB and the scripts print one-line summaries by default.
- **Is my data sent anywhere?** The scripts have no network calls and `raw/` stays on your machine. Whatever your assistant sends to its model depends on which assistant you use.
- **Does it work offline?** The files do. The wiki is local and needs no server. Whether the assistant works offline depends on which assistant you use.
- **Am I locked to one model?** No. The contract is plain markdown plus Python, so any agent that reads files works.

### When something looks wrong

- **Empty wiki after ingest.** Check that the file is in `raw/` and that you actually asked the assistant to ingest it. Nothing fills the wiki by itself.
- **Broken wikilinks.** Run the lint skill. It lists links that point nowhere so you can fix or remove them.
- **Stale claims.** Run refresh. It shows which raw files changed since their source pages were written.
- **Too many pages.** That's normal. Use `wiki/index.md` and the search script to find your way around.
- **The answer ignored the wiki.** Ask the assistant to use the wiki skill and cite the pages it read. If the pages are not there yet, ingest the source first.

---

## 5. Start

Pick the path that fits. All three give you the same template.

### On GitHub

1. Open the repository and click **Use this template**, then **Create a new repository**. Or from a terminal with the [GitHub CLI](https://cli.github.com): `gh repo create my-notebook --template jonyfs/llm-wiki-template --private --clone`.
2. Clone your new repository and open the folder with your assistant: Claude Code, Cursor, GitHub Copilot, OpenCode or Codex.
3. The copy includes the template's own site in `github-pages/` and its workflows. You do not need them for a notebook. Delete `github-pages/`, `.github/workflows/pages.yml` and `.github/workflows/lighthouse.yml`, or use the script below and let it do that.
4. Copy a file into `raw/` and ask: "Ingest `raw/<file>` into the wiki." Then ask a question about it.

### With a local clone

```bash
git clone https://github.com/jonyfs/llm-wiki-template.git my-notebook
cd my-notebook
python3 -m unittest discover -s tests -t .   # sanity check
python3 scripts/lint.py                      # an empty wiki should pass
```

To make it your own history instead of the template's, run `rm -rf .git && git init -b main` and commit.

### With the starter script

`scripts/new-llm-wiki.sh` does the whole clean start in one command. It clones the template (or creates a GitHub repo from it with `--github`), starts a fresh git history, removes the template's GitHub Pages site and workflows, drops the author's citation file and the internal catalogs, resets `wiki/log.md`, writes a short README for your notebook and runs the checks. It refuses to run if the target folder is not empty, and it checks that it is inside a template copy before it deletes anything.

```bash
curl -fsSL https://raw.githubusercontent.com/jonyfs/llm-wiki-template/main/scripts/new-llm-wiki.sh -o new-llm-wiki.sh
bash new-llm-wiki.sh my-notebook                    # local folder
bash new-llm-wiki.sh my-notebook --github           # private GitHub repo, cloned and pushed
bash new-llm-wiki.sh my-notebook --github --public  # same, public
bash new-llm-wiki.sh my-notebook --keep-pages       # keep the GitHub Pages site
```

It also records which template commit your copy started from in `.agents/template.lock`, so the updater below knows its base later. It needs bash, git and python3, plus the GitHub CLI for `--github`. On Windows, use Git Bash or WSL. The full script is at the end of this README.

### Updating a copy or fork

Notebooks made from this template, and forks of it, can pull in the template's newer skills, scripts, tests and rules without losing their own work. Ask your assistant to run `/wiki-update`. The `wiki-update` skill runs the updater, explains what is new, merges the files you customized and checks the result. Or do it by hand:

```bash
curl -fsSL https://raw.githubusercontent.com/jonyfs/llm-wiki-template/main/scripts/update-llm-wiki.sh -o update-llm-wiki.sh   # older copies do not have it yet
bash update-llm-wiki.sh                                  # dry run: shows what would change, touches nothing
bash update-llm-wiki.sh --apply --branch update-llm-wiki # apply it on a new branch
bash update-llm-wiki.sh --finish                         # after you resolved every *.template-new file
```

The template says which files it owns in `.agents/template-manifest`. For each one, the updater compares your file with the version your copy started from and with the template's current version:

| State of the file | What happens |
|---|---|
| New in the template | Added |
| You never changed it, the template did | Updated |
| Only you changed it | Kept |
| Both changed it, in different places | Merged |
| Both changed the same lines | Yours is kept. `FILE.template-new` and `FILE.template-base` appear next to it for you or your assistant to merge |
| `raw/`, `wiki/`, `README.md`, `LICENSE`, your site | Never touched. The only write is one line appended to `wiki/log.md` |

It is a dry run unless you pass `--apply`, and `--apply` needs a clean git tree. The base version lives in `.agents/template.lock`, which `new-llm-wiki.sh` writes for new notebooks. An older copy without it still works: files that match one of the template's past versions count as unmodified. `--prune` also deletes files the template dropped, but only if you never changed them. Afterwards read `docs/migration.md` for changes that affect existing wiki pages, and run `python3 scripts/lint.py`. The full script is at the end of this README.

## Showcase

Built something with this template? Open a Discussion ("Show and tell") and it may be linked here.

## Status

Actively maintained. Last reviewed: 2026-10-27. CI runs on every push and pull request.

## Credits

This template began from [caelaxie/llm-wiki-template](https://github.com/caelaxie/llm-wiki-template), which laid the foundation for the `raw/ -> wiki/` model this repo builds on. The underlying idea comes from Andrej Karpathy's [LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

## The starter script

This is `scripts/new-llm-wiki.sh`, pasted in full so you can read it before you run it.

````bash
#!/usr/bin/env bash
# Start a new notebook from the LLM Wiki Template.
#
#   new-llm-wiki.sh my-notebook                 clone the template into ./my-notebook and start a fresh git history
#   new-llm-wiki.sh my-notebook --github        create a private GitHub repo from the template with the gh CLI, clone it, clean it, push
#   new-llm-wiki.sh my-notebook --github --public
#   new-llm-wiki.sh my-notebook --keep-pages    keep the GitHub Pages site and its workflows
#
# By default the copy loses the template's own GitHub Pages site, its workflows, its marketing docs and its
# log history, so the notebook starts clean. Needs bash, git and python3 (plus gh for --github).
# Environment: TEMPLATE_URL and TEMPLATE_BRANCH override the clone source; TEMPLATE_REPO overrides the --github source.
set -euo pipefail

TEMPLATE_URL="${TEMPLATE_URL:-https://github.com/jonyfs/llm-wiki-template.git}"
TEMPLATE_BRANCH="${TEMPLATE_BRANCH:-main}"
TEMPLATE_REPO="${TEMPLATE_REPO:-jonyfs/llm-wiki-template}"

name=""; use_github=0; visibility="--private"; keep_pages=0; run_checks=1

usage() { sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; }
die() { echo "error: $*" >&2; exit 1; }

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --github) use_github=1 ;;
    --public) visibility="--public" ;;
    --keep-pages) keep_pages=1 ;;
    --no-check) run_checks=0 ;;
    -*) die "unknown option: $1 (try --help)" ;;
    *) [ -z "$name" ] || die "only one notebook name, got '$name' and '$1'"; name="$1" ;;
  esac
  shift
done

[ -n "$name" ] || { usage; exit 2; }
command -v git >/dev/null || die "git is required"
command -v python3 >/dev/null || die "python3 is required"
if [ -e "$name" ] && [ -n "$(ls -A "$name" 2>/dev/null || true)" ]; then die "'$name' already exists and is not empty"; fi

# The exact template commit the copy starts from, so scripts/update-llm-wiki.sh knows its base later.
template_ref="$(git ls-remote "$TEMPLATE_URL" "refs/heads/$TEMPLATE_BRANCH" 2>/dev/null | cut -f1 | head -1 || true)"

if [ "$use_github" -eq 1 ]; then
  command -v gh >/dev/null || die "--github needs the GitHub CLI (https://cli.github.com) and 'gh auth login'"
  case "$name" in */*) die "with --github the name must be a plain repo name, not a path" ;; esac
  echo "Creating $name on GitHub from $TEMPLATE_REPO ..."
  gh repo create "$name" --template "$TEMPLATE_REPO" "$visibility" --clone
else
  echo "Cloning $TEMPLATE_URL ($TEMPLATE_BRANCH) into $name ..."
  git clone --quiet --depth 1 --branch "$TEMPLATE_BRANCH" "$TEMPLATE_URL" "$name"
  rm -rf "$name/.git"
fi

cd "$name"
# Everything below deletes files, so make sure this really is a template copy before touching anything.
[ -f AGENTS.md ] && [ -d .agents/skills ] && [ -d wiki ] || die "this does not look like the LLM Wiki Template, stopping before any cleanup"

# Template-only files: the author's citation file and the internal improvement catalog.
rm -rf CITATION.cff IMPROVEMENTS.md docs/images tests/test_readme.py

if [ -n "$template_ref" ]; then
  printf 'template=%s\nref=%s\nupdated=%s\n' "$TEMPLATE_URL" "$template_ref" "$(date +%Y-%m-%d)" > .agents/template.lock
fi

if [ "$keep_pages" -eq 0 ]; then
  echo "Removing the template's GitHub Pages site and its workflows ..."
  rm -rf github-pages \
    .github/workflows/pages.yml .github/workflows/lighthouse.yml \
    PAGES_IMPROVEMENTS.md PAGES_GROWTH_200.md DISCOVERABILITY.md DESIGN_SYSTEM.md \
    tests/test_github_pages.py
fi

NAME="$name" KEEP_PAGES="$keep_pages" python3 - <<'PY'
import datetime, os, re, pathlib

today = datetime.date.today().isoformat()
name = os.path.basename(os.environ["NAME"].rstrip("/"))

# AGENTS.md: drop the rules about keeping the template's site in sync, which no longer apply.
if os.environ["KEEP_PAGES"] == "0":
    p = pathlib.Path("AGENTS.md")
    s = p.read_text(encoding="utf-8")
    s = re.sub(r"\n## GitHub Pages synchronization\n.*?(?=\n## )", "", s, flags=re.S)
    s = s.replace(", the GitHub Pages copy in `github-pages/`,", ",")
    s = re.sub(r" Pages with translations \(`github-pages/assets/i18n\.js`\) need the same pass in every language\.", "", s)
    p.write_text(s, encoding="utf-8")

# wiki/log.md: keep the header, start a fresh history.
log = pathlib.Path("wiki/log.md")
text = log.read_text(encoding="utf-8")
head = text.split("\n## [", 1)[0].rstrip() + "\n"
log.write_text(head + f"\n## [{today}] bootstrap | Start {name} from llm-wiki-template\n\nCreated from the LLM Wiki Template. Add sources to `raw/`, then ask the assistant to ingest them.\n", encoding="utf-8")

# README.md: a short one for the new notebook.
pathlib.Path("README.md").write_text(f"""# {name}

A notebook that an AI assistant writes and keeps up to date, built from the
[LLM Wiki Template](https://github.com/jonyfs/llm-wiki-template).

- `raw/` holds your sources. The assistant reads them and never edits them.
- `wiki/` holds the linked markdown pages the assistant writes. Start at `wiki/index.md`.
- `AGENTS.md` and `.agents/skills/` tell the assistant how to ingest, answer, check and clean up.

## First steps

1. Copy a file into `raw/`, or paste a link and let the assistant ask before saving it there.
2. Ask your assistant: "Ingest raw/<file> into the wiki."
3. Ask a question: "What does the wiki say about ...?"
4. Now and then: "Run lint on the wiki."
5. To get the template's newer skills and scripts later: ask your assistant to run `/wiki-update`, or run `bash scripts/update-llm-wiki.sh`.

Checks you can run yourself:

```bash
python3 -m unittest discover -s tests -t .
python3 scripts/lint.py
python3 scripts/wiki_search.py "<terms>"
```
""", encoding="utf-8")
PY

if [ "$use_github" -eq 0 ]; then
  git init -q -b main
fi
git add -A
git commit -q -m "Start notebook from llm-wiki-template" || echo "note: could not commit (set git user.name and user.email, then commit yourself)"
if [ "$use_github" -eq 1 ]; then git push -q -u origin HEAD; fi

if [ "$run_checks" -eq 1 ]; then
  echo "Running the template's checks ..."
  if python3 -m unittest discover -s tests -t . >/dev/null 2>&1 && python3 scripts/lint.py >/dev/null 2>&1; then
    echo "Checks passed."
  else
    echo "warning: a check failed. Run 'python3 -m unittest discover -s tests -t .' and 'python3 scripts/lint.py' inside $name to see why."
  fi
fi

cat <<EOF

Done. Your notebook is in ./$name
  cd $name
  1. Copy a file into raw/ (or paste a link to your assistant).
  2. Ask your assistant: "Ingest raw/<file> into the wiki."
  3. Ask it a question about what you added.
EOF
````

## The update script

This is `scripts/update-llm-wiki.sh`, pasted in full for the same reason.

````bash
#!/usr/bin/env bash
# Update a notebook that was made from, or forked from, the LLM Wiki Template.
#
#   update-llm-wiki.sh                       dry run: show what the template would change here
#   update-llm-wiki.sh --apply               apply it (needs a clean git tree)
#   update-llm-wiki.sh --apply --branch NAME create a branch first, then apply
#   update-llm-wiki.sh --finish              after resolving every *.template-new file, record the new base
#   Options: --ref REF (template branch, tag or commit), --prune (delete files the template dropped, only when
#   you never changed them), --allow-dirty, --no-log, --no-check, --force-self, -h.
#
# It only touches files the template owns, as listed in .agents/template-manifest. It never touches raw/ or wiki/
# (apart from one line appended to wiki/log.md), README.md, or the files you customized: where both sides changed
# a file it merges cleanly or, if it cannot, leaves your file alone and writes FILE.template-new and
# FILE.template-base next to it so you or your assistant can resolve it. Needs bash, git and python3.
# Environment: TEMPLATE_URL and TEMPLATE_BRANCH override where the template comes from.
set -euo pipefail

TEMPLATE_URL="${TEMPLATE_URL:-https://github.com/jonyfs/llm-wiki-template.git}"
TEMPLATE_BRANCH="${TEMPLATE_BRANCH:-main}"
LOCK=".agents/template.lock"
PENDING=".agents/template.pending"

die() { echo "error: $*" >&2; exit 1; }
usage() { sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; }

# Everything lives in a function and the call is on one line, so bash has read the whole script before this file
# can be replaced by the update it is applying.
main() {
  local apply=0 ref="" branch="" allow_dirty=0 prune=0 write_log=1 run_checks=1 finish=0 force_self=0
  while [ $# -gt 0 ]; do
    case "$1" in
      -h|--help) usage; return 0 ;;
      --apply) apply=1 ;;
      --finish) finish=1 ;;
      --prune) prune=1 ;;
      --allow-dirty) allow_dirty=1 ;;
      --no-log) write_log=0 ;;
      --no-check) run_checks=0 ;;
      --force-self) force_self=1 ;;
      --ref) shift; [ $# -gt 0 ] || die "--ref needs a value"; ref="$1" ;;
      --branch) shift; [ $# -gt 0 ] || die "--branch needs a name"; branch="$1" ;;
      *) die "unknown option: $1 (try --help)" ;;
    esac
    shift
  done

  command -v git >/dev/null || die "git is required"
  local root; root=$(git rev-parse --show-toplevel 2>/dev/null) || die "run this inside your notebook's git repository"
  cd "$root"
  [ -f AGENTS.md ] && [ -d .agents/skills ] && [ -d wiki ] || die "this does not look like an LLM wiki notebook (AGENTS.md, .agents/skills/ and wiki/ are expected)"
  if [ "$force_self" -eq 0 ] && git remote get-url origin 2>/dev/null | grep -q "jonyfs/llm-wiki-template"; then
    die "this is the template repository itself, not a copy of it (use --force-self to run anyway)"
  fi

  if [ "$finish" -eq 1 ]; then
    [ -f "$PENDING" ] || die "nothing to finish: there is no $PENDING"
    local left; left=$(find . \( -name '*.template-new' -o -name '*.template-base' \) -not -path './.git/*' | sort)
    if [ -n "$left" ]; then echo "Still unresolved:"; echo "$left" | sed 's/^/  /'; return 2; fi
    local pref; pref=$(sed -n 's/^ref=//p' "$PENDING" | head -1)
    write_lock "$pref"; rm -f "$PENDING"
    echo "Recorded template base ${pref:0:7} in $LOCK. Review the changes and commit them."
    return 0
  fi

  if [ "$apply" -eq 1 ] && [ "$allow_dirty" -eq 0 ] && [ -n "$(git status --porcelain)" ]; then
    die "the working tree has uncommitted changes. Commit or stash them first (or pass --allow-dirty)"
  fi
  if [ "$apply" -eq 1 ] && [ -n "$branch" ]; then git switch -c "$branch" || die "could not create branch '$branch'"; fi

  tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
  echo "Fetching $TEMPLATE_URL ..."
  git clone --quiet --no-checkout --filter=blob:none "$TEMPLATE_URL" "$tmp/t" 2>/dev/null \
    || git clone --quiet --no-checkout "$TEMPLATE_URL" "$tmp/t" || die "could not clone the template"

  local target new base=""
  target="${ref:-origin/$TEMPLATE_BRANCH}"
  new=$(tg rev-parse --verify --quiet "$target^{commit}") || new=$(tg rev-parse --verify --quiet "origin/$target^{commit}") || die "unknown template ref '$target'"
  if [ -f "$LOCK" ]; then
    local b; b=$(sed -n 's/^ref=//p' "$LOCK" | head -1)
    if [ -n "$b" ] && tg cat-file -e "$b^{commit}" 2>/dev/null; then base="$b"; fi
  fi
  tg show "$new:.agents/template-manifest" > "$tmp/manifest" 2>/dev/null || die "that template version has no .agents/template-manifest, so it cannot be applied safely"

  if [ -n "$base" ]; then echo "Your copy is based on template ${base:0:7}; updating to ${new:0:7}."
  else echo "No $LOCK here, so the base version is unknown. Files are matched against the template's history instead."; fi
  if [ "$base" = "$new" ] && [ ! -f "$PENDING" ]; then echo "Already up to date."; return 0; fi

  tg ls-tree -r "$new" > "$tmp/tree"
  cut -f2 "$tmp/tree" > "$tmp/newtree"
  : > "$tmp/plan"

  local meta path mode pol status hasbase h
  while IFS=$'\t' read -r meta path; do
    mode="${meta%% *}"
    [ "$mode" = 120000 ] && continue
    pol=$(policy_of "$path")
    case "$pol" in managed|merge|once) ;; *) continue ;; esac
    tg show "$new:$path" > "$tmp/new" || die "could not read $path from the template"
    hasbase=0
    if [ ! -e "$path" ] && [ ! -L "$path" ]; then status=ADD
    elif cmp -s "$path" "$tmp/new"; then status=SAME
    elif [ "$pol" = once ]; then status=KEEP_ONCE
    else
      status=CONFLICT
      if [ -n "$base" ] && tg show "$base:$path" > "$tmp/base" 2>/dev/null; then
        hasbase=1
        if cmp -s "$path" "$tmp/base"; then status=UPDATE
        elif cmp -s "$tmp/new" "$tmp/base"; then status=KEEP_LOCAL
        elif git merge-file -p "$path" "$tmp/base" "$tmp/new" > "$tmp/merged" 2>/dev/null; then status=MERGE
        fi
      else
        h=$(git hash-object "$path")
        if history_has "$new" "$path" "$h"; then status=UPDATE; fi
      fi
    fi
    [ "$status" = SAME ] && continue
    printf '%s\t%s\n' "$status" "$path" >> "$tmp/plan"
    [ "$apply" -eq 1 ] || continue
    case "$status" in
      ADD|UPDATE) install_file "$tmp/new" "$path" "$mode" ;;
      MERGE) install_file "$tmp/merged" "$path" "$mode" ;;
      CONFLICT)
        install_file "$tmp/new" "$path.template-new" "$mode"
        if [ "$hasbase" -eq 1 ]; then install_file "$tmp/base" "$path.template-base" 100644; fi ;;
    esac
  done < "$tmp/tree"

  # Files the template dropped since your base. Only a file you never changed is deleted, and only with --prune.
  if [ -n "$base" ]; then
    tg ls-tree -r --name-only "$base" > "$tmp/basetree"
    while IFS= read -r path; do
      grep -qxF -- "$path" "$tmp/newtree" && continue
      [ "$(policy_of "$path")" = managed ] || continue
      [ -f "$path" ] || continue
      if tg show "$base:$path" 2>/dev/null | cmp -s - "$path"; then
        printf '%s\t%s\n' DROPPED "$path" >> "$tmp/plan"
        if [ "$apply" -eq 1 ] && [ "$prune" -eq 1 ]; then rm -f "$path"; fi
      else
        printf '%s\t%s\n' DROPPED_EDITED "$path" >> "$tmp/plan"
      fi
    done < "$tmp/basetree"
  fi

  local lpol lpath ltarget lcur
  while IFS=$'\t' read -r lpol lpath ltarget; do
    [ "$lpol" = link ] || continue
    if [ -L "$lpath" ]; then
      lcur=$(readlink "$lpath")
      if [ "$lcur" = "$ltarget" ]; then continue; else printf '%s\t%s\n' LINK_DIFFERENT "$lpath" >> "$tmp/plan"; fi
    elif [ -e "$lpath" ]; then printf '%s\t%s\n' LINK_BLOCKED "$lpath" >> "$tmp/plan"
    else
      printf '%s\t%s\n' LINK_ADD "$lpath" >> "$tmp/plan"
      if [ "$apply" -eq 1 ]; then mkdir -p "$(dirname "$lpath")"; ln -s "$ltarget" "$lpath"; fi
    fi
  done < "$tmp/manifest"

  report "$apply"
  echo
  echo "What changed in the template since then (commits touching skills, scripts, tests and rules):"
  if [ -n "$base" ]; then
    tg log --no-merges --format='  %h %s' "$base..$new" -- .agents scripts tests AGENTS.md docs/migration.md | head -40
  else
    tg log --no-merges -n 25 --format='  %h %s' "$new" -- .agents scripts tests AGENTS.md docs/migration.md
  fi

  local changes conflicts
  changes=$(grep -cE "^(ADD|UPDATE|MERGE|CONFLICT|LINK_ADD)"$'\t'  "$tmp/plan" || true)
  conflicts=$(grep -c "^CONFLICT"$'\t'  "$tmp/plan" || true)

  if [ "$apply" -eq 0 ]; then
    echo
    echo "Nothing was changed (dry run). To apply: bash scripts/update-llm-wiki.sh --apply [--branch NAME]"
    return 0
  fi

  if [ "$conflicts" -gt 0 ]; then
    printf 'ref=%s\n' "$new" > "$PENDING"
  else
    write_lock "$new"; rm -f "$PENDING"
  fi

  if [ "$write_log" -eq 1 ] && [ "$changes" -gt 0 ] && [ -f wiki/log.md ]; then
    [ -n "$(tail -c1 wiki/log.md)" ] && echo >> wiki/log.md
    printf '\n## [%s] maintenance | Update template files to %s\n\nApplied %s template changes (%s need a manual merge). Source: %s.\n' \
      "$(date +%Y-%m-%d)" "${new:0:7}" "$changes" "$conflicts" "$TEMPLATE_URL" >> wiki/log.md
  fi

  if [ "$run_checks" -eq 1 ]; then
    echo
    echo "Running the notebook's checks ..."
    if command -v python3 >/dev/null && python3 -m unittest discover -s tests -t . >/dev/null 2>&1 && python3 scripts/lint.py >/dev/null 2>&1; then
      echo "Checks passed."
    else
      echo "A check failed (expected while conflicts or old wiki pages remain). Run 'python3 -m unittest discover -s tests -t .' and 'python3 scripts/lint.py' to see why."
    fi
  fi

  echo
  if [ "$conflicts" -gt 0 ]; then
    echo "$conflicts file(s) need a manual merge. For each FILE, merge FILE.template-new into FILE (keep your customizations, adopt the template's changes),"
    echo "then delete FILE.template-new and FILE.template-base. When none are left, run: bash scripts/update-llm-wiki.sh --finish"
    echo "Also read docs/migration.md for changes that affect existing wiki pages, then run: python3 scripts/lint.py"
    return 2
  fi
  echo "Applied. Read docs/migration.md for changes that affect existing wiki pages, run python3 scripts/lint.py, then review and commit."
}

tg() { git -C "$tmp/t" "$@"; }

policy_of() { # print the manifest policy for a template path
  local p="$1" pol pat rest
  while IFS=$'\t' read -r pol pat rest; do
    case "$pol" in ''|'#'*) continue ;; esac
    # shellcheck disable=SC2254
    case "$p" in $pat) echo "$pol"; return 0 ;; esac
  done < "$tmp/manifest"
  echo none
}

history_has() { # is this exact file content one of the template's past versions?
  local new="$1" p="$2" h="$3" c
  for c in $(tg log --format=%H "$new" -- "$p"); do
    [ "$(tg rev-parse "$c:$p" 2>/dev/null)" = "$h" ] && return 0
  done
  return 1
}

install_file() { # src dest mode: replace through a temp file so the old inode is never half-written
  local src="$1" dest="$2" mode="$3" t
  mkdir -p "$(dirname "$dest")"
  t="$dest.tmp.$$"
  cp "$src" "$t"
  if [ "$mode" = 100755 ]; then chmod 755 "$t"; fi
  mv -f "$t" "$dest"
}

write_lock() { printf 'template=%s\nref=%s\nupdated=%s\n' "$TEMPLATE_URL" "$1" "$(date +%Y-%m-%d)" > "$LOCK"; }

report() {
  local applied="$1" st label n
  echo
  for st in ADD UPDATE MERGE CONFLICT KEEP_LOCAL KEEP_ONCE DROPPED DROPPED_EDITED LINK_ADD LINK_DIFFERENT LINK_BLOCKED; do
    n=$(grep -c "^$st"$'\t' "$tmp/plan" || true)
    [ "$n" -gt 0 ] || continue
    case "$st" in
      ADD) label="new in the template (added)" ;;
      UPDATE) label="you never changed it, the template did (updated)" ;;
      MERGE) label="both sides changed it, merged cleanly" ;;
      CONFLICT) label="both sides changed it and it could not be merged (yours is kept; FILE.template-new has the template's)" ;;
      KEEP_LOCAL) label="you customized it and the template did not change it (kept)" ;;
      KEEP_ONCE) label="differs from the template but is only ever copied when missing (kept)" ;;
      DROPPED) label="removed from the template, you never changed it (deleted only with --prune)" ;;
      DROPPED_EDITED) label="removed from the template but you changed it (kept)" ;;
      LINK_ADD) label="missing agent entry point (symlink added)" ;;
      LINK_DIFFERENT) label="symlink points somewhere else (kept)" ;;
      LINK_BLOCKED) label="a real file sits where the template has a symlink (kept)" ;;
    esac
    echo "$st: $n  $label"
    grep "^$st"$'\t' "$tmp/plan" | cut -f2 | sed 's/^/    /'
  done
  if [ ! -s "$tmp/plan" ]; then echo "Every managed file already matches the template."; fi
  [ "$applied" -eq 1 ] || true
}

main "$@"; exit $?
````

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
log.write_text(head + f"\n## [{today}] bootstrap | Start {name} from llm-wiki-template\n\nCreated from the LLM Wiki Template. Open the folder with your assistant and run `/wiki-ingest` on a first source.\n", encoding="utf-8")

# README.md: a short one for the new notebook.
pathlib.Path("README.md").write_text(f"""# {name}

A notebook that an AI assistant writes and keeps up to date, built from the
[LLM Wiki Template](https://github.com/jonyfs/llm-wiki-template).

- `raw/` holds your sources. The assistant reads them and never edits them.
- `wiki/` holds the linked markdown pages the assistant writes. Start at `wiki/index.md`.
- `AGENTS.md` and `.agents/skills/` tell the assistant how to ingest, answer, check and clean up.

## First steps

Open this folder with your assistant, then run the skills from its prompt:

1. Add a source: `/wiki-ingest <path or link>`. It asks before saving a copy in `raw/`.
2. Ask a question: `/wiki-query What does the wiki say about ...?`
3. Now and then: `/wiki-lint`.
4. To get the template's newer skills and scripts later: `/wiki-update`.

If your assistant has no slash commands, name the skill in a sentence, such as "Use wiki-ingest on <file>."
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
  1. Open the folder with your assistant.
  2. Add a source: /wiki-ingest <path or link>   (it asks before saving a copy in raw/)
  3. Ask about it: /wiki-query <your question>
EOF

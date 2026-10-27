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

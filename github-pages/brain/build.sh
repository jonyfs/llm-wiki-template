#!/usr/bin/env bash
# Rebuild the landing page graph from the LLM Wiki Brain plugin (https://github.com/jonyfs/llm-wiki-brain).
#
#   github-pages/brain/build.sh            build from the pinned tag below
#   BRAIN_REF=0.6.0 github-pages/brain/build.sh
#
# It clones the plugin into a temporary folder, bundles the plugin's own view and engine together with the files in this
# folder (a tiny Obsidian shim, the demo vault and the page glue) and writes github-pages/assets/brain.js and brain.css.
# Both are committed, so the site needs no build step. Needs git, node and npm; esbuild is installed in the temporary
# folder only. Nothing here runs when the site is published.
set -euo pipefail

BRAIN_REPO="${BRAIN_REPO:-https://github.com/jonyfs/llm-wiki-brain.git}"
BRAIN_REF="${BRAIN_REF:-0.5.2}"
here="$(cd "$(dirname "$0")" && pwd)"
assets="$here/../assets"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

command -v git >/dev/null || { echo "error: git is required" >&2; exit 1; }
command -v npm >/dev/null || { echo "error: node and npm are required" >&2; exit 1; }

git clone -q -c advice.detachedHead=false --depth 1 --branch "$BRAIN_REF" "$BRAIN_REPO" "$tmp/brain"
sha="$(git -C "$tmp/brain" rev-parse --short HEAD)"
mkdir -p "$tmp/brain/site"
cp "$here/obsidian-shim.ts" "$here/demo.ts" "$here/site.ts" "$tmp/brain/site/"
(cd "$tmp/brain" && npm install --no-save --no-audit --no-fund esbuild@0.24 >/dev/null)

(cd "$tmp/brain" && npx esbuild site/site.ts --bundle --minify --format=iife --target=es2018 \
  --alias:obsidian=./site/obsidian-shim.ts \
  --banner:js="/* LLM Wiki Brain $BRAIN_REF ($sha), built by github-pages/brain/build.sh. Source: $BRAIN_REPO */" \
  --outfile="$assets/brain.js" --log-level=warning)

{
  echo "/* LLM Wiki Brain $BRAIN_REF ($sha) styles, then the page adapter. Built by github-pages/brain/build.sh. */"
  cat "$tmp/brain/styles.css"
  echo
  cat "$here/adapter.css"
} > "$assets/brain.css"

echo "Built assets/brain.js ($(wc -c < "$assets/brain.js") bytes) and assets/brain.css from $BRAIN_REF ($sha)."

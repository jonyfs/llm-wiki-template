#!/usr/bin/env bash
# Set up your LLM wiki on macOS. Double-click this file in Finder.
#
# It checks that git is available (installing Apple's developer tools if not), asks for a folder name,
# then runs new-llm-wiki.sh from this same folder. Your wiki is created in Documents/<name>.
# Nothing is deleted outside the new folder. You can read this file before running it.

set -uo pipefail
cd "$(dirname "$0")" || exit 1
SCRIPT_DIR="$(pwd)"

finish() {
  echo
  read -r -p "Press Return to close this window..." _ || true
}

fail() {
  echo
  echo "Stopped: $*"
  finish
  exit 1
}

echo "LLM Wiki installer for macOS"
echo

if ! xcode-select -p >/dev/null 2>&1; then
  echo "Apple's developer tools are missing. They include git, which this installer needs."
  echo "A macOS window is opening to install them. When it finishes, double-click this file again."
  xcode-select --install >/dev/null 2>&1 || true
  finish
  exit 0
fi

command -v git >/dev/null 2>&1 || fail "git is still missing. Install Apple's developer tools, then run this again."

if ! command -v python3 >/dev/null 2>&1; then
  echo "note: python3 is missing, so the template's checks will be skipped. The wiki still works."
  RUN_CHECKS="--no-check"
else
  RUN_CHECKS=""
fi

echo "Folder name for your wiki (letters, numbers, dot, dash or underscore, no spaces)."
read -r -p "Name: " NAME || fail "no name given."
case "$NAME" in
  ""|.|..|*[!A-Za-z0-9._-]*) fail "use only letters, numbers, dot, dash or underscore, for example my-wiki." ;;
esac

TARGET="$HOME/Documents/$NAME"
[ -e "$TARGET" ] && fail "$TARGET already exists. Choose another name."

mkdir -p "$HOME/Documents" || fail "could not create $HOME/Documents."
cd "$HOME/Documents" || fail "could not open $HOME/Documents."

echo
echo "Creating your wiki in $TARGET ..."
if ! bash "$SCRIPT_DIR/new-llm-wiki.sh" "$NAME" $RUN_CHECKS; then
  fail "the wiki could not be created. The messages above say why. Fix that, then run this again."
fi

echo
echo "Your wiki is ready in: $TARGET"
echo "Open that folder with your assistant (Claude Code, Cursor, Copilot or OpenCode) and start with /wiki-ingest."
open "$TARGET" >/dev/null 2>&1 || true
finish

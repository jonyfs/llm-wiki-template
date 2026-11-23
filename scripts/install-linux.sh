#!/usr/bin/env bash
# Set up your LLM wiki on Linux. Run: bash install-linux.sh
#
# It installs git and python3 with your package manager if they are missing (asks for your password once),
# asks for a folder name, then runs new-llm-wiki.sh from this same folder. Your wiki is created in ~/Documents/<name>.
# Nothing is deleted outside the new folder. You can read this file before running it.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

fail() { echo "Stopped: $*" >&2; exit 1; }

echo "LLM Wiki installer for Linux"
echo

SUDO=""
if [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1; then
  SUDO="sudo"
fi

install_packages() {
  if command -v apt-get >/dev/null 2>&1; then
    $SUDO apt-get update -qq && $SUDO apt-get install -y git python3
  elif command -v dnf >/dev/null 2>&1; then
    $SUDO dnf install -y git python3
  elif command -v pacman >/dev/null 2>&1; then
    $SUDO pacman -S --needed --noconfirm git python
  elif command -v zypper >/dev/null 2>&1; then
    $SUDO zypper --non-interactive install git python3
  else
    fail "no supported package manager found (apt, dnf, pacman or zypper). Install git and python3 yourself, then run this again."
  fi
}

MISSING=""
command -v git >/dev/null 2>&1 || MISSING="git"
command -v python3 >/dev/null 2>&1 || MISSING="$MISSING python3"

if [ -n "$MISSING" ]; then
  echo "Missing:$MISSING. Installing them now (your password may be asked)."
  install_packages || fail "the installation of$MISSING did not finish."
fi

command -v git >/dev/null 2>&1 || fail "git is still missing after the installation."
RUN_CHECKS=""
command -v python3 >/dev/null 2>&1 || { echo "note: python3 is missing, so the template's checks will be skipped."; RUN_CHECKS="--no-check"; }

echo "Folder name for your wiki (letters, numbers, dot, dash or underscore, no spaces)."
read -r -p "Name: " NAME || fail "no name given."
case "$NAME" in
  ""|*[!A-Za-z0-9._-]*) fail "use only letters, numbers, dot, dash or underscore, for example my-wiki." ;;
esac

TARGET="$HOME/Documents/$NAME"
[ -e "$TARGET" ] && fail "$TARGET already exists. Choose another name."

mkdir -p "$HOME/Documents"
cd "$HOME/Documents"

echo
echo "Creating your wiki in $TARGET ..."
bash "$SCRIPT_DIR/new-llm-wiki.sh" "$NAME" $RUN_CHECKS || fail "the wiki could not be created. The messages above say why."

echo
echo "Your wiki is ready in: $TARGET"
echo "Open that folder with your assistant and start with /wiki-ingest."

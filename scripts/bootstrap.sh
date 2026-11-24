#!/usr/bin/env bash
# One-command installer for macOS and Linux. Paste this line into the Terminal and press Return:
#
#   bash -c "$(curl -fsSL https://raw.githubusercontent.com/jonyfs/llm-wiki-template/main/scripts/bootstrap.sh)"
#
# It makes sure git is installed (asks for your password on Linux if it is missing), downloads the template
# with git clone into a temporary folder, runs that folder's installer, then deletes the temporary folder.
# The installer installs python3 on Linux when it is missing. Your wiki is created in Documents/<name>.
# Nothing is deleted outside the temporary folder. You can read this file before running it.
#
# Set TEMPLATE_URL or TEMPLATE_BRANCH to install from another copy of the template.
set -uo pipefail

TEMPLATE_URL="${TEMPLATE_URL:-https://github.com/jonyfs/llm-wiki-template.git}"
TEMPLATE_BRANCH="${TEMPLATE_BRANCH:-main}"

fail() {
  echo
  echo "Stopped: $*"
  exit 1
}

# Piped input (curl ... | bash) is the script itself, so answers must come from the terminal.
if [ ! -t 0 ] && [ -r /dev/tty ]; then
  exec </dev/tty
fi

case "$(uname -s)" in
  Darwin) PLATFORM=macos ;;
  Linux) PLATFORM=linux ;;
  *) fail "this command is for macOS and Linux. On Windows, paste the PowerShell command from the install guide instead." ;;
esac

echo "LLM Wiki installer ($PLATFORM)"
echo

install_git() {
  if [ "$PLATFORM" = macos ]; then
    echo "git is missing. Apple's developer tools include it, and a window is opening to install them."
    xcode-select --install >/dev/null 2>&1 || true
    fail "when Apple's developer tools finish installing, paste this command again."
  fi

  SUDO=""
  if [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
  fi

  echo "git is missing. Installing it now (your password may be asked)."
  if command -v apt-get >/dev/null 2>&1; then
    $SUDO apt-get update -qq && $SUDO apt-get install -y git
  elif command -v dnf >/dev/null 2>&1; then
    $SUDO dnf install -y git
  elif command -v pacman >/dev/null 2>&1; then
    $SUDO pacman -Sy --needed --noconfirm git
  elif command -v zypper >/dev/null 2>&1; then
    $SUDO zypper --non-interactive install git
  else
    fail "no supported package manager found (apt, dnf, pacman or zypper). Install git from https://git-scm.com, then paste this command again."
  fi
}

command -v git >/dev/null 2>&1 || install_git
command -v git >/dev/null 2>&1 || fail "git is still missing. Install it, then paste this command again."

WORK="$(mktemp -d)" || fail "could not create a temporary folder."
trap 'rm -rf "$WORK"' EXIT

echo "Downloading the template from $TEMPLATE_URL ..."
git clone --quiet --depth 1 --branch "$TEMPLATE_BRANCH" "$TEMPLATE_URL" "$WORK/template" \
  || fail "the template could not be downloaded. Check your internet connection and paste this command again."

case "$PLATFORM" in
  macos) INSTALLER="$WORK/template/scripts/install-macos.command" ;;
  linux) INSTALLER="$WORK/template/scripts/install-linux.sh" ;;
esac

echo
bash "$INSTALLER"

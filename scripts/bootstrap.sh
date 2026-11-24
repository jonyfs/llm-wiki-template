#!/usr/bin/env bash
# One command to install the LLM Wiki Template on macOS or Linux. Paste this line into the Terminal and press Return:
#
#   bash -c "$(curl -fsSL https://raw.githubusercontent.com/jonyfs/llm-wiki-template/main/scripts/bootstrap.sh)"
#
# Like SDKMAN, it installs into a folder in your home directory (~/.llm-wiki), adds an `llm-wiki` command to
# your shell's startup file, and then creates your first wiki. It installs git first if git is missing.
# Later, `llm-wiki new` creates another wiki and `llm-wiki update` gets the newest template.
# Your wiki is created in Documents/<name>. Nothing outside ~/.llm-wiki and your shell startup file is changed.
# You can read this file before running it.
#
# Set TEMPLATE_URL, TEMPLATE_BRANCH or LLM_WIKI_HOME to install from another copy or into another folder.
set -uo pipefail

TEMPLATE_URL="${TEMPLATE_URL:-https://github.com/jonyfs/llm-wiki-template.git}"
TEMPLATE_BRANCH="${TEMPLATE_BRANCH:-main}"
LLM_WIKI_HOME="${LLM_WIKI_HOME:-$HOME/.llm-wiki}"
MARK_BEGIN="# >>> llm-wiki >>>"
MARK_END="# <<< llm-wiki <<<"

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

# Download the template into its own folder, or update the copy that is already there.
if [ -d "$LLM_WIKI_HOME/.git" ]; then
  echo "Updating the template in $LLM_WIKI_HOME ..."
  git -C "$LLM_WIKI_HOME" pull --ff-only --quiet \
    || fail "the template in $LLM_WIKI_HOME could not be updated. Check your internet connection and paste this command again."
elif [ -e "$LLM_WIKI_HOME" ]; then
  fail "$LLM_WIKI_HOME exists but is not an LLM Wiki installation. Move or rename it, then paste this command again."
else
  echo "Downloading the template from $TEMPLATE_URL ..."
  git clone --quiet --depth 1 --branch "$TEMPLATE_BRANCH" "$TEMPLATE_URL" "$LLM_WIKI_HOME" \
    || fail "the template could not be downloaded. Check your internet connection and paste this command again."
fi
chmod +x "$LLM_WIKI_HOME/scripts/llm-wiki"

# Add the llm-wiki command to the shell's startup file, once. Like SDKMAN, a marked block is written and
# later runs replace it instead of adding another copy.
case "${SHELL:-}" in
  */zsh) RC="$HOME/.zshrc" ;;
  *) if [ "$PLATFORM" = macos ]; then RC="$HOME/.bash_profile"; else RC="$HOME/.bashrc"; fi ;;
esac
touch "$RC" || fail "could not write to $RC."
if grep -qF "$MARK_BEGIN" "$RC"; then
  # Remove the old block, then write the current one.
  sed -i.llm-wiki-bak "/$MARK_BEGIN/,/$MARK_END/d" "$RC" && rm -f "$RC.llm-wiki-bak"
fi
{
  echo "$MARK_BEGIN"
  echo "export PATH=\"$LLM_WIKI_HOME/scripts:\$PATH\""
  echo "$MARK_END"
} >> "$RC"
echo "Added the llm-wiki command to $RC."

echo
bash "$LLM_WIKI_HOME/scripts/llm-wiki" new

echo
echo "Done. Open a new Terminal window and type: llm-wiki help"

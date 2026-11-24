# Install your LLM wiki, step by step

This guide creates a wiki on your computer with one installer. You do not need to use the terminal. You need an internet connection and an AI assistant to work with the wiki (Claude Code, Cursor, GitHub Copilot, OpenCode or Codex).

Plan for a short session. The slowest part is installing git and Apple's developer tools, which only happens once.

## Fastest way: one command

Copy the command for your system, paste it into the program below, and press Enter. It checks for git, installs what is missing, downloads the template from GitHub and starts the installer. You do not need to download or unzip anything.

- **macOS or Linux.** Open **Terminal** and paste:

  ```bash
  bash -c "$(curl -fsSL https://raw.githubusercontent.com/jonyfs/llm-wiki-template/main/scripts/bootstrap.sh)"
  ```

- **Windows.** Open **PowerShell** (press the Start key, type `PowerShell`, press Enter) and paste:

  ```powershell
  irm https://raw.githubusercontent.com/jonyfs/llm-wiki-template/main/scripts/bootstrap.ps1 | iex
  ```

Answer the questions on screen. The wiki is created in your **Documents** folder.

The command installs the template into `~/.llm-wiki` (on Windows, `%USERPROFILE%\.llm-wiki`) and adds an `llm-wiki` command, like SDKMAN does for Java. Open a new terminal window, then use:

- `llm-wiki new`: create another wiki (asks for a name).
- `llm-wiki update`: get the newest version of the template.
- `llm-wiki help`: list the commands.

If you prefer to see each step with a file to double-click, use the steps below.

## Before you start

1. Choose a name for your wiki, for example `my-wiki` or `sleep-research`. Use only letters, numbers, dots, dashes and underscores. No spaces, and do not start with a dash.
2. Download the template. Open <https://github.com/jonyfs/llm-wiki-template>, click the green **Code** button, then **Download ZIP**.
3. Unzip the file. Your browser may unzip it for you into your Downloads folder. Keep the unzipped folder, because the installer lives inside it.

## macOS

**What the installer does.** It checks for git. If git is missing, it opens Apple's developer tools installer. When that finishes, you run the installer again. Then it asks for the name of your wiki and creates it in your **Documents** folder.

**Steps**

1. Open the unzipped folder `llm-wiki-template-main`, then the `scripts` folder.
2. Double-click `install-macos.command`.
3. If macOS says the file is from an unidentified developer, right-click the file, choose **Open**, then click **Open** again in the window that appears. You do this once.
4. If a window asks to install **Command Line Tools for Xcode**, click **Install** and wait. It can take a while. When it finishes, double-click `install-macos.command` again.
5. A Terminal window opens and shows `Name:`. Type your wiki name and press Return.
6. Wait for the message `Your wiki is ready in: ...`. Finder opens the new folder.
7. Press Return to close the window.

**What success looks like.** A folder such as `Documents/my-wiki` with `AGENTS.md`, `wiki/` and `raw/` inside.

## Windows

**What the installer does.** It checks for git. If git is missing, it installs it with winget, which comes with Windows 10 and 11. Then it asks for the name of your wiki and creates it in your **Documents** folder.

**Steps**

1. Open the unzipped folder `llm-wiki-template-main`, then the `scripts` folder.
2. Double-click `install-windows.cmd`.
3. If Windows shows a blue **Windows protected your PC** window, click **More info**, then **Run anyway**. You do this once.
4. If git is missing, Windows may ask whether to allow the installation (a User Account Control window). Click **Yes**. The installation can take a few minutes.
5. A PowerShell window shows `Name`. Type your wiki name and press Enter.
6. Wait for `Your wiki is ready in: ...`. File Explorer opens the new folder.
7. Press Enter to close the window.

**If git was installed but the installer says it is not visible yet.** Close the window and double-click `install-windows.cmd` again. Windows only updates the list of programs when a new window opens.

**If winget is missing.** Install git yourself from <https://git-scm.com/download/win>, accept the defaults, then double-click `install-windows.cmd` again.

## Linux

**What the installer does.** It installs git and python3 with your package manager (apt on Ubuntu and Debian, dnf on Fedora, pacman on Arch, zypper on openSUSE). It asks for your password once. Then it asks for the name of your wiki and creates it in `~/Documents`.

**Steps**

1. Open a terminal in the unzipped folder. In most file managers, right-click inside the folder and choose **Open in Terminal**.
2. Type `bash scripts/install-linux.sh` and press Enter.
3. Type your password when asked. Nothing appears while you type, which is normal.
4. Type your wiki name and press Enter.
5. Wait for `Your wiki is ready in: ...`.

**What success looks like.** A folder `~/Documents/my-wiki` with `AGENTS.md`, `wiki/` and `raw/` inside.

## Open the wiki with your assistant

1. Open the wiki folder in your assistant. In Claude Code, run `claude` inside the folder. In Cursor, choose **File > Open Folder**.
2. Add your first source. Type `/wiki-ingest` and then a file path or a link. The assistant asks before it saves a copy in `raw/`.
3. Ask a question. Type `/wiki-query` and your question. The answer cites the wiki pages it used.

If your assistant does not understand the slash commands, write the skill name in a sentence, for example: "Use wiki-ingest on ~/Downloads/paper.pdf."

## When something goes wrong

| What you see | What to do |
|---|---|
| "git is missing" and the installer stops | Install git from <https://git-scm.com>, then run the installer again. |
| "already exists" | A folder with that name is already in Documents. Choose another name. |
| "use letters, numbers, dot, dash or underscore" | Remove spaces and accents from the name. Do not start it with a dash. |
| "the template could not be downloaded" | Check your internet connection and run the installer again. |
| "python is not installed ... checks were skipped" | The wiki still works. Python is only needed to run the template's own checks, which are optional. |
| "a check failed" | The wiki was created. Open the folder in a terminal and run `python -m unittest discover -s tests -t .` to see which check failed. Ask your assistant for help with the output. |
| The window closes before you can read the message | Open the installer again from a terminal: on macOS and Linux run it with `bash`, on Windows open PowerShell in the `scripts` folder and run `powershell -ExecutionPolicy Bypass -File install-windows.ps1`. |

## Notes on what the installer does

- It deletes nothing outside the new folder. Before it removes any file in the copy, it checks that the copy really is the template.
- The wiki starts with its own git history, so your changes are never mixed with the template's.
- The installer runs the template's tests and checks on the code it has just downloaded. Read the scripts first if you want to see exactly what they do: `scripts/new-llm-wiki.sh` (macOS and Linux) or `scripts/new-llm-wiki.ps1` (Windows).
- To get the template's later improvements, open the wiki folder with your assistant and run `/wiki-update`.

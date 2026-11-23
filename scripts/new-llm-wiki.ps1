# Start a new notebook from the LLM Wiki Template on Windows.
# PowerShell port of new-llm-wiki.sh with the same steps and the same result.
#
#   powershell -ExecutionPolicy Bypass -File scripts\new-llm-wiki.ps1 -Name my-wiki
#   ... -KeepPages      keep the GitHub Pages site and its workflows
#   ... -NoCheck        skip the template's checks
#
# Needs git. Python is optional: without it the template's checks are skipped.
param(
  [Parameter(Mandatory = $true)][string]$Name,
  [switch]$KeepPages,
  [switch]$NoCheck
)

$ErrorActionPreference = 'Stop'
$TemplateUrl = if ($env:TEMPLATE_URL) { $env:TEMPLATE_URL } else { 'https://github.com/jonyfs/llm-wiki-template.git' }
$TemplateBranch = if ($env:TEMPLATE_BRANCH) { $env:TEMPLATE_BRANCH } else { 'main' }
$Utf8 = New-Object System.Text.UTF8Encoding($false)

function Fail([string]$Message) { throw "Stopped: $Message" }

if ($Name -notmatch '^[A-Za-z0-9._-]+$') { Fail 'use only letters, numbers, dot, dash or underscore in the name.' }
if (Test-Path -LiteralPath $Name) {
  if ((Get-ChildItem -LiteralPath $Name -Force | Measure-Object).Count -gt 0) { Fail "'$Name' already exists and is not empty." }
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Fail 'git is required. The Windows installer installs it for you.' }
$HasPython = [bool](Get-Command python -ErrorAction SilentlyContinue)

# The exact template commit the copy starts from, so scripts/update-llm-wiki.sh knows its base later.
$TemplateRef = ''
$lsRemote = git ls-remote $TemplateUrl "refs/heads/$TemplateBranch" 2>$null
if ($lsRemote) { $TemplateRef = ($lsRemote -split "`t")[0] }

Write-Host "Cloning $TemplateUrl ($TemplateBranch) into $Name ..."
git clone --quiet --depth 1 --branch $TemplateBranch $TemplateUrl $Name
if ($LASTEXITCODE -ne 0) { Fail 'the template could not be downloaded. Check your internet connection and run this again.' }

Set-Location -LiteralPath $Name
Remove-Item -LiteralPath '.git' -Recurse -Force

# Everything below deletes files, so make sure this really is a template copy before touching anything.
if (-not ((Test-Path 'AGENTS.md') -and (Test-Path '.agents/skills') -and (Test-Path 'wiki'))) {
  Fail 'this does not look like the LLM Wiki Template; stopping before any cleanup.'
}

# Template-only files: the author's citation file and the internal improvement catalog.
Remove-Item -LiteralPath 'CITATION.cff', 'IMPROVEMENTS.md', 'docs/images', 'tests/test_readme.py' -Recurse -Force -ErrorAction SilentlyContinue

if ($TemplateRef) {
  $lock = "template=$TemplateUrl`nref=$TemplateRef`nupdated=$(Get-Date -Format yyyy-MM-dd)`n"
  [System.IO.File]::WriteAllText((Join-Path (Get-Location) '.agents/template.lock'), $lock, $Utf8)
}

if (-not $KeepPages) {
  Write-Host "Removing the template's GitHub Pages site and its workflows ..."
  Remove-Item -LiteralPath 'github-pages', '.github/workflows/pages.yml', '.github/workflows/lighthouse.yml',
    'PAGES_IMPROVEMENTS.md', 'PAGES_GROWTH_200.md', 'DISCOVERABILITY.md', 'DESIGN_SYSTEM.md',
    'tests/test_github_pages.py' -Recurse -Force -ErrorAction SilentlyContinue
}

$Today = Get-Date -Format yyyy-MM-dd

# AGENTS.md: drop the rules about keeping the template's site in sync, which no longer apply.
if (-not $KeepPages) {
  $agents = [System.IO.File]::ReadAllText((Resolve-Path 'AGENTS.md'))
  $agents = [regex]::Replace($agents, '(?s)\r?\n## GitHub Pages synchronization\r?\n.*?(?=\r?\n## )', '')
  $agents = $agents.Replace(', the GitHub Pages copy in `github-pages/`,', ',')
  $agents = [regex]::Replace($agents, ' Pages with translations \(`github-pages/assets/i18n\.js`\) need the same pass in every language\.', '')
  [System.IO.File]::WriteAllText((Resolve-Path 'AGENTS.md'), $agents, $Utf8)
}

# wiki/log.md: keep the header, start a fresh history.
$logPath = Join-Path (Get-Location) 'wiki/log.md'
$logText = [System.IO.File]::ReadAllText($logPath)
$head = ($logText -split "`n## \[", 2)[0].TrimEnd() + "`n"
$logBody = "`n## [$Today] bootstrap | Start $Name from llm-wiki-template`n`nCreated from the LLM Wiki Template. Open the folder with your assistant and run ``/wiki-ingest`` on a first source.`n"
[System.IO.File]::WriteAllText($logPath, $head + $logBody, $Utf8)

# README.md: a short one for the new notebook.
$readme = @"
# $Name

A notebook that an AI assistant writes and keeps up to date, built from the
[LLM Wiki Template](https://github.com/jonyfs/llm-wiki-template).

- ``raw/`` holds your sources. The assistant reads them and never edits them.
- ``wiki/`` holds the linked markdown pages the assistant writes. Start at ``wiki/index.md``.
- ``AGENTS.md`` and ``.agents/skills/`` tell the assistant how to ingest, answer, check and clean up.

## First steps

Open this folder with your assistant, then run the skills from its prompt:

1. Add a source: ``/wiki-ingest <path or link>``. It asks before saving a copy in ``raw/``.
2. Ask a question: ``/wiki-query What does the wiki say about ...?``
3. Now and then: ``/wiki-lint``.
4. To get the template's newer skills and scripts later: ``/wiki-update``.

If your assistant has no slash commands, name the skill in a sentence, such as "Use wiki-ingest on <file>."
"@
[System.IO.File]::WriteAllText((Join-Path (Get-Location) 'README.md'), ($readme -replace "`r`n", "`n") + "`n", $Utf8)

git init -q -b main
git add -A
git commit -q -m 'Start notebook from llm-wiki-template'
if ($LASTEXITCODE -ne 0) { Write-Host 'note: could not commit. Set git user.name and user.email, then commit yourself.' }

if (-not $NoCheck -and $HasPython) {
  Write-Host 'Running the template''s checks ...'
  python -m unittest discover -s tests -t . *> $null
  $ok = ($LASTEXITCODE -eq 0)
  python scripts/lint.py *> $null
  $ok = $ok -and ($LASTEXITCODE -eq 0)
  if ($ok) { Write-Host 'Checks passed.' } else { Write-Host "warning: a check failed. Run 'python -m unittest discover -s tests -t .' and 'python scripts/lint.py' inside $Name to see why." }
} elseif (-not $HasPython) {
  Write-Host 'note: python is not installed, so the template''s checks were skipped. The wiki still works.'
}

Write-Host ''
Write-Host "Done. Your notebook is in .\$Name"
Write-Host '  1. Open the folder with your assistant.'
Write-Host '  2. Add a source: /wiki-ingest <path or link>   (it asks before saving a copy in raw/)'
Write-Host '  3. Ask about it: /wiki-query <your question>'

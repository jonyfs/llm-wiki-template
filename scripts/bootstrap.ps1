# One command to install the LLM Wiki Template on Windows. Open PowerShell (Start menu, type "PowerShell"),
# paste this line, press Enter:
#
#   irm https://raw.githubusercontent.com/jonyfs/llm-wiki-template/main/scripts/bootstrap.ps1 | iex
#
# Like SDKMAN, it installs into a folder in your user profile (%USERPROFILE%\.llm-wiki), adds that folder's
# scripts to your user PATH so the `llm-wiki` command works in new windows, and then creates your first wiki.
# It installs git with winget first if git is missing. Your wiki is created in Documents\<name>.
# You can read this file before running it.
#
# Set $env:TEMPLATE_URL, $env:TEMPLATE_BRANCH or $env:LLM_WIKI_HOME first to change the source or the folder.
$ErrorActionPreference = 'Stop'
$TemplateUrl = if ($env:TEMPLATE_URL) { $env:TEMPLATE_URL } else { 'https://github.com/jonyfs/llm-wiki-template.git' }
$TemplateBranch = if ($env:TEMPLATE_BRANCH) { $env:TEMPLATE_BRANCH } else { 'main' }
$InstallDir = if ($env:LLM_WIKI_HOME) { $env:LLM_WIKI_HOME } else { Join-Path $env:USERPROFILE '.llm-wiki' }

function Refresh-Path {
  $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
  $user = [Environment]::GetEnvironmentVariable('Path', 'User')
  $env:Path = "$machine;$user"
}

# Run a git command and return its exit code, without PowerShell 5.1 turning git's stderr into an error.
function Invoke-Git([string[]]$Arguments) {
  $previous = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  & git @Arguments
  $code = $LASTEXITCODE
  $ErrorActionPreference = $previous
  return $code
}

try {
  Write-Host 'LLM Wiki installer for Windows'
  Write-Host ''

  if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
      throw 'git is missing and winget is not available. Install Git from https://git-scm.com, then paste this command again.'
    }
    Write-Host 'git is missing. Installing it with winget (Windows may ask for permission) ...'
    winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
    Refresh-Path
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
      throw 'git was installed but is not visible yet. Close this window, open PowerShell again and paste this command again.'
    }
  }

  # Download the template into its own folder, or update the copy that is already there.
  if (Test-Path -LiteralPath (Join-Path $InstallDir '.git')) {
    Write-Host "Updating the template in $InstallDir ..."
    if ((Invoke-Git @('-C', $InstallDir, 'pull', '--ff-only', '--quiet')) -ne 0) {
      throw "the template in $InstallDir could not be updated. Check your internet connection and paste this command again."
    }
  }
  elseif (Test-Path -LiteralPath $InstallDir) {
    throw "$InstallDir exists but is not an LLM Wiki installation. Move or rename it, then paste this command again."
  }
  else {
    Write-Host "Downloading the template from $TemplateUrl ..."
    if ((Invoke-Git @('clone', '--quiet', '--depth', '1', '--branch', $TemplateBranch, $TemplateUrl, $InstallDir)) -ne 0) {
      throw 'the template could not be downloaded. Check your internet connection and paste this command again.'
    }
  }

  # Add the scripts folder to the user PATH once, so llm-wiki works in new windows.
  $bin = Join-Path $InstallDir 'scripts'
  $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
  if (-not $userPath) { $userPath = '' }
  if (($userPath -split ';') -notcontains $bin) {
    $newPath = if ($userPath) { "$($userPath.TrimEnd(';'));$bin" } else { $bin }
    [Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
    Write-Host "Added $bin to your user PATH."
  }

  Write-Host ''
  # A separate process, as the other installers do, so its checks cannot change this script's exit handling.
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $bin 'llm-wiki.ps1') new

  Write-Host ''
  Write-Host 'Done. Open a new PowerShell window and type: llm-wiki help'
}
catch {
  Write-Host ''
  Write-Host "Stopped: $($_.Exception.Message)" -ForegroundColor Red
}

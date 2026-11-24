# One-command installer for Windows. Open PowerShell (Start menu, type "PowerShell"), paste this line, press Enter:
#
#   irm https://raw.githubusercontent.com/jonyfs/llm-wiki-template/main/scripts/bootstrap.ps1 | iex
#
# It makes sure git is installed (installs it with winget if it is missing), downloads the template with
# git clone into a temporary folder, runs that folder's install-windows.ps1, then deletes the temporary folder.
# Your wiki is created in Documents\<name>. Nothing is deleted outside the temporary folder.
# You can read this file before running it.
#
# Set $env:TEMPLATE_URL or $env:TEMPLATE_BRANCH first to install from another copy of the template.
$ErrorActionPreference = 'Stop'
$TemplateUrl = if ($env:TEMPLATE_URL) { $env:TEMPLATE_URL } else { 'https://github.com/jonyfs/llm-wiki-template.git' }
$TemplateBranch = if ($env:TEMPLATE_BRANCH) { $env:TEMPLATE_BRANCH } else { 'main' }

function Refresh-Path {
  $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
  $user = [Environment]::GetEnvironmentVariable('Path', 'User')
  $env:Path = "$machine;$user"
}

$work = $null
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

  $work = Join-Path ([IO.Path]::GetTempPath()) ('llm-wiki-' + [guid]::NewGuid().ToString('N'))
  New-Item -ItemType Directory -Force -Path $work | Out-Null
  $template = Join-Path $work 'template'

  Write-Host "Downloading the template from $TemplateUrl ..."
  # Windows PowerShell 5.1 turns git's stderr into errors under Stop, so check the exit code instead.
  $previous = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  git clone --quiet --depth 1 --branch $TemplateBranch $TemplateUrl $template
  $cloneExit = $LASTEXITCODE
  $ErrorActionPreference = $previous
  if ($cloneExit -ne 0) { throw 'the template could not be downloaded. Check your internet connection and paste this command again.' }

  & (Join-Path $template 'scripts\install-windows.ps1')
}
catch {
  Write-Host ''
  Write-Host "Stopped: $($_.Exception.Message)" -ForegroundColor Red
}
finally {
  if ($work -and (Test-Path -LiteralPath $work)) { Remove-Item -LiteralPath $work -Recurse -Force }
}

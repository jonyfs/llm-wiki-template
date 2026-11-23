# Set up your LLM wiki on Windows. Use install-windows.cmd (double-click) instead of running this file directly.
#
# It installs git with winget if it is missing, asks for a folder name, then runs new-llm-wiki.ps1 from this
# same folder. Your wiki is created in Documents\<name>. Nothing is deleted outside the new folder.
# You can read this file before running it.
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

function Pause-Close {
  Write-Host ''
  Read-Host 'Press Enter to close this window' | Out-Null
}

function Refresh-Path {
  $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
  $user = [Environment]::GetEnvironmentVariable('Path', 'User')
  $env:Path = "$machine;$user"
}

try {
  Write-Host 'LLM Wiki installer for Windows'
  Write-Host ''

  if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
      throw 'git is missing and winget is not available. Install Git from https://git-scm.com, then run this again.'
    }
    Write-Host 'git is missing. Installing it with winget (Windows may ask for permission) ...'
    winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
    Refresh-Path
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
      throw 'git was installed but is not visible yet. Close this window, double-click install-windows.cmd again.'
    }
  }

  Write-Host 'Folder name for your wiki (letters, numbers, dot, dash or underscore, no spaces).'
  $name = Read-Host 'Name'
  if ($name -notmatch '^[A-Za-z0-9._-]+$') { throw 'use only letters, numbers, dot, dash or underscore, for example my-wiki.' }

  $documents = [Environment]::GetFolderPath('MyDocuments')
  $target = Join-Path $documents $name
  if (Test-Path -LiteralPath $target) { throw "$target already exists. Choose another name." }

  New-Item -ItemType Directory -Force -Path $documents | Out-Null
  Set-Location -LiteralPath $documents

  Write-Host ''
  Write-Host "Creating your wiki in $target ..."
  & (Join-Path $PSScriptRoot 'new-llm-wiki.ps1') -Name $name
  if ($LASTEXITCODE -ne 0) { throw 'the wiki could not be created. The messages above say why.' }

  Write-Host ''
  Write-Host "Your wiki is ready in: $target"
  Write-Host 'Open that folder with your assistant and start with /wiki-ingest.'
  Start-Process explorer.exe -ArgumentList $target
}
catch {
  Write-Host ''
  Write-Host "Stopped: $($_.Exception.Message)" -ForegroundColor Red
}
finally {
  Pause-Close
}

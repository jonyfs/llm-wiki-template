# The llm-wiki command for Windows. The one-command installer adds this folder to your PATH.
# Run it through llm-wiki.cmd, which is what the PATH finds.
#
#   llm-wiki new      create a new wiki (asks for a name, creates it in Documents)
#   llm-wiki update   get the newest version of the template
#   llm-wiki where    show where the template is installed
param([Parameter(Position = 0)][string]$Command = 'help')

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot

function Show-Usage {
  Write-Host 'Usage: llm-wiki <command>'
  Write-Host ''
  Write-Host '  new      create a new wiki (asks for a name)'
  Write-Host '  update   get the newest version of the template'
  Write-Host '  where    show where the template is installed'
}

switch ($Command) {
  'new' {
    # A separate process, so the installer's own exit handling stays in its own window.
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'install-windows.ps1')
  }
  'update' {
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    git -C $Root pull --ff-only --quiet
    $code = $LASTEXITCODE
    $ErrorActionPreference = $previous
    if ($code -ne 0) { throw 'the template could not be updated. Check your internet connection.' }
    Write-Host "Template updated in $Root."
  }
  'where' { Write-Host $Root }
  { $_ -in 'help', '-h', '--help' } { Show-Usage }
  default { Write-Host "Unknown command: $Command"; Show-Usage; exit 1 }
}

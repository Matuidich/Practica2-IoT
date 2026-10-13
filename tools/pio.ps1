$ErrorActionPreference = 'Stop'
$taskProjectRoot = Split-Path -Parent $PSScriptRoot
$env:PLATFORMIO_CORE_DIR = Join-Path $taskProjectRoot '.tools\platformio'
& (Join-Path $PSScriptRoot 'python.ps1') -m platformio @args
exit $LASTEXITCODE

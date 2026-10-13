# Uses the project-local interpreter when available; forwards all arguments.
$ErrorActionPreference = 'Stop'
$taskProjectRoot = Split-Path -Parent $PSScriptRoot
$taskPython = Join-Path $taskProjectRoot '.tools\python\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) {
    $taskPython = (Get-Command python -ErrorAction Stop).Source
}
& $taskPython @args
exit $LASTEXITCODE

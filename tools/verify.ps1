param([switch]$SoftwareOnly)
$ErrorActionPreference = 'Stop'
$taskProjectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $taskProjectRoot
try {
    & (Join-Path $PSScriptRoot 'python.ps1') -m unittest discover -s server/tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Fallaron las pruebas Python.' }
    & (Join-Path $PSScriptRoot 'python.ps1') -m tools.test_firmware
    if ($LASTEXITCODE -ne 0) { throw 'Fallaron las pruebas nativas C++.' }
    & (Join-Path $PSScriptRoot 'python.ps1') -m tools.smoke_test --duration 5
    if ($LASTEXITCODE -ne 0) { throw 'Falló la integración TCP.' }
    if (-not $SoftwareOnly) {
        & (Join-Path $PSScriptRoot 'pio.ps1') run -d firmware -e sensor -e actuator
        if ($LASTEXITCODE -ne 0) { throw 'Falló la compilación ESP32.' }
    }
} finally {
    Pop-Location
}

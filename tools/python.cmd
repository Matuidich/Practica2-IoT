@echo off
setlocal
if exist "%~dp0..\.tools\python\python.exe" (
    "%~dp0..\.tools\python\python.exe" %*
) else (
    python %*
)
exit /b %errorlevel%

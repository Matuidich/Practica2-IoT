@echo off
setlocal
set "PLATFORMIO_CORE_DIR=%~dp0..\.tools\platformio"
call "%~dp0python.cmd" -m platformio %*
exit /b %errorlevel%

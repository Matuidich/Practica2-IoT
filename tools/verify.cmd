@echo off
call "%~dp0python.cmd" -m tools.verify %*
exit /b %errorlevel%

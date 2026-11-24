@echo off
rem The llm-wiki command on Windows. Runs llm-wiki.ps1 with a policy that allows only this script.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0llm-wiki.ps1" %*

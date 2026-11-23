@echo off
rem Set up your LLM wiki on Windows. Double-click this file.
rem It runs install-windows.ps1 with a policy that allows this one script, and leaves the PowerShell rules for your
rem whole computer unchanged.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-windows.ps1"

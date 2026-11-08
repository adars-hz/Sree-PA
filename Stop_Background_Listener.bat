@echo off
title Stop SREE Background Assistant
echo Stopping SREE Background Listener...
powershell -Command "Get-Process -Name powershell | Where-Object { $_.MainWindowTitle -eq '' } | Stop-Process -Force -ErrorAction SilentlyContinue"
echo [+] SREE background listener stopped.
timeout /t 2 >nul


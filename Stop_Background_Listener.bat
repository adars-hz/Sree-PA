@echo off
title Stop SREE Background Assistant
echo Stopping SREE Background Listener...
powershell -Command "Get-CimInstance Win32_Process -Filter \"Name = 'powershell.exe'\" | Where-Object { $_.CommandLine -like '*background_listener*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
echo [+] SREE background listener stopped.
timeout /t 2 >nul


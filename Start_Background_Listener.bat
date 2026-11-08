@echo off
title SREE Background Assistant
cd /d "%~dp0"
echo Starting SREE Background Voice Listener (Listening for 'Hey Sree')...
wscript.exe //B //Nologo scripts\launch_silent.vbs
echo [+] SREE is now active and listening in the background!
echo Say 'Hey Sree' anytime to speak.
timeout /t 3 >nul


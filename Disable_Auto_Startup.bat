@echo off
title Disable SREE Auto-Startup
cd /d "%~dp0"
python scripts\install_startup.py disable
pause


@echo off
title SREE Voice Biometric Enrollment
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -NoProfile -File "scripts\enroll_voice.ps1"

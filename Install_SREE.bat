@echo off
title SREE AI Assistant - One-Click Installer
cd /d "%~dp0"
cls
echo ===================================================================
echo             SREE - PERSONAL AI ASSISTANT INSTALLER
echo ===================================================================
echo.
echo Installing SREE as a native Windows software on your PC...
echo.

if not exist "dist\SREE.exe" (
    echo [*] Standalone executable not found. Building SREE.exe now...
    python -m pip install pyinstaller pillow pystray --quiet
    pyinstaller sree.spec --noconfirm --clean
)

if not exist "dist\SREE.exe" (
    echo.
    echo [!] Build failed or python was not found. 
    echo Please make sure Python is installed and run Build_EXE.bat first.
    pause
    exit /b 1
)

echo [*] Creating Windows Desktop Shortcut...
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%USERPROFILE%\Desktop\SREE AI Assistant.lnk'); $s.TargetPath = '%~dp0dist\SREE.exe'; $s.WorkingDirectory = '%~dp0dist'; if (Test-Path '%~dp0sree.ico') { $s.IconLocation = '%~dp0sree.ico,0' }; $s.Description = 'SREE - JARVIS AI Assistant & Desktop Controller'; $s.Save()"

echo [*] Creating Windows Start Menu Entry...
if not exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\SREE" mkdir "%APPDATA%\Microsoft\Windows\Start Menu\Programs\SREE"
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\SREE\SREE AI Assistant.lnk'); $s.TargetPath = '%~dp0dist\SREE.exe'; $s.WorkingDirectory = '%~dp0dist'; if (Test-Path '%~dp0sree.ico') { $s.IconLocation = '%~dp0sree.ico,0' }; $s.Description = 'SREE - JARVIS AI Assistant & Desktop Controller'; $s.Save()"

echo [*] Configuring 24/7 Windows Auto-Startup...
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\SREE.lnk'); $s.TargetPath = '%~dp0dist\SREE.exe'; $s.WorkingDirectory = '%~dp0dist'; $s.Description = 'SREE Background AI Assistant'; $s.Save()"

echo.
echo ===================================================================
echo [+] INSTALLATION SUCCESSFUL!
echo ===================================================================
echo  1. Desktop Shortcut created:   Desktop \ SREE AI Assistant
echo  2. Start Menu program added:    Start Menu \ SREE \ SREE AI Assistant
echo  3. System Tray HUD enabled:     Arc Reactor icon next to Windows clock
echo  4. Auto-Start enabled:          SREE will boot silently with Windows
echo  5. Background Voice:            Say 'Hey Sree' anytime to speak
echo ===================================================================
echo.
echo Launching SREE now...
start "" "%~dp0dist\SREE.exe"
timeout /t 3 >nul

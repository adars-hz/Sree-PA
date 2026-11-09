@echo off
title Build SREE Standalone Executable (.exe)
cd /d "%~dp0"
echo ========================================================
echo        BUILDING SREE STANDALONE EXECUTABLE (.EXE)
echo ========================================================
echo.
echo [1/3] Checking dependencies (pyinstaller, pillow, pystray)...
python -m pip install pyinstaller pillow pystray --quiet

echo [2/3] Compiling SREE.exe using PyInstaller...
pyinstaller sree.spec --noconfirm --clean

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo [+] BUILD SUCCESSFUL!
    echo [+] Executable created at: dist\SREE.exe
    echo [+] You can run dist\SREE.exe or run Install_SREE.bat
    echo ========================================================
) else (
    echo.
    echo [!] Build encountered errors. Please check output above.
)
pause

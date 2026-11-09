@echo off
title Build SREE Standalone Executable (.exe)
cd /d "%~dp0"
echo ========================================================
echo        BUILDING SREE STANDALONE EXECUTABLE (.EXE)
echo ========================================================
echo.
echo Checking dependencies...
python -m pip install pyinstaller pillow --quiet

echo Building SREE.exe using PyInstaller...
pyinstaller sree.spec --noconfirm --clean

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo [+] BUILD SUCCESSFUL!
    echo [+] Executable created at: dist\SREE.exe
    echo ========================================================
) else (
    echo.
    echo [!] Build encountered errors. Please check the output above.
)
pause


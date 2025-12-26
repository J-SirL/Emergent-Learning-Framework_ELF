@echo off
REM Automated Node.js Installer for Terminal Emulator
REM Uses winget (Windows Package Manager) if available

echo ============================================================
echo Node.js Installation for Terminal Emulator
echo ============================================================
echo.

REM Check if Node.js is already installed
where node >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Node.js is already installed!
    node --version
    npm --version
    echo.
    echo Run quick-start.bat to launch the terminal emulator.
    pause
    exit /b 0
)

echo Node.js is not installed. Installing now...
echo.

REM Try winget first (Windows 10/11)
echo Attempting installation via winget...
winget --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] winget found. Installing Node.js LTS...
    winget install OpenJS.NodeJS.LTS --silent --accept-source-agreements --accept-package-agreements
    if %errorlevel% equ 0 (
        echo.
        echo ============================================================
        echo [SUCCESS] Node.js installed successfully!
        echo ============================================================
        echo.
        echo IMPORTANT: Please restart your terminal for the changes to take effect.
        echo.
        echo After restarting, run: quick-start.bat
        echo.
        pause
        exit /b 0
    ) else (
        echo [ERROR] winget installation failed.
    )
)

echo.
echo ============================================================
echo Automated installation not available
echo ============================================================
echo.
echo Please install Node.js manually:
echo.
echo 1. Open your browser
echo 2. Go to: https://nodejs.org/
echo 3. Download the LTS version (recommended)
echo 4. Run the installer
echo 5. Restart this terminal
echo 6. Run: quick-start.bat
echo.
echo Or use PowerShell with administrator rights:
echo   winget install OpenJS.NodeJS.LTS
echo.
pause

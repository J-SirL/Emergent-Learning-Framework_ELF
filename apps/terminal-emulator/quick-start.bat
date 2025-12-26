@echo off
REM Terminal Emulator - Quick Start Script for Windows
REM This script automates the initial setup and runs the app in development mode

echo =====================================
echo Terminal Emulator - Quick Start
echo =====================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+ from python.org
    pause
    exit /b 1
)
echo [OK] Python found

REM Check Node
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Please install Node.js 16+ from nodejs.org
    pause
    exit /b 1
)
echo [OK] Node.js found
echo.

REM Create .env if it doesn't exist
if not exist .env (
    echo Creating .env file...
    copy .env.example .env
    echo [OK] .env created - you can edit it later for GitHub integration
) else (
    echo [OK] .env already exists
)
echo.

REM Install Python dependencies
echo Installing Python dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies
    pause
    exit /b 1
)
echo [OK] Python dependencies installed
echo.

REM Install React dependencies
echo Installing React dependencies (this may take a minute)...
cd ui\react
call npm install
if errorlevel 1 (
    echo [ERROR] Failed to install React dependencies
    cd ..\..
    pause
    exit /b 1
)
cd ..\..
echo [OK] React dependencies installed
echo.

REM Start Vite dev server in background
echo Starting React dev server...
start /B cmd /c "cd ui\react && npm run dev"
timeout /t 3 >nul
echo [OK] React dev server started at http://localhost:5173
echo.

REM Start Python app
echo Starting Python application...
echo.
echo =====================================
echo The terminal emulator window should open now!
echo Press Ctrl+C here to stop everything.
echo =====================================
echo.

python main.py

REM Cleanup: kill Vite server when Python app closes
taskkill /F /FI "WINDOWTITLE eq Vite*" >nul 2>&1
echo.
echo Application closed.
pause

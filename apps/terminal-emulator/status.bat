@echo off
REM Terminal Emulator - Installation Status Checker

echo ============================================================
echo TERMINAL EMULATOR - INSTALLATION STATUS
echo ============================================================
echo.

REM Check Python
echo [1/4] Checking Python...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('python --version') do echo     [OK] %%i
) else (
    echo     [ERROR] Python not found
    echo     Install from: https://python.org
)

REM Check PySide6
echo.
echo [2/4] Checking PySide6...
python -c "import PySide6; print('[OK] PySide6 installed')" 2>nul
if %errorlevel% neq 0 (
    echo     [ERROR] PySide6 not installed
    echo     Run: pip install -r requirements.txt
)

REM Check Node.js
echo.
echo [3/4] Checking Node.js...
where node >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('node --version') do echo     [OK] Node.js %%i
) else (
    echo     [ERROR] Node.js not found
    echo     Run: install-nodejs.bat
)

REM Check React build
echo.
echo [4/4] Checking React build...
if exist "ui\react\dist\index.html" (
    echo     [OK] React app built
) else (
    echo     [PENDING] React app not built
    echo     After Node.js is installed, run:
    echo     cd ui/react ^&^& npm install ^&^& npm run build
)

echo.
echo ============================================================
echo NEXT STEPS
echo ============================================================
echo.

REM Determine what to do next
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo 1. Install Node.js
    echo    Run: install-nodejs.bat
    echo    Or download from: https://nodejs.org
    echo.
    echo 2. After Node.js is installed, restart terminal and run:
    echo    quick-start.bat
) else (
    if exist "ui\react\dist\index.html" (
        echo Everything is ready!
        echo.
        echo Run: python main.py
        echo.
        echo Or use: quick-start.bat for development mode
    ) else (
        echo 1. Install React dependencies:
        echo    cd ui/react
        echo    npm install
        echo.
        echo 2. Build React app:
        echo    npm run build
        echo.
        echo 3. Run the terminal emulator:
        echo    python main.py
    )
)

echo.
echo ============================================================
pause

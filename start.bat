@echo off
setlocal

title Cargo - LAN File Transfer

echo ==========================================
echo              CARGO
echo        LAN File Transfer System
echo ==========================================
echo.

REM ==========================================
REM 1. Check Python
REM ==========================================

echo [1/5] Verifying Python...

python --version >nul 2>&1

if errorlevel 1 (
    echo.
    echo [ERROR] Python was not found.
    echo.
    echo Install Python 3.13 or higher and try again.
    echo.
    pause
    exit /b 1
)

python --version
echo Python OK.
echo.

REM ==========================================
REM 2. Create virtual environment
REM ==========================================

echo [2/5] Verifying virtual environment...

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found.
    echo Creating .venv...
    echo.

    python -m venv .venv

    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to create virtual environment.
        echo.
        pause
        exit /b 1
    )

    echo Virtual environment created.
) else (
    echo Virtual environment found.
)

echo.

REM ==========================================
REM 3. Install dependencies
REM ==========================================

echo [3/5] Verificando dependencias...

call .venv\Scripts\activate.bat

python -m pip install --upgrade pip

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to update pip.
    echo.
    pause
    exit /b 1
)

python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install dependencies.
    echo.
    pause
    exit /b 1
)

echo.
echo Dependencies OK.
echo.

REM ==========================================
REM 4. Check Docker
REM ==========================================

echo [4/5] Verifying Docker...

docker info >nul 2>&1

if errorlevel 1 (
    echo.
    echo [ERROR] Docker is not running or not installed.
    echo.
    echo Open Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)

echo Docker OK.
echo.

REM ==========================================
REM 5. Start Cargo
REM ==========================================

echo [5/5] Initiating Cargo...
echo.
echo ==========================================
echo              CARGO ONLINE
echo ==========================================
echo.
echo Web UI:
echo http://localhost:8000
echo.
echo Upload:
echo http://localhost:8000/upload
echo.
echo Download:
echo http://localhost:8000/download
echo.
echo API:
echo http://localhost:8000/api/v1
echo.
echo ==========================================
echo.
echo Press Ctrl+C to stop Cargo and close the application.
echo.

docker compose up --build

echo.
echo Cargo was stopped.
echo.

pause
endlocal
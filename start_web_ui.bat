@echo off
REM Multi-Agent Orchestration Web UI Startup Script for Windows

echo.
echo 🚀 Starting Multi-Agent Orchestration Web UI...
echo.

REM Check if .env file exists
if not exist .env (
    echo ⚠️  Warning: .env file not found!
    echo Creating .env from .env.example...
    if exist .env.example (
        copy .env.example .env
        echo ✅ Created .env file. Please edit it with your ANTHROPIC_API_KEY
        echo.
        pause
    ) else (
        echo ❌ Error: .env.example not found!
        echo Please create a .env file with your ANTHROPIC_API_KEY
        pause
        exit /b 1
    )
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not in PATH!
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check if dependencies are installed
echo 📦 Checking dependencies...
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo ⚠️  Dependencies not installed. Installing now...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Error: Failed to install dependencies
        pause
        exit /b 1
    )
    echo ✅ Dependencies installed successfully
)

REM Check if ANTHROPIC_API_KEY is set
findstr /C:"ANTHROPIC_API_KEY=sk-" .env >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Warning: ANTHROPIC_API_KEY not set in .env file!
    echo The web UI requires a valid Anthropic API key to function.
    echo Please edit .env and add your API key.
    echo.
    pause
)

echo.
echo ✨ Starting server...
echo 📍 URL: http://localhost:8000
echo 🛑 Press Ctrl+C to stop the server
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

REM Start the server
python web_ui\server.py

#!/bin/bash

# Multi-Agent Orchestration Web UI Startup Script

echo "🚀 Starting Multi-Agent Orchestration Web UI..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Creating .env from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file. Please edit it with your ANTHROPIC_API_KEY"
        echo ""
        read -p "Press Enter to continue after setting your API key, or Ctrl+C to exit..."
    else
        echo "❌ Error: .env.example not found!"
        echo "Please create a .env file with your ANTHROPIC_API_KEY"
        exit 1
    fi
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed!"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "⚠️  Dependencies not installed. Installing now..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to install dependencies"
        exit 1
    fi
    echo "✅ Dependencies installed successfully"
fi

# Check if ANTHROPIC_API_KEY is set
if ! grep -q "ANTHROPIC_API_KEY=sk-" .env 2>/dev/null; then
    echo "⚠️  Warning: ANTHROPIC_API_KEY not set in .env file!"
    echo "The web UI requires a valid Anthropic API key to function."
    echo "Please edit .env and add your API key."
    echo ""
    read -p "Press Enter to continue anyway, or Ctrl+C to exit..."
fi

echo ""
echo "✨ Starting server..."
echo "📍 URL: http://localhost:8000"
echo "🛑 Press Ctrl+C to stop the server"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start the server
cd "$(dirname "$0")"
python3 web_ui/server.py

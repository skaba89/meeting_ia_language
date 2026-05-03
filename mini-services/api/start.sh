#!/bin/bash
# Start the FastAPI backend server for MeetingAI Copilot
# This script is called by `bun run dev` from the mini-service package.json

cd "$(dirname "$0")"

# Install Python dependencies if needed
if [ ! -f ".deps_installed" ]; then
    echo "📦 Installing Python dependencies..."
    pip3 install -q fastapi uvicorn[standard] sqlalchemy python-jose[cryptography] passlib[bcrypt] python-multipart pydantic pydantic-settings httpx aiofiles 2>&1 | tail -1
    touch .deps_installed
fi

# Ensure uploads directory exists
mkdir -p uploads

# Start the FastAPI server with auto-reload
echo "🚀 Starting MeetingAI Copilot API on port 8000..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

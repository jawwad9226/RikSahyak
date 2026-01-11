#!/bin/bash
# Backend startup with Firebase emulator

set -e

export FIRESTORE_EMULATOR_HOST=localhost:8080
export PYTHONUNBUFFERED=1

echo "🚀 Starting RikSahyak Backend (with Firestore Emulator)"
echo "📌 FIRESTORE_EMULATOR_HOST=$FIRESTORE_EMULATOR_HOST"
echo ""

cd /home/jawwad-ahmad/Documents/RikSahyak/backend

# Install dependencies
pip install -q -r requirements.txt

# Start server
echo "✅ Starting FastAPI server on http://127.0.0.1:8000"
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload


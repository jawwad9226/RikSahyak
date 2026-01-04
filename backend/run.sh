#!/bin/bash

# RikSahayak Backend Startup Script

echo "🚀 Starting RikSahayak Backend..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating template..."
    cat > .env << EOF
HOST=0.0.0.0
PORT=8000
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
FIREBASE_DATABASE_URL=your_firebase_url_here
EOF
    echo "📝 Please update .env with your Firebase credentials"
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Start server
echo "✅ Starting FastAPI server on http://0.0.0.0:8000"
echo "📚 API Docs available at http://localhost:8000/docs"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

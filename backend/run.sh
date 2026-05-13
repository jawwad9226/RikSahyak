#!/bin/bash

if command -v conda >/dev/null 2>&1; then
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate riksahyak
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# RikSahyak Backend Startup Script
echo "🚀 Starting RikSahyak Backend (Env: riksahyak)..."

# Start server
echo "✅ FastAPI server starting on http://0.0.0.0:8000"
echo "📚 API Docs available at http://localhost:8000/docs"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

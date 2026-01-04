#!/bin/bash

# RikSahayak - Quick Start Setup Script
# Run this once to set everything up

set -e

echo "🚀 RikSahayak - Quick Setup"
echo "================================"
echo ""

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 16+"
    exit 1
fi
echo "✅ Node.js version: $(node -v)"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi
echo "✅ Python version: $(python3 --version)"

echo ""
echo "📦 Installing frontend dependencies..."
npm install

echo ""
echo "📦 Installing backend dependencies..."
cd backend
pip install -r requirements.txt
cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Setup Firebase:"
echo "   - Go to https://console.firebase.google.com"
echo "   - Create project 'riksahayak'"
echo "   - Download service account JSON"
echo "   - Place at: backend/firebase-credentials.json"
echo "   - Copy config to: src/services/firebase.ts"
echo ""
echo "2. Get your IP address:"
echo "   - macOS/Linux: ifconfig | grep 'inet '"
echo "   - Windows: ipconfig"
echo "   - Update src/services/api.ts with API_BASE_URL"
echo ""
echo "3. Run the backend:"
echo "   cd backend && chmod +x run.sh && ./run.sh"
echo ""
echo "4. Run the frontend (new terminal):"
echo "   npm start"
echo "   Scan QR code with Expo Go"
echo ""
echo "📚 See SETUP.md for detailed instructions"

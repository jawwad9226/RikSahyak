#!/bin/bash
# Start Firebase emulator (Firestore only, with UI enabled)

set -e

echo "🔥 Starting Firebase Emulator (Firestore only)..."
echo ""
echo "Firestore: http://localhost:8080"
echo "Emulator UI: http://localhost:4000"
echo ""

# Check if firebase-tools is installed
if ! command -v firebase &> /dev/null; then
    echo "❌ firebase-tools not found. Install with:"
    echo "   npm install -g firebase-tools"
    exit 1
fi

# Start emulator
firebase emulators:start --only firestore --project=riksahyak-demo


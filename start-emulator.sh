#!/bin/bash
# Start Firebase emulator (Firestore only, with UI enabled)

# Activate Conda Environment
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate riksahyak

set -e

echo "🔥 Starting Firebase Emulator (Firestore only)..."
echo ""
echo "Firestore: http://localhost:8080"
echo "Emulator UI: http://localhost:4000"
echo ""

# Check if firebase-tools is installed
FIREBASE_CMD="firebase"
if ! command -v firebase &> /dev/null; then
    if [ -f "./node_modules/.bin/firebase" ]; then
        FIREBASE_CMD="./node_modules/.bin/firebase"
    else
        echo "❌ firebase-tools not found. Attempting to install locally..."
        npm install firebase-tools
        if [ -f "./node_modules/.bin/firebase" ]; then
            FIREBASE_CMD="./node_modules/.bin/firebase"
        else
            echo "❌ Failed to install firebase-tools."
            exit 1
        fi
    fi
fi

# Start emulator
$FIREBASE_CMD emulators:start --only firestore --project=riksahyak-demo



# Firebase Emulator Setup Guide (STEP 1)

## Overview
This sets up a **local Firestore emulator** for development. No cloud credentials needed. All data stays on your machine.

## Prerequisites
- Node.js 14+ (for firebase-tools)
- Python 3.9+ (backend already has firebase-admin)

## Installation & Start

### 1. Install Firebase Tools (one-time)
```bash
npm install -g firebase-tools
```

### 2. Start the Emulator
From the RikSahyak root directory:
```bash
chmod +x start-emulator.sh
./start-emulator.sh
```

You should see:
```
✔ Hub started successfully
✔ Firestore Emulator started on localhost:8080
✔ Emulator UI started on localhost:4000
```

### 3. In a NEW terminal, Initialize Demo Data
```bash
cd backend
export FIRESTORE_EMULATOR_HOST=localhost:8080
python3 init_emulator.py
```

You should see:
```
✅ Created user: PAS-001 (Raj Kumar)
✅ Created user: PAS-002 (Priya Singh)
✅ Created user: DRV-1001 (Ramesh)
✅ Created user: DRV-1002 (Suresh)
✅ Created user: DRV-1003 (Mahesh)
```

### 4. In another NEW terminal, Start the Backend
```bash
cd backend
chmod +x run-with-emulator.sh
./run-with-emulator.sh
```

The backend will automatically connect to the emulator (via `FIRESTORE_EMULATOR_HOST` env var).

## Verification

### Check Emulator UI
Open: http://localhost:4000

You should see:
- **Firestore** section
- **Collections**: `users` with 5 documents

### Test Backend Connection
```bash
curl http://127.0.0.1:8000/health
```

Should return:
```json
{"status": "healthy"}
```

## What's Running
| Service | URL | Purpose |
|---------|-----|---------|
| Firestore Emulator | localhost:8080 | Local database |
| Emulator UI | localhost:4000 | Web console |
| FastAPI Backend | 127.0.0.1:8000 | REST API |

## Stopping
1. Emulator: Press `Ctrl+C` in emulator terminal
2. Backend: Press `Ctrl+C` in backend terminal

## Important Notes
- **No credentials needed** for emulator mode
- **All data is in-memory** (wiped on restart)
- Set `FIRESTORE_EMULATOR_HOST=localhost:8080` in any new backend terminal

## Next Steps (After Verification)
Once verified, proceed to **STEP 2: Data Models** to define Firestore collections.

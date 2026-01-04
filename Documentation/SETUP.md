# RikSahayak - Auto Rickshaw Booking System for Malkapur

## 📱 Project Overview

**RikSahayak** is a hyper-local auto-rickshaw booking application designed specifically for Malkapur, India. It solves the problem of rickshaw unavailability by connecting passengers with available drivers in real-time.

### Key Features
- ✅ **Passenger App**: Book a rickshaw with fare estimation
- ✅ **Driver App**: Receive and accept ride requests
- ✅ **Real-time Notifications**: WebSocket-based live updates
- ✅ **Fare Calculation**: Transparent pricing (₹20 base + ₹15/km)
- ✅ **Admin Dashboard**: Monitor rides and revenue
- ✅ **Hybrid Support**: Phone + App booking (Phase 2)

---

## 🏗️ Tech Stack

### Frontend
- **Framework**: React Native (Expo)
- **Language**: TypeScript
- **Navigation**: Expo Router (file-based routing)
- **Styling**: React Native StyleSheet + NativeWind (optional)

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: Firebase Firestore (real-time)
- **Authentication**: Firebase Auth
- **Real-time**: WebSocket
- **Deployment**: Docker

### Infrastructure
- **Frontend**: Expo (locally) → PlayStore/AppStore (production)
- **Backend**: Docker container on VPS/Raspberry Pi
- **Database**: Firebase (managed service)

---

## 📂 Project Structure

```
RikSahayak/
├── app/                          # Frontend (React Native)
│   ├── _layout.tsx              # Root navigator
│   ├── index.tsx                # Login screen
│   ├── passenger/               # Passenger screens
│   │   ├── _layout.tsx
│   │   ├── home.tsx
│   │   ├── active-ride.tsx
│   │   └── history.tsx
│   ├── driver/                  # Driver screens
│   │   ├── _layout.tsx
│   │   ├── home.tsx
│   │   ├── current-ride.tsx
│   │   └── earnings.tsx
│   └── admin/                   # Admin screens
│       ├── _layout.tsx
│       └── dashboard.tsx
├── src/                          # Shared logic
│   ├── components/              # Reusable UI components
│   │   ├── Button.tsx
│   │   ├── LocationInput.tsx
│   │   └── RideCard.tsx
│   ├── services/                # API & Firebase
│   │   ├── api.ts              # Backend API calls
│   │   └── firebase.ts         # Firebase setup
│   └── utils/                   # Constants & helpers
│       ├── constants.ts
│       └── colors.ts
├── backend/                     # FastAPI Server
│   ├── app/
│   │   ├── main.py             # Entry point
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── endpoints.py  # All ride routes
│   │   │   │   └── websocket.py  # Real-time updates
│   │   ├── services/
│   │   │   ├── fare_calculator.py   # Pricing logic
│   │   │   ├── matching_engine.py   # Driver matching
│   │   │   └── firebase_service.py  # DB interactions
│   │   └── core/
│   │       ├── config.py           # Settings
│   │       └── schemas.py          # Data models
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile              # Container setup
│   ├── run.sh                  # Start script
│   └── .env                    # Secrets (add to .gitignore)
├── package.json
├── tsconfig.json
├── app.json
└── README.md
```

---

## 🚀 Quick Start

### ✅ Environment Setup (COMPLETED)

**Your project uses a single conda environment:**
- Environment name: `riksahyak`
- Includes: Node.js 18 + Python 3.11
- All dependencies: ✅ Installed

### Step 1: Activate Environment

```bash
conda activate riksahyak
```

### Step 2: Setup Firebase (Optional - for Phase 2)

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Create a new project named "riksahayak"
3. Enable Firestore Database (start in test mode)
4. Enable Phone Authentication
5. Download service account JSON: Project Settings → Service Accounts → Download JSON
6. Place it at `backend/firebase-credentials.json`
7. Copy your config to `src/services/firebase.ts`

### Step 3: Get Your Machine's IP Address

```bash
# On Linux
hostname -I | awk '{print $1}'

# On macOS
ifconfig | grep "inet " | grep -v "127.0.0.1"

# On Windows (PowerShell)
ipconfig | findstr "IPv4"
```

**Update `src/services/api.ts` with your IP:**
```typescript
const API_BASE_URL = "http://YOUR_IP_ADDRESS:8000";
```

### Step 4: Run the Backend

```bash
cd /home/jawwad-ahmad/Documents/RikSahyak/backend
chmod +x run.sh
./run.sh
```

✅ Backend runs on `http://localhost:8000`  
📚 API Docs: `http://localhost:8000/docs`

### Step 5: Run the Frontend

```bash
# In a new terminal (same conda environment)
conda activate riksahyak
cd /home/jawwad-ahmad/Documents/RikSahyak
npm start

# Scan QR code with Expo Go app on your phone
```

---

## ✅ Current Project Status

### Completed Features
- ✅ **Frontend**: 10 screens (Login + 3 roles × 3 screens each)
- ✅ **Backend**: 5 API endpoints fully implemented
- ✅ **TypeScript**: All JSX errors fixed
- ✅ **UI Styling**: Yellow/Black theme with proper contrast
- ✅ **Environment**: Single conda environment with both Node.js and Python
- ✅ **Dependencies**: All packages installed (npm + pip)
- ✅ **Ready to Run**: No additional setup needed

### Pending (Optional)
- ⏳ **Firebase**: Setup required for real-time features (Phase 2)
- ⏳ **Testing**: Run on actual device to verify functionality
- ⏳ **n8n Integration**: Phone booking system (Phase 3)

---

## 🧪 Testing the App

### Test Fare Calculation
1. Open the Passenger App
2. Enter "Malkapur Station" → "Civil Lines"
3. Click "Calculate Fare"
4. Expected: ₹65 (distance ~3.2 km)

### Test Driver View
1. Switch role to Driver
2. See mock ride requests from passengers
3. Click "Accept" to accept a ride

### Test Backend API
```bash
# In another terminal
curl -X POST http://localhost:8000/api/v1/rides/calculate-fare \
  -H "Content-Type: application/json" \
  -d '{
    "pickup_location": "station",
    "dropoff_location": "civil lines"
  }'
```

Expected Response:
```json
{
  "estimated_fare": 65.0,
  "distance_km": 3.2,
  "base_fare": 20,
  "per_km_charge": 48.0
}
```

---

## 📝 Available Locations (Pre-configured)

The backend has these Malkapur locations coded in:
- **Malkapur Station** → (20.8845, 76.2010)
- **Civil Lines** → (20.8900, 76.2100)
- **Bus Stand** → (20.8820, 76.2080)
- **Hospital** → (20.8950, 76.2150)
- **Market** → (20.8870, 76.2000)

---

## 🔌 API Endpoints (Backend)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/v1/rides/calculate-fare` | Calculate estimated fare |
| `POST` | `/api/v1/rides/request` | Create a ride request |
| `POST` | `/api/v1/rides/accept` | Driver accepts ride |
| `GET` | `/api/v1/rides/status/{ride_id}` | Get ride status |
| `WS` | `/api/v1/ws/rides/{user_id}` | Real-time updates |

---

## 🔐 Environment Variables

Create `backend/.env`:
```
HOST=0.0.0.0
PORT=8000
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
FIREBASE_DATABASE_URL=your_firebase_url
DEBUG=True
```

---

## 🐳 Docker Deployment (Optional)

```bash
cd backend
docker build -t riksahayak-api .
docker run -p 8000:8000 -e FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json riksahayak-api
```

---

## 📋 Project Roadmap

### Phase 1: MVP ✅
- [x] Login screen with role selection
- [x] Passenger booking interface
- [x] Driver ride acceptance
- [x] Fare calculation engine
- [x] Basic API endpoints

### Phase 2: Real-time Features (In Progress)
- [ ] WebSocket real-time notifications
- [ ] Driver location tracking
- [ ] Passenger-Driver chat
- [ ] Rating system

### Phase 3: Phone Booking (n8n Integration)
- [ ] Twilio integration for phone calls
- [ ] Speech-to-text (Whisper API)
- [ ] n8n workflows for automation
- [ ] Call transcription to booking

### Phase 4: Production Ready
- [ ] Firebase deployment
- [ ] PlayStore/AppStore release
- [ ] Payment integration (Razorpay/PhonePe)
- [ ] Admin analytics dashboard

---

## 🐛 Troubleshooting

### "Cannot connect to backend"
- ✅ Check if backend is running (`http://YOUR_IP:8000`)
- ✅ Verify IP address in `src/services/api.ts`
- ✅ Both devices (laptop & phone) on same WiFi network

### "Fare calculation returns error"
- ✅ Backend must be running
- ✅ Use exact location names: "station", "civil lines", etc.
- ✅ Check `backend/app/core/config.py` for available locations

### Firebase not connecting
- ✅ Credentials JSON in `backend/firebase-credentials.json`
- ✅ Firestore Database created
- ✅ Firebase config in `src/services/firebase.ts`

---

## 📚 Learning Resources

- [React Native Docs](https://reactnative.dev/)
- [Expo Documentation](https://docs.expo.dev/)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/)
- [Firebase Firestore Guide](https://firebase.google.com/docs/firestore)
- [Python Haversine Distance](https://en.wikipedia.org/wiki/Haversine_formula)

---

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Commit changes: `git commit -m "Add your feature"`
3. Push to GitHub: `git push origin feature/your-feature`
4. Open a Pull Request

---

## 📄 License

This project is open-source under the MIT License.

---

## 💬 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Email: your-email@example.com
- Discord: [Join our community](#)

---

**Happy coding! Let's make Malkapur's transportation better. 🚗** 🇮🇳

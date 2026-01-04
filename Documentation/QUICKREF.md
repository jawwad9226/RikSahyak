# 🎯 RikSahayak - Quick Reference Card

## 🚀 Start Project in 3 Commands

```bash
# Step 1: Activate conda environment
conda activate riksahyak

# Step 2: Start Backend (Terminal 1)
cd /home/jawwad-ahmad/Documents/RikSahyak/backend && ./run.sh

# Step 3: Start Frontend (Terminal 2)
cd /home/jawwad-ahmad/Documents/RikSahyak && npm start
```

---

## ✅ Current Status

- ✅ **Environment:** Single conda env `riksahyak` (Node.js 18 + Python 3.11)
- ✅ **TypeScript:** All JSX errors fixed
- ✅ **UI:** Yellow/Black theme with proper contrast
- ✅ **Dependencies:** All installed (npm + pip)
- ✅ **Ready to run immediately**

---

## 📱 Test the App

| Feature | Steps | Expected Result |
|---------|-------|-----------------|
| **Login** | Open app | See 3 role buttons (Driver/Passenger/Admin) |
| **Passenger** | Select "Passenger" → Enter "station" → "civil lines" | Fare calculated as ₹65 |
| **Driver** | Select "Driver" | See list of ride requests |
| **Accept Ride** | Click "Accept" on any ride | See confirmation |
| **Admin** | Select "Admin" | See dashboard stats |

---

## 🔗 API Testing

### Quick Test
```bash
curl -X POST http://localhost:8000/api/v1/rides/calculate-fare \
  -H "Content-Type: application/json" \
  -d '{"pickup_location": "station", "dropoff_location": "civil lines"}'
```

### Expected Response
```json
{
  "estimated_fare": 65.0,
  "distance_km": 3.2,
  "base_fare": 20,
  "per_km_charge": 48.0
}
```

### API Documentation
Open: `http://localhost:8000/docs` (Interactive Swagger UI)

---

## 📍 Available Locations

- `station` → Malkapur Station
- `civil lines` → Civil Lines
- `bus stand` → Bus Stand
- `hospital` → Hospital
- `market` → Market

---

## 💰 Fare Formula

```
₹20 (Base) + (Distance × ₹15)

Example:
3 km → ₹20 + (3 × ₹15) = ₹65
```

---

## 📂 Important Files to Edit

| File | Purpose |
|------|---------|
| `src/services/api.ts` | Update API_BASE_URL with your IP |
| `src/services/firebase.ts` | Add Firebase config |
| `backend/.env` | Add environment variables |
| `backend/app/core/config.py` | Add more Malkapur locations |

---

## 🔧 Configuration

### Activate Conda Environment (Required)
```bash
conda activate riksahyak
```

### Get Your IP (for API calls)
```bash
# Linux
hostname -I | awk '{print $1}'

# macOS
ifconfig | grep "inet " | grep -v 127.0.0.1

# Windows
ipconfig

# Update src/services/api.ts:
const API_BASE_URL = "http://YOUR_IP:8000";
```

### Backend Dependencies (Already Installed)
```bash
# Installed in conda environment
pip list | grep -i fastapi
```
cd backend
pip install -r requirements.txt
```

### Frontend Dependencies
```bash
npm install
```

---

## 📊 Project Structure at a Glance

```
RikSahayak/
├── app/                    ← Screens
│   ├── index.tsx          (Login)
│   ├── passenger/         (Book rides)
│   ├── driver/            (Accept rides)
│   └── admin/             (Dashboard)
├── backend/               ← API Server
│   ├── app/
│   │   ├── api/v1/        (Routes)
│   │   ├── services/      (Logic)
│   │   └── core/          (Config)
│   └── run.sh             (Start)
├── src/                   ← Shared Code
│   ├── services/          (API, Firebase)
│   └── utils/             (Colors, Constants)
└── docs/                  ← Documentation
    ├── SETUP.md           ← Read this first!
    ├── ARCHITECTURE.md    (How it works)
    └── PROJECT_GUIDE.md   (Full guide)
```

---

## 🎬 Common Commands

### Frontend
```bash
npm start          # Start Expo dev server
npm run android    # Run on Android
npm run ios        # Run on iOS
npm run web        # Run on web
npm lint           # Check code
```

### Backend
```bash
cd backend && ./run.sh     # Start FastAPI server
python -m pytest           # Run tests
pip install -r requirements.txt  # Install deps
```

### Docker
```bash
cd backend
docker build -t riksahayak-api .
docker run -p 8000:8000 riksahayak-api
```

---

## 🔑 Key Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/v1/rides/calculate-fare` | Get estimated price |
| `POST` | `/api/v1/rides/request` | Create booking |
| `POST` | `/api/v1/rides/accept` | Driver accepts |
| `GET` | `/api/v1/rides/status/{id}` | Check status |
| `WS` | `/api/v1/ws/rides/{user_id}` | Real-time updates |

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't connect to backend | Check IP in `src/services/api.ts` |
| Fare calculation wrong | Verify location names match `config.py` |
| Module not found | Run `npm install` or `pip install -r requirements.txt` |
| Backend won't start | Check port 8000 isn't in use |
| App crashes | Check browser console (F12) for errors |

---

## 📚 Documentation Map

| Document | Read When |
|----------|-----------|
| **README.md** | First time, project overview |
| **SETUP.md** | Setting up locally |
| **ARCHITECTURE.md** | Understanding system design |
| **PROJECT_GUIDE.md** | How to use & extend |
| **CHECKLIST.md** | Verify completion |
| **This File** | Quick reference |

---

## 🎯 What's Next

### Immediate (30 min)
- [ ] Run backend & frontend
- [ ] Test fare calculation
- [ ] Check all screens load

### Short Term (Week 1)
- [ ] Setup Firebase
- [ ] Add phone authentication
- [ ] Connect to Firestore

### Medium Term (Week 2-3)
- [ ] Implement real WebSocket
- [ ] Add location tracking
- [ ] Setup payment system

### Long Term (Week 4+)
- [ ] Deploy to production
- [ ] Add n8n workflows
- [ ] PlayStore release

---

## 💻 System Requirements

| Component | Requirement |
|-----------|-------------|
| **Node.js** | 16+ |
| **Python** | 3.11+ |
| **RAM** | 4GB minimum |
| **Disk Space** | 500MB |
| **OS** | macOS, Windows, Linux |

---

## 🎨 Color Scheme

```
Primary:   #FFC107 (Yellow) - Buttons, highlights
Secondary: #000000 (Black)  - Text, borders
Light:     #F5F5F5 (Gray)   - Backgrounds
Dark:      #333333 (Dark)   - Admin theme
```

---

## 🔐 Before Production

```
☐ Setup Firebase
☐ Configure .env with secrets
☐ Enable HTTPS
☐ Setup authentication
☐ Add payment validation
☐ Test thoroughly
☐ Deploy backend
☐ Release on PlayStore
```

---

## 📞 Help Resources

- **React Native**: https://reactnative.dev
- **Expo**: https://docs.expo.dev
- **FastAPI**: https://fastapi.tiangolo.com
- **Firebase**: https://firebase.google.com/docs
- **Haversine**: https://en.wikipedia.org/wiki/Haversine_formula

---

## ✅ Success Checklist

Your project works when:
- ✅ Backend starts without errors
- ✅ Frontend shows all screens
- ✅ Fare calculation shows ₹65 for station→civil lines
- ✅ Driver sees request list
- ✅ Admin sees dashboard
- ✅ API docs load at localhost:8000/docs

---

**You're all set! Start building! 🚀**

*Questions? Check the docs or read ARCHITECTURE.md for details.*

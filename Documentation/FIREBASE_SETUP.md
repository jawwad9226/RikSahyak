# 🔥 Firebase Integration Guide - RikSahyak

## Current Status
- ✅ Backend code ready for Firebase
- ✅ Frontend Firebase config template exists
- ⚠️ **Need: Firebase project credentials**

---

## Step 1: Create Firebase Project (10 minutes)

### 1.1 Go to Firebase Console
```
https://console.firebase.google.com/
```

### 1.2 Create New Project
1. Click "Add project"
2. Project name: **RikSahyak** (or your preferred name)
3. Disable Google Analytics (optional for hackathon)
4. Click "Create project"

### 1.3 Add Firebase to Android App
1. Click "Android" icon
2. Package name: `com.riksahyak.app` (match app.json)
3. Download `google-services.json`
4. Save to: `/android/app/google-services.json`

---

## Step 2: Set Up Firestore Database (5 minutes)

### 2.1 Create Database
1. Go to "Firestore Database" in left menu
2. Click "Create database"
3. Choose "Start in test mode" (for hackathon)
4. Select location: `asia-south1` (India)
5. Click "Enable"

### 2.2 Create Collections
Create these collections manually or let the app create them:

```
rides/
  └─ {rideId}/
      ├─ passenger_id: string
      ├─ driver_id: string
      ├─ status: string ('requested', 'accepted', 'started', 'completed')
      ├─ pickup: {lat, lng, address}
      ├─ dropoff: {lat, lng, address}
      ├─ fare: number
      ├─ created_at: timestamp
      └─ updated_at: timestamp

drivers/
  └─ {driverId}/
      ├─ name: string
      ├─ phone: string
      ├─ vehicle: {type, number}
      ├─ status: string ('available', 'busy')
      ├─ location: {lat, lng}
      ├─ rating: number
      └─ total_rides: number

passengers/
  └─ {passengerId}/
      ├─ name: string
      ├─ phone: string
      ├─ total_rides: number
      └─ rating: number
```

---

## Step 3: Get Service Account Key (Backend)

### 3.1 Generate Service Account
1. Go to Project Settings (gear icon)
2. Go to "Service accounts" tab
3. Click "Generate new private key"
4. Click "Generate key"
5. Save as: `backend/firebase-service-account.json`

### 3.2 Update .env File
```bash
cd /home/jawwad-ahmad/Documents/RikSahyak/backend
nano .env
```

Add this line:
```env
FIREBASE_CREDENTIALS_PATH=/home/jawwad-ahmad/Documents/RikSahyak/backend/firebase-service-account.json
```

---

## Step 4: Get Web App Config (Frontend)

### 4.1 Add Web App
1. In Project Settings
2. Scroll down to "Your apps"
3. Click "Web" icon (</>) 
4. App nickname: "RikSahyak Web"
5. Don't check "Firebase Hosting"
6. Click "Register app"

### 4.2 Copy Config
You'll see something like:
```javascript
const firebaseConfig = {
  apiKey: "AIza...",
  authDomain: "riksahyak-xxxxx.firebaseapp.com",
  projectId: "riksahyak-xxxxx",
  storageBucket: "riksahyak-xxxxx.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abcdef"
};
```

### 4.3 Update Frontend Config
```bash
cd /home/jawwad-ahmad/Documents/RikSahyak
nano src/services/firebase.ts
```

Replace the placeholder config with your actual config.

---

## Step 5: Enable Authentication (5 minutes)

### 5.1 Enable Phone Auth
1. Go to "Authentication" in left menu
2. Click "Get started"
3. Go to "Sign-in method" tab
4. Enable "Phone" provider
5. Save

### 5.2 (Optional) Enable Email Auth
For testing, enable "Email/Password" as well.

---

## Step 6: Test Firebase Connection

### 6.1 Test Backend
```bash
cd /home/jawwad-ahmad/Documents/RikSahyak/backend
python3 << 'EOF'
from app.services.firebase_service import db

# Test connection
test_data = {
    "test": "connection",
    "timestamp": "2026-01-06"
}

# Try to write to Firestore
db.collection('test').document('test_doc').set(test_data)
print("✅ Firebase backend connection successful!")

# Try to read
doc = db.collection('test').document('test_doc').get()
if doc.exists:
    print(f"✅ Read test data: {doc.to_dict()}")
else:
    print("❌ Could not read test data")
EOF
```

### 6.2 Test Frontend (After Mobile App Starts)
In your app code, add:
```typescript
import { db } from '@/services/firebase';
import { collection, addDoc } from 'firebase/firestore';

// Test write
const testRef = await addDoc(collection(db, 'test'), {
  test: 'frontend connection',
  timestamp: new Date()
});
console.log('✅ Firebase frontend connection successful!');
```

---

## Step 7: Update Security Rules (Production)

### 7.1 For Hackathon (Open Access)
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if true;  // ONLY FOR HACKATHON!
    }
  }
}
```

### 7.2 For Production (Secure Access)
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Rides can be read/written by passenger or driver
    match /rides/{rideId} {
      allow read: if request.auth != null;
      allow create: if request.auth != null;
      allow update: if request.auth.uid == resource.data.passenger_id 
                    || request.auth.uid == resource.data.driver_id;
    }
    
    // Users can only access their own data
    match /drivers/{driverId} {
      allow read: if true;  // Drivers visible to all
      allow write: if request.auth.uid == driverId;
    }
    
    match /passengers/{passengerId} {
      allow read, write: if request.auth.uid == passengerId;
    }
  }
}
```

---

## Checklist

- [ ] Firebase project created
- [ ] Firestore database enabled
- [ ] Service account key downloaded
- [ ] Backend `.env` updated with credentials path
- [ ] Web app config copied
- [ ] Frontend `firebase.ts` updated with config
- [ ] Phone authentication enabled
- [ ] Backend connection tested
- [ ] Frontend connection tested (when app runs)
- [ ] Security rules set to test mode

---

## Quick Commands Summary

```bash
# 1. Check if Firebase service account exists
ls -l backend/firebase-service-account.json

# 2. Test backend Firebase connection
cd backend && python3 -c "from app.services.firebase_service import db; print('✅ Connected')"

# 3. Start backend with Firebase
cd backend && uvicorn app.main:app --reload

# 4. Start frontend
npx expo start
```

---

## Common Issues

### Issue: "Could not initialize Firebase"
**Solution:** Check that `firebase-service-account.json` path in `.env` is absolute

### Issue: "Permission denied" in Firestore
**Solution:** Check security rules in Firebase Console

### Issue: "Network request failed"
**Solution:** 
1. Check backend is running on port 8000
2. Check your IP address in Expo
3. Update `API_BASE_URL` in frontend

---

## Next Steps After Firebase Setup

Once Firebase is working:

1. ✅ Test ride creation from frontend
2. ✅ Test real-time updates
3. ✅ Test driver matching
4. ✅ Add authentication flow
5. ✅ Test on mobile device

---

**Estimated Time: 30-45 minutes total**

Once Firebase is connected, your app will have:
- Real-time ride updates
- Driver-passenger matching
- Persistent data storage
- User authentication
- Ready for demo!


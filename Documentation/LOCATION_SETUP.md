# 📍 Location System - Quick Setup & Testing

## ✅ Step 1: Files Are Already Created

You don't need to create anything - all files are ready:

### Backend Services (4 new files):
```
backend/app/core/locations_db.py          ✅ Locations database
backend/app/services/distance_service.py  ✅ Distance calculation
backend/app/services/nominatim_service.py ✅ Location search
backend/app/services/location_ai.py       ✅ AI learning system
```

### Frontend Components (2 new files):
```
src/components/LocationInput.tsx   ✅ Search component
src/components/LocationMap.tsx     ✅ Map display component
```

### Updated Files:
```
app/passenger/home.tsx             ✅ Uses new location system
backend/app/services/fare_calculator.py    ✅ Real distance calculation
backend/app/api/v1/endpoints.py    ✅ New API endpoints
```

---

## ✅ Step 2: Update IP Addresses

Find your IP:
```bash
hostname -I | awk '{print $1}'
# Example output: 192.168.1.5
```

Update these 2 files with YOUR IP:

### File 1: `app/passenger/home.tsx`
Find line ~37:
```typescript
const API_URL = "http://192.168.1.5:8000"; // Change THIS IP
```

### File 2: `src/components/LocationInput.tsx`
Find line ~50:
```typescript
const API_URL = 'http://192.168.1.5:8000'; // Change THIS IP
```

---

## ✅ Step 3: Run the Application

```bash
# Terminal 1: Backend
conda activate riksahyak
cd /home/jawwad-ahmad/Documents/RikSahyak/backend
./run.sh

# Terminal 2: Frontend
conda activate riksahyak
cd /home/jawwad-ahmad/Documents/RikSahyak
npm start
```

---

## ✅ Step 4: Test the System

### **Test in Expo App:**

1. **Open Passenger Screen**
2. **Search for a location:**
   - Type "railway" in pickup
   - Should see instant results
   - Tap "Malkapur Railway Station"

3. **Search another location:**
   - Type "hospital" in dropoff
   - Should see results
   - Tap "Malkapur City Hospital"

4. **View Map:**
   - Tap "View Route on Map 🗺️"
   - Should show map with markers and route line

5. **Calculate Fare:**
   - Tap "Calculate Fare"
   - Should show:
     - Estimated fare
     - Distance in km
     - Time estimate
     - Breakdown

---

## 🧪 Advanced Testing (API Testing)

### **Test 1: Search Location**
```bash
curl -X POST http://192.168.1.5:8000/api/v1/rides/search-location \
  -H "Content-Type: application/json" \
  -d '{"query": "railway"}'
```

**Expected Response:**
```json
{
  "exact_matches": [
    {
      "id": "malkapur_station",
      "name": "Malkapur Railway Station",
      "latitude": 20.8845,
      "longitude": 76.2010,
      "type": "exact_match",
      "category": "station",
      "landmark": "Central Railway Station"
    }
  ],
  "fuzzy_matches": [],
  "nominatim_results": [...],
  "all_results": [...]
}
```

### **Test 2: Calculate Fare (Real Distance)**
```bash
curl -X POST http://192.168.1.5:8000/api/v1/rides/calculate-fare \
  -H "Content-Type: application/json" \
  -d '{
    "pickup_coords": {
      "latitude": 20.8845,
      "longitude": 76.2010
    },
    "dropoff_coords": {
      "latitude": 20.8900,
      "longitude": 76.2100
    }
  }'
```

**Expected Response:**
```json
{
  "estimated_fare": 65.0,
  "distance_km": 3.2,
  "base_fare": 20,
  "per_km_charge": 48.0,
  "estimated_time_minutes": 12,
  "distance_method": "osrm",
  "is_estimate": false
}
```

### **Test 3: Check AI Learning**
```bash
curl http://192.168.1.5:8000/api/v1/rides/ai-statistics
```

**Expected Response:**
```json
{
  "total_searches": 5,
  "total_alternative_names": 3,
  "total_typo_corrections": 1,
  "popular_routes": 2,
  "locations_learned": 2
}
```

---

## 🎯 What to Expect

### **First Run:**
- Location search works instantly (local database)
- Nominatim adds street-level details
- Fare calculated using OSRM routing
- AI stats show 0 (no learning yet)

### **After Multiple Searches:**
- AI learns alternative names
- Future searches show suggestions first
- Typo tolerance improves
- Popular routes are detected

### **After 1 Week:**
- System becomes very personalized
- AI predictions improve
- Autocomplete suggestions work great
- Typos automatically corrected

---

## 🔧 Troubleshooting

### **Issue: "Cannot connect to backend"**
**Solution:**
- Check backend is running (`./run.sh`)
- Verify IP address is correct
- Make sure phone and laptop on same WiFi

### **Issue: Location search returns no results**
**Solution:**
- Check Nominatim service (try in browser):
  ```
  https://nominatim.openstreetmap.org/search?q=railway%20Malkapur%20India&format=json
  ```
- Check backend logs for errors

### **Issue: Fare calculation shows wrong distance**
**Solution:**
- OSRM might be slow (uses `distance_method: "haversine"`)
- Both are correct, OSRM is more accurate
- Check `is_estimate` field in response

### **Issue: Map not showing**
**Solution:**
- Make sure `react-native-maps` is installed
- Check provider is `PROVIDER_OSMDROID`
- Verify coordinates are valid

---

## 📊 Database Overview

### **Locations Available (Malkapur):**
1. **Malkapur Railway Station**
   - Coordinates: (20.8845, 76.2010)
   - Aliases: "railway stn", "station", "central station", etc.

2. **Civil Lines**
   - Coordinates: (20.8900, 76.2100)
   - Aliases: "civil", "civil area", "government area", etc.

3. **Bus Stand**
   - Coordinates: (20.8820, 76.2080)
   - Aliases: "bus station", "transport hub", etc.

4. **Hospital**
   - Coordinates: (20.8950, 76.2150)
   - Aliases: "health center", "medical center", "clinic", etc.

5. **Market**
   - Coordinates: (20.8870, 76.2000)
   - Aliases: "bazaar", "shopping area", etc.

### **Adding New Locations:**

Edit `backend/app/core/locations_db.py`:

```python
"your_location_id": LocationInfo(
    id="your_location_id",
    primary_name="Location Name",
    coordinates=(latitude, longitude),
    street_name="Street Name",
    landmark="Landmark Description",
    category="category_type",  # station, market, hospital, etc.
    description="Description",
    nearby_streets=["Street 1", "Street 2"],
    alternative_names=["alias1", "alias2"],
),
```

---

## 💡 Tips for Best Results

### **1. Update Your IP:**
```bash
# Get IP (Linux)
hostname -I | awk '{print $1}'

# Get IP (macOS)
ifconfig | grep "inet " | grep -v 127.0.0.1

# Get IP (Windows)
ipconfig | findstr "IPv4"
```

### **2. Keep Phone & Laptop on Same Network:**
- Both must be on same WiFi
- Mobile hotspot works too

### **3. Test Each Component Separately:**
1. Test location search first
2. Then test fare calculation
3. Finally test map view

### **4. Monitor AI Learning:**
```bash
# Watch AI improve
curl http://192.168.1.5:8000/api/v1/rides/ai-statistics

# Check learning data file
cat backend/app/data/location_learning.json
```

---

## 🎓 Learning Resources

**What Each Component Does:**

1. **LocationInput (Frontend)**
   - Sends search query to backend
   - Shows results with similarity %
   - Selects location

2. **Nominatim Service (Backend)**
   - Searches OpenStreetMap
   - Returns street-level results
   - No API key needed

3. **Distance Service (Backend)**
   - Tries OSRM (real routing)
   - Falls back to Haversine
   - Returns distance in km

4. **AI Learning (Backend)**
   - Tracks user searches
   - Learns alternative names
   - Predicts next destination

5. **LocationMap (Frontend)**
   - Shows route on map
   - Displays distance
   - OpenStreetMap provider

---

## ✨ Next Steps (Day by Day Improvements)

### **Today:**
- ✅ Test basic search and location selection
- ✅ Test fare calculation
- ✅ Test map display

### **Tomorrow:**
- Add more locations to database
- Test typo tolerance
- Monitor AI learning

### **This Week:**
- Add search favorites feature
- Add location history
- Enhance AI predictions

### **Next Week:**
- Add live traffic layer
- Add route optimization
- Add share location feature

---

## 🎉 You're All Set!

The location and mapping system is ready to use. Every search and location selection will make the system smarter over time through AI learning.

**Questions?** Check the full documentation in `LOCATION_SYSTEM.md`

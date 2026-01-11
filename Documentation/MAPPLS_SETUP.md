# MapmyIndia (Mappls) Integration Guide

## ✅ **What We Just Added:**

### **New MapmyIndia Service:**
- `backend/app/services/mappls_service.py` - Complete MapmyIndia API integration
- Better coverage for Malkapur than Google Maps
- FREE tier: 10,000 API calls/month

### **Updated Search Logic:**
1. **Local Database** (15 locations) → Instant, FREE
2. **MapmyIndia API** → Accurate Indian data
3. **Nominatim/OSM** → Fallback
4. **Auto-caching** → Saves results locally

---

## 🚀 **How to Get MapmyIndia API Keys:**

### **Step 1: Sign Up (FREE)**
1. Go to: https://mappls.com/api
2. Click **"Sign Up"** or **"Get Started Free"**
3. Fill in your details:
   - Name: Your name
   - Email: Your email
   - Company: RikSahyak (or your company name)
   - Use Case: "Ride booking app for Malkapur"

### **Step 2: Verify Email**
- Check your email for verification link
- Click to verify your account

### **Step 3: Create API Credentials**
1. Login to MapmyIndia dashboard
2. Go to **"API Console"** or **"Credentials"**
3. Click **"Create New Credential"** or **"Get API Key"**
4. Select **"REST API"**
5. Copy your:
   - **Client ID**
   - **Client Secret** 
   - **Access Token** (or API Key)

---

## 🔧 **How to Configure:**

### **Option 1: Environment Variables (RECOMMENDED)**

Create or edit `.env` file in `backend/` folder:

```bash
cd backend
nano .env
```

Add these lines:
```
MAPPLS_API_KEY=your_access_token_here
MAPPLS_CLIENT_ID=your_client_id_here
MAPPLS_CLIENT_SECRET=your_client_secret_here
```

Save and exit (Ctrl+X, then Y, then Enter)

### **Option 2: Direct Configuration**

Edit `backend/app/core/config.py`:

```python
MAPPLS_API_KEY = "your_actual_api_key_here"
MAPPLS_CLIENT_ID = "your_client_id"
MAPPLS_CLIENT_SECRET = "your_client_secret"
```

---

## 📊 **API Limits:**

### **FREE Tier:**
- 10,000 requests/month
- 50 requests/minute
- Perfect for testing and prototype

### **Paid Plans (if you need more):**
- **Basic**: ₹3,000/month (50,000 requests)
- **Standard**: ₹5,000/month (100,000 requests)
- **Enterprise**: Custom pricing

---

## ✅ **Testing:**

### **1. Restart Backend:**
```bash
cd backend
./run.sh
```

### **2. Test on Phone:**
- Search for: "railway station"
- Search for: "hospital"
- Search for: "market"

### **3. Check Logs:**
Look for:
```
MapmyIndia found 5 results for 'railway station'
```

If you see this → MapmyIndia is working! ✅

If you see:
```
MapmyIndia API key not configured - skipping
```
→ Add your API key to `.env` file

---

## 🎯 **How It Works:**

### **Search Flow:**
```
User searches "station"
    ↓
1. Check local DB (15 locations) → Found? Return instantly ✅
    ↓ (not found)
2. Call MapmyIndia API → Get Indian location data
    ↓
3. Filter to 10km from Malkapur center
    ↓
4. Cache result in local DB → Next time FREE ✅
    ↓
5. Return to user
```

### **Benefits:**
- ✅ First search: Uses MapmyIndia (accurate)
- ✅ Second search: Uses cache (FREE & instant)
- ✅ Builds local database automatically
- ✅ No manual data entry needed

---

## 🔍 **Monitoring Usage:**

### **Check API Usage:**
1. Login to MapmyIndia dashboard
2. Go to **"Analytics"** or **"Usage"**
3. See requests count

### **Stay Within Free Tier:**
- 10,000 requests/month
- Average 330 requests/day
- If 100 users/day × 3 searches each = 300 requests/day
- You're safe! ✅

---

## ⚠️ **Troubleshooting:**

### **"MapmyIndia API key not configured"**
→ Add API key to `.env` file and restart backend

### **"MapmyIndia API key invalid"**
→ Check if you copied the correct token from dashboard

### **"MapmyIndia rate limit exceeded"**
→ You've used 10,000 requests this month
→ Wait for next month or upgrade plan

### **No MapmyIndia results showing**
→ Check backend logs
→ Verify API key is correct
→ Try searching broader terms like "malkapur station"

---

## 📝 **Next Steps:**

### **After Setup:**
1. Test 10-20 different Malkapur locations
2. Check if results are accurate
3. Monitor API usage in dashboard
4. Local cache will grow automatically

### **Optional Enhancements:**
- Add more local locations manually (I can help!)
- Contribute to OpenStreetMap for your area
- Upgrade to paid plan if needed (after testing)

---

## 🆘 **Need Help?**

Just tell me:
1. "I got my MapmyIndia API key" → I'll help you configure
2. "MapmyIndia not working" → I'll debug
3. "Want to add more locations" → I'll add them manually
4. "Want to try Google instead" → I can switch to Google API

---

**Ready to get your MapmyIndia API key? It takes 5 minutes!** 🚀

# Operator Fallback - Quick Start Guide

## What Was Added?

### 1. Operator Portal UI (`public/operator.html`)
A modern web interface for operators to manually create rides from incoming calls.

**Features:**
- 📞 Incoming call details display
- 📝 Call transcript viewer
- 📋 Pre-filled form with passenger details
- ☎️ One-click callback button
- ✓ Create Ride with auto-calculated fare
- ✓ Mark as Handled

### 2. Backend Operator Endpoint
**POST `/api/v1/operator/create-ride`**
- Creates rides directly from operator portal
- Same validation as regular rides (enforces single active ride)
- Logs operator ID for audit trail
- Returns 409 if passenger has active ride

## How to Use

### Start Backend
```bash
cd backend
python -m uvicorn app.main:app --reload
```

### Open Operator Portal
Navigate to:
```
http://localhost:8000/operator.html
```

### Create a Test Ride
1. **Portal loads** with sample call data:
   - Passenger: Phone number filled
   - Location: Malkapur Main Market → Railway Station
   - Coordinates: Pre-filled (19.2183, 75.5678) → (19.2200, 75.5700)

2. **Edit form** if needed:
   - Change passenger name/phone
   - Adjust pickup/dropoff locations or coordinates
   - Add special notes (elderly, accessibility, etc.)

3. **Click "Create Ride"**:
   - Form submits to `/api/v1/operator/create-ride`
   - Success: Shows ride ID and "Mark Handled" button
   - Conflict: Shows error if passenger has active ride

4. **Mark Call Handled**:
   - Resets form for next incoming call

## Test the Endpoint

### With curl:
```bash
curl -X POST http://localhost:8000/api/v1/operator/create-ride \
  -H "Content-Type: application/json" \
  -d '{
    "passenger_id": "test_passenger",
    "passenger_name": "Rajesh Kumar",
    "passenger_phone": "+91-9876543210",
    "pickup_location": "Malkapur Main Market",
    "dropoff_location": "Railway Station",
    "pickup_coords": {"latitude": 19.2183, "longitude": 75.5678},
    "dropoff_coords": {"latitude": 19.2200, "longitude": 75.5700},
    "distance_km": "2.5",
    "estimated_fare": "70.00",
    "special_notes": "Elderly passenger",
    "operator_id": "operator_demo"
  }'
```

### With Python script:
```bash
python backend/test_operator_endpoint.py
```

## Integration Points

### When to Route to Operator Portal

In your call handling system:
```javascript
// If AI POC fails
if (aiConfidence < threshold || userRequestedOperator) {
  // Open operator UI
  window.open('/operator.html', 'OperatorWindow', 'width=900,height=1000');
}
```

### How Rides Are Tagged
Rides created via operator get metadata:
```javascript
{
  "created_by": "operator",
  "operator_id": "operator_demo",
  "special_notes": "Elderly passenger needs careful driving"
}
```

## API Response Examples

### Success (200)
```json
{
  "ride_id": "ride_1704974400123",
  "status": "REQUESTED",
  "message": "Operator ride created for Rajesh Kumar",
  "passenger_phone": "+91-9876543210",
  "special_notes": "Elderly passenger, special care needed"
}
```

### Conflict - Passenger Has Active Ride (409)
```json
{
  "detail": {
    "error": "Passenger already has an active ride",
    "code": "RIDE_CONFLICT"
  }
}
```

## Files Changed
- ✅ `public/operator.html` - New operator portal
- ✅ `backend/app/api/v1/endpoints.py` - New operator endpoint
- ✅ `backend/app/main.py` - Registered operator router
- ✅ `Documentation/OPERATOR_FALLBACK.md` - Full documentation
- ✅ `backend/test_operator_endpoint.py` - Test script

## What's Next?

### Demo Enhancements (Optional):
1. **Call Transcript Integration**: Connect real speech-to-text
2. **Auto-location Parsing**: Extract pickup/dropoff from transcript
3. **Driver Assignment**: Auto-match available drivers
4. **Call Recording**: Store call audio with ride
5. **Operator Dashboard**: View call queue and metrics

### Production Readiness:
1. **Authentication**: Secure operator login
2. **Rate Limiting**: Prevent abuse
3. **Phone Validation**: Verify passenger phone format
4. **Data Encryption**: Protect PII in special notes
5. **Audit Logging**: Track all operator actions
6. **Admin Review**: Flag operator-created rides for QA

## Testing Checklist

- [ ] Operator portal loads at `/operator.html`
- [ ] Form shows sample call data
- [ ] Coordinates pre-filled with Malkapur locations
- [ ] "Call Passenger" opens dialer (tel: protocol)
- [ ] "Create Ride" submits form successfully
- [ ] Backend returns 200 with ride_id
- [ ] Ride appears in Firestore rides collection
- [ ] 409 error when passenger has active ride
- [ ] "Mark Handled" resets form for next call
- [ ] Special notes are preserved in ride record

## Troubleshooting

### "Can't connect to backend"
- Ensure backend is running on port 8000
- Check CORS is enabled (should allow * origins)

### "409 Conflict" on first request
- Passenger already has an active ride
- Clean test data: Use unique passenger IDs for testing

### Form not submitting
- Check browser console for errors
- Verify backend is accepting requests
- Ensure coordinates are valid numbers

### Special notes not saved
- Check they're included in form payload
- Verify backend accepts special_notes field

## Documentation
For complete documentation, see: `Documentation/OPERATOR_FALLBACK.md`

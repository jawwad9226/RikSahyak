# Operator Fallback Feature

## Overview
The operator fallback feature provides a manual override for incoming call bookings when:
- AI POC (Proof of Concept) fails to understand the caller
- Passenger explicitly requests to speak with a human operator
- Call transcription or intent detection has confidence issues

## Architecture

### Frontend: Operator Portal (`public/operator.html`)

A minimal, self-contained HTML+CSS+JS web UI that:
- Displays incoming call details (caller ID, timestamp, duration)
- Shows AI-generated call transcript
- Parses pickup/dropoff locations from transcript
- One-click "Create Ride" button with form pre-fill
- Buttons for callback and marking call as handled

**Features:**
- ☎️ **Call Passenger**: Click to dial back using tel: protocol
- ✓ **Create Ride**: Submit parsed details to operator endpoint
- ✓ **Mark Handled**: Mark call as processed (UI reset)
- Special notes field for elderly passengers or accessibility needs

**Workflow:**
1. Operator sees incoming call with transcript
2. Manually parses pickup/dropoff from conversation
3. Fills form with passenger details (auto-populated from call)
4. Clicks "Create Ride"
5. Ride is created in backend
6. Marks as handled, waits for next call

### Backend: Operator Endpoint

**POST `/api/v1/operator/create-ride`**

Creates a ride request from operator interaction, bypassing AI.

**Request Payload:**
```json
{
  "passenger_id": "passenger_1234567890",
  "passenger_name": "Rajesh Kumar",
  "passenger_phone": "+91-9876543210",
  "pickup_location": "Malkapur Main Market",
  "dropoff_location": "Railway Station",
  "pickup_coords": {
    "latitude": 19.2183,
    "longitude": 75.5678
  },
  "dropoff_coords": {
    "latitude": 19.2200,
    "longitude": 75.5700
  },
  "distance_km": "2.5",
  "estimated_fare": "70.00",
  "special_notes": "Elderly passenger, special care needed",
  "operator_id": "operator_demo"
}
```

**Response (Success 200):**
```json
{
  "ride_id": "ride_1234567890",
  "status": "REQUESTED",
  "message": "Operator ride created for Rajesh Kumar",
  "passenger_phone": "+91-9876543210",
  "special_notes": "Elderly passenger, special care needed"
}
```

**Response (Conflict 409):**
```json
{
  "detail": {
    "error": "Passenger already has an active ride",
    "code": "RIDE_CONFLICT"
  }
}
```

**Error Handling:**
- Returns 409 Conflict if passenger already has active ride
- Returns 500 if backend error occurs
- Logs operator ID and ride creation for audit trail

## Integration Points

### Call Flow Trigger
When AI POC fails or user requests operator:
1. Call handling system routes to operator UI popup
2. Operator UI shows call transcript and parsed details
3. Operator creates ride via form submission
4. Backend validates and creates ride with operator metadata

### Fallback Logic (Frontend)
```typescript
// In app passenger/home.tsx or call handler
if (aiPOCFailed || userRequestedOperator) {
  // Open operator UI as modal/popup
  window.open('/operator.html', 'OperatorWindow');
}
```

### Operator Metadata
Rides created via operator are tagged with:
- `created_by: "operator"`
- `operator_id: "operator_xxx"`
- Special notes for driver context

## Demo Setup

### Running Operator UI Locally

1. **Start backend:**
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload
   ```

2. **Open operator portal:**
   ```
   http://localhost:8000/operator.html
   ```

3. **Test ride creation:**
   - Fill form with sample data (coordinates pre-filled)
   - Click "Create Ride"
   - Check backend logs for ride creation
   - Response shows ride_id

### Sample Test Data
The operator UI comes with prefilled coordinates for Malkapur:
- **Pickup:** Malkapur Main Market (19.2183, 75.5678)
- **Dropoff:** Railway Station (19.2200, 75.5700)
- **Distance:** ~2.5 km
- **Estimated Fare:** ₹70 (base ₹50 + ₹12/km)

## Files Changed

### Backend
- **endpoints.py**: Added `operator_router` and `/api/v1/operator/create-ride` endpoint
- **main.py**: Registered operator router

### Frontend
- **public/operator.html**: New operator portal UI (self-contained)

## Future Enhancements

1. **Call Transcript Integration**: Real speech-to-text transcripts instead of mock
2. **NLP Parsing**: Auto-extract location from transcript using NLP
3. **Driver Assignment**: Immediate driver matching after ride creation
4. **Call Recording**: Store call recordings linked to ride
5. **Operator Dashboard**: View queue of pending calls, metrics, etc.
6. **Authentication**: Secure operator access (currently demo mode)
7. **Admin Review**: Flag operator-created rides for quality audit

## Testing Checklist

- [ ] Operator UI loads at `/operator.html`
- [ ] Form pre-fills with sample coordinates
- [ ] "Create Ride" submits to `/api/v1/operator/create-ride`
- [ ] Backend returns 200 with ride_id
- [ ] Ride appears in passenger's active rides
- [ ] Special notes are captured
- [ ] 409 conflict returned if passenger has active ride
- [ ] "Mark Handled" button resets UI

## Security Notes (Demo)

Currently **no authentication** - operator portal is open for demo.

**Production recommendations:**
- Require operator login
- Use JWT or session tokens
- Log all operator actions (audit trail)
- Rate limit ride creation (prevent abuse)
- Validate passenger phone format
- Encrypt special notes if PII sensitive

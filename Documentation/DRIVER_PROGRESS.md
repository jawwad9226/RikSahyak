# Driver Progress Milestones - Implementation Guide

## Overview

Driver progress tracking allows drivers to update their progress through a ride without map/location dependency. Tracks four key milestones from pickup to dropoff.

## Progress States

```python
enum DriverProgress:
    NOT_STARTED = "NOT_STARTED"                    # Initial state
    ON_THE_WAY_TO_PICKUP = "ON_THE_WAY_TO_PICKUP"  # En route to pickup
    ARRIVED_AT_PICKUP = "ARRIVED_AT_PICKUP"        # Arrived at pickup point
    ON_THE_WAY_TO_DROPOFF = "ON_THE_WAY_TO_DROPOFF" # En route to dropoff
```

## Endpoint

### POST `/api/v1/rides/{ride_id}/driver-progress`

Updates driver progress for a specific ride.

#### Request
```json
{
  "driver_id": "driver_12345",
  "progress": "ON_THE_WAY_TO_PICKUP"
}
```

#### Response (200)
```json
{
  "ride_id": "RIDE-0001",
  "driver_id": "driver_12345",
  "progress": "ON_THE_WAY_TO_PICKUP",
  "message": "Driver progress updated to ON_THE_WAY_TO_PICKUP"
}
```

#### Response (404)
```json
{
  "detail": "Ride not found"
}
```

#### Response (409 - Wrong Driver)
```json
{
  "detail": {
    "error": "Driver driver_99999 is not assigned to ride RIDE-0001",
    "code": "FORBIDDEN"
  }
}
```

#### Response (409 - Ride Completed/Cancelled)
```json
{
  "detail": {
    "error": "Cannot update progress for COMPLETED ride",
    "code": "INVALID_STATE"
  }
}
```

#### Response (400 - Invalid Progress)
```json
{
  "detail": "Invalid progress: INVALID_VALUE. Must be one of ['NOT_STARTED', 'ON_THE_WAY_TO_PICKUP', 'ARRIVED_AT_PICKUP', 'ON_THE_WAY_TO_DROPOFF']"
}
```

## Validation Rules

| Rule | Details |
|------|---------|
| Assigned Driver Only | Only the assigned driver can update progress |
| Not Completed | Cannot update if ride status is COMPLETED or CANCELLED |
| Valid Progress | Must be one of 4 enum values |
| Ride Exists | Returns 404 if ride not found |

## Database Storage

Progress updates are stored in Firestore with:
```json
{
  "driver_progress": "ON_THE_WAY_TO_PICKUP",
  "progress_updated_at": "2026-01-12T10:30:45.123456Z"
}
```

## Implementation Details

### Files Modified
- **app/core/schemas.py** - Added DriverProgress enum
- **app/services/ride_firestore.py** - Added update_driver_progress() function
- **app/api/v1/endpoints.py** - Added endpoint with validation

### Validation Flow
```
POST /rides/{ride_id}/driver-progress
    ↓
Check ride exists? → 404 if not
    ↓
Check ride not COMPLETED/CANCELLED? → 409 if invalid state
    ↓
Check driver assigned to ride? → 409 if not
    ↓
Check driver_id matches? → 409 FORBIDDEN if mismatch
    ↓
Validate progress enum? → 400 if invalid
    ↓
✓ Update driver_progress and progress_updated_at
    ↓
Return 200 with updated data
```

## Testing

### Run Test Suite
```bash
python backend/test_driver_progress.py
```

Tests:
1. Valid progress update (ON_THE_WAY_TO_PICKUP)
2. All progress states (ARRIVED_AT_PICKUP, ON_THE_WAY_TO_DROPOFF)
3. Invalid progress value rejection (400)
4. Wrong driver rejection (409)
5. Non-existent ride (404)
6. Cannot update completed ride (409)

### Manual Test with curl
```bash
# Assume ride RIDE-0001 with driver driver_12345

# Update to on the way to pickup
curl -X POST http://localhost:8000/api/v1/rides/RIDE-0001/driver-progress \
  -H "Content-Type: application/json" \
  -d '{
    "driver_id": "driver_12345",
    "progress": "ON_THE_WAY_TO_PICKUP"
  }'

# Response: 200 with updated progress

# Try with wrong driver
curl -X POST http://localhost:8000/api/v1/rides/RIDE-0001/driver-progress \
  -H "Content-Type: application/json" \
  -d '{
    "driver_id": "driver_99999",
    "progress": "ON_THE_WAY_TO_PICKUP"
  }'

# Response: 409 FORBIDDEN
```

## Usage Example

### Complete Progress Flow
```python
# Driver gets assigned ride
# RIDE-0001 status: DRIVER_ASSIGNED

# Driver starts heading to pickup
POST /rides/RIDE-0001/driver-progress
{
  "driver_id": "driver_12345",
  "progress": "ON_THE_WAY_TO_PICKUP"
}
# Status: 200 OK

# Driver arrives at pickup point
POST /rides/RIDE-0001/driver-progress
{
  "driver_id": "driver_12345",
  "progress": "ARRIVED_AT_PICKUP"
}
# Status: 200 OK

# Passenger boards, driver heads to dropoff
POST /rides/RIDE-0001/driver-progress
{
  "driver_id": "driver_12345",
  "progress": "ON_THE_WAY_TO_DROPOFF"
}
# Status: 200 OK

# Mark ride as IN_PROGRESS
POST /rides/RIDE-0001/start
{}

# Complete the ride
POST /rides/RIDE-0001/complete
{}
# Status: 200 OK, Ride COMPLETED

# Try to update progress after completion
POST /rides/RIDE-0001/driver-progress
{
  "driver_id": "driver_12345",
  "progress": "ON_THE_WAY_TO_DROPOFF"
}
# Status: 409, Cannot update completed ride
```

## Integration Points

### Frontend Usage
```javascript
// When driver updates location/status
const updateProgress = async (rideId, driverId, progress) => {
  const response = await fetch(
    `/api/v1/rides/${rideId}/driver-progress`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        driver_id: driverId,
        progress: progress
      })
    }
  );
  
  if (response.status === 200) {
    const data = await response.json();
    console.log(`Progress updated to: ${data.progress}`);
  } else if (response.status === 409) {
    console.error('Invalid state or wrong driver');
  } else if (response.status === 404) {
    console.error('Ride not found');
  }
};

// Usage
updateProgress('RIDE-0001', 'driver_12345', 'ON_THE_WAY_TO_PICKUP');
```

## Error Handling

| Status | Error | Meaning |
|--------|-------|---------|
| 200 | None | Success, progress updated |
| 400 | Invalid progress value | Progress not in enum |
| 404 | Ride not found | Ride ID doesn't exist |
| 409 | Invalid state | Ride completed/cancelled |
| 409 | Wrong driver | Driver not assigned or mismatch |
| 500 | Server error | Unexpected backend error |

## Features

✅ **Simple State Tracking** - No GPS/map dependency
✅ **Strict Validation** - Only assigned driver can update
✅ **Immutable States** - Cannot update completed rides
✅ **Timestamped** - Records when progress was updated
✅ **Clear Enum** - Type-safe progress values
✅ **Comprehensive Tests** - 8 test cases covering all scenarios

## Future Enhancements

1. **Auto-Progress** - Auto-update progress based on location tracking
2. **Progress History** - Store all progress updates with timestamps
3. **Passenger Notifications** - Notify passenger on each milestone
4. **ETA Calculation** - Calculate remaining time to next milestone
5. **Analytics** - Track average time between milestones
6. **Geo-Fencing** - Auto-update progress at specific coordinates

## Notes

- No map or GPS integration required
- Pure database state tracking
- Validates authorization (only assigned driver)
- Prevents state violations
- Simple enum-based API
- Lightweight and performant

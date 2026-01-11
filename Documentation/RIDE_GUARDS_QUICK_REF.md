# Ride Guards Implementation - Quick Reference

## What Was Implemented

Strict guards for ride endpoints enforcing:
- **Single active ride per passenger/driver**
- **Valid state transitions** (REQUESTED → DRIVER_ASSIGNED → IN_PROGRESS → COMPLETED)
- **409 Conflict responses** for violations

## Files Changed

| File | Changes | Purpose |
|------|---------|---------|
| `backend/app/services/ride_firestore.py` | +126 lines | Core validation logic |
| `backend/app/api/v1/endpoints.py` | +275 lines | Error handling in endpoints |
| `backend/test_ride_guards.py` | +493 lines (NEW) | 27 comprehensive tests |

## Key Features

### 1. Exception Classes
```python
RideConflictError      # code: "CONFLICT" (409)
RideStateError         # code: "INVALID_STATE" (409)
```

### 2. Validation Helpers
```python
_has_passenger_active_ride(passenger_id)  # Check active rides
_has_driver_active_ride(driver_id)        # Check driver conflicts
_validate_state_transition(from, to)      # Validate transitions
```

### 3. Updated Functions
```python
create_ride()        # Checks passenger active rides
assign_driver()      # Checks driver active rides + state
update_status()      # Validates transitions
```

### 4. Updated Endpoints (5 total)
```
POST /rides/request           # 409: Passenger has active ride
POST /rides/accept            # 409: Driver has active ride / invalid state
POST /rides/{id}/start        # 409: Invalid state transition
POST /rides/{id}/complete     # 409: Invalid state transition
POST /rides/{id}/cancel       # 409: Can't cancel IN_PROGRESS
```

## State Transitions

### Valid Paths
```
REQUESTED → DRIVER_ASSIGNED → IN_PROGRESS → COMPLETED
           ↓
           CANCELLED (before IN_PROGRESS)
```

### Invalid Attempts (409 Conflict)
- IN_PROGRESS → CANCELLED ❌
- REQUESTED → IN_PROGRESS ❌ (skips DRIVER_ASSIGNED)
- COMPLETED → CANCELLED ❌

## Response Format

```json
409 Conflict:
{
  "detail": {
    "error": "Passenger xxx already has an active ride",
    "code": "CONFLICT"
  }
}
```

## Test Coverage

**27 tests** across 3 classes:
- Creation guards (5 tests)
- Driver assignment guards (4 tests)
- State transitions (18 tests)

Run tests:
```bash
cd backend
pytest test_ride_guards.py -v
```

## Commit Details

```
Commit: 69427c5
Message: backend: enforce single-active-ride and strict state transitions (409 conflicts)
Files: 3 changed, +1191 insertions(-)
```

## Active Statuses

These statuses indicate an ongoing ride:
- `REQUESTED` - Awaiting driver assignment
- `DRIVER_ASSIGNED` - Driver assigned, awaiting start
- `IN_PROGRESS` - Ride in progress

Terminal statuses (no longer active):
- `COMPLETED` - Ride finished
- `CANCELLED` - Ride cancelled

## Business Rules

### Passenger Constraints
- ❌ Cannot create new ride if already has active ride
- ✅ Can create new ride after COMPLETED or CANCELLED

### Driver Constraints
- ❌ Cannot accept ride if already has active ride
- ✅ Can accept ride after COMPLETED or CANCELLED

### Lifecycle Rules
- ❌ Cannot skip transitions (e.g., REQUESTED → IN_PROGRESS)
- ❌ Cannot cancel after IN_PROGRESS starts
- ✅ Can cancel before IN_PROGRESS (REQUESTED or DRIVER_ASSIGNED)

## Implementation Details

### Single Active Ride Check
```python
# For passengers: checks REQUESTED, DRIVER_ASSIGNED, IN_PROGRESS
# For drivers: checks DRIVER_ASSIGNED, IN_PROGRESS
```

### State Validation
```python
VALID_TRANSITIONS = {
    "REQUESTED": ["DRIVER_ASSIGNED", "CANCELLED"],
    "DRIVER_ASSIGNED": ["IN_PROGRESS", "CANCELLED"],
    "IN_PROGRESS": ["COMPLETED"],
    "COMPLETED": [],
    "CANCELLED": [],
}
```

### Timestamps Updated
- `created_at` - When ride created
- `assigned_at` - When driver assigned
- `started_at` - When ride started
- `completed_at` - When ride completed
- `cancelled_at` - When ride cancelled

## Testing

All endpoints have try-catch blocks handling:
- ✅ Success scenarios (200)
- ✅ Conflicts (409 with error code)
- ✅ Not found (404)
- ✅ Server errors (500)

Example test:
```python
def test_create_ride_conflict_with_existing_requested(self):
    # Create first ride
    ride_id_1 = create_ride(payload1)
    
    # Try to create second for same passenger
    with pytest.raises(RideConflictError):
        create_ride(payload2)  # 409 Conflict
```

---

**Status**: ✅ Complete and committed
**Ready for**: Testing, deployment, production use

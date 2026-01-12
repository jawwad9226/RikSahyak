from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from app.services.firebase_init import get_db
from app.core.firestore_models import (
    COLLECTION_RIDES,
    COLLECTION_DRIVERS,
    COLLECTION_USERS,
    RideDoc,
)


class RideConflictError(Exception):
    """Raised when a ride operation conflicts with business rules."""
    def __init__(self, message: str, code: str = "CONFLICT"):
        self.message = message
        self.code = code
        super().__init__(message)


class RideStateError(Exception):
    """Raised when a ride state transition is invalid."""
    def __init__(self, message: str, code: str = "INVALID_STATE"):
        self.message = message
        self.code = code
        super().__init__(message)


# Valid state transitions
VALID_TRANSITIONS = {
    "REQUESTED": ["DRIVER_ASSIGNED", "CANCELLED"],
    "DRIVER_ASSIGNED": ["IN_PROGRESS", "CANCELLED"],
    "IN_PROGRESS": ["COMPLETED"],
    "COMPLETED": [],
    "CANCELLED": [],
}

# Active statuses (ride is ongoing)
ACTIVE_STATUSES = ["REQUESTED", "DRIVER_ASSIGNED", "IN_PROGRESS"]


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _format_ride_id(n: int) -> str:
    return f"RIDE-{n:04d}"


def _has_passenger_active_ride(passenger_id: str) -> bool:
    """Check if passenger has any active ride (REQUESTED, DRIVER_ASSIGNED, or IN_PROGRESS)."""
    db = get_db()
    from google.cloud.firestore import FieldFilter
    
    for status in ACTIVE_STATUSES:
        query = db.collection(COLLECTION_RIDES).where(
            filter=FieldFilter("passenger_id", "==", passenger_id)
        ).where(
            filter=FieldFilter("status", "==", status)
        ).limit(1)
        for _ in query.stream():
            return True
    return False


def _has_driver_active_ride(driver_id: str) -> bool:
    """Check if driver has any active ride (DRIVER_ASSIGNED or IN_PROGRESS)."""
    db = get_db()
    from google.cloud.firestore import FieldFilter
    
    for status in ["DRIVER_ASSIGNED", "IN_PROGRESS"]:
        query = db.collection(COLLECTION_RIDES).where(
            filter=FieldFilter("driver_id", "==", driver_id)
        ).where(
            filter=FieldFilter("status", "==", status)
        ).limit(1)
        for _ in query.stream():
            return True
    return False


def _validate_state_transition(current_status: str, new_status: str) -> None:
    """Validate that state transition is allowed."""
    if new_status not in VALID_TRANSITIONS.get(current_status, []):
        raise RideStateError(
            f"Invalid transition from {current_status} to {new_status}",
            code="INVALID_STATE"
        )



def _get_and_increment_counter(db) -> int:
    """Get and increment ride counter. Simple approach without transaction for dev."""
    counters_ref = db.collection("meta").document("counters")
    snap = counters_ref.get()
    data = snap.to_dict() if snap.exists else {"ride_next_id": 1}
    current = int(data.get("ride_next_id", 1))
    data["ride_next_id"] = current + 1
    counters_ref.set(data)
    return current


def create_ride(payload: Dict[str, Any]) -> str:
    """
    Create a ride document with deterministic sequential ID.
    
    Args:
        payload: Ride data (must include passenger_id)
        
    Returns:
        ride_id: The created ride ID
        
    Raises:
        RideConflictError: If passenger already has an active ride
    """
    # Check for active rides first
    passenger_id = payload.get("passenger_id")
    if passenger_id and _has_passenger_active_ride(passenger_id):
        raise RideConflictError(
            f"Passenger {passenger_id} already has an active ride",
            code="CONFLICT"
        )
    
    db = get_db()
    next_id = _get_and_increment_counter(db)
    ride_id = _format_ride_id(next_id)
    ride_ref = db.collection(COLLECTION_RIDES).document(ride_id)
    payload_copy = dict(payload)
    payload_copy["id"] = ride_id
    payload_copy.setdefault("created_at", _now_iso())
    ride_ref.set(payload_copy)
    return ride_id


def get_ride(ride_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    doc = db.collection(COLLECTION_RIDES).document(ride_id).get()
    if not doc.exists:
        return None
    d = doc.to_dict()
    d["id"] = ride_id
    return d


def set_candidate_drivers(ride_id: str, driver_ids: List[str]) -> None:
    db = get_db()
    db.collection(COLLECTION_RIDES).document(ride_id).update({
        "candidate_drivers": driver_ids
    })


def assign_driver(ride_id: str, driver_id: str) -> None:
    """
    Assign driver to ride and set DRIVER_ASSIGNED status.
    
    Args:
        ride_id: The ride to assign to
        driver_id: The driver ID
        
    Raises:
        RideConflictError: If driver already has an active ride
        RideStateError: If ride is not in REQUESTED status
    """
    db = get_db()
    ride_ref = db.collection(COLLECTION_RIDES).document(ride_id)
    ride_snap = ride_ref.get()
    
    if not ride_snap.exists:
        raise ValueError(f"Ride {ride_id} not found")
    
    ride = ride_snap.to_dict()
    current_status = ride.get("status")
    
    # Validate current status
    if current_status != "REQUESTED":
        raise RideStateError(
            f"Can only assign driver to REQUESTED ride, current status is {current_status}",
            code="INVALID_STATE"
        )
    
    # Check if driver has active ride
    if _has_driver_active_ride(driver_id):
        raise RideConflictError(
            f"Driver {driver_id} already has an active ride",
            code="CONFLICT"
        )
    
    db.collection(COLLECTION_RIDES).document(ride_id).update({
        "driver_id": driver_id,
        "status": "DRIVER_ASSIGNED",
        "assigned_at": _now_iso(),
    })


def update_status(ride_id: str, status: str) -> None:
    """
    Update ride status with validation of state transitions.
    
    Args:
        ride_id: The ride to update
        status: The new status
        
    Raises:
        RideStateError: If state transition is invalid
    """
    db = get_db()
    ride_ref = db.collection(COLLECTION_RIDES).document(ride_id)
    ride_snap = ride_ref.get()
    
    if not ride_snap.exists:
        raise ValueError(f"Ride {ride_id} not found")
    
    ride = ride_snap.to_dict()
    current_status = ride.get("status")
    
    # Validate transition
    _validate_state_transition(current_status, status)
    
    patch = {"status": status}
    now = _now_iso()
    if status == "COMPLETED":
        patch["completed_at"] = now
    elif status == "IN_PROGRESS":
        patch["started_at"] = now
    elif status == "CANCELLED":
        patch["cancelled_at"] = now
    
    db.collection(COLLECTION_RIDES).document(ride_id).update(patch)


def update_driver_progress(ride_id: str, driver_id: str, progress: str) -> None:
    """
    Update driver progress for a ride with validation.
    
    Args:
        ride_id: The ride to update
        driver_id: The driver making the update (must be assigned driver)
        progress: The new progress (NOT_STARTED, ON_THE_WAY_TO_PICKUP, ARRIVED_AT_PICKUP, ON_THE_WAY_TO_DROPOFF)
        
    Raises:
        ValueError: If ride not found
        RideStateError: If ride is completed/cancelled or driver is not assigned
        RideConflictError: If driver is not the assigned driver
    """
    # Valid progress enum values
    VALID_PROGRESS = [
        "NOT_STARTED",
        "ON_THE_WAY_TO_PICKUP",
        "ARRIVED_AT_PICKUP",
        "ON_THE_WAY_TO_DROPOFF",
    ]
    
    if progress not in VALID_PROGRESS:
        raise ValueError(f"Invalid progress: {progress}. Must be one of {VALID_PROGRESS}")
    
    db = get_db()
    ride_ref = db.collection(COLLECTION_RIDES).document(ride_id)
    ride_snap = ride_ref.get()
    
    if not ride_snap.exists:
        raise ValueError(f"Ride {ride_id} not found")
    
    ride = ride_snap.to_dict()
    current_status = ride.get("status")
    assigned_driver_id = ride.get("driver_id")
    
    # Check ride is not completed or cancelled
    if current_status in ["COMPLETED", "CANCELLED"]:
        raise RideStateError(
            f"Cannot update progress for {current_status} ride",
            code="INVALID_STATE"
        )
    
    # Check driver is assigned to this ride
    if not assigned_driver_id:
        raise RideStateError(
            f"No driver assigned to ride {ride_id}",
            code="INVALID_STATE"
        )
    
    # Check it's the assigned driver making the update
    if assigned_driver_id != driver_id:
        raise RideConflictError(
            f"Driver {driver_id} is not assigned to ride {ride_id}",
            code="FORBIDDEN"
        )
    
    # Update progress
    db.collection(COLLECTION_RIDES).document(ride_id).update({
        "driver_progress": progress,
        "progress_updated_at": _now_iso(),
    })


def list_drivers_ordered() -> List[Dict[str, Any]]:
    """Get deterministic list of drivers. Prefer drivers collection, else users with role=driver.
    Returns minimal fields plus 'coords' if available.
    """
    db = get_db()
    drivers = [d.to_dict() | {"driver_id": d.id} for d in db.collection(COLLECTION_DRIVERS).stream()]
    if not drivers:
        # Fallback to users where role == 'driver'
        users = [d.to_dict() for d in db.collection(COLLECTION_USERS).stream()]
        drivers = [
            {
                "driver_id": u.get("user_id") or u.get("id"),
                "name": u.get("name"),
                "phone": u.get("phone"),
                "vehicle_number": u.get("vehicle_number"),
                # no coords in users by default
            }
            for u in users if (u.get("role") == "driver")
        ]
    drivers.sort(key=lambda d: d.get("driver_id") or "")
    return drivers


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    from math import radians, sin, cos, sqrt, atan2
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return round(R * c, 3)


def find_drivers_for_ride(ride_id: str, max_results: int = 3) -> List[Dict[str, Any]]:
    ride = get_ride(ride_id)
    if not ride:
        return []
    pickup = ride.get("pickup_coords") or {}
    lat1 = pickup.get("latitude")
    lon1 = pickup.get("longitude")
    out: List[Dict[str, Any]] = []

    for d in list_drivers_ordered()[: max(1, max_results)]:
        coords = d.get("coords") or {}
        distance_km = None
        if lat1 is not None and lon1 is not None and coords:
            distance_km = haversine_km(lat1, lon1, coords.get("latitude"), coords.get("longitude"))
        out.append({
            "driver_id": d.get("driver_id"),
            "name": d.get("name"),
            "phone": d.get("phone"),
            "vehicle_number": d.get("vehicle_number"),
            "distance_km": distance_km,
        })
    return out


def list_requested_rides() -> List[Dict[str, Any]]:
    """Get all rides with status=REQUESTED, ordered by created_at."""
    db = get_db()
    from google.cloud.firestore import FieldFilter
    query = db.collection(COLLECTION_RIDES).where(
        filter=FieldFilter("status", "==", "REQUESTED")
    ).order_by("created_at")
    rides = []
    for doc in query.stream():
        ride_data = doc.to_dict()
        ride_data["id"] = doc.id
        rides.append(ride_data)
    return rides


def get_driver_assigned_ride(driver_id: str) -> Optional[Dict[str, Any]]:
    """Get the ride currently assigned to this driver (DRIVER_ASSIGNED or IN_PROGRESS)."""
    db = get_db()
    from google.cloud.firestore import FieldFilter
    # Check DRIVER_ASSIGNED first
    query = db.collection(COLLECTION_RIDES).where(
        filter=FieldFilter("driver_id", "==", driver_id)
    ).where(
        filter=FieldFilter("status", "==", "DRIVER_ASSIGNED")
    ).limit(1)
    for doc in query.stream():
        ride_data = doc.to_dict()
        ride_data["id"] = doc.id
        return ride_data
    
    # Check IN_PROGRESS
    from google.cloud.firestore import FieldFilter
    query = db.collection(COLLECTION_RIDES).where(
        filter=FieldFilter("driver_id", "==", driver_id)
    ).where(
        filter=FieldFilter("status", "==", "IN_PROGRESS")
    ).limit(1)
    for doc in query.stream():
        ride_data = doc.to_dict()
        ride_data["id"] = doc.id
        return ride_data
    
    return None


def get_passenger_current_ride(passenger_id: str) -> Optional[Dict[str, Any]]:
    """Get the current ride for a passenger (any ride that's not completed or cancelled)."""
    db = get_db()
    from google.cloud.firestore import FieldFilter
    statuses = ["REQUESTED", "DRIVER_ASSIGNED", "IN_PROGRESS"]
    
    for status in statuses:
        query = db.collection(COLLECTION_RIDES).where(
            filter=FieldFilter("passenger_id", "==", passenger_id)
        ).where(
            filter=FieldFilter("status", "==", status)
        ).limit(1)
        for doc in query.stream():
            ride_data = doc.to_dict()
            ride_data["id"] = doc.id
            return ride_data
    
    return None


def get_admin_stats() -> Dict[str, Any]:
    """Get comprehensive admin dashboard statistics."""
    db = get_db()
    
    # Get all rides
    rides_ref = db.collection(COLLECTION_RIDES)
    all_rides = rides_ref.stream()
    
    total_rides = 0
    total_revenue = 0
    active_rides = 0
    today_rides = 0
    today_revenue = 0
    completed_rides = 0
    
    from datetime import datetime, timedelta
    
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_start_iso = today_start.isoformat() + "Z"
    
    for ride_doc in all_rides:
        ride = ride_doc.to_dict()
        total_rides += 1
        
        status = ride.get("status", "")
        if status in ["REQUESTED", "DRIVER_ASSIGNED", "IN_PROGRESS"]:
            active_rides += 1
        
        if status == "COMPLETED":
            completed_rides += 1
            fare = ride.get("fare", 0)
            total_revenue += fare
            
            # Check if completed today
            completed_at = ride.get("completed_at", "")
            if completed_at and completed_at >= today_start_iso:
                today_rides += 1
                today_revenue += fare
    
    # Get active drivers (drivers with rides in progress or assigned)
    active_drivers = set()
    active_rides_query = rides_ref.where("status", "in", ["DRIVER_ASSIGNED", "IN_PROGRESS"]).stream()
    for ride_doc in active_rides_query:
        ride = ride_doc.to_dict()
        driver_id = ride.get("driver_id")
        if driver_id:
            active_drivers.add(driver_id)
    
    # Get total passengers (unique users who created rides)
    passengers = set()
    all_rides_query = rides_ref.stream()
    for ride_doc in all_rides_query:
        ride = ride_doc.to_dict()
        passenger_id = ride.get("passenger_id")
        if passenger_id:
            passengers.add(passenger_id)
    
    # For now, average rating is dummy
    average_rating = 4.7
    
    return {
        "totalRides": total_rides,
        "totalRevenue": total_revenue,
        "activeDrivers": len(active_drivers),
        "activeRides": active_rides,
        "todayRides": today_rides,
        "todayRevenue": today_revenue,
        "totalPassengers": len(passengers),
        "averageRating": average_rating,
    }

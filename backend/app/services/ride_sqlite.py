import os
import json
import sqlite3
from typing import Any, Dict, List, Optional
from datetime import datetime
import random

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "riksahyak.db")

class RideConflictError(Exception):
    def __init__(self, message: str, code: str = "CONFLICT"):
        self.message = message
        self.code = code
        super().__init__(message)

class RideStateError(Exception):
    def __init__(self, message: str, code: str = "INVALID_STATE"):
        self.message = message
        self.code = code
        super().__init__(message)

VALID_TRANSITIONS = {
    "REQUESTED": ["DRIVER_ASSIGNED", "CANCELLED"],
    "DRIVER_ASSIGNED": ["IN_PROGRESS", "COMPLETED", "CANCELLED"],
    "IN_PROGRESS": ["COMPLETED"],
    "COMPLETED": [],
    "CANCELLED": [],
}
ACTIVE_STATUSES = ["REQUESTED", "DRIVER_ASSIGNED", "IN_PROGRESS"]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rides (
                id TEXT PRIMARY KEY,
                passenger_id TEXT,
                driver_id TEXT,
                status TEXT,
                data JSON,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS drivers (
                driver_id TEXT PRIMARY KEY,
                data JSON
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                data JSON
            )
        """)
        # Create counters table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS counters (
                name TEXT PRIMARY KEY,
                value INTEGER
            )
        """)
        # Create table for AI Training Flywheel (failed SMS parses)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS failed_sms_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT,
                text_message TEXT,
                raw_ai_output TEXT,
                created_at TEXT
            )
        """)
        conn.commit()

# Initialize DB on import
init_db()

def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"

def _format_ride_id(n: int) -> str:
    return f"RIDE-{n:04d}"

def _has_passenger_active_ride(passenger_id: str) -> bool:
    with get_db() as conn:
        placeholders = ",".join("?" * len(ACTIVE_STATUSES))
        query = f"SELECT 1 FROM rides WHERE passenger_id = ? AND status IN ({placeholders}) LIMIT 1"
        res = conn.execute(query, [passenger_id] + ACTIVE_STATUSES).fetchone()
        return bool(res)

def _has_driver_active_ride(driver_id: str) -> bool:
    with get_db() as conn:
        res = conn.execute(
            "SELECT 1 FROM rides WHERE driver_id = ? AND status IN ('DRIVER_ASSIGNED', 'IN_PROGRESS') LIMIT 1",
            (driver_id,)
        ).fetchone()
        return bool(res)

def _validate_state_transition(current_status: str, new_status: str) -> None:
    if new_status not in VALID_TRANSITIONS.get(current_status, []):
        raise RideStateError(f"Invalid transition from {current_status} to {new_status}", code="INVALID_STATE")

def _get_driver_info(driver_id: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        # Check drivers table
        res = conn.execute("SELECT data FROM drivers WHERE driver_id = ?", (driver_id,)).fetchone()
        if res:
            data = json.loads(res["data"])
            data["driver_id"] = driver_id
            return data
        
        # Check users table
        res = conn.execute("SELECT data FROM users WHERE user_id = ?", (driver_id,)).fetchone()
        if res:
            data = json.loads(res["data"])
            if data.get("role") == "driver":
                data["driver_id"] = driver_id
                return data
    
    # Fallback to JSON file if present
    try:
        from app.services.json_store import load_drivers_store
        store = load_drivers_store()
        for driver in store.get("drivers", []):
            if driver.get("driver_id") == driver_id:
                return driver
    except Exception:
        pass
    
    return None

def _get_and_increment_counter() -> int:
    with get_db() as conn:
        res = conn.execute("SELECT value FROM counters WHERE name = 'ride_next_id'").fetchone()
        if not res:
            conn.execute("INSERT INTO counters (name, value) VALUES ('ride_next_id', 2)")
            return 1
        current = res["value"]
        conn.execute("UPDATE counters SET value = ? WHERE name = 'ride_next_id'", (current + 1,))
        return current

def create_ride(payload: Dict[str, Any]) -> str:
    passenger_id = payload.get("passenger_id")
    if passenger_id and _has_passenger_active_ride(passenger_id):
        raise RideConflictError(f"Passenger {passenger_id} already has an active ride", code="CONFLICT")
    
    next_id = _get_and_increment_counter()
    ride_id = _format_ride_id(next_id)
    payload_copy = dict(payload)
    payload_copy["id"] = ride_id
    payload_copy.setdefault("created_at", _now_iso())
    
    with get_db() as conn:
        conn.execute(
            "INSERT INTO rides (id, passenger_id, driver_id, status, data, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (ride_id, passenger_id, payload_copy.get("driver_id"), payload_copy.get("status", "REQUESTED"), json.dumps(payload_copy), payload_copy["created_at"])
        )
    return ride_id

def get_ride(ride_id: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        res = conn.execute("SELECT data FROM rides WHERE id = ?", (ride_id,)).fetchone()
        if not res:
            return None
        d = json.loads(res["data"])
        d["id"] = ride_id
        return d

def _update_ride_data(ride_id: str, update_dict: dict) -> None:
    ride = get_ride(ride_id)
    if not ride:
        return
    ride.update(update_dict)
    
    # Update relational columns if they are present in update_dict
    status = update_dict.get("status", ride.get("status"))
    driver_id = update_dict.get("driver_id", ride.get("driver_id"))
    
    with get_db() as conn:
        conn.execute(
            "UPDATE rides SET status = ?, driver_id = ?, data = ? WHERE id = ?",
            (status, driver_id, json.dumps(ride), ride_id)
        )

def set_candidate_drivers(ride_id: str, driver_ids: List[str]) -> None:
    _update_ride_data(ride_id, {"candidate_drivers": driver_ids})

def assign_driver(ride_id: str, driver_id: str) -> None:
    ride = get_ride(ride_id)
    if not ride:
        raise ValueError(f"Ride {ride_id} not found")
    
    current_status = ride.get("status")
    if current_status != "REQUESTED":
        raise RideStateError(f"Can only assign driver to REQUESTED ride, current status is {current_status}", code="INVALID_STATE")
    
    if _has_driver_active_ride(driver_id):
        raise RideConflictError(f"Driver {driver_id} already has an active ride", code="CONFLICT")
    
    driver_info = _get_driver_info(driver_id)
    pickup_otp = f"{random.randint(1000, 9999)}"
    
    update_data = {
        "driver_id": driver_id,
        "status": "DRIVER_ASSIGNED",
        "assigned_at": _now_iso(),
        "pickup_otp": pickup_otp,
    }
    
    if driver_info:
        update_data["driver_name"] = driver_info.get("name", driver_info.get("driver_name"))
        update_data["driver_phone"] = driver_info.get("phone", driver_info.get("driver_phone"))
        update_data["vehicle_number"] = driver_info.get("vehicle_number")
    
    _update_ride_data(ride_id, update_data)

def update_status(ride_id: str, status: str, otp: str = None) -> None:
    ride = get_ride(ride_id)
    if not ride:
        raise ValueError(f"Ride {ride_id} not found")
    
    current_status = ride.get("status")
    _validate_state_transition(current_status, status)
    
    if status == "IN_PROGRESS":
        stored_otp = ride.get("pickup_otp")
        if stored_otp and otp != stored_otp:
            raise ValueError("Invalid OTP. Please ask passenger for the correct code.")
    
    patch = {"status": status}
    now = _now_iso()
    if status == "COMPLETED":
        patch["completed_at"] = now
    elif status == "IN_PROGRESS":
        patch["started_at"] = now
    elif status == "CANCELLED":
        patch["cancelled_at"] = now
    
    _update_ride_data(ride_id, patch)

def update_driver_progress(ride_id: str, driver_id: str, progress: str) -> None:
    VALID_PROGRESS = ["NOT_STARTED", "ON_THE_WAY_TO_PICKUP", "ARRIVED_AT_PICKUP", "ON_THE_WAY_TO_DROPOFF"]
    if progress not in VALID_PROGRESS:
        raise ValueError(f"Invalid progress: {progress}. Must be one of {VALID_PROGRESS}")
    
    ride = get_ride(ride_id)
    if not ride:
        raise ValueError(f"Ride {ride_id} not found")
    
    current_status = ride.get("status")
    assigned_driver_id = ride.get("driver_id")
    
    if current_status in ["COMPLETED", "CANCELLED"]:
        raise RideStateError(f"Cannot update progress for {current_status} ride", code="INVALID_STATE")
    
    if not assigned_driver_id:
        raise RideStateError(f"No driver assigned to ride {ride_id}", code="INVALID_STATE")
    
    if assigned_driver_id != driver_id:
        raise RideConflictError(f"Driver {driver_id} is not assigned to ride {ride_id}", code="FORBIDDEN")
    
    _update_ride_data(ride_id, {"driver_progress": progress, "progress_updated_at": _now_iso()})

def add_driver(driver_data: Dict[str, Any]) -> str:
    driver_id = driver_data.get("driver_id")
    if not driver_id:
        driver_id = f"DRV-{random.randint(1000, 9999)}"
        driver_data["driver_id"] = driver_id
        
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO drivers (driver_id, data) VALUES (?, ?)",
            (driver_id, json.dumps(driver_data))
        )
        conn.commit()
    return driver_id

def list_drivers_ordered() -> List[Dict[str, Any]]:
    with get_db() as conn:
        drivers = []
        for row in conn.execute("SELECT data FROM drivers").fetchall():
            drivers.append(json.loads(row["data"]))
            
        if not drivers:
            for row in conn.execute("SELECT data FROM users").fetchall():
                u = json.loads(row["data"])
                if u.get("role") == "driver":
                    drivers.append({
                        "driver_id": u.get("user_id") or u.get("id"),
                        "name": u.get("name"),
                        "phone": u.get("phone"),
                        "vehicle_number": u.get("vehicle_number"),
                    })
    
    # Fallback to JSON file if present
    if not drivers:
        try:
            from app.services.json_store import load_drivers_store
            store = load_drivers_store()
            for d in store.get("drivers", []):
                drivers.append(d)
        except Exception:
            pass

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
    with get_db() as conn:
        rides = []
        for row in conn.execute("SELECT data FROM rides WHERE status = 'REQUESTED' ORDER BY created_at"):
            rides.append(json.loads(row["data"]))
        return rides

def get_driver_assigned_ride(driver_id: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        res = conn.execute(
            "SELECT data FROM rides WHERE driver_id = ? AND status = 'DRIVER_ASSIGNED' LIMIT 1",
            (driver_id,)
        ).fetchone()
        if res:
            return json.loads(res["data"])
            
        res = conn.execute(
            "SELECT data FROM rides WHERE driver_id = ? AND status = 'IN_PROGRESS' LIMIT 1",
            (driver_id,)
        ).fetchone()
        if res:
            return json.loads(res["data"])
            
    return None

def get_passenger_current_ride(passenger_id: str) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        placeholders = ",".join("?" * len(ACTIVE_STATUSES))
        query = f"SELECT data FROM rides WHERE passenger_id = ? AND status IN ({placeholders}) LIMIT 1"
        res = conn.execute(query, [passenger_id] + ACTIVE_STATUSES).fetchone()
        if res:
            return json.loads(res["data"])
    return None

def get_admin_stats() -> Dict[str, Any]:
    with get_db() as conn:
        total_rides = 0
        total_revenue = 0
        active_rides = 0
        today_rides = 0
        today_revenue = 0
        completed_rides = 0
        active_drivers = set()
        passengers = set()
        
        today_start_iso = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
        
        for row in conn.execute("SELECT data FROM rides").fetchall():
            ride = json.loads(row["data"])
            total_rides += 1
            
            status = ride.get("status", "")
            if status in ACTIVE_STATUSES:
                active_rides += 1
                driver_id = ride.get("driver_id")
                if driver_id and status in ["DRIVER_ASSIGNED", "IN_PROGRESS"]:
                    active_drivers.add(driver_id)
            
            if status == "COMPLETED":
                completed_rides += 1
                fare = ride.get("fare", 0)
                total_revenue += fare
                
                completed_at = ride.get("completed_at", "")
                if completed_at and completed_at >= today_start_iso:
                    today_rides += 1
                    today_revenue += fare
            
            passenger_id = ride.get("passenger_id")
            if passenger_id:
                passengers.add(passenger_id)
        
        return {
            "totalRides": total_rides,
            "totalRevenue": total_revenue,
            "activeDrivers": len(active_drivers),
            "activeRides": active_rides,
            "todayRides": today_rides,
            "todayRevenue": today_revenue,
            "totalPassengers": len(passengers),
            "averageRating": 4.7,
        }

def log_failed_sms_parse(phone_number: str, text_message: str, raw_ai_output: str) -> None:
    """
    Logs failed SMS parse attempts for the AI Training Flywheel.
    These logs can be used later to fine-tune the local LLM.
    """
    with get_db() as conn:
        conn.execute(
            "INSERT INTO failed_sms_logs (phone_number, text_message, raw_ai_output, created_at) VALUES (?, ?, ?, ?)",
            (phone_number, text_message, raw_ai_output, _now_iso())
        )
        conn.commit()

def get_failed_sms_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieves the most recent failed SMS parses for AI fine-tuning.
    """
    with get_db() as conn:
        logs = []
        for row in conn.execute("SELECT * FROM failed_sms_logs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall():
            logs.append(dict(row))
        return logs

def get_all_users() -> Dict[str, Any]:
    with get_db() as conn:
        drivers = []
        for row in conn.execute("SELECT data FROM drivers").fetchall():
            d = json.loads(row["data"])
            d["role"] = "driver"
            drivers.append(d)
            
        passengers = {}
        for row in conn.execute("SELECT data FROM rides").fetchall():
            r = json.loads(row["data"])
            pid = r.get("passenger_id")
            if pid and pid not in passengers:
                passengers[pid] = {
                    "id": pid,
                    "role": "passenger",
                    "name": r.get("passenger_name", "Unknown"),
                    "phone": r.get("passenger_phone", "Unknown"),
                    "total_rides": 1,
                    "last_ride": r.get("created_at", "")
                }
            elif pid in passengers:
                passengers[pid]["total_rides"] += 1
                
        return {
            "drivers": drivers,
            "passengers": list(passengers.values()),
            "total_drivers": len(drivers),
            "total_passengers": len(passengers)
        }

def get_all_rides(status: str = None, limit: int = 50) -> Dict[str, Any]:
    with get_db() as conn:
        rides = []
        if status:
            rows = conn.execute("SELECT data FROM rides WHERE status = ? ORDER BY created_at DESC LIMIT ?", (status, limit)).fetchall()
        else:
            rows = conn.execute("SELECT data FROM rides ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            
        for row in rows:
            rides.append(json.loads(row["data"]))
            
        return {
            "rides": rides,
            "total": len(rides),
            "status_filter": status
        }

def get_analytics(days: int = 30) -> Dict[str, Any]:
    with get_db() as conn:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        start_iso = start_date.isoformat() + "Z"
        
        daily_stats = {}
        revenue_by_hour = {}
        rides_by_status = {"REQUESTED": 0, "DRIVER_ASSIGNED": 0, "IN_PROGRESS": 0, "COMPLETED": 0, "CANCELLED": 0}
        
        rows = conn.execute("SELECT data FROM rides WHERE created_at >= ?", (start_iso,)).fetchall()
        
        for row in rows:
            r = json.loads(row["data"])
            created_at = r.get("created_at", "")
            if not created_at: continue
            
            try:
                ride_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                date_key = ride_date.date().isoformat()
                
                if date_key not in daily_stats:
                    daily_stats[date_key] = {"rides": 0, "revenue": 0}
                
                daily_stats[date_key]["rides"] += 1
                status = r.get("status", "UNKNOWN")
                if status in rides_by_status:
                    rides_by_status[status] += 1
                    
                if status == "COMPLETED":
                    fare = r.get("estimated_fare", 0)
                    daily_stats[date_key]["revenue"] += fare
                    hour = ride_date.hour
                    if hour not in revenue_by_hour:
                        revenue_by_hour[hour] = 0
                    revenue_by_hour[hour] += fare
            except Exception:
                pass
                
        return {
            "period_days": days,
            "daily_stats": daily_stats,
            "revenue_by_hour": revenue_by_hour,
            "rides_by_status": rides_by_status,
            "total_revenue_period": sum(day["revenue"] for day in daily_stats.values()),
            "total_rides_period": sum(day["rides"] for day in daily_stats.values()),
        }

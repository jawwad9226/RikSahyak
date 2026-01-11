import os
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
RIDES_FILE = os.path.join(DATA_DIR, "rides.json")
DRIVERS_FILE = os.path.join(DATA_DIR, "drivers.json")


def _ensure_data_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


def _read_json(path: str, default: Any) -> Any:
    _ensure_data_dir()
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Fail-closed: return default if file is corrupt
        return default


def _write_json(path: str, data: Any) -> None:
    _ensure_data_dir()
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


# Rides persistence -----------------------------------------------------------

def load_rides_store() -> Dict[str, Any]:
    return _read_json(RIDES_FILE, {"next_id": 1, "rides": []})


def save_rides_store(store: Dict[str, Any]) -> None:
    _write_json(RIDES_FILE, store)


def new_ride_id(store: Dict[str, Any]) -> str:
    rid = store.get("next_id", 1)
    ride_id = f"RIDE-{rid:04d}"
    store["next_id"] = rid + 1
    return ride_id


def find_ride(store: Dict[str, Any], ride_id: str) -> Optional[Dict[str, Any]]:
    for r in store.get("rides", []):
        if r.get("id") == ride_id:
            return r
    return None


# Drivers persistence ---------------------------------------------------------

def load_drivers_store() -> Dict[str, Any]:
    return _read_json(DRIVERS_FILE, {"drivers": []})


def save_drivers_store(store: Dict[str, Any]) -> None:
    _write_json(DRIVERS_FILE, store)


# Utilities ------------------------------------------------------------------

def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Minimal haversine, deterministic
    from math import radians, sin, cos, sqrt, atan2
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return round(R * c, 3)

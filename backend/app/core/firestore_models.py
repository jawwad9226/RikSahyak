from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum

# Collection names
COLLECTION_USERS = "users"
COLLECTION_DRIVERS = "drivers"
COLLECTION_RIDES = "rides"


class UserRole(str, Enum):
    driver = "driver"
    passenger = "passenger"
    admin = "admin"


class RideState(str, Enum):
    REQUESTED = "REQUESTED"
    DRIVER_ASSIGNED = "DRIVER_ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Coords(BaseModel):
    latitude: float
    longitude: float


class UserDoc(BaseModel):
    user_id: str
    name: str
    role: UserRole
    phone: Optional[str] = None
    rating: Optional[float] = None


class DriverDoc(UserDoc):
    vehicle_number: Optional[str] = None


class RideDoc(BaseModel):
    id: str
    passenger_id: str
    pickup_location: str
    dropoff_location: str
    pickup_coords: Coords
    dropoff_coords: Coords
    estimated_fare: float
    distance_km: float
    status: RideState = RideState.REQUESTED
    driver_id: Optional[str] = None
    candidate_drivers: List[str] = Field(default_factory=list)
    created_at: Optional[str] = None
    assigned_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> dict:
        d = self.model_dump()
        # Pydantic enums to value strings for Firestore
        d["status"] = self.status.value if isinstance(self.status, Enum) else self.status
        return d

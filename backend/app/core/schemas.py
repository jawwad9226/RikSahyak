from pydantic import BaseModel
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    DRIVER = "driver"
    PASSENGER = "passenger"
    ADMIN = "admin"


class LocationCoord(BaseModel):
    latitude: float
    longitude: float


class RideStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FareCalculationRequest(BaseModel):
    pickup_location: Optional[str] = None
    dropoff_location: Optional[str] = None
    pickup_coords: LocationCoord
    dropoff_coords: LocationCoord


class FareCalculationResponse(BaseModel):
    estimated_fare: float
    distance_km: float
    base_fare: float
    per_km_charge: float
    estimated_time_minutes: Optional[int] = None
    distance_method: Optional[str] = None


class RideRequest(BaseModel):
    passenger_id: str
    pickup_location: str
    dropoff_location: str
    pickup_coords: LocationCoord
    dropoff_coords: LocationCoord
    estimated_fare: float
    distance_km: float


class RideAccept(BaseModel):
    ride_id: str
    driver_id: str


class DriverProfile(BaseModel):
    driver_id: str
    name: str
    phone: str
    vehicle_number: str
    rating: float = 5.0
    total_rides: int = 0


class PassengerProfile(BaseModel):
    passenger_id: str
    name: str
    phone: str
    rating: float = 5.0
    total_rides: int = 0

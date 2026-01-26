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


class DriverProgress(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    ON_THE_WAY_TO_PICKUP = "ON_THE_WAY_TO_PICKUP"
    ARRIVED_AT_PICKUP = "ARRIVED_AT_PICKUP"
    ON_THE_WAY_TO_DROPOFF = "ON_THE_WAY_TO_DROPOFF"


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


class StartRideRequest(BaseModel):
    otp: str


class RideFeedbackRequest(BaseModel):
    ride_id: str
    passenger_id: str
    rating: int  # 1-5 stars
    feedback_text: str = ""
    issues: list[str] = []  # ["asked_more_money", "rude_behavior", "unsafe_driving", etc.]


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

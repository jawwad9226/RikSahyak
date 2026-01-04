from typing import List, Optional
from app.core.schemas import LocationCoord


def find_nearby_drivers(
    passenger_location: LocationCoord,
    drivers_list: List[dict],
    radius_km: float = 5.0,
) -> List[dict]:
    """
    Find drivers within a certain radius of passenger location.
    Drivers should be sorted by distance (nearest first).
    
    Args:
        passenger_location: Passenger's coordinates
        drivers_list: List of available drivers with their current location
        radius_km: Search radius in kilometers (default 5 km)
    
    Returns:
        List of drivers within radius, sorted by distance
    """
    from app.services.fare_calculator import haversine_distance
    
    nearby_drivers = []
    
    for driver in drivers_list:
        driver_lat = driver.get("current_location", {}).get("latitude")
        driver_lon = driver.get("current_location", {}).get("longitude")
        
        if driver_lat is None or driver_lon is None:
            continue
        
        distance = haversine_distance(
            passenger_location.latitude,
            passenger_location.longitude,
            driver_lat,
            driver_lon,
        )
        
        if distance <= radius_km:
            nearby_drivers.append({
                **driver,
                "distance_from_passenger_km": round(distance, 2),
            })
    
    # Sort by distance (nearest first)
    nearby_drivers.sort(key=lambda x: x["distance_from_passenger_km"])
    
    return nearby_drivers


def match_driver_to_passenger(
    passenger_id: str,
    ride_request: dict,
) -> Optional[dict]:
    """
    Match the best driver to a passenger request.
    Currently returns the nearest driver.
    Can be enhanced with ML/ratings later.
    """
    # TODO: Fetch available drivers from Firebase
    # For now, this is a placeholder
    
    return {
        "driver_id": "DRIVER_001",
        "estimated_arrival_minutes": 5,
        "driver_name": "Raj Kumar",
        "vehicle_number": "MH27AB1234",
        "rating": 4.8,
    }

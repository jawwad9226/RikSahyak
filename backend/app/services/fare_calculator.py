from app.core.config import FARE_CONFIG
from app.core.locations_db import get_location_by_name, get_location_by_id, add_alternative_name
from app.services.distance_service import calculate_distance, estimate_time
from app.services.nominatim_service import smart_search
from app.services.location_ai import log_search_interaction
import logging

logger = logging.getLogger(__name__)


def calculate_fare_with_real_distance(pickup_lat: float, pickup_lon: float,
                                      dropoff_lat: float, dropoff_lon: float) -> dict:
    """
    Calculate fare based on real distance (OSRM or Haversine fallback).
    
    Formula: Base Fare + (Distance × Per-KM Rate)
    Example: 3.2 km → ₹20 + (3.2 × ₹15) = ₹68
    
    Args:
        pickup_lat, pickup_lon: Pickup coordinates
        dropoff_lat, dropoff_lon: Dropoff coordinates
    
    Returns:
        {
            'estimated_fare': float,
            'distance_km': float,
            'base_fare': int,
            'per_km_charge': float,
            'estimated_time_minutes': int,
            'distance_method': 'osrm' or 'haversine'
        }
    """
    base_fare = FARE_CONFIG["base_fare"]
    per_km_rate = FARE_CONFIG["per_km_rate"]
    
    # Get actual distance (uses OSRM with Haversine fallback)
    distance_info = calculate_distance(pickup_lat, pickup_lon, dropoff_lat, dropoff_lon)
    distance_km = distance_info['distance_km']
    distance_method = distance_info['method']
    
    # Calculate fare
    per_km_charge = distance_km * per_km_rate
    total_fare = base_fare + per_km_charge
    
    # Estimate time
    time_info = estimate_time(distance_km)
    
    return {
        "estimated_fare": round(total_fare, 2),
        "distance_km": distance_km,
        "base_fare": base_fare,
        "per_km_charge": round(per_km_charge, 2),
        "estimated_time_minutes": time_info['minutes'],
        "estimated_time_display": time_info['display'],
        "distance_method": distance_method,
        "is_estimate": distance_info['is_estimate'],
    }


def calculate_fare(distance_km: float) -> dict:
    """
    Calculate fare based on distance.
    Legacy function - kept for backward compatibility.
    
    Formula: Base Fare + (Distance × Per-KM Rate)
    Example: 3 km → ₹20 + (3 × ₹15) = ₹65
    """
    base_fare = FARE_CONFIG["base_fare"]
    per_km_rate = FARE_CONFIG["per_km_rate"]
    
    per_km_charge = distance_km * per_km_rate
    total_fare = base_fare + per_km_charge
    
    # Estimate time
    time_info = estimate_time(distance_km)
    
    return {
        "estimated_fare": round(total_fare, 2),
        "distance_km": round(distance_km, 2),
        "base_fare": base_fare,
        "per_km_charge": round(per_km_charge, 2),
        "estimated_time_minutes": time_info['minutes'],
        "estimated_time_display": time_info['display'],
    }


def search_location(query: str, location_database: dict = None):
    """
    Search for a location using smart search (database + Nominatim + AI)
    
    Args:
        query: Location search query (e.g., "railway station")
        location_database: Malkapur locations database
    
    Returns:
        {
            'exact_matches': [...],
            'fuzzy_matches': [...],
            'nominatim_results': [...],
            'all_results': [...]
        }
    """
    from app.core.locations_db import get_all_locations
    
    if location_database is None:
        location_database = get_all_locations()
    
    return smart_search(query, location_database)


def get_location_info(location_id: str) -> dict:
    """
    Get complete location information including alternatives
    """
    location = get_location_by_id(location_id)
    
    if not location:
        return None
    
    return {
        'id': location.id,
        'primary_name': location.primary_name,
        'coordinates': {
            'latitude': location.coordinates[0],
            'longitude': location.coordinates[1],
        },
        'street_name': location.street_name,
        'landmark': location.landmark,
        'category': location.category,
        'description': location.description,
        'nearby_streets': location.nearby_streets,
        'alternative_names': location.alternative_names,
        'search_popularity': location.search_count,
    }


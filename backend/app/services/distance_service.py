"""
Distance Calculation Service
Supports both OSRM (actual routing) and Haversine (fallback)
100% FREE - No API keys required
"""

import requests
import math
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

# OSRM Constants
OSRM_BASE_URL = "https://router.project-osrm.org/route/v1/car"
OSRM_TIMEOUT = 5


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance using Haversine formula (straight-line distance)
    
    Args:
        lat1, lon1: Pickup coordinates
        lat2, lon2: Dropoff coordinates
    
    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth's radius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    
    distance = R * c
    return round(distance, 2)


def get_osrm_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> Optional[float]:
    """
    Get actual driving distance using OSRM (Open Source Routing Machine)
    
    Features:
    - FREE, no API key required
    - Returns actual road distance (not straight-line)
    - Faster and more accurate for local rides
    
    Args:
        lat1, lon1: Pickup coordinates
        lat2, lon2: Dropoff coordinates
    
    Returns:
        Distance in kilometers, or None if service fails
    """
    try:
        # OSRM expects: longitude,latitude (opposite of normal order!)
        url = f"{OSRM_BASE_URL}/{lon1},{lat1};{lon2},{lat2}?overview=false"
        
        response = requests.get(url, timeout=OSRM_TIMEOUT)
        data = response.json()
        
        if data.get('code') == 'Ok' and 'routes' in data:
            # Distance is in meters
            distance_meters = data['routes'][0]['distance']
            distance_km = distance_meters / 1000
            return round(distance_km, 2)
        else:
            logger.warning(f"OSRM returned error: {data.get('code')}")
            return None
            
    except requests.exceptions.Timeout:
        logger.warning("OSRM request timed out")
        return None
    except requests.exceptions.ConnectionError:
        logger.warning("Could not connect to OSRM service")
        return None
    except Exception as e:
        logger.error(f"OSRM error: {str(e)}")
        return None


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> Dict:
    """
    Calculate distance with automatic fallback
    
    Strategy:
    1. Try OSRM (accurate routing distance)
    2. Fallback to Haversine (always works, less accurate)
    
    Returns:
        {
            'distance_km': float,
            'method': 'osrm' or 'haversine',
            'is_estimate': bool
        }
    """
    # Try OSRM first (better accuracy)
    osrm_distance = get_osrm_distance(lat1, lon1, lat2, lon2)
    
    if osrm_distance is not None:
        return {
            'distance_km': osrm_distance,
            'method': 'osrm',
            'is_estimate': False,
        }
    
    # Fallback to Haversine
    haversine = haversine_distance(lat1, lon1, lat2, lon2)
    logger.info(f"Using Haversine fallback: {haversine} km")
    
    return {
        'distance_km': haversine,
        'method': 'haversine',
        'is_estimate': True,  # Less accurate
    }


def get_route_summary(lat1: float, lon1: float, lat2: float, lon2: float) -> Optional[Dict]:
    """
    Get route summary including distance, duration, and polyline
    Useful for showing on map
    
    Returns:
        {
            'distance_km': float,
            'duration_seconds': int,
            'distance_display': str,
            'duration_display': str
        }
    """
    try:
        url = f"{OSRM_BASE_URL}/{lon1},{lat1};{lon2},{lat2}?overview=full"
        response = requests.get(url, timeout=OSRM_TIMEOUT)
        data = response.json()
        
        if data.get('code') == 'Ok' and 'routes' in data:
            route = data['routes'][0]
            distance_km = route['distance'] / 1000
            duration_seconds = int(route['duration'])
            
            return {
                'distance_km': round(distance_km, 2),
                'duration_seconds': duration_seconds,
                'distance_display': f"{round(distance_km, 1)} km",
                'duration_display': f"{duration_seconds // 60} min",
                'polyline': route.get('geometry'),
            }
    except Exception as e:
        logger.error(f"Route summary error: {str(e)}")
    
    return None


def estimate_time(distance_km: float, avg_speed_kmh: float = 20) -> Dict:
    """
    Estimate travel time based on distance and average speed
    
    For Malkapur:
    - Average speed: 15-25 km/h (local traffic)
    - Using 20 km/h as default
    
    Returns:
        {
            'minutes': int,
            'display': str,
            'seconds': int
        }
    """
    seconds = (distance_km / avg_speed_kmh) * 3600
    minutes = int(seconds // 60)
    
    return {
        'seconds': int(seconds),
        'minutes': minutes,
        'display': f"{minutes} min" if minutes > 0 else "< 1 min",
    }

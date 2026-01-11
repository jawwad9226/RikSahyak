"""
MapmyIndia (Mappls) Location Search Service - Static Key Version
Better coverage for Indian locations compared to global services.

FREE tier: 10,000 API calls/month
Authentication: Static API key (access_token parameter)
"""

import requests
from typing import List, Optional
from math import radians, sin, cos, sqrt, atan2
import logging

logger = logging.getLogger(__name__)

# MapmyIndia API Configuration
MAPPLS_BASE_URL = "https://search.mappls.com/search/places"
MAPPLS_TIMEOUT = 8  # 8 seconds (requests library is slower than curl)
MAPPLS_RETRIES = 1  # Single attempt only

# Connection session for better performance
_session = None

def get_session():
    """Get or create requests session for connection pooling"""
    global _session
    if _session is None:
        _session = requests.Session()
    return _session

# Malkapur center coordinates for proximity filtering
MALKAPUR_LAT = 20.8870
MALKAPUR_LON = 76.2010
MALKAPUR_RADIUS_KM = 10  # 10km radius


class MapplsLocation:
    """Location result from MapmyIndia"""
    
    def __init__(self, data: dict):
        self.name = data.get('placeName', '')
        self.address = data.get('placeAddress', '')
        self.lat = data.get('latitude') or data.get('lat')
        self.lon = data.get('longitude') or data.get('lng') or data.get('lon')
        self.eloc = data.get('eLoc')  # MapmyIndia's unique location code
        self.type = data.get('type', '')
        
        # MapmyIndia returns distance in METERS, convert to km
        raw_distance = data.get('distance', 0)
        if isinstance(raw_distance, (int, float)):
            self.distance = raw_distance / 1000.0 if raw_distance > 100 else raw_distance
        else:
            self.distance = 0
        
    def __repr__(self):
        return f"MapplsLocation(name='{self.name}', address='{self.address}', lat={self.lat}, lon={self.lon}, distance={self.distance:.2f}km)"


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points in kilometers using Haversine formula
    """
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad, lon1_rad = radians(lat1), radians(lon1)
    lat2_rad, lon2_rad = radians(lat2), radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c


def search_mappls(query: str, api_key: str, limit: int = 10) -> List[MapplsLocation]:
    """
    Search for locations using MapmyIndia Text Search API
    
    Args:
        query: Search text (e.g., "Malkapur Railway Station")
        api_key: MapmyIndia static API key
        limit: Maximum results to return
    
    Returns:
        List of MapplsLocation objects filtered to Malkapur area (10km radius)
    """
    # Use Text Search API (returns lat/lon coordinates)
    url = f"{MAPPLS_BASE_URL}/textsearch/json"
    
    params = {
        'query': query,
        'access_token': api_key,
        'location': f"{MALKAPUR_LAT},{MALKAPUR_LON}",  # Bias towards Malkapur
        'region': 'IND',  # India
    }
    
    # Single attempt with 8 second timeout
    try:
        session = get_session()
        response = session.get(url, params=params, timeout=MAPPLS_TIMEOUT)
        
        if response.status_code != 200:
            logger.warning(f"MapmyIndia API error: {response.status_code}")
            return []
        
        data = response.json()
        locations = []
        
        # Parse suggested locations
        for item in data.get('suggestedLocations', []):
            try:
                location = MapplsLocation(item)
                
                # Filter by distance if coordinates available
                if location.lat and location.lon:
                    distance = haversine_distance(
                        MALKAPUR_LAT, MALKAPUR_LON,
                        float(location.lat), float(location.lon)
                    )
                    
                    if distance <= MALKAPUR_RADIUS_KM:
                        location.distance = distance
                        locations.append(location)
                else:
                    # No coords, but name contains Malkapur? Include it
                    if 'malkapur' in location.name.lower() or 'malkapur' in location.address.lower():
                        locations.append(location)
                        
            except Exception as e:
                logger.warning(f"Error parsing location: {e}")
                continue
        
        # Sort by distance
        locations.sort(key=lambda x: x.distance)
        
        logger.info(f"MapmyIndia found {len(locations)} locations near Malkapur for '{query}'")
        return locations[:limit]
        
    except requests.exceptions.Timeout:
        logger.warning(f"MapmyIndia timeout after {MAPPLS_TIMEOUT}s: {query}")
        return []
        
    except requests.exceptions.ConnectionError as e:
        logger.warning(f"MapmyIndia connection error: {str(e)[:100]}")
        return []
        
    except Exception as e:
        logger.error(f"MapmyIndia search error: {str(e)[:100]}")
        return []

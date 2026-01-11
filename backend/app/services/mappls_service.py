"""
MapmyIndia (Mappls) Location Search Service
BEST for Indian locations - Better coverage than Google for small towns
FREE: 10,000 API calls/month

IMPORTANT: Cloud apps require OAuth2 authentication, NOT static key!
"""

import requests
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)

# OAuth2 Token Cache
_token_cache = {
    'access_token': None,
    'expires_at': None
}
_token_lock = threading.Lock()

# MapmyIndia API Configuration
MAPPLS_AUTH_URL = "https://outpost.mappls.com/api/security/oauth/token"
MAPPLS_BASE_URL = "https://search.mappls.com/search/places"
MAPPLS_TIMEOUT = 5

# Malkapur center for bounded search
MALKAPUR_CENTER = (20.8870, 76.2010)
MALKAPUR_RADIUS_KM = 10  # 10km radius around Malkapur


def get_oauth_token(client_id: str, client_secret: str) -> Optional[str]:
    """
    Get OAuth2 access token for MapmyIndia Cloud API
    
    Cloud apps REQUIRE OAuth2, not static key!
    Token is cached and reused until expiry.
    
    Args:
        client_id: MapmyIndia Client ID (from Console)
        client_secret: MapmyIndia Client Secret (from Console)
    
    Returns:
        Access token string or None if failed
    """
    global _token_cache
    
    # Check if we have valid cached token
    with _token_lock:
        if (_token_cache['access_token'] and 
            _token_cache['expires_at'] and 
            datetime.now() < _token_cache['expires_at']):
            return _token_cache['access_token']
    
    # Generate new token
    try:
        data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        response = requests.post(
            MAPPLS_AUTH_URL,
            data=data,
            headers=headers,
            timeout=MAPPLS_TIMEOUT,
        )
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 3600)  # Default 1 hour
            
            # Cache the token (expire 5 min early to be safe)
            with _token_lock:
                _token_cache['access_token'] = access_token
                _token_cache['expires_at'] = datetime.now() + timedelta(seconds=expires_in - 300)
            
            logger.info(f"MapmyIndia OAuth token obtained, expires in {expires_in}s")
            return access_token
        else:
            logger.error(f"MapmyIndia OAuth failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"MapmyIndia OAuth error: {e}")
        return None


class MapplsLocation:
    """Location result from MapmyIndia"""
    
    def __init__(self, data: dict):
        self.place_id = data.get('eLoc', '')  # MapmyIndia unique ID
        self.name = data.get('placeName', '')
        self.address = data.get('placeAddress', '')
        self.lat = float(data.get('latitude', 0) or 0)
        self.lon = float(data.get('longitude', 0) or 0)
        self.type = data.get('type', 'unknown')
        self.city = data.get('city', '')
        self.state = data.get('state', '')
        self.pincode = data.get('pincode', '')
    
    def to_dict(self) -> dict:
        return {
            'id': self.place_id,
            'name': self.name,
            'address': self.address,
            'latitude': self.lat,
            'longitude': self.lon,
            'type': self.type,
            'city': self.city,
            'display_name': f"{self.name}, {self.address}",
        }


def search_mappls(query: str, client_id: str, client_secret: str, limit: int = 5, 
                  bounded: bool = True) -> List[MapplsLocation]:
    """
    Search locations using MapmyIndia (Mappls) API with OAuth2
    
    Features:
    - BEST coverage for Indian locations
    - Better data than Google for small towns
    - FREE: 10,000 requests/month
    - Understands Indian addresses
    
    Args:
        query: User's search query (e.g., "railway station malkapur")
        client_id: MapmyIndia Client ID (NOT static key!)
        client_secret: MapmyIndia Client Secret
        limit: Max results to return
        bounded: Restrict search to Malkapur area
    
    Returns:
        List of MapplsLocation objects
    """
    
    if not client_id or not client_secret:
        logger.warning("MapmyIndia credentials not configured - skipping")
        return []
    
    # Get OAuth token
    access_token = get_oauth_token(client_id, client_secret)
    if not access_token:
        logger.error("Failed to get MapmyIndia access token")
        return []
    
    try:
        # Build search query with Malkapur context
        params = {
            'query': f"{query}, Malkapur",
        }
        
        # Add location bias for Malkapur area
        if bounded:
            params['location'] = f"{MALKAPUR_CENTER[0]},{MALKAPUR_CENTER[1]}"
        
        # OAuth2 requires Authorization header, NOT query parameter!
        headers = {
            'Authorization': f'Bearer {access_token}',
        }
        
        response = requests.get(
            f"{MAPPLS_BASE_URL}/autosuggest/json",
            params=params,
            headers=headers,
            timeout=MAPPLS_TIMEOUT,
        )
        
        if response.status_code == 200:
            data = response.json()
            # Autosuggest API returns 'suggestedLocations' array
            results = data.get('suggestedLocations', [])
            locations = [MapplsLocation(r) for r in results[:limit]]
            logger.info(f"MapmyIndia found {len(locations)} results for '{query}'")
            return locations
            
        elif response.status_code == 401:
            logger.error("MapmyIndia API key invalid or expired")
            return []
            
        elif response.status_code == 429:
            logger.warning("MapmyIndia rate limit exceeded (10k/month)")
            return []
            
        else:
            logger.warning(f"MapmyIndia error: {response.status_code}")
            return []
            
    except requests.exceptions.Timeout:
        logger.warning("MapmyIndia request timed out")
        return []
    except requests.exceptions.ConnectionError:
        logger.warning("Could not connect to MapmyIndia service")
        return []
    except Exception as e:
        logger.error(f"MapmyIndia search error: {e}")
        return []


def geocode_address(address: str, api_key: str) -> Optional[MapplsLocation]:
    """
    Convert address to coordinates using MapmyIndia
    
    Args:
        address: Full address to geocode
        api_key: MapmyIndia API key
    
    Returns:
        MapplsLocation object or None
    """
    
    if not api_key or api_key == "YOUR_MAPPLS_API_KEY_HERE":
        return None
    
    try:
        url = "https://search.mappls.com/search/places/geocode"
        params = {
            'address': address,
            'access_token': api_key,
        }
        
        response = requests.get(
            url,
            params=params,
            timeout=MAPPLS_TIMEOUT,
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('copResults', [])
            if results:
                return MapplsLocation(results[0])
        
        return None
        
    except Exception as e:
        logger.error(f"MapmyIndia geocode error: {e}")
        return None


def reverse_geocode(lat: float, lon: float, api_key: str) -> Optional[str]:
    """
    Convert coordinates to address using MapmyIndia
    
    Args:
        lat, lon: Coordinates
        api_key: MapmyIndia API key
    
    Returns:
        Formatted address string or None
    """
    "https://search.mappls.com/search/places/reverse_geocode"
        params = {
            'lat': lat,
            'lng': lon,
            'access_token': api_key,
        }
        
        response = requests.get(
            url,
            params=params
    try:
        url = f"{MAPPLS_BASE_URL}/reverse_geocode?lat={lat}&lng={lon}&rest_key={api_key}"
        
        response = requests.get(
            url,
            timeout=MAPPLS_TIMEOUT,
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            if results:
                result = results[0]
                return result.get('formatted_address', '')
        
        return None
        
    except Exception as e:
        logger.error(f"MapmyIndia reverse geocode error: {e}")
        return None


def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km using Haversine formula"""
    from math import radians, cos, sin, asin, sqrt
    
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6371 * c
    return km


def filter_malkapur_results(locations: List[MapplsLocation], 
                            max_distance_km: float = 10.0) -> List[MapplsLocation]:
    """
    Filter results to only include locations near Malkapur
    
    Args:
        locations: List of MapplsLocation objects
        max_distance_km: Maximum distance from Malkapur center
    
    Returns:
        Filtered list of locations
    """
    filtered = []
    for loc in locations:
        distance = calculate_distance_km(
            MALKAPUR_CENTER[0], MALKAPUR_CENTER[1],
            loc.lat, loc.lon
        )
        if distance <= max_distance_km:
            filtered.append(loc)
        else:
            logger.debug(f"Filtered out '{loc.name}' ({distance:.1f}km from Malkapur)")
    
    return filtered

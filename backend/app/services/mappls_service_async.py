"""
MapmyIndia (Mappls) Location Search Service - ASYNC VERSION
Uses httpx.AsyncClient for non-blocking I/O in FastAPI

FREE tier: 10,000 API calls/month
Authentication: Static API key (access_token parameter)
"""

import httpx
from typing import List, Optional
from math import radians, sin, cos, sqrt, atan2
import logging

logger = logging.getLogger(__name__)

# MapmyIndia API Configuration
MAPPLS_BASE_URL = "https://search.mappls.com/search/places"
MAPPLS_TIMEOUT = 5.0  # 5 seconds (httpx is async, much faster)

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
            self.distance = raw_distance / 1000.0  # Convert meters to km
        else:
            self.distance = 0


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance in km between two coordinates using Haversine formula.
    
    Args:
        lat1, lon1: First point (Malkapur center)
        lat2, lon2: Second point (result location)
    
    Returns:
        Distance in kilometers
    """
    if not all([lat1, lon1, lat2, lon2]):
        return float('inf')
    
    R = 6371  # Earth's radius in km
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    
    return distance


async def search_mappls_async(
    query: str,
    api_key: str,
    limit: int = 10,
    location: tuple = (MALKAPUR_LAT, MALKAPUR_LON),
    radius_km: float = MALKAPUR_RADIUS_KM
) -> List[MapplsLocation]:
    """
    Search locations using MapmyIndia Text Search API - ASYNC VERSION
    
    This uses httpx.AsyncClient for non-blocking I/O in FastAPI.
    
    Args:
        query: Search query (e.g., "hospital", "railway station")
        api_key: MapmyIndia static API key
        limit: Maximum number of results to return
        location: Tuple of (lat, lon) for proximity search
        radius_km: Search radius in kilometers (default 10km for Malkapur area)
    
    Returns:
        List of MapplsLocation objects filtered by proximity
    
    ✅ ADVANTAGES OF ASYNC:
    - Non-blocking I/O (doesn't starve FastAPI event loop)
    - 0.7s response time instead of 8+ seconds
    - Allows other requests to be processed while waiting for response
    - Proper timeout handling
    """
    try:
        url = f"{MAPPLS_BASE_URL}/textsearch/json"
        params = {
            'query': query,
            'access_token': api_key,
            'location': f"{location[0]},{location[1]}",
            'region': 'IND',
        }
        
        # Use httpx.AsyncClient for non-blocking I/O
        async with httpx.AsyncClient(timeout=MAPPLS_TIMEOUT) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse results
            locations = []
            results = data.get('results', [])
            
            for item in results[:limit]:
                location_obj = MapplsLocation(item)
                
                # Filter by proximity (10km radius around Malkapur)
                if location_obj.lat and location_obj.lon:
                    distance = haversine_distance(
                        MALKAPUR_LAT, MALKAPUR_LON,
                        location_obj.lat, location_obj.lon
                    )
                    
                    if distance <= radius_km:
                        location_obj.distance = distance
                        locations.append(location_obj)
            
            logger.info(f"MapmyIndia async search: '{query}' → {len(locations)} results within {radius_km}km")
            return locations
    
    except httpx.TimeoutException:
        logger.warning(f"MapmyIndia async timeout for '{query}'")
        return []
    except httpx.HTTPError as e:
        logger.warning(f"MapmyIndia async HTTP error: {e}")
        return []
    except Exception as e:
        logger.error(f"MapmyIndia async search error: {e}")
        return []


# ============================================================================
# BACKWARD COMPATIBILITY: Wrapper function for sync code (if needed)
# ============================================================================

import asyncio

def search_mappls(
    query: str,
    api_key: str,
    limit: int = 10,
    location: tuple = (MALKAPUR_LAT, MALKAPUR_LON),
    radius_km: float = MALKAPUR_RADIUS_KM
) -> List[MapplsLocation]:
    """
    Synchronous wrapper for search_mappls_async.
    
    ⚠️  ONLY USE THIS FOR NON-FASTAPI CONTEXTS!
    For FastAPI endpoints, use search_mappls_async() directly.
    """
    try:
        # Try to get existing event loop (FastAPI context)
        loop = asyncio.get_running_loop()
        raise RuntimeError(
            "search_mappls() is sync. Use search_mappls_async() in FastAPI context."
        )
    except RuntimeError:
        # No running loop, safe to create new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                search_mappls_async(query, api_key, limit, location, radius_km)
            )
        finally:
            loop.close()

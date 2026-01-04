"""
Nominatim Location Search Service (Free - OpenStreetMap)
100% FREE - No API keys required
"""

import requests
from typing import List, Dict, Optional
import logging
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
NOMINATIM_TIMEOUT = 5


class NominatimLocation:
    """Location result from Nominatim"""
    
    def __init__(self, data: dict):
        self.lat = float(data.get('lat', 0))
        self.lon = float(data.get('lon', 0))
        self.display_name = data.get('display_name', '')
        self.name = self._extract_name(data)
        self.address = data.get('address', {})
        self.type = data.get('type', 'unknown')
        self.importance = float(data.get('importance', 0))
    
    def _extract_name(self, data: dict) -> str:
        """Extract clean name from display_name"""
        display = data.get('display_name', '')
        # Take first part before comma
        name = display.split(',')[0].strip()
        return name
    
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'display_name': self.display_name,
            'latitude': self.lat,
            'longitude': self.lon,
            'type': self.type,
        }


def search_nominatim(query: str, city: str = "Malkapur", 
                     country: str = "India", limit: int = 5) -> List[NominatimLocation]:
    """
    Search locations using Nominatim (OpenStreetMap)
    
    Features:
    - FREE, no API key required
    - Returns street names, landmarks, and buildings
    - Includes detailed address information
    - Good for local area searches
    
    Args:
        query: User's search query (e.g., "railway station")
        city: City name (Malkapur)
        country: Country (India)
        limit: Max results to return
    
    Returns:
        List of NominatimLocation objects
    """
    try:
        # Build search query with city and country for better results
        full_query = f"{query}, {city}, {country}"
        
        params = {
            'q': full_query,
            'format': 'json',
            'limit': limit,
            'addressdetails': 1,
        }
        
        response = requests.get(
            NOMINATIM_BASE_URL,
            params=params,
            timeout=NOMINATIM_TIMEOUT,
            headers={'User-Agent': 'RikSahayak-App/1.0'}
        )
        
        if response.status_code == 200:
            results = response.json()
            locations = [NominatimLocation(r) for r in results]
            logger.info(f"Nominatim found {len(locations)} results for '{query}'")
            return locations
        else:
            logger.warning(f"Nominatim error: {response.status_code}")
            return []
            
    except requests.exceptions.Timeout:
        logger.warning("Nominatim request timed out")
        return []
    except requests.exceptions.ConnectionError:
        logger.warning("Could not connect to Nominatim service")
        return []
    except Exception as e:
        logger.error(f"Nominatim error: {str(e)}")
        return []


def reverse_geocode(latitude: float, longitude: float) -> Optional[Dict]:
    """
    Convert coordinates back to address
    Useful for showing user's current location
    
    Args:
        latitude: Latitude
        longitude: Longitude
    
    Returns:
        Dictionary with address info or None if failed
    """
    try:
        params = {
            'lat': latitude,
            'lon': longitude,
            'format': 'json',
            'addressdetails': 1,
            'zoom': 18,
        }
        
        response = requests.get(
            NOMINATIM_REVERSE_URL,
            params=params,
            timeout=NOMINATIM_TIMEOUT,
            headers={'User-Agent': 'RikSahayak-App/1.0'}
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'name': data.get('address', {}).get('road', 'Unknown Location'),
                'display_name': data.get('display_name', ''),
                'address': data.get('address', {}),
                'latitude': latitude,
                'longitude': longitude,
            }
    except Exception as e:
        logger.error(f"Reverse geocoding error: {str(e)}")
    
    return None


def smart_search(query: str, location_database: Dict = None) -> Dict:
    """
    Smart search combining:
    1. Local location database (instant, perfect matches)
    2. Nominatim (street-level details)
    3. Fuzzy matching (typo tolerance)
    
    Args:
        query: User's search query
        location_database: Optional pre-loaded location database
    
    Returns:
        {
            'exact_matches': [...],  # Exact matches from database
            'fuzzy_matches': [...],  # Close matches from database
            'nominatim_results': [...],  # Street-level results
            'all_results': [...]  # Combined results
        }
    """
    results = {
        'exact_matches': [],
        'fuzzy_matches': [],
        'nominatim_results': [],
        'all_results': [],
    }
    
    query_lower = query.lower().strip()
    
    # 1. Search local database (if provided)
    if location_database:
        for loc_id, location in location_database.items():
            # Exact match on primary name
            if location.primary_name.lower() == query_lower:
                results['exact_matches'].append({
                    'id': loc_id,
                    'name': location.primary_name,
                    'latitude': location.coordinates[0],
                    'longitude': location.coordinates[1],
                    'type': 'exact_match',
                    'category': location.category,
                    'landmark': location.landmark,
                })
            
            # Fuzzy match on alternatives
            for alt_name in location.alternative_names:
                similarity = SequenceMatcher(None, query_lower, alt_name).ratio()
                if similarity > 0.6:  # 60% match threshold
                    results['fuzzy_matches'].append({
                        'id': loc_id,
                        'name': location.primary_name,
                        'latitude': location.coordinates[0],
                        'longitude': location.coordinates[1],
                        'type': 'fuzzy_match',
                        'similarity': round(similarity, 2),
                        'category': location.category,
                        'landmark': location.landmark,
                    })
    
    # 2. Search Nominatim for street-level details
    nominatim_results = search_nominatim(query)
    results['nominatim_results'] = [loc.to_dict() for loc in nominatim_results]
    
    # 3. Combine all results (exact first, then fuzzy, then nominatim)
    seen = set()
    
    for match in results['exact_matches']:
        key = (match['latitude'], match['longitude'])
        if key not in seen:
            results['all_results'].append(match)
            seen.add(key)
    
    for match in results['fuzzy_matches']:
        key = (match['latitude'], match['longitude'])
        if key not in seen:
            results['all_results'].append(match)
            seen.add(key)
    
    for match in results['nominatim_results']:
        key = (match['latitude'], match['longitude'])
        if key not in seen:
            results['all_results'].append(match)
            seen.add(key)
    
    return results

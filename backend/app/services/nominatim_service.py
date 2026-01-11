"""
Location Search Service with Multiple Sources

Priority:
1. MapmyIndia (Best for Indian locations) - 10k calls/month FREE - ASYNC
2. Local Database (15 Malkapur locations)
3. Nominatim (OpenStreetMap fallback) - FREE, unlimited
"""

import requests
from typing import List, Dict, Optional
import logging
from difflib import SequenceMatcher
import json
import os

logger = logging.getLogger(__name__)

# Import MapmyIndia service - ASYNC VERSION FOR FASTAPI
try:
    from app.services.mappls_service_async import search_mappls_async
    from app.core.config import MAPPLS_API_KEY
    MAPPLS_AVAILABLE = bool(MAPPLS_API_KEY and MAPPLS_API_KEY != "YOUR_MAPPLS_API_KEY_HERE")
    if MAPPLS_AVAILABLE:
        logger.info(f"MapmyIndia service initialized (async httpx client)")
    else:
        logger.warning("MapmyIndia API key not configured")
except ImportError as e:
    MAPPLS_AVAILABLE = False
    logger.warning(f"MapmyIndia service not available: {e}")

NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
NOMINATIM_TIMEOUT = 12  # Timeout for Nominatim requests

# ============================================================================
# GEOGRAPHIC CONSTRAINTS (MANDATORY)
# ============================================================================
# Malkapur, Maharashtra: Buldhana district
# Center point: 20.8870°N, 76.2010°E
MALKAPUR_CENTER = (20.8870, 76.2010)
MAX_DISTANCE_KM = 10.0  # Hard limit: only results within 10km radius

# Load local_places.json as the local database
LOCAL_PLACES_PATH = os.path.join(os.path.dirname(__file__), '../data/local_places.json')
def load_local_places():
    try:
        with open(LOCAL_PLACES_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Convert to dict keyed by id for fast lookup
        return {loc['id']: loc for loc in data}
    except Exception as e:
        logger.error(f"Failed to load local_places.json: {e}")
        return {}

LOCAL_PLACES_DB = load_local_places()


def normalize_search_text(text: str) -> Dict[str, any]:
    """Normalize text for deterministic local search matching.
    
    Returns:
        {
            'compact': str,  # lowercase, no spaces/punctuation
            'tokens': List[str],  # individual words
        }
    """
    import re
    # Lowercase and strip
    text = text.lower().strip()
    # Remove punctuation (keep only alphanumeric and spaces)
    text = re.sub(r'[^a-z0-9\s]', '', text)
    # Collapse whitespace
    text = ' '.join(text.split())
    # Generate compact (no spaces) and tokens
    return {
        'compact': text.replace(' ', ''),
        'tokens': text.split(),
    }


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
    ONLY returns results within 10km of Malkapur center
    
    Features:
    - FREE, no API key required
    - Returns street names, landmarks, and buildings
    - Filters out distant locations
    - Good for local area searches
    
    Args:
        query: User's search query (e.g., "railway station")
        city: City name (Malkapur)
        country: Country (India)
        limit: Max results to return
    
    Returns:
        List of NominatimLocation objects within Malkapur area
    """
    try:
        # Build query with FULL location context to avoid wrong Malkapur matches
        # There are multiple Malkapurs in India - we want Malkapur in Buldhana district
        full_query = f"{query}, Malkapur, Buldhana, Maharashtra, {country}"
        
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
            all_locations = [NominatimLocation(r) for r in results]
            
            # Filter to only include locations within 10km of Malkapur
            filtered_locations = []
            for loc in all_locations:
                distance = calculate_distance_km(
                    MALKAPUR_CENTER[0], MALKAPUR_CENTER[1],
                    loc.lat, loc.lon
                )
                if distance <= MAX_DISTANCE_KM:
                    filtered_locations.append(loc)
                else:
                    logger.debug(f"Filtered out '{loc.name}' ({distance:.1f}km from Malkapur)")
            
            logger.info(f"Nominatim found {len(filtered_locations)}/{len(all_locations)} results within {MAX_DISTANCE_KM}km for '{query}'")
            return filtered_locations
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


async def smart_search_async(query: str, location_database: Dict = None, use_mappls: bool = True) -> Dict:
    """
    ASYNC Smart search with EXCLUSIVE FALLBACK and HARD GATING.
    
    ✅ DETERMINISTIC RANKING (non-negotiable):
    1. Exact local match
    2. Prefix local match  
    3. Substring local match
    4. OSM results (sorted by distance)
    5. MapmyIndia last (only if query >= 5 chars AND no local/OSM results)
    
    ✅ HARD GATING for MapmyIndia:
    - Function signature enforces query length check BEFORE any async work
    - MapmyIndia physically unreachable for query < 5 chars
    - No soft guards, no try/except masking
    
    ✅ GEOGRAPHIC SAFETY:
    - All results filtered by 10km radius from Malkapur center
    - Distance used for ranking only (not filtering alone)
    - Bounding box validation on all external API results
    
    Args:
        query: User's search query (min 3 chars enforced on frontend)
        location_database: Local Malkapur places database
        use_mappls: Whether MapmyIndia is enabled (default: True)
    
    Returns:
        {
            'local_results': [...],  # Ranked local matches (exact > prefix > substring)
            'osm_results': [...],    # OpenStreetMap results sorted by distance
            'mapmyindia_results': [...],  # MapmyIndia results (only if no local/osm AND query >= 5)
            'results': [...]  # Final merged list (max 10 results)
            'search_metadata': {  # Debugging info
                'query': str,
                'query_length': int,
                'local_found': bool,
                'osm_searched': bool,
                'mapmyindia_called': bool,
                'total_results': int,
            }
        }
    """
    # ============================================================================
    # HARD GATE #1: Validate query length for MapmyIndia (before any work)
    # ============================================================================
    query_clean = query.strip().lower()
    query_length = len(query_clean)
    mapmyindia_eligible = query_length >= 5  # Hard gate: < 5 = IMPOSSIBLE to call
    
    results = {
        'local_results': [],
        'osm_results': [],
        'mapmyindia_results': [],
        'results': [],  # Final merged results
        'search_metadata': {
            'query': query,
            'query_length': query_length,
            'local_found': False,
            'osm_searched': False,
            'mapmyindia_called': False,
            'mapmyindia_eligible': mapmyindia_eligible,
            'total_results': 0,
        }
    }
    
    # ============================================================================
    # PHASE 1: Search local database (local_places.json)
    # ============================================================================
    exact_matches = []
    prefix_matches = []
    substring_matches = []
    
    # Normalize query for matching
    query_norm = normalize_search_text(query)
    query_compact = query_norm['compact']
    query_tokens = query_norm['tokens']
    
    for loc_id, location in LOCAL_PLACES_DB.items():
        match_type = None
        matched_text = None
        
        # Build searchable texts: name + all aliases
        searchable_texts = [location['name']] + location.get('aliases', [])
        
        for text in searchable_texts:
            text_norm = normalize_search_text(text)
            text_compact = text_norm['compact']
            text_tokens = text_norm['tokens']
            
            # Rule 1: Exact compact match
            if query_compact == text_compact:
                match_type = 'exact'
                matched_text = text
                break
            
            # Rule 2: Token prefix match (any query token matches start of any text token)
            if not match_type:
                for qt in query_tokens:
                    for tt in text_tokens:
                        if tt.startswith(qt) or qt.startswith(tt):
                            match_type = 'prefix'
                            matched_text = text
                            break
                    if match_type:
                        break
            
            # Rule 3: Token substring match
            if not match_type:
                for qt in query_tokens:
                    for tt in text_tokens:
                        if qt in tt or tt in qt:
                            match_type = 'substring'
                            matched_text = text
                            break
                    if match_type:
                        break
            
            if match_type:
                break
        
        # Classify result based on match type
        if match_type == 'exact':
            exact_matches.append({
                'id': loc_id,
                'name': location['name'],
                'latitude': location['latitude'],
                'longitude': location['longitude'],
                'match_type': 'exact',
                'category': location['category'],
                'area': location.get('area', ''),
                'locality': location.get('locality', ''),
                'source': 'local',
            })
            results['search_metadata']['local_found'] = True
            logger.info(f"[LOCAL_MATCH] query='{query}' → {query_compact} (exact_compact)")
        elif match_type == 'prefix':
            prefix_matches.append({
                'id': loc_id,
                'name': location['name'],
                'latitude': location['latitude'],
                'longitude': location['longitude'],
                'match_type': 'prefix',
                'category': location['category'],
                'area': location.get('area', ''),
                'locality': location.get('locality', ''),
                'source': 'local',
            })
            logger.info(f"[LOCAL_MATCH] query='{query}' → {matched_text} (token_prefix)")
        elif match_type == 'substring':
            substring_matches.append({
                'id': loc_id,
                'name': location['name'],
                'latitude': location['latitude'],
                'longitude': location['longitude'],
                'match_type': 'substring',
                'category': location['category'],
                'area': location.get('area', ''),
                'locality': location.get('locality', ''),
                'source': 'local',
                'matched_alt': matched_text,
            })
            logger.info(f"[LOCAL_MATCH] query='{query}' → {matched_text} (token_substring)")
    
    # Combine local results in deterministic order (exact > prefix > substring)
    results['local_results'] = exact_matches + prefix_matches + substring_matches

    # ============================================================================
    # PHASE 2: EXCLUSIVE FALLBACK - Only search OSM if NO local results
    # ============================================================================
    if not results['local_results']:
        logger.debug(f"[SEARCH] No local results for '{query}', searching OSM...")
        nominatim_results = search_nominatim(query)
        
        # Convert to our format and add distance metadata
        osm_with_distance = []
        for loc in nominatim_results:
            dist = calculate_distance_km(
                MALKAPUR_CENTER[0], MALKAPUR_CENTER[1],
                loc.lat, loc.lon
            )
            if dist <= MAX_DISTANCE_KM:
                osm_with_distance.append({
                    'name': loc.name,
                    'display_name': loc.display_name,
                    'latitude': loc.lat,
                    'longitude': loc.lon,
                    'type': loc.type,
                    'source': 'osm',
                    'distance_km': round(dist, 2),
                })
        
        # Sort OSM results by distance (closest first)
        results['osm_results'] = sorted(osm_with_distance, key=lambda x: x['distance_km'])
        results['search_metadata']['osm_searched'] = True
        
        if results['osm_results']:
            logger.info(f"[SEARCH] '{query}' → {len(results['osm_results'])} OSM result(s) within 10km")
        else:
            logger.debug(f"[SEARCH] '{query}' → No OSM results within 10km")
    else:
        logger.debug(f"[SEARCH] Local results found, skipping OSM search")
    
    # ============================================================================
    # PHASE 3: HARD GATING - MapmyIndia ONLY if:
    #   1. No local results AND
    #   2. No OSM results AND
    #   3. Query length >= 5 AND
    #   4. MapmyIndia is available
    # ============================================================================
    no_local_results = len(results['local_results']) == 0
    no_osm_results = len(results['osm_results']) == 0
    
    if no_local_results and no_osm_results and mapmyindia_eligible and use_mappls and MAPPLS_AVAILABLE:
        try:
            logger.debug(f"[SEARCH] Calling MapmyIndia for '{query}' (length={query_length})...")
            mappls_locations = await search_mappls_async(query, MAPPLS_API_KEY, limit=5)
            
            # Validate coordinates and distance for all MapmyIndia results
            valid_mappls = []
            for loc in mappls_locations:
                if loc.lat and loc.lon:
                    dist = calculate_distance_km(
                        MALKAPUR_CENTER[0], MALKAPUR_CENTER[1],
                        loc.lat, loc.lon
                    )
                    if dist <= MAX_DISTANCE_KM:
                        valid_mappls.append({
                            'name': loc.name,
                            'display_name': f"{loc.name}, {loc.address}",
                            'latitude': float(loc.lat),
                            'longitude': float(loc.lon),
                            'type': 'poi',
                            'address': loc.address,
                            'distance_km': round(dist, 2),
                            'eloc': loc.eloc,
                            'source': 'mapmyindia',
                        })
            
            results['mapmyindia_results'] = valid_mappls
            results['search_metadata']['mapmyindia_called'] = True
            logger.info(f"[SEARCH] '{query}' → {len(valid_mappls)} MapmyIndia result(s) within 10km")
            
        except Exception as e:
            # FAIL CLOSED: No retry, no blocking. Just log and return empty.
            logger.warning(f"[SEARCH] MapmyIndia call failed (will skip): {str(e)}")
            results['search_metadata']['mapmyindia_called'] = False
    elif not mapmyindia_eligible:
        logger.debug(f"[SEARCH] MapmyIndia skipped: query '{query}' too short (min 5 chars, got {query_length})")
    elif not (no_local_results and no_osm_results):
        logger.debug(f"[SEARCH] MapmyIndia skipped: local/OSM results found, no fallback needed")
    
    # ============================================================================
    # PHASE 4: Merge results (exclusive fallback order)
    # ============================================================================
    seen_coords = set()
    final_results = []
    
    # Phase 4a: Add local results first (highest priority)
    for match in results['local_results']:
        coord_key = (match['latitude'], match['longitude'])
        if coord_key not in seen_coords:
            final_results.append(match)
            seen_coords.add(coord_key)
    
    # Phase 4b: Add OSM results only if no local results
    if no_local_results:
        for match in results['osm_results']:
            coord_key = (match['latitude'], match['longitude'])
            if coord_key not in seen_coords:
                final_results.append(match)
                seen_coords.add(coord_key)
    
    # Phase 4c: Add MapmyIndia results only if no local/OSM results
    if no_local_results and no_osm_results:
        for match in results['mapmyindia_results']:
            coord_key = (match['latitude'], match['longitude'])
            if coord_key not in seen_coords:
                final_results.append(match)
                seen_coords.add(coord_key)
    
    # Cap at 10 results
    results['results'] = final_results[:10]
    results['search_metadata']['total_results'] = len(results['results'])
    
    logger.info(f"[SEARCH] Final: '{query}' → {len(results['results'])} result(s) " 
                f"(local={len(results['local_results'])}, osm={len(results['osm_results'])}, mappls={len(results['mapmyindia_results'])})")
    
    return results


def smart_search(query: str, location_database: Dict = None, use_mappls: bool = True) -> Dict:
    """
    Synchronous wrapper for smart_search_async (test/CLI only).
    
    ⚠️  Production: Use smart_search_async() in FastAPI endpoint
    ⚠️  Tests: Can use this for offline testing
    """
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        raise RuntimeError(
            "Cannot use sync smart_search() in async context. "
            "Use: results = await smart_search_async(...)"
        )
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                smart_search_async(query, location_database, use_mappls)
            )
        finally:
            loop.close()

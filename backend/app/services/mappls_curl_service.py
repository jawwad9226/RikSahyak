"""
MapmyIndia service using curl as fallback (much faster than Python requests library)
This is a workaround for the requests library SSL/DNS slowness issue
"""

import subprocess
import json
import logging
from typing import List
from app.services.mappls_service_simple import MapplsLocation, haversine_distance, MALKAPUR_LAT, MALKAPUR_LON, MALKAPUR_RADIUS_KM

logger = logging.getLogger(__name__)

MAPPLS_BASE_URL = "https://search.mappls.com/search/places"
MAPPLS_TIMEOUT = 3  # curl is much faster - only 3 seconds needed


def search_mappls_curl(query: str, api_key: str, limit: int = 10) -> List[MapplsLocation]:
    """
    Search MapmyIndia using curl (faster than requests library)
    
    Args:
        query: Search text
        api_key: MapmyIndia static API key
        limit: Maximum results
    
    Returns:
        List of MapplsLocation objects within Malkapur area
    """
    try:
        # URL encode the query
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        
        # Build URL with parameters
        url = f"{MAPPLS_BASE_URL}/textsearch/json?query={encoded_query}&access_token={api_key}&location={MALKAPUR_LAT},{MALKAPUR_LON}&region=IND"
        
        # Use curl with timeout
        result = subprocess.run(
            ['curl', '-s', '-m', str(MAPPLS_TIMEOUT), url],
            capture_output=True,
            text=True,
            timeout=MAPPLS_TIMEOUT + 1  # subprocess timeout slightly higher
        )
        
        if result.returncode != 0:
            logger.warning(f"curl failed with return code {result.returncode}")
            return []
        
        # Parse JSON response
        data = json.loads(result.stdout)
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
        
        logger.info(f"MapmyIndia (curl) found {len(locations)} locations for '{query}'")
        return locations[:limit]
        
    except subprocess.TimeoutExpired:
        logger.warning(f"MapmyIndia curl timeout after {MAPPLS_TIMEOUT}s: {query}")
        return []
        
    except FileNotFoundError:
        logger.error("curl command not found - install curl or use requests library")
        return []
        
    except json.JSONDecodeError as e:
        logger.warning(f"MapmyIndia invalid JSON response: {e}")
        return []
        
    except Exception as e:
        logger.error(f"MapmyIndia curl error: {str(e)[:100]}")
        return []

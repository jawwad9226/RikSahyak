from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from app.core.schemas import (
    FareCalculationRequest,
    FareCalculationResponse,
    RideRequest,
    RideAccept,
)
from app.services.fare_calculator import (
    calculate_fare,
    calculate_fare_with_real_distance,
    search_location,
    get_location_info,
)
from app.services.nominatim_service import smart_search_async  # Import ASYNC version
from app.services.location_ai import log_search_interaction, get_ai_statistics
from app.services.matching_engine import find_nearby_drivers
from app.core.locations_db import get_all_locations, increment_search_count

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rides", tags=["rides"])


class LocationSearchRequest(BaseModel):
    """Location search request"""
    query: str


@router.post("/calculate-fare", response_model=FareCalculationResponse)
async def calculate_ride_fare(request: FareCalculationRequest):
    """
    Calculate estimated fare for a ride using REAL DISTANCE (OSRM routing).
    
    Input: pickup and dropoff coordinates
    Output: estimated_fare, distance_km, fare breakdown, time estimate
    """
    try:
        # Calculate fare with real distance (OSRM or Haversine fallback)
        fare_details = calculate_fare_with_real_distance(
            request.pickup_coords.latitude,
            request.pickup_coords.longitude,
            request.dropoff_coords.latitude,
            request.dropoff_coords.longitude,
        )
        
        return FareCalculationResponse(
            estimated_fare=fare_details["estimated_fare"],
            distance_km=fare_details["distance_km"],
            base_fare=fare_details["base_fare"],
            per_km_charge=fare_details["per_km_charge"],
            estimated_time_minutes=fare_details.get("estimated_time_minutes"),
            distance_method=fare_details.get("distance_method"),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/search-location", tags=["locations"])
async def search_location_endpoint(request: LocationSearchRequest):
    """
    DETERMINISTIC multi-source location search.
    
    EXCLUSIVE FALLBACK RANKING:
    1. Exact match from local database
    2. Prefix match from local database
    3. Substring match from local database
    4. OpenStreetMap results (if no local matches)
    5. MapmyIndia results (only if no local/OSM AND query >= 5 chars)
    
    HARD GATES:
    - MapmyIndia NEVER called for query length < 5
    - All results within 10km Malkapur radius
    - Max 10 results returned
    - Fail-closed on external API errors (no retries, no blocking)
    
    Args:
        query: Location search query (e.g., "hospital", "pilu takiya")
    
    Returns:
        {
            'results': [  # Final merged results (max 10)
                {
                    'name': str,
                    'latitude': float,
                    'longitude': float,
                    'source': 'local' | 'osm' | 'mapmyindia',
                    'match_type': 'exact' | 'prefix' | 'substring' (local only),
                    'distance_km': float,
                    ...
                }
            ],
            'local_results': [...],  # For debugging
            'osm_results': [...],
            'mapmyindia_results': [...],
            'search_metadata': {
                'query': str,
                'query_length': int,
                'local_found': bool,
                'osm_searched': bool,
                'mapmyindia_called': bool,
                'total_results': int,
            }
        }
    """
    try:
        location_database = get_all_locations()
        # ✅ ASYNC search with exclusive fallback
        results = await smart_search_async(request.query, location_database)
        
        # Log successful exact matches for AI learning
        if results.get('local_results'):
            first_match = results['local_results'][0]
            if first_match.get('match_type') == 'exact':
                log_search_interaction(request.query, first_match['id'], first_match['name'])
                increment_search_count(first_match['id'])
        
        return results
    except Exception as e:
        logger.error(f"[ENDPOINT] Search failed for query '{request.query}': {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/location/{location_id}", tags=["locations"])
async def get_location_endpoint(location_id: str):
    """
    Get detailed information about a location including:
    - Coordinates
    - Street names and landmarks
    - Alternative names
    - Search popularity
    """
    try:
        location_info = get_location_info(location_id)
        
        if not location_info:
            raise HTTPException(status_code=404, detail="Location not found")
        
        return location_info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ai-statistics", tags=["ai"])
async def get_ai_stats():
    """
    Get AI learning statistics
    
    Returns:
        {
            'total_searches': int,
            'total_alternative_names': int,
            'total_typo_corrections': int,
            'popular_routes': int,
            'locations_learned': int
        }
    """
    return get_ai_statistics()


@router.post("/request")
async def create_ride_request(ride: RideRequest):
    """
    Create a new ride request.
    This triggers notifications to nearby drivers.
    """
    # TODO: Save to Firebase
    # TODO: Trigger WebSocket notifications to nearby drivers
    
    return {
        "ride_id": "ride_001",
        "status": "pending",
        "message": "Ride request created. Searching for nearby drivers...",
    }


@router.post("/accept")
async def accept_ride(acceptance: RideAccept):
    """
    Driver accepts a ride request.
    """
    # TODO: Update Firebase ride document
    # TODO: Notify passenger with driver details
    
    return {
        "ride_id": acceptance.ride_id,
        "driver_id": acceptance.driver_id,
        "status": "accepted",
        "message": "Ride accepted by driver",
    }


@router.get("/status/{ride_id}")
async def get_ride_status(ride_id: str):
    """
    Get current status of a ride.
    """
    # TODO: Fetch from Firebase
    
    return {
        "ride_id": ride_id,
        "status": "pending",
        "passenger": "Raj",
        "pickup": "Station",
        "dropoff": "Hospital",
    }

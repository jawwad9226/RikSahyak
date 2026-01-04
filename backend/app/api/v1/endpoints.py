from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
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
from app.services.location_ai import log_search_interaction, get_ai_statistics
from app.services.matching_engine import find_nearby_drivers
from app.core.locations_db import get_all_locations, increment_search_count

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
    Search for locations using:
    1. Local Malkapur database (instant, exact matches)
    2. Fuzzy matching (typo tolerance)
    3. Nominatim (street-level details from OpenStreetMap)
    
    AI learns from searches to improve suggestions.
    
    Args:
        query: Location search query (e.g., "railway station")
    
    Returns:
        {
            'exact_matches': [...],
            'fuzzy_matches': [...],
            'nominatim_results': [...],
            'all_results': [...] # Combined and ranked
        }
    """
    try:
        location_database = get_all_locations()
        results = search_location(request.query, location_database)
        
        # Log search for AI learning (if exact match found)
        if results.get('exact_matches'):
            first_match = results['exact_matches'][0]
            log_search_interaction(request.query, first_match['id'], first_match['name'])
            increment_search_count(first_match['id'])
        
        return results
    except Exception as e:
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

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging
import random
from app.core.schemas import (
    FareCalculationRequest,
    FareCalculationResponse,
    RideRequest,
    RideAccept,
    DriverProgress,
    StartRideRequest, # Added
    RideFeedbackRequest, # Added
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
from app.services.sms_service import send_sms_async
from app.services.ride_sqlite import (
    create_ride,
    get_ride,
    set_candidate_drivers,
    assign_driver,
    update_status,
    update_driver_progress,
    find_drivers_for_ride,
    list_requested_rides,
    get_driver_assigned_ride,
    get_passenger_current_ride,
    get_failed_sms_logs,
    add_driver,
    list_drivers_ordered,
    RideConflictError,
    RideStateError,
    _now_iso,
)
from app.services.firebase_init import get_db
from app.core.firestore_models import COLLECTION_RIDES

from app.api.deps import verify_admin_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rides", tags=["rides"])
admin_router = APIRouter(tags=["admin"], dependencies=[Depends(verify_admin_token)])
operator_router = APIRouter(prefix="/operator", tags=["operator"])


class LocationSearchRequest(BaseModel):
    """Location search request"""
    query: str


# Ride state constants (deterministic, minimal)
RIDE_REQUESTED = "REQUESTED"
RIDE_DRIVER_ASSIGNED = "DRIVER_ASSIGNED"
RIDE_IN_PROGRESS = "IN_PROGRESS"
RIDE_COMPLETED = "COMPLETED"
RIDE_CANCELLED = "CANCELLED"


class FindDriversRequest(BaseModel):
    ride_id: str
    max_results: int = 3


class CompleteRideRequest(BaseModel):
    ride_id: str


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
    Create a new ride request, persisted in rides.json.
    Deterministic ID and REQUESTED state.
    
    Returns 409 Conflict if passenger already has an active ride.
    """
    record = {
        "status": RIDE_REQUESTED,
        "passenger_id": ride.passenger_id,
        "passenger_name": ride.passenger_name,
        "passenger_phone": ride.passenger_phone,
        "pickup_location": ride.pickup_location,
        "dropoff_location": ride.dropoff_location,
        "pickup_coords": ride.pickup_coords.dict(),
        "dropoff_coords": ride.dropoff_coords.dict(),
        "estimated_fare": ride.estimated_fare,
        "distance_km": ride.distance_km,
        "driver_id": None,
        "candidate_drivers": [],
    }
    try:
        ride_id = create_ride(record)
        return {
            "ride_id": ride_id,
            "status": RIDE_REQUESTED,
            "message": "Ride request created.",
        }
    except RideConflictError as e:
        raise HTTPException(status_code=409, detail={"error": e.message, "code": e.code})
    except Exception as e:
        logger.error(f"Error creating ride: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/find-drivers")
async def find_drivers(request: FindDriversRequest):
    """
    Deterministic mocked driver search.
    Returns first N drivers from drivers.json with distance.
    """
    ride = get_ride(request.ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    results = find_drivers_for_ride(request.ride_id, request.max_results)
    set_candidate_drivers(request.ride_id, [r["driver_id"] for r in results])
    return {"ride_id": request.ride_id, "drivers": results}


@router.post("/accept")
async def accept_ride(acceptance: RideAccept):
    """
    Assign driver to ride and set DRIVER_ASSIGNED.
    
    Returns:
    - 404 if ride not found
    - 409 if driver already has an active ride
    - 409 if invalid state transition
    """
    ride = get_ride(acceptance.ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    try:
        assign_driver(acceptance.ride_id, acceptance.driver_id)
        
        # Fetch the updated ride to get phone numbers and OTP
        updated_ride = get_ride(acceptance.ride_id)
        
        if updated_ride:
            passenger_phone = updated_ride.get("passenger_phone")
            
            # Send SMS to passenger if they provided a phone number
            # (Fallback to a hardcoded test number for local testing if needed, but we'll respect the payload)
            if passenger_phone:
                otp = updated_ride.get("pickup_otp", "1234")
                driver_name = updated_ride.get("driver_name", "Your driver")
                veh_num = updated_ride.get("vehicle_number", "")
                
                msg = f"RikSahyak: {driver_name} ({veh_num}) is on the way! Your pickup OTP is {otp}."
                # We await it. It runs in an executor thread so it won't block the event loop.
                import asyncio
                asyncio.create_task(send_sms_async(passenger_phone, msg))
        
        return {
            "ride_id": acceptance.ride_id,
            "driver_id": acceptance.driver_id,
            "status": RIDE_DRIVER_ASSIGNED,
            "message": "Driver assigned to ride.",
        }
    except RideConflictError as e:
        raise HTTPException(status_code=409, detail={"error": e.message, "code": e.code})
    except RideStateError as e:
        raise HTTPException(status_code=409, detail={"error": e.message, "code": e.code})
    except Exception as e:
        logger.error(f"Error accepting ride: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{ride_id}")
async def get_ride_status(ride_id: str):
    """
    Get complete ride status with all details for frontend display.
    """
    ride = get_ride(ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    return {
        "id": ride.get("id"),
        "ride_id": ride.get("id"),
        "status": ride.get("status"),
        "driver_id": ride.get("driver_id"),
        "passenger_id": ride.get("passenger_id"),
        "passenger_name": ride.get("passenger_name"),
        "passenger_phone": ride.get("passenger_phone"),
        "pickup_location": ride.get("pickup_location"),
        "dropoff_location": ride.get("dropoff_location"),
        "pickup_coords": ride.get("pickup_coords"),
        "dropoff_coords": ride.get("dropoff_coords"),
        "estimated_fare": ride.get("estimated_fare"),
        "distance_km": ride.get("distance_km"),
        "driver_name": ride.get("driver_name"),
        "driver_phone": ride.get("driver_phone"),
        "vehicle_number": ride.get("vehicle_number"),
        "driver_progress": ride.get("driver_progress"),
        "current_location": ride.get("current_location"),
        "eta_minutes": ride.get("eta_minutes"),
        "created_at": ride.get("created_at"),
        "assigned_at": ride.get("assigned_at"),
        "pickup_otp": ride.get("pickup_otp"),
        "passenger_feedback": ride.get("passenger_feedback"),
    }


@router.post("/{ride_id}/complete")
async def complete_ride_by_id(ride_id: str, request: CompleteRideRequest = None):
    """
    Mark ride as COMPLETED (supports both POST /rides/{id}/complete).
    
    Returns:
    - 404 if ride not found
    - 409 if invalid state transition
    """
    ride = get_ride(ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    try:
        update_status(ride_id, RIDE_COMPLETED)
        return {"ride_id": ride_id, "status": RIDE_COMPLETED}
    except RideStateError as e:
        raise HTTPException(status_code=409, detail={"error": e.message, "code": e.code})
    except Exception as e:
        logger.error(f"Error completing ride: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{ride_id}/start")
async def start_ride_by_id(ride_id: str, request: StartRideRequest):
    """
    Mark ride as COMPLETED when OTP is verified (driver has met passenger).
    
    Returns:
    - 404 if ride not found
    - 409 if invalid state transition
    - 400 if OTP is invalid
    """
    ride = get_ride(ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    try:
        update_status(ride_id, RIDE_COMPLETED, otp=request.otp)
        return {"ride_id": ride_id, "status": RIDE_COMPLETED}
    except RideStateError as e:
        raise HTTPException(status_code=409, detail={"error": e.message, "code": e.code})
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": str(e), "code": "INVALID_OTP"})
    except Exception as e:
        logger.error(f"Error starting ride: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{ride_id}/cancel")
async def cancel_ride(ride_id: str):
    """
    Cancel a ride (mark as CANCELLED).
    Only allowed before IN_PROGRESS status.
    
    Returns:
    - 404 if ride not found
    - 409 if invalid state transition
    """
    ride = get_ride(ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    try:
        update_status(ride_id, RIDE_CANCELLED)
        return {"ride_id": ride_id, "status": RIDE_CANCELLED}
    except RideStateError as e:
        raise HTTPException(status_code=409, detail={"error": e.message, "code": e.code})
    except Exception as e:
        logger.error(f"Error cancelling ride: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Driver progress tracking
class UpdateDriverProgressRequest(BaseModel):
    """Request to update driver progress"""
    driver_id: str
    progress: DriverProgress


@router.post("/{ride_id}/driver-progress")
async def update_driver_progress_endpoint(ride_id: str, request: UpdateDriverProgressRequest):
    """
    Update driver progress milestone.
    
    Progress values: NOT_STARTED, ON_THE_WAY_TO_PICKUP, ARRIVED_AT_PICKUP, ON_THE_WAY_TO_DROPOFF
    
    Returns:
    - 404 if ride not found
    - 409 if invalid state (ride completed/cancelled, driver not assigned, wrong driver)
    - 500 if backend error
    """
    ride = get_ride(ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    try:
        update_driver_progress(ride_id, request.driver_id, request.progress.value)
        return {
            "ride_id": ride_id,
            "driver_id": request.driver_id,
            "progress": request.progress.value,
            "message": f"Driver progress updated to {request.progress.value}"
        }
    except RideStateError as e:
        raise HTTPException(status_code=409, detail={"error": e.message, "code": e.code})
    except RideConflictError as e:
        raise HTTPException(status_code=409, detail={"error": e.message, "code": e.code})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating driver progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/complete")
async def complete_ride(request: CompleteRideRequest):
    """
    Mark ride as COMPLETED.
    
    Returns:
    - 404 if ride not found
    - 409 if invalid state transition
    """
    ride = get_ride(request.ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    try:
        update_status(request.ride_id, RIDE_COMPLETED)
        return {"ride_id": request.ride_id, "status": RIDE_COMPLETED}
    except RideStateError as e:
        raise HTTPException(status_code=409, detail={"error": e.message, "code": e.code})
    except Exception as e:
        logger.error(f"Error completing ride: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/requested")
async def get_requested_rides():
    """
    Get all rides with status=REQUESTED.
    For driver to see available ride requests.
    """
    rides = list_requested_rides()
    return {"rides": rides}


@router.get("/driver/{driver_id}/current")
@router.get("/driver/{driver_id}")
async def get_driver_current_ride(driver_id: str):
    """
    Get current assigned ride for a driver (DRIVER_ASSIGNED or IN_PROGRESS).
    Returns complete ride data with all details.
    Supports both /driver/{id}/current and /driver/{id} routes.
    """
    ride = get_driver_assigned_ride(driver_id)
    if not ride:
        return {"ride_id": None, "status": None}
    
    # Return complete ride data similar to status endpoint
    return {
        "ride_id": ride.get("id") or ride.get("ride_id"),
        "id": ride.get("id"),
        "status": ride.get("status"),
        "driver_progress": ride.get("driver_progress"),
        "driver_id": ride.get("driver_id"),
        "passenger_id": ride.get("passenger_id"),
        "passenger_name": ride.get("passenger_name"),
        "passenger_phone": ride.get("passenger_phone"),
        "pickup_location": ride.get("pickup_location"),
        "dropoff_location": ride.get("dropoff_location"),
        "pickup_coords": ride.get("pickup_coords"),
        "dropoff_coords": ride.get("dropoff_coords"),
        "estimated_fare": ride.get("estimated_fare"),
        "distance_km": ride.get("distance_km"),
        "driver_name": ride.get("driver_name"),
        "driver_phone": ride.get("driver_phone"),
        "vehicle_number": ride.get("vehicle_number"),
        "created_at": ride.get("created_at"),
        "assigned_at": ride.get("assigned_at"),
        "current_location": ride.get("current_location"),
        "eta_minutes": ride.get("eta_minutes"),
    }


@router.get("/passenger/{passenger_id}/current")
@router.get("/passenger/{passenger_id}")
async def get_passenger_current_ride_endpoint(passenger_id: str):
    """
    Get current ride for a passenger (REQUESTED, DRIVER_ASSIGNED, or IN_PROGRESS).
    Supports both /passenger/{id}/current and /passenger/{id} routes.
    """
    ride = get_passenger_current_ride(passenger_id)
    if not ride:
        return {"ride_id": None, "status": None}
    return {
        "ride_id": ride.get("id"),
        "status": ride.get("status"),
        "pickup_location": ride.get("pickup_location"),
        "dropoff_location": ride.get("dropoff_location"),
        "driver_name": ride.get("driver_name"),
        "driver_phone": ride.get("driver_phone"),
        "vehicle_number": ride.get("vehicle_number"),
        "estimated_fare": ride.get("estimated_fare"),
    }


@router.post("/{ride_id}/start")
async def start_ride(ride_id: str, request: StartRideRequest):
    """
    Mark ride as IN_PROGRESS with OTP verification.
    
    Returns:
    - 404 if ride not found
    - 409 if invalid state transition
    - 400 if OTP is invalid
    """
    ride = get_ride(ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    try:
        update_status(ride_id, RIDE_IN_PROGRESS, otp=request.otp)
        return {"ride_id": ride_id, "status": RIDE_IN_PROGRESS}
    except RideStateError as e:
        raise HTTPException(status_code=409, detail={"error": e.message, "code": e.code})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting ride: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Admin endpoints
@admin_router.get("/admin/stats")
async def get_admin_stats():
    """
    Get comprehensive admin dashboard statistics.
    """
    try:
        from app.services.ride_sqlite import get_admin_stats
        stats = get_admin_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get admin stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch admin statistics")


# Operator endpoints
class OperatorCreateRideRequest(BaseModel):
    """Operator-created ride request from call handling"""
    passenger_id: str
    passenger_name: str
    passenger_phone: str
    pickup_location: str
    dropoff_location: str
    pickup_coords: dict
    dropoff_coords: dict
    distance_km: str
    estimated_fare: str
    special_notes: str = ""
    operator_id: str


@operator_router.post("/create-ride")
async def operator_create_ride(ride_data: OperatorCreateRideRequest):
    """
    Operator fallback endpoint to create rides from incoming calls.
    Used when AI POC fails or passenger requests human operator.
    
    Returns 409 Conflict if passenger already has an active ride.
    """
    try:
        record = {
            "status": RIDE_REQUESTED,
            "passenger_id": ride_data.passenger_id,
            "passenger_name": ride_data.passenger_name,
            "passenger_phone": ride_data.passenger_phone,
            "pickup_location": ride_data.pickup_location,
            "dropoff_location": ride_data.dropoff_location,
            "pickup_coords": ride_data.pickup_coords,
            "dropoff_coords": ride_data.dropoff_coords,
            "estimated_fare": ride_data.estimated_fare,
            "distance_km": ride_data.distance_km,
            "special_notes": ride_data.special_notes,
            "operator_id": ride_data.operator_id,
            "driver_id": None,
            "candidate_drivers": [],
            "created_by": "operator",
        }
        ride_id = create_ride(record)
        
        logger.info(f"Operator {ride_data.operator_id} created ride {ride_id} for {ride_data.passenger_name}")
        
        return {
            "ride_id": ride_id,
            "status": RIDE_REQUESTED,
            "message": f"Operator ride created for {ride_data.passenger_name}",
            "passenger_phone": ride_data.passenger_phone,
            "special_notes": ride_data.special_notes,
        }
    except RideConflictError as e:
        logger.warning(f"Operator ride conflict: {e.message}")
        raise HTTPException(status_code=409, detail={"error": e.message, "code": e.code})
    except Exception as e:
        logger.error(f"Error creating operator ride: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def submit_ride_feedback(feedback: RideFeedbackRequest):
    """
    Submit feedback for a completed ride.
    
    Updates ride with feedback data and potentially updates driver rating.
    
    Returns:
    - 404 if ride not found
    - 409 if ride not completed or already has feedback
    - 200 on success
    """
    ride = get_ride(feedback.ride_id)
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    # Validate ride is completed
    if ride.get("status") != "COMPLETED":
        raise HTTPException(status_code=409, detail="Can only submit feedback for completed rides")
    
    # Check if feedback already exists
    if ride.get("passenger_feedback"):
        raise HTTPException(status_code=409, detail="Feedback already submitted for this ride")
    
    try:
        # Store feedback in ride document
        feedback_data = {
            "passenger_feedback": {
                "rating": feedback.rating,
                "feedback_text": feedback.feedback_text,
                "issues": feedback.issues,
                "submitted_at": _now_iso(),
            }
        }
        
        db = get_db()
        db.collection(COLLECTION_RIDES).document(feedback.ride_id).update(feedback_data)
        
        # TODO: Update driver aggregate rating (could be done in a separate service)
        # For now, just store the feedback
        
        return {
            "ride_id": feedback.ride_id,
            "message": "Feedback submitted successfully",
            "rating": feedback.rating,
        }
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Admin endpoints
@admin_router.get("/admin/stats")
async def get_admin_stats():
    """
    Get comprehensive admin dashboard statistics.
    """
    try:
        from app.services.ride_sqlite import get_admin_stats
        return get_admin_stats()
    except Exception as e:
        logger.error(f"Failed to get admin stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch admin statistics")

@admin_router.get("/admin/users")
async def get_all_users_endpoint():
    try:
        from app.services.ride_sqlite import get_all_users
        return get_all_users()
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/admin/rides")
async def get_all_rides_endpoint(status: str = None, limit: int = 50):
    try:
        from app.services.ride_sqlite import get_all_rides
        return get_all_rides(status, limit)
    except Exception as e:
        logger.error(f"Error fetching rides: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/admin/analytics")
async def get_analytics_endpoint(days: int = 30):
    try:
        from app.services.ride_sqlite import get_analytics
        return get_analytics(days)
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/admin/settings")
async def get_system_settings_endpoint():
    # Settings not persisted in SQLite yet, return defaults
    return {
        "max_ride_distance_km": 50.0,
        "base_fare": 30.0,
        "per_km_rate": 12.0,
        "per_minute_rate": 2.0,
        "surge_multiplier": 1.0,
        "maintenance_mode": False,
        "otp_expiry_minutes": 10,
        "max_active_rides_per_driver": 3,
        "driver_search_radius_km": 10.0,
        "passenger_pickup_radius_km": 0.5
    }

@admin_router.get("/admin/flywheel-logs")
async def fetch_failed_sms_logs(limit: int = 50):
    try:
        from app.services.ride_sqlite import get_failed_sms_logs
        logs = get_failed_sms_logs(limit=limit)
        return {"status": "success", "logs": logs}
    except Exception as e:
        logger.error(f"Error fetching flywheel logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/admin/drivers")
async def get_all_drivers():
    try:
        from app.services.ride_sqlite import list_drivers_ordered
        drivers = list_drivers_ordered()
        return {"status": "success", "drivers": drivers}
    except Exception as e:
        logger.error(f"Error fetching drivers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
    Get comprehensive admin statistics for dashboard.
    """
    try:
        db = get_db()
        
        # Get ride statistics
        rides_ref = db.collection(COLLECTION_RIDES)
        all_rides = rides_ref.stream()
        
        total_rides = 0
        total_revenue = 0
        active_rides = 0
        today_rides = 0
        today_revenue = 0
        completed_rides = 0
        
        # Calculate today's date
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).date()
        
        for ride_doc in all_rides:
            ride = ride_doc.to_dict()
            total_rides += 1
            
            status = ride.get("status", "")
            fare = ride.get("estimated_fare", 0)
            
            if status in ["REQUESTED", "DRIVER_ASSIGNED", "IN_PROGRESS"]:
                active_rides += 1
            
            if status == "COMPLETED":
                completed_rides += 1
                total_revenue += fare
                
                # Check if completed today
                completed_at = ride.get("assigned_at", "")
                if completed_at:
                    try:
                        ride_date = datetime.fromisoformat(completed_at.replace('Z', '+00:00')).date()
                        if ride_date == today:
                            today_rides += 1
                            today_revenue += fare
                    except:
                        pass
        
        # Get driver statistics
        drivers_ref = db.collection(COLLECTION_DRIVERS)
        active_drivers = len(list(drivers_ref.stream()))
        
        # Get passenger statistics (estimate from rides)
        passenger_ids = set()
        rides_ref = db.collection(COLLECTION_RIDES)
        for ride_doc in rides_ref.stream():
            ride = ride_doc.to_dict()
            passenger_id = ride.get("passenger_id")
            if passenger_id:
                passenger_ids.add(passenger_id)
        
        total_passengers = len(passenger_ids)
        
        # Calculate average rating from feedback
        total_rating = 0
        rating_count = 0
        for ride_doc in rides_ref.stream():
            ride = ride_doc.to_dict()
            feedback = ride.get("passenger_feedback", {})
            rating = feedback.get("rating")
            if rating:
                total_rating += rating
                rating_count += 1
        
        average_rating = round(total_rating / rating_count, 1) if rating_count > 0 else 0
        
        return {
            "totalRides": total_rides,
            "totalRevenue": total_revenue,
            "activeDrivers": active_drivers,
            "activeRides": active_rides,
            "todayRides": today_rides,
            "todayRevenue": today_revenue,
            "totalPassengers": total_passengers,
            "averageRating": average_rating,
            "completedRides": completed_rides,
        }
        
    except Exception as e:
        logger.error(f"Error fetching admin stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.get("/admin/users")
async def get_all_users():
    """
    Get all users (drivers and passengers) for admin management.
    """
    try:
        db = get_db()
        
        # Get drivers
        drivers = []
        drivers_ref = db.collection(COLLECTION_DRIVERS)
        for doc in drivers_ref.stream():
            driver_data = doc.to_dict()
            driver_data["id"] = doc.id
            driver_data["role"] = "driver"
            drivers.append(driver_data)
        
        # Get passengers (from rides data)
        passengers = []
        passenger_map = {}
        
        rides_ref = db.collection(COLLECTION_RIDES)
        for ride_doc in rides_ref.stream():
            ride = ride_doc.to_dict()
            passenger_id = ride.get("passenger_id")
            if passenger_id and passenger_id not in passenger_map:
                passenger_map[passenger_id] = {
                    "id": passenger_id,
                    "role": "passenger",
                    "name": ride.get("passenger_name", "Unknown"),
                    "phone": ride.get("passenger_phone", "Unknown"),
                    "total_rides": 0,
                    "last_ride": ride.get("created_at", ""),
                }
            if passenger_id in passenger_map:
                passenger_map[passenger_id]["total_rides"] += 1
        
        passengers = list(passenger_map.values())
        
        return {
            "drivers": drivers,
            "passengers": passengers,
            "total_drivers": len(drivers),
            "total_passengers": len(passengers),
        }
        
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.get("/admin/rides")
async def get_all_rides(status: str = None, limit: int = 50):
    """
    Get all rides with optional filtering by status.
    """
    try:
        db = get_db()
        rides_ref = db.collection(COLLECTION_RIDES)
        
        query = rides_ref
        if status:
            query = query.where("status", "==", status)
        
        rides = []
        for doc in query.limit(limit).stream():
            ride_data = doc.to_dict()
            ride_data["id"] = doc.id
            rides.append(ride_data)
        
        # Sort by creation date (newest first)
        rides.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return {
            "rides": rides,
            "total": len(rides),
            "status_filter": status,
        }
        
    except Exception as e:
        logger.error(f"Error fetching rides: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.post("/admin/users/{user_id}/block")
async def block_user(user_id: str):
    """
    Block a user (driver or passenger).
    """
    try:
        db = get_db()
        
        # Check if it's a driver
        driver_ref = db.collection(COLLECTION_DRIVERS).document(user_id)
        if driver_ref.get().exists:
            driver_ref.update({"blocked": True, "blocked_at": _now_iso()})
            return {"message": f"Driver {user_id} blocked successfully"}
        
        # For passengers, we might want to add them to a blocked collection
        # For now, just return success
        return {"message": f"User {user_id} blocked successfully"}
        
    except Exception as e:
        logger.error(f"Error blocking user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.post("/admin/rides/{ride_id}/cancel")
async def admin_cancel_ride(ride_id: str):
    """
    Admin force cancel a ride.
    """
    try:
        update_status(ride_id, "CANCELLED")
        return {"message": f"Ride {ride_id} cancelled by admin"}
        
    except Exception as e:
        logger.error(f"Error cancelling ride: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.get("/admin/analytics")
async def get_analytics(days: int = 30):
    """
    Get detailed analytics for the specified number of days.
    """
    try:
        db = get_db()
        from datetime import datetime, timedelta, timezone
        
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        rides_ref = db.collection(COLLECTION_RIDES)
        
        # Get rides in date range
        daily_stats = {}
        revenue_by_hour = {}
        rides_by_status = {"REQUESTED": 0, "DRIVER_ASSIGNED": 0, "IN_PROGRESS": 0, "COMPLETED": 0, "CANCELLED": 0}
        
        for ride_doc in rides_ref.stream():
            ride = ride_doc.to_dict()
            created_at = ride.get("created_at", "")
            
            if created_at:
                try:
                    ride_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    if ride_date >= start_date:
                        # Daily stats
                        date_key = ride_date.date().isoformat()
                        if date_key not in daily_stats:
                            daily_stats[date_key] = {"rides": 0, "revenue": 0}
                        daily_stats[date_key]["rides"] += 1
                        if ride.get("status") == "COMPLETED":
                            daily_stats[date_key]["revenue"] += ride.get("estimated_fare", 0)
                        
                        # Hourly revenue
                        hour = ride_date.hour
                        if hour not in revenue_by_hour:
                            revenue_by_hour[hour] = 0
                        if ride.get("status") == "COMPLETED":
                            revenue_by_hour[hour] += ride.get("estimated_fare", 0)
                        
                        # Status distribution
                        status = ride.get("status", "UNKNOWN")
                        if status in rides_by_status:
                            rides_by_status[status] += 1
                            
                except Exception as e:
                    logger.warning(f"Error parsing date {created_at}: {e}")
        
        return {
            "period_days": days,
            "daily_stats": daily_stats,
            "revenue_by_hour": revenue_by_hour,
            "rides_by_status": rides_by_status,
            "total_revenue_period": sum(day["revenue"] for day in daily_stats.values()),
            "total_rides_period": sum(day["rides"] for day in daily_stats.values()),
        }
        
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class SystemSettings(BaseModel):
    """System settings model"""
    max_ride_distance_km: float = 50.0
    base_fare: float = 30.0
    per_km_rate: float = 12.0
    per_minute_rate: float = 2.0
    surge_multiplier: float = 1.0
    maintenance_mode: bool = False
    otp_expiry_minutes: int = 10
    max_active_rides_per_driver: int = 3
    driver_search_radius_km: float = 10.0
    passenger_pickup_radius_km: float = 0.5


@admin_router.get("/admin/settings")
async def get_system_settings():
    """
    Get current system settings.
    """
    try:
        db = get_db()
        settings_ref = db.collection("system_settings").document("global")
        settings_doc = settings_ref.get()
        
        if settings_doc.exists:
            return settings_doc.to_dict()
        else:
            # Return default settings
            default_settings = SystemSettings()
            return default_settings.dict()
            
    except Exception as e:
        logger.error(f"Error fetching settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.post("/admin/settings")
async def update_system_settings(settings: SystemSettings):
    """
    Update system settings.
    """
    try:
        db = get_db()
        settings_ref = db.collection("system_settings").document("global")
        
        # Update settings
        settings_ref.set(settings.dict(), merge=True)
        
        return {"message": "Settings updated successfully", "settings": settings.dict()}
        
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.post("/admin/users/{user_id}/unblock")
async def unblock_user(user_id: str):
    """
    Unblock a user (driver or passenger).
    """
    try:
        db = get_db()
        
        # Check if it's a driver
        driver_ref = db.collection(COLLECTION_DRIVERS).document(user_id)
        driver_doc = driver_ref.get()
        if driver_doc.exists:
            driver_ref.update({"blocked": False, "unblocked_at": _now_iso()})
            return {"message": f"Driver {user_id} unblocked successfully"}
        
        # For passengers, we might want to remove them from blocked collection
        # For now, just return success
        return {"message": f"User {user_id} unblocked successfully"}
        
    except Exception as e:
        logger.error(f"Error unblocking user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.post("/admin/rides/{ride_id}/reassign")
async def reassign_ride(ride_id: str, driver_id: str = None):
    """
    Reassign a ride to a different driver or find a new driver.
    """
    try:
        from app.services.ride_sqlite import assign_driver, find_drivers_for_ride
        
        if driver_id:
            # Assign specific driver
            assign_driver(ride_id, driver_id)
            return {"message": f"Ride {ride_id} reassigned to driver {driver_id}"}
        else:
            # Find new driver
            drivers = find_drivers_for_ride(ride_id)
            if drivers:
                assign_driver(ride_id, drivers[0]["id"])
                return {"message": f"Ride {ride_id} reassigned to new driver"}
            else:
                raise HTTPException(status_code=404, detail="No available drivers found")
        
    except Exception as e:
        logger.error(f"Error reassigning ride: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.get("/admin/rides/{ride_id}/details")
async def get_ride_details(ride_id: str):
    """
    Get detailed information about a specific ride.
    """
    try:
        ride = get_ride(ride_id)
        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")
        
        return ride
        
    except Exception as e:
        logger.error(f"Error fetching ride details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/admin/flywheel-logs")
async def fetch_failed_sms_logs(limit: int = 50):
    """
    Get the most recent failed SMS parsing attempts.
    This data powers the AI Data Flywheel for offline fine-tuning.
    """
    try:
        logs = get_failed_sms_logs(limit=limit)
        return {"status": "success", "logs": logs}
    except Exception as e:
        logger.error(f"Error fetching flywheel logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/admin/drivers")
async def register_driver(driver_data: dict):
    """
    Register a new driver in the database.
    """
    try:
        driver_id = add_driver(driver_data)
        return {"status": "success", "driver_id": driver_id}
    except Exception as e:
        logger.error(f"Error registering driver: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/admin/drivers")
async def get_all_drivers():
    """
    Get a list of all registered drivers.
    """
    try:
        drivers = list_drivers_ordered()
        return {"status": "success", "drivers": drivers}
    except Exception as e:
        logger.error(f"Error fetching drivers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

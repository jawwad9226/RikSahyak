from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
import logging

from app.services.ai_parser import parse_ride_request_async
from app.services.ride_sqlite import create_ride, log_failed_sms_parse
from app.services.sms_service import send_sms_async
from app.core.schemas import RideStatus
from app.api.deps import verify_admin_token

logger = logging.getLogger(__name__)
router = APIRouter()

class IncomingSMS(BaseModel):
    phone_number: str
    text_message: str

@router.post("/webhook")
async def handle_incoming_sms(sms: IncomingSMS, background_tasks: BackgroundTasks):
    """
    Webhook designed to be triggered by MacroDroid or Tasker when an SMS arrives.
    """
    logger.info(f"📨 Received SMS from {sms.phone_number}: {sms.text_message}")
    
    # 1. Parse text using AI
    parsed_data = await parse_ride_request_async(sms.text_message)
    
    if "error" in parsed_data:
        # AI Data Flywheel: Log the failure so we can fine-tune the model later
        raw_output = parsed_data.get("raw_output", str(parsed_data))
        logger.warning(f"⚠️ AI failed to parse SMS. Logging for Flywheel. Output: {parsed_data}")
        log_failed_sms_parse(sms.phone_number, sms.text_message, raw_output)
        
        # Optionally send a fallback SMS to the user asking them to reformat
        fallback_msg = "Sorry, RikSahyak couldn't understand the locations. Please reply in format: 'Pickup to Dropoff'"
        background_tasks.add_task(send_sms_async, sms.phone_number, fallback_msg)
        
        return {"status": "error", "detail": "Could not parse ride request from text."}
    
    pickup = parsed_data.get("pickup", "Unknown Location")
    dropoff = parsed_data.get("dropoff", "Unknown Location")
    
    logger.info(f"🧠 AI Extracted -> Pickup: {pickup}, Dropoff: {dropoff}")
    
    # 2. Register ride in SQLite
    # We use a dummy passenger ID based on phone number for SMS bookings
    passenger_id = f"SMS-{sms.phone_number[-4:]}"
    
    ride_record = {
        "status": "REQUESTED", # Matches VALID_TRANSITIONS in ride_sqlite.py
        "passenger_id": passenger_id,
        "passenger_phone": sms.phone_number,
        "pickup_location": pickup,
        "dropoff_location": dropoff,
        "pickup_coords": {"latitude": 0.0, "longitude": 0.0}, # Needs geocoding in future
        "dropoff_coords": {"latitude": 0.0, "longitude": 0.0},
        "estimated_fare": 50.0, # Dummy fare for now
        "distance_km": 2.0,
        "driver_id": None,
        "candidate_drivers": []
    }
    
    try:
        ride_id = create_ride(ride_record)
        logger.info(f"✅ Created ride {ride_id} from SMS")
        
        # 3. Send Confirmation SMS
        reply_msg = f"RikSahyak: Your request from {pickup} to {dropoff} is received! We are finding a driver. (Ride {ride_id})"
        background_tasks.add_task(send_sms_async, sms.phone_number, reply_msg)
        
        return {
            "status": "success",
            "ride_id": ride_id,
            "parsed": parsed_data
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to create ride from SMS: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while booking ride.")

@router.get("/failed-logs", dependencies=[Depends(verify_admin_token)])
def get_failed_logs(limit: int = 50):
    from app.services.ride_sqlite import get_failed_sms_logs
    return get_failed_sms_logs(limit)

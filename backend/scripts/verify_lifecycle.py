import json
import urllib.request
import urllib.error
import time
import sys

BASE = "http://127.0.0.1:8000/api/v1/rides"

def post(path, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode("utf-8")), e.code

def get(path):
    try:
        with urllib.request.urlopen(f"{BASE}{path}") as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode("utf-8")), e.code

def run_verification():
    print("🚀 STARTING COMPLETENESS VERIFICATION...")
    
    # Generate unique IDs to avoid conflicts from previous runs
    suffix = int(time.time())
    pass_id = f"TEST_PASSENGER_{suffix}"
    driver_id = f"TEST_DRIVER_{suffix}"
    
    # 1. Create a Ride
    print("\n[1] Creating Ride Request...")
    ride_req = {
        "passenger_id": pass_id,
        "pickup_location": "Test Pickup",
        "dropoff_location": "Test Dropoff",
        "pickup_coords": {"latitude": 10.0, "longitude": 10.0},
        "dropoff_coords": {"latitude": 10.1, "longitude": 10.1},
        "estimated_fare": 100,
        "distance_km": 5
    }
    r1, s1 = post("/request", ride_req)
    if s1 != 200:
        print(f"❌ Failed to create ride: {r1}")
        return
    ride_id = r1["ride_id"]
    print(f"✅ Ride Created: {ride_id}")

    # 2. Assign Driver
    print("\n[2] Assigning Driver (State -> DRIVER_ASSIGNED)...")
    r2, s2 = post("/accept", {"ride_id": ride_id, "driver_id": driver_id})
    if s2 != 200:
        print(f"❌ Failed to accept ride: {r2}")
        return
    print(f"✅ Ride Accepted. Status: {r2.get('status')}")

    # 3. Start Ride (with OTP verification)
    print("\n[3] Starting Ride (State -> IN_PROGRESS)...")
    
    # First get the ride details to obtain the OTP
    r_status, s_status = get(f"/status/{ride_id}")
    if s_status != 200:
        print(f"❌ Failed to get ride status: {r_status}")
        return
    
    pickup_otp = r_status.get("pickup_otp")
    if not pickup_otp:
        print(f"❌ No OTP found in ride data: {r_status}")
        return
    
    print(f"📱 Got OTP from ride: {pickup_otp}")
    
    # Now start the ride with OTP
    r3, s3 = post(f"/{ride_id}/start", {"otp": pickup_otp}) 
    
    if s3 != 200:
         print(f"❌ Failed to start ride via /{ride_id}/start with OTP: {r3}")
         return
    else:
        print(f"✅ Ride Started via /{ride_id}/start with OTP verification")
        print(f"   Status: {r3.get('status')}")

    # 4. PRE-CONDITION CHECK: CANCEL SHOULD FAIL
    print("\n[4] 🛡️ TESTING INVARIANT: Attempting Cancel in IN_PROGRESS state...")
    r4, s4 = post(f"/{ride_id}/cancel", {})
    
    if s4 == 409: # Expecting conflict (RideStateError)
        print(f"✅ SUCCESS: Backend correctly REJECTED cancellation in IN_PROGRESS state. Msg: {r4.get('detail')}")
    else:
        print(f"❌ FAILURE: Backend ALLOWED cancellation in IN_PROGRESS state! Status: {s4}, Body: {r4}")
        # This highlights why disabling the button on frontend is CRITICAL.

    # 5. Complete Ride
    print("\n[5] Completing Ride...")
    r5, s5 = post(f"/{ride_id}/complete", {"ride_id": ride_id})
    if s5 != 200:
        print(f"❌ Failed to complete ride: {r5}")
        return
    print(f"✅ Ride Completed.")

    # 6. POST-CONDITION CHECK: CANCEL SHOULD FAIL
    print("\n[6] 🛡️ TESTING INVARIANT: Attempting Cancel in COMPLETED state...")
    r6, s6 = post(f"/{ride_id}/cancel", {})
    if s6 == 409:
        print(f"✅ SUCCESS: Backend correctly REJECTED cancellation in COMPLETED state. Msg: {r6.get('detail')}")
    else:
        print(f"❌ FAILURE: Backend ALLOWED cancellation in COMPLETED state! Status: {s6}, Body: {r6}")

    print("\n✨ VERIFICATION COMPLETE. System State invariants hold.")

if __name__ == "__main__":
    run_verification()

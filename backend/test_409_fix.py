#!/usr/bin/env python3
"""Test script to verify the 409 Conflict fix for ride creation."""

import sys
import os
import json
import requests
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

# Test backend health first
print("=" * 60)
print("Testing Backend Health Endpoint")
print("=" * 60)

try:
    response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
    print(f"Health Check: {response.status_code}")
    print(f"Response: {response.json()}")
    if response.status_code != 200:
        print("⚠️  Health check failed!")
except Exception as e:
    print(f"❌ Health check error: {e}")

print("\n" + "=" * 60)
print("Testing Ride Creation (POST /api/v1/rides/request)")
print("=" * 60)

# Create a unique passenger ID for testing
test_passenger_id = f"test-passenger-{datetime.now().timestamp()}"
print(f"Testing with passenger_id: {test_passenger_id}")

ride_request = {
    "passenger_id": test_passenger_id,
    "pickup_location": "Test Location A",
    "dropoff_location": "Test Location B",
    "pickup_coords": {
        "latitude": 28.7041,
        "longitude": 77.1025
    },
    "dropoff_coords": {
        "latitude": 28.6139,
        "longitude": 77.2090
    },
    "estimated_fare": 150.00,
    "distance_km": 12.5
}

try:
    print(f"\nSending POST request to /api/v1/rides/request")
    print(f"Payload: {json.dumps(ride_request, indent=2)}")
    
    response = requests.post(
        "http://localhost:8000/api/v1/rides/request",
        json=ride_request,
        timeout=5
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("\n✅ SUCCESS! Ride created successfully")
        ride_id = response.json().get("ride_id")
        if ride_id:
            print(f"Ride ID: {ride_id}")
            
            # Try to get the ride status
            print(f"\nVerifying ride was created in database...")
            status_response = requests.get(
                f"http://localhost:8000/api/v1/rides/status/{ride_id}",
                timeout=5
            )
            if status_response.status_code == 200:
                print(f"✅ Ride verification successful: {status_response.json()}")
            else:
                print(f"⚠️  Could not verify ride: {status_response.status_code}")
    elif response.status_code == 409:
        print("\n❌ CONFLICT (409): Passenger already has an active ride or query issue")
        print(f"Error details: {response.json()}")
    else:
        print(f"\n❌ Unexpected status code: {response.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("Testing Duplicate Ride Request (should get 409)")
print("=" * 60)

try:
    print(f"\nSending duplicate POST request with same passenger_id...")
    response = requests.post(
        "http://localhost:8000/api/v1/rides/request",
        json=ride_request,
        timeout=5
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 409:
        print(f"✅ Correctly returned 409 Conflict for duplicate request")
        print(f"Error details: {response.json()}")
    else:
        print(f"Response: {response.json()}")
        
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)

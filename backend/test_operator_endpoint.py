#!/usr/bin/env python3
"""
Test script for operator fallback endpoint
"""
import requests
import json
import sys

API_BASE = "http://localhost:8000/api/v1"

def test_operator_create_ride():
    """Test operator ride creation"""
    
    payload = {
        "passenger_id": f"passenger_test_{int(__import__('time').time())}",
        "passenger_name": "Test Passenger",
        "passenger_phone": "+91-9876543210",
        "pickup_location": "Malkapur Main Market",
        "dropoff_location": "Railway Station",
        "pickup_coords": {
            "latitude": 19.2183,
            "longitude": 75.5678
        },
        "dropoff_coords": {
            "latitude": 19.2200,
            "longitude": 75.5700
        },
        "distance_km": "2.5",
        "estimated_fare": "70.00",
        "special_notes": "Test passenger with special needs",
        "operator_id": "operator_test"
    }
    
    print("=" * 60)
    print("OPERATOR FALLBACK ENDPOINT TEST")
    print("=" * 60)
    print(f"\n📡 Testing: POST {API_BASE}/operator/create-ride")
    print(f"🚗 Passenger: {payload['passenger_name']}")
    print(f"📍 Route: {payload['pickup_location']} → {payload['dropoff_location']}")
    print(f"👤 Operator: {payload['operator_id']}")
    
    try:
        response = requests.post(
            f"{API_BASE}/operator/create-ride",
            json=payload,
            timeout=5
        )
        
        print(f"\n✓ Response Status: {response.status_code}")
        print(f"✓ Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ SUCCESS: Ride created!")
            print(f"   Ride ID: {result.get('ride_id')}")
            print(f"   Status: {result.get('status')}")
            return True
        elif response.status_code == 409:
            print(f"\n⚠️  CONFLICT: {response.json().get('detail', {}).get('error')}")
            return True
        else:
            print(f"\n❌ ERROR: Unexpected status code")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: Cannot connect to backend at {API_BASE}")
        print("   Make sure backend is running: python -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

def test_operator_conflict():
    """Test 409 conflict when passenger has active ride"""
    
    # Use same passenger ID to trigger conflict
    payload = {
        "passenger_id": "passenger_conflict_test",
        "passenger_name": "Conflict Test",
        "passenger_phone": "+91-9999999999",
        "pickup_location": "Location A",
        "dropoff_location": "Location B",
        "pickup_coords": {"latitude": 19.2183, "longitude": 75.5678},
        "dropoff_coords": {"latitude": 19.2200, "longitude": 75.5700},
        "distance_km": "2.5",
        "estimated_fare": "70.00",
        "special_notes": "",
        "operator_id": "operator_test"
    }
    
    print("\n" + "=" * 60)
    print("TEST: Duplicate Ride (409 Conflict)")
    print("=" * 60)
    
    try:
        # First request - should succeed
        response1 = requests.post(
            f"{API_BASE}/operator/create-ride",
            json=payload,
            timeout=5
        )
        print(f"\n1️⃣  First request: {response1.status_code}")
        if response1.status_code == 200:
            print(f"   ✓ Ride created: {response1.json().get('ride_id')}")
        
        # Second request with same passenger - should fail
        response2 = requests.post(
            f"{API_BASE}/operator/create-ride",
            json=payload,
            timeout=5
        )
        print(f"\n2️⃣  Second request (same passenger): {response2.status_code}")
        if response2.status_code == 409:
            print(f"   ✓ Got expected 409 Conflict!")
            print(f"   Error: {response2.json().get('detail', {}).get('error')}")
            return True
        else:
            print(f"   ❌ Expected 409 but got {response2.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        return False

if __name__ == "__main__":
    success1 = test_operator_create_ride()
    success2 = test_operator_conflict()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"✓ Basic ride creation: {'PASS' if success1 else 'FAIL'}")
    print(f"✓ Conflict detection: {'PASS' if success2 else 'FAIL'}")
    
    if success1 and success2:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)

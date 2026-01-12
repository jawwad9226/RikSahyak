#!/usr/bin/env python3
"""
Test script for driver progress tracking endpoints
"""
import requests
import json
import sys
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1"

def log_test(test_name: str, status: str):
    """Log test result"""
    symbol = "✓" if status == "PASS" else "✗"
    print(f"{symbol} {test_name}: {status}")

def test_driver_progress():
    """Test driver progress update endpoint"""
    
    print("=" * 70)
    print("DRIVER PROGRESS TRACKING TEST SUITE")
    print("=" * 70)
    
    results = []
    
    # 1. Create a test ride first
    print("\n1️⃣  Creating test ride...")
    try:
        ride_payload = {
            "passenger_id": f"passenger_progress_{int(datetime.now().timestamp())}",
            "pickup_location": "Test Pickup",
            "dropoff_location": "Test Dropoff",
            "pickup_coords": {"latitude": 19.2183, "longitude": 75.5678},
            "dropoff_coords": {"latitude": 19.2200, "longitude": 75.5700},
            "estimated_fare": 100.0,
            "distance_km": 2.5,
        }
        
        ride_response = requests.post(
            f"{API_BASE}/rides/request",
            json=ride_payload,
            timeout=5
        )
        
        if ride_response.status_code != 200:
            print(f"  ✗ Failed to create ride: {ride_response.text}")
            return results
        
        ride_id = ride_response.json().get("ride_id")
        print(f"  ✓ Ride created: {ride_id}")
        
    except Exception as e:
        print(f"  ✗ Error creating ride: {e}")
        return results
    
    # 2. Assign a driver to the ride
    print("\n2️⃣  Assigning driver...")
    driver_id = f"driver_test_{int(datetime.now().timestamp())}"
    try:
        assign_payload = {
            "ride_id": ride_id,
            "driver_id": driver_id
        }
        
        assign_response = requests.post(
            f"{API_BASE}/rides/accept",
            json=assign_payload,
            timeout=5
        )
        
        if assign_response.status_code != 200:
            print(f"  ✗ Failed to assign driver: {assign_response.text}")
            return results
        
        print(f"  ✓ Driver {driver_id} assigned")
        
    except Exception as e:
        print(f"  ✗ Error assigning driver: {e}")
        return results
    
    # 3. Test valid progress update
    print("\n3️⃣  Testing valid progress update...")
    try:
        progress_payload = {
            "driver_id": driver_id,
            "progress": "ON_THE_WAY_TO_PICKUP"
        }
        
        response = requests.post(
            f"{API_BASE}/rides/{ride_id}/driver-progress",
            json=progress_payload,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ Progress updated to {result['progress']}")
            print(f"    Response: {json.dumps(result, indent=2)}")
            log_test("Valid progress update (ON_THE_WAY_TO_PICKUP)", "PASS")
            results.append(("Valid progress update", True))
        else:
            print(f"  ✗ Failed: {response.status_code} - {response.text}")
            log_test("Valid progress update (ON_THE_WAY_TO_PICKUP)", "FAIL")
            results.append(("Valid progress update", False))
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        log_test("Valid progress update", "FAIL")
        results.append(("Valid progress update", False))
    
    # 4. Test all progress states
    print("\n4️⃣  Testing all progress states...")
    progress_states = [
        "ARRIVED_AT_PICKUP",
        "ON_THE_WAY_TO_DROPOFF",
    ]
    
    for progress in progress_states:
        try:
            payload = {
                "driver_id": driver_id,
                "progress": progress
            }
            
            response = requests.post(
                f"{API_BASE}/rides/{ride_id}/driver-progress",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"  ✓ Progress: {progress}")
                log_test(f"Progress update ({progress})", "PASS")
                results.append((f"Progress: {progress}", True))
            else:
                print(f"  ✗ Progress {progress}: {response.status_code}")
                log_test(f"Progress update ({progress})", "FAIL")
                results.append((f"Progress: {progress}", False))
                
        except Exception as e:
            print(f"  ✗ Error testing {progress}: {e}")
            log_test(f"Progress update ({progress})", "FAIL")
            results.append((f"Progress: {progress}", False))
    
    # 5. Test invalid progress value
    print("\n5️⃣  Testing invalid progress value...")
    try:
        payload = {
            "driver_id": driver_id,
            "progress": "INVALID_PROGRESS"
        }
        
        response = requests.post(
            f"{API_BASE}/rides/{ride_id}/driver-progress",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 400 or response.status_code == 422:
            print(f"  ✓ Correctly rejected invalid progress: {response.status_code}")
            log_test("Invalid progress rejection", "PASS")
            results.append(("Invalid progress rejection", True))
        else:
            print(f"  ✗ Did not reject invalid progress (got {response.status_code})")
            log_test("Invalid progress rejection", "FAIL")
            results.append(("Invalid progress rejection", False))
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        log_test("Invalid progress rejection", "FAIL")
        results.append(("Invalid progress rejection", False))
    
    # 6. Test wrong driver cannot update progress
    print("\n6️⃣  Testing wrong driver cannot update progress...")
    try:
        wrong_driver_id = f"driver_wrong_{int(datetime.now().timestamp())}"
        payload = {
            "driver_id": wrong_driver_id,
            "progress": "ON_THE_WAY_TO_PICKUP"
        }
        
        response = requests.post(
            f"{API_BASE}/rides/{ride_id}/driver-progress",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 409:
            print(f"  ✓ Correctly rejected wrong driver: {response.status_code}")
            print(f"    Error: {response.json()}")
            log_test("Wrong driver rejection (409)", "PASS")
            results.append(("Wrong driver rejection", True))
        else:
            print(f"  ✗ Did not reject wrong driver (got {response.status_code})")
            log_test("Wrong driver rejection (409)", "FAIL")
            results.append(("Wrong driver rejection", False))
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        log_test("Wrong driver rejection", "FAIL")
        results.append(("Wrong driver rejection", False))
    
    # 7. Test non-existent ride
    print("\n7️⃣  Testing non-existent ride...")
    try:
        payload = {
            "driver_id": driver_id,
            "progress": "ON_THE_WAY_TO_PICKUP"
        }
        
        response = requests.post(
            f"{API_BASE}/rides/RIDE-9999/driver-progress",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 404:
            print(f"  ✓ Correctly returned 404 for non-existent ride")
            log_test("Non-existent ride (404)", "PASS")
            results.append(("Non-existent ride", True))
        else:
            print(f"  ✗ Did not return 404 (got {response.status_code})")
            log_test("Non-existent ride (404)", "FAIL")
            results.append(("Non-existent ride", False))
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        log_test("Non-existent ride", "FAIL")
        results.append(("Non-existent ride", False))
    
    # 8. Complete ride and test cannot update progress
    print("\n8️⃣  Testing cannot update progress on completed ride...")
    try:
        # First mark ride as in progress
        requests.post(
            f"{API_BASE}/rides/{ride_id}/start",
            json={},
            timeout=5
        )
        
        # Complete the ride
        requests.post(
            f"{API_BASE}/rides/{ride_id}/complete",
            json={},
            timeout=5
        )
        
        # Try to update progress
        payload = {
            "driver_id": driver_id,
            "progress": "ON_THE_WAY_TO_PICKUP"
        }
        
        response = requests.post(
            f"{API_BASE}/rides/{ride_id}/driver-progress",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 409:
            print(f"  ✓ Correctly rejected progress update on completed ride: {response.status_code}")
            print(f"    Error: {response.json()}")
            log_test("Progress update on completed ride (409)", "PASS")
            results.append(("Progress on completed ride rejection", True))
        else:
            print(f"  ✗ Did not reject (got {response.status_code})")
            log_test("Progress update on completed ride (409)", "FAIL")
            results.append(("Progress on completed ride rejection", False))
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        log_test("Progress on completed ride rejection", "FAIL")
        results.append(("Progress on completed ride rejection", False))
    
    return results


if __name__ == "__main__":
    try:
        results = test_driver_progress()
        
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        for test_name, success in results:
            status = "✓ PASS" if success else "✗ FAIL"
            print(f"{status}: {test_name}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n✅ All tests passed!")
            sys.exit(0)
        else:
            print(f"\n❌ {total - passed} test(s) failed")
            sys.exit(1)
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend at http://localhost:8000")
        print("Make sure backend is running: python -m uvicorn app.main:app --reload")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

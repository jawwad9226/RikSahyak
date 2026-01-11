"""
Unit tests for ride state management and conflict prevention.

Tests cover:
- Single active ride enforcement
- Valid state transitions
- 409 Conflict responses for violations
"""

import pytest
import sys
import os

# Add backend app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

from app.services.ride_firestore import (
    create_ride,
    assign_driver,
    update_status,
    get_ride,
    RideConflictError,
    RideStateError,
)
from app.services.firebase_init import get_db
from app.core.firestore_models import COLLECTION_RIDES


class TestRideCreationGuards:
    """Test guards for creating new rides."""
    
    def setup_method(self):
        """Clean up test data before each test."""
        self._cleanup_test_rides()
    
    def teardown_method(self):
        """Clean up test data after each test."""
        self._cleanup_test_rides()
    
    @staticmethod
    def _cleanup_test_rides():
        """Remove all test rides from Firestore."""
        db = get_db()
        rides_ref = db.collection(COLLECTION_RIDES)
        for doc in rides_ref.stream():
            doc.reference.delete()
    
    def test_create_ride_success_no_existing_rides(self):
        """Verify ride creation succeeds when passenger has no active rides."""
        payload = {
            "passenger_id": "test-passenger-1",
            "pickup_location": "A",
            "dropoff_location": "B",
            "pickup_coords": {"latitude": 10.0, "longitude": 20.0},
            "dropoff_coords": {"latitude": 11.0, "longitude": 21.0},
            "estimated_fare": 100.0,
            "distance_km": 5.0,
        }
        
        ride_id = create_ride(payload)
        assert ride_id.startswith("RIDE-")
        
        ride = get_ride(ride_id)
        assert ride is not None
        assert ride["status"] == "REQUESTED"
        assert ride["passenger_id"] == "test-passenger-1"
    
    def test_create_ride_conflict_with_existing_requested(self):
        """Verify 409 Conflict when passenger has REQUESTED ride."""
        payload1 = {
            "passenger_id": "test-passenger-2",
            "pickup_location": "A",
            "dropoff_location": "B",
            "pickup_coords": {"latitude": 10.0, "longitude": 20.0},
            "dropoff_coords": {"latitude": 11.0, "longitude": 21.0},
            "estimated_fare": 100.0,
            "distance_km": 5.0,
        }
        
        # Create first ride
        ride_id_1 = create_ride(payload1)
        assert get_ride(ride_id_1)["status"] == "REQUESTED"
        
        # Try to create second ride for same passenger
        payload2 = dict(payload1)
        with pytest.raises(RideConflictError) as exc_info:
            create_ride(payload2)
        
        assert exc_info.value.code == "CONFLICT"
        assert "already has an active ride" in exc_info.value.message
    
    def test_create_ride_conflict_with_existing_driver_assigned(self):
        """Verify 409 Conflict when passenger has DRIVER_ASSIGNED ride."""
        passenger_id = "test-passenger-3"
        
        # Create and assign a ride
        payload1 = {
            "passenger_id": passenger_id,
            "pickup_location": "A",
            "dropoff_location": "B",
            "pickup_coords": {"latitude": 10.0, "longitude": 20.0},
            "dropoff_coords": {"latitude": 11.0, "longitude": 21.0},
            "estimated_fare": 100.0,
            "distance_km": 5.0,
        }
        
        ride_id_1 = create_ride(payload1)
        assign_driver(ride_id_1, "test-driver-1")
        
        assert get_ride(ride_id_1)["status"] == "DRIVER_ASSIGNED"
        
        # Try to create second ride for same passenger
        payload2 = dict(payload1)
        with pytest.raises(RideConflictError) as exc_info:
            create_ride(payload2)
        
        assert exc_info.value.code == "CONFLICT"
    
    def test_create_ride_conflict_with_existing_in_progress(self):
        """Verify 409 Conflict when passenger has IN_PROGRESS ride."""
        passenger_id = "test-passenger-4"
        
        # Create, assign, and start a ride
        payload1 = {
            "passenger_id": passenger_id,
            "pickup_location": "A",
            "dropoff_location": "B",
            "pickup_coords": {"latitude": 10.0, "longitude": 20.0},
            "dropoff_coords": {"latitude": 11.0, "longitude": 21.0},
            "estimated_fare": 100.0,
            "distance_km": 5.0,
        }
        
        ride_id_1 = create_ride(payload1)
        assign_driver(ride_id_1, "test-driver-2")
        update_status(ride_id_1, "IN_PROGRESS")
        
        assert get_ride(ride_id_1)["status"] == "IN_PROGRESS"
        
        # Try to create second ride for same passenger
        payload2 = dict(payload1)
        with pytest.raises(RideConflictError) as exc_info:
            create_ride(payload2)
        
        assert exc_info.value.code == "CONFLICT"
    
    def test_create_ride_success_after_completion(self):
        """Verify ride creation succeeds after previous ride is completed."""
        passenger_id = "test-passenger-5"
        
        # Create, assign, start, and complete a ride
        payload1 = {
            "passenger_id": passenger_id,
            "pickup_location": "A",
            "dropoff_location": "B",
            "pickup_coords": {"latitude": 10.0, "longitude": 20.0},
            "dropoff_coords": {"latitude": 11.0, "longitude": 21.0},
            "estimated_fare": 100.0,
            "distance_km": 5.0,
        }
        
        ride_id_1 = create_ride(payload1)
        assign_driver(ride_id_1, "test-driver-3")
        update_status(ride_id_1, "IN_PROGRESS")
        update_status(ride_id_1, "COMPLETED")
        
        assert get_ride(ride_id_1)["status"] == "COMPLETED"
        
        # Create second ride for same passenger should succeed
        payload2 = dict(payload1)
        ride_id_2 = create_ride(payload2)
        assert ride_id_2 != ride_id_1
        assert get_ride(ride_id_2)["status"] == "REQUESTED"


class TestDriverAssignmentGuards:
    """Test guards for assigning drivers to rides."""
    
    def setup_method(self):
        """Clean up test data before each test."""
        self._cleanup_test_rides()
    
    def teardown_method(self):
        """Clean up test data after each test."""
        self._cleanup_test_rides()
    
    @staticmethod
    def _cleanup_test_rides():
        """Remove all test rides from Firestore."""
        db = get_db()
        rides_ref = db.collection(COLLECTION_RIDES)
        for doc in rides_ref.stream():
            doc.reference.delete()
    
    def test_assign_driver_success_to_requested_ride(self):
        """Verify driver assignment succeeds for REQUESTED ride with no driver conflicts."""
        payload = {
            "passenger_id": "test-passenger-6",
            "pickup_location": "A",
            "dropoff_location": "B",
            "pickup_coords": {"latitude": 10.0, "longitude": 20.0},
            "dropoff_coords": {"latitude": 11.0, "longitude": 21.0},
            "estimated_fare": 100.0,
            "distance_km": 5.0,
        }
        
        ride_id = create_ride(payload)
        assign_driver(ride_id, "test-driver-4")
        
        ride = get_ride(ride_id)
        assert ride["status"] == "DRIVER_ASSIGNED"
        assert ride["driver_id"] == "test-driver-4"
    
    def test_assign_driver_conflict_driver_has_assigned_ride(self):
        """Verify 409 Conflict when driver already has DRIVER_ASSIGNED ride."""
        # Create two rides
        ride_payload_1 = {
            "passenger_id": "test-passenger-7",
            "pickup_location": "A",
            "dropoff_location": "B",
            "pickup_coords": {"latitude": 10.0, "longitude": 20.0},
            "dropoff_coords": {"latitude": 11.0, "longitude": 21.0},
            "estimated_fare": 100.0,
            "distance_km": 5.0,
        }
        
        ride_payload_2 = {
            "passenger_id": "test-passenger-8",
            "pickup_location": "C",
            "dropoff_location": "D",
            "pickup_coords": {"latitude": 12.0, "longitude": 22.0},
            "dropoff_coords": {"latitude": 13.0, "longitude": 23.0},
            "estimated_fare": 150.0,
            "distance_km": 7.0,
        }
        
        ride_id_1 = create_ride(ride_payload_1)
        ride_id_2 = create_ride(ride_payload_2)
        
        # Assign first ride to driver
        assign_driver(ride_id_1, "test-driver-5")
        assert get_ride(ride_id_1)["status"] == "DRIVER_ASSIGNED"
        
        # Try to assign second ride to same driver
        with pytest.raises(RideConflictError) as exc_info:
            assign_driver(ride_id_2, "test-driver-5")
        
        assert exc_info.value.code == "CONFLICT"
        assert "already has an active ride" in exc_info.value.message
    
    def test_assign_driver_conflict_driver_has_in_progress_ride(self):
        """Verify 409 Conflict when driver already has IN_PROGRESS ride."""
        # Create two rides
        ride_payload_1 = {
            "passenger_id": "test-passenger-9",
            "pickup_location": "A",
            "dropoff_location": "B",
            "pickup_coords": {"latitude": 10.0, "longitude": 20.0},
            "dropoff_coords": {"latitude": 11.0, "longitude": 21.0},
            "estimated_fare": 100.0,
            "distance_km": 5.0,
        }
        
        ride_payload_2 = {
            "passenger_id": "test-passenger-10",
            "pickup_location": "C",
            "dropoff_location": "D",
            "pickup_coords": {"latitude": 12.0, "longitude": 22.0},
            "dropoff_coords": {"latitude": 13.0, "longitude": 23.0},
            "estimated_fare": 150.0,
            "distance_km": 7.0,
        }
        
        ride_id_1 = create_ride(ride_payload_1)
        ride_id_2 = create_ride(ride_payload_2)
        
        # Assign and start first ride
        assign_driver(ride_id_1, "test-driver-6")
        update_status(ride_id_1, "IN_PROGRESS")
        assert get_ride(ride_id_1)["status"] == "IN_PROGRESS"
        
        # Try to assign second ride to same driver
        with pytest.raises(RideConflictError) as exc_info:
            assign_driver(ride_id_2, "test-driver-6")
        
        assert exc_info.value.code == "CONFLICT"
    
    def test_assign_driver_state_error_already_assigned(self):
        """Verify error when trying to assign driver to non-REQUESTED ride."""
        payload = {
            "passenger_id": "test-passenger-11",
            "pickup_location": "A",
            "dropoff_location": "B",
            "pickup_coords": {"latitude": 10.0, "longitude": 20.0},
            "dropoff_coords": {"latitude": 11.0, "longitude": 21.0},
            "estimated_fare": 100.0,
            "distance_km": 5.0,
        }
        
        ride_id = create_ride(payload)
        assign_driver(ride_id, "test-driver-7")
        
        # Try to assign another driver to already-assigned ride
        with pytest.raises(RideStateError) as exc_info:
            assign_driver(ride_id, "test-driver-8")
        
        assert exc_info.value.code == "INVALID_STATE"


class TestStateTransitions:
    """Test valid and invalid state transitions."""
    
    def setup_method(self):
        """Clean up test data before each test."""
        self._cleanup_test_rides()
    
    def teardown_method(self):
        """Clean up test data after each test."""
        self._cleanup_test_rides()
    
    @staticmethod
    def _cleanup_test_rides():
        """Remove all test rides from Firestore."""
        db = get_db()
        rides_ref = db.collection(COLLECTION_RIDES)
        for doc in rides_ref.stream():
            doc.reference.delete()
    
    def test_valid_transition_requested_to_driver_assigned(self):
        """Verify valid transition: REQUESTED -> DRIVER_ASSIGNED."""
        payload = {
            "passenger_id": "test-passenger-12",
            "pickup_location": "A",
            "dropoff_location": "B",
            "pickup_coords": {"latitude": 10.0, "longitude": 20.0},
            "dropoff_coords": {"latitude": 11.0, "longitude": 21.0},
            "estimated_fare": 100.0,
            "distance_km": 5.0,
        }
        
        ride_id = create_ride(payload)
        assert get_ride(ride_id)["status"] == "REQUESTED"
        
        assign_driver(ride_id, "test-driver-9")
        assert get_ride(ride_id)["status"] == "DRIVER_ASSIGNED"
    
    def test_valid_transition_driver_assigned_to_in_progress(self):
        """Verify valid transition: DRIVER_ASSIGNED -> IN_PROGRESS."""
        payload = {
            "passenger_id": "test-passenger-13",
            "pickup_location": "A",
            "dropoff_location": "B",
            "pickup_coords": {"latitude": 10.0, "longitude": 20.0},
            "dropoff_coords": {"latitude": 11.0, "longitude": 21.0},
            "estimated_fare": 100.0,
            "distance_km": 5.0,
        }
        
        ride_id = create_ride(payload)
        assign_driver(ride_id, "test-driver-10")
        assert get_ride(ride_id)["status"] == "DRIVER_ASSIGNED"
        
        update_status(ride_id, "IN_PROGRESS")
        assert get_ride(ride_id)["status"] == "IN_PROGRESS"
    
    def test_valid_transition_in_progress_to_completed(self):
        """Verify valid transition: IN_PROGRESS -> COMPLETED."""
        payload = {
            "passenger_id": "test-passenger-14",
            "pickup_location": "A",
            "dropoff_location": "B",
            "pickup_coords": {"latitude": 10.0, "longitude": 20.0},
            "dropoff_coords": {"latitude": 11.0, "longitude": 21.0},
            "estimated_fare": 100.0,
            "distance_km": 5.0,
        }
        
        ride_id = create_ride(payload)
        assign_driver(ride_id, "test-driver-11")
        update_status(ride_id, "IN_PROGRESS")
        assert get_ride(ride_id)["status"] == "IN_PROGRESS"
        
        update_status(ride_id, "COMPLETED")
        ride = get_ride(ride_id)
        assert ride["status"] == "COMPLETED"
        assert "completed_at" in ride
    
    def test_valid_transition_requested_to_cancelled(self):
        """Verify valid transition: REQUESTED -> CANCELLED."""
        payload = {
            "passenger_id": "test-passenger-15",
            "pickup_location": "A",
            "dropoff_location": "B",
            "pickup_coords": {"latitude": 10.0, "longitude": 20.0},
            "dropoff_coords": {"latitude": 11.0, "longitude": 21.0},
            "estimated_fare": 100.0,
            "distance_km": 5.0,
        }
        
        ride_id = create_ride(payload)
        assert get_ride(ride_id)["status"] == "REQUESTED"
        
        update_status(ride_id, "CANCELLED")
        assert get_ride(ride_id)["status"] == "CANCELLED"
    
    def test_valid_transition_driver_assigned_to_cancelled(self):
        """Verify valid transition: DRIVER_ASSIGNED -> CANCELLED."""
        payload = {
            "passenger_id": "test-passenger-16",
            "pickup_location": "A",
            "dropoff_location": "B",
            "pickup_coords": {"latitude": 10.0, "longitude": 20.0},
            "dropoff_coords": {"latitude": 11.0, "longitude": 21.0},
            "estimated_fare": 100.0,
            "distance_km": 5.0,
        }
        
        ride_id = create_ride(payload)
        assign_driver(ride_id, "test-driver-12")
        assert get_ride(ride_id)["status"] == "DRIVER_ASSIGNED"
        
        update_status(ride_id, "CANCELLED")
        assert get_ride(ride_id)["status"] == "CANCELLED"
    
    def test_invalid_transition_in_progress_to_cancelled(self):
        """Verify error on invalid transition: IN_PROGRESS -> CANCELLED."""
        payload = {
            "passenger_id": "test-passenger-17",
            "pickup_location": "A",
            "dropoff_location": "B",
            "pickup_coords": {"latitude": 10.0, "longitude": 20.0},
            "dropoff_coords": {"latitude": 11.0, "longitude": 21.0},
            "estimated_fare": 100.0,
            "distance_km": 5.0,
        }
        
        ride_id = create_ride(payload)
        assign_driver(ride_id, "test-driver-13")
        update_status(ride_id, "IN_PROGRESS")
        
        # Should not allow cancellation from IN_PROGRESS
        with pytest.raises(RideStateError) as exc_info:
            update_status(ride_id, "CANCELLED")
        
        assert exc_info.value.code == "INVALID_STATE"
    
    def test_invalid_transition_requested_to_in_progress(self):
        """Verify error on invalid transition: REQUESTED -> IN_PROGRESS (skip DRIVER_ASSIGNED)."""
        payload = {
            "passenger_id": "test-passenger-18",
            "pickup_location": "A",
            "dropoff_location": "B",
            "pickup_coords": {"latitude": 10.0, "longitude": 20.0},
            "dropoff_coords": {"latitude": 11.0, "longitude": 21.0},
            "estimated_fare": 100.0,
            "distance_km": 5.0,
        }
        
        ride_id = create_ride(payload)
        
        # Should not allow direct transition to IN_PROGRESS
        with pytest.raises(RideStateError) as exc_info:
            update_status(ride_id, "IN_PROGRESS")
        
        assert exc_info.value.code == "INVALID_STATE"
    
    def test_invalid_transition_completed_to_cancelled(self):
        """Verify error on invalid transition: COMPLETED -> CANCELLED."""
        payload = {
            "passenger_id": "test-passenger-19",
            "pickup_location": "A",
            "dropoff_location": "B",
            "pickup_coords": {"latitude": 10.0, "longitude": 20.0},
            "dropoff_coords": {"latitude": 11.0, "longitude": 21.0},
            "estimated_fare": 100.0,
            "distance_km": 5.0,
        }
        
        ride_id = create_ride(payload)
        assign_driver(ride_id, "test-driver-14")
        update_status(ride_id, "IN_PROGRESS")
        update_status(ride_id, "COMPLETED")
        
        # Should not allow transition from COMPLETED
        with pytest.raises(RideStateError) as exc_info:
            update_status(ride_id, "CANCELLED")
        
        assert exc_info.value.code == "INVALID_STATE"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

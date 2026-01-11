"""
Initialize Firestore emulator with demo data.
Run this once after emulator starts.
"""
import os
import sys

# Set emulator host before importing firebase
os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"

from firebase_admin import firestore
from app.services.firebase_init import get_db

def init_emulator_data():
    """Create demo users, drivers, and initial data"""
    db = get_db()
    
    print("📝 Initializing Firestore Emulator with demo data...\n")
    
    # Create demo users
    users_data = {
        "PAS-001": {
            "user_id": "PAS-001",
            "name": "Raj Kumar",
            "role": "passenger",
            "phone": "+91-9000000001",
            "rating": 4.8,
        },
        "PAS-002": {
            "user_id": "PAS-002",
            "name": "Priya Singh",
            "role": "passenger",
            "phone": "+91-9000000002",
            "rating": 4.9,
        },
        "DRV-1001": {
            "user_id": "DRV-1001",
            "name": "Ramesh",
            "role": "driver",
            "phone": "+91-9000000001",
            "vehicle_number": "MH-28-AB-1234",
            "rating": 4.7,
        },
        "DRV-1002": {
            "user_id": "DRV-1002",
            "name": "Suresh",
            "role": "driver",
            "phone": "+91-9000000002",
            "vehicle_number": "MH-28-CD-5678",
            "rating": 4.6,
        },
        "DRV-1003": {
            "user_id": "DRV-1003",
            "name": "Mahesh",
            "role": "driver",
            "phone": "+91-9000000003",
            "vehicle_number": "MH-28-EF-9012",
            "rating": 4.8,
        },
    }
    
    for user_id, user_data in users_data.items():
        db.collection("users").document(user_id).set(user_data)
        print(f"✅ Created user: {user_id} ({user_data['name']})")

    # Seed drivers collection with coords for deterministic distance
    drivers_data = {
        "DRV-1001": {
            "driver_id": "DRV-1001",
            "name": "Ramesh",
            "phone": "+91-9000000001",
            "vehicle_number": "MH-28-AB-1234",
            "coords": {"latitude": 20.8875, "longitude": 76.2055},
        },
        "DRV-1002": {
            "driver_id": "DRV-1002",
            "name": "Suresh",
            "phone": "+91-9000000002",
            "vehicle_number": "MH-28-CD-5678",
            "coords": {"latitude": 20.8890, "longitude": 76.2100},
        },
        "DRV-1003": {
            "driver_id": "DRV-1003",
            "name": "Mahesh",
            "phone": "+91-9000000003",
            "vehicle_number": "MH-28-EF-9012",
            "coords": {"latitude": 20.8825, "longitude": 76.2005},
        },
    }

    for driver_id, driver in drivers_data.items():
        db.collection("drivers").document(driver_id).set(driver)
        print(f"✅ Created driver: {driver_id} ({driver['name']}) with coords")
    
    print("\n✨ Firestore emulator initialized with demo data!")
    print("\nUsers created:")
    print("  Passengers: PAS-001, PAS-002")
    print("  Drivers: DRV-1001, DRV-1002, DRV-1003")


if __name__ == "__main__":
    try:
        init_emulator_data()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

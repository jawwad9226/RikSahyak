import os
import sys
from pathlib import Path

os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "127.0.0.1:8080")

# Ensure backend package root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.firebase_init import get_db
from app.core.firestore_models import (
    COLLECTION_USERS,
    COLLECTION_DRIVERS,
    COLLECTION_RIDES,
)


def main():
    db = get_db()
    users = list(db.collection(COLLECTION_USERS).stream())
    drivers = list(db.collection(COLLECTION_DRIVERS).stream())
    rides = list(db.collection(COLLECTION_RIDES).stream())

    print("Collections summary:")
    print(f"  users:   {len(users)} docs")
    print(f"  drivers: {len(drivers)} docs")
    print(f"  rides:   {len(rides)} docs")

    if users:
        u0 = users[0].to_dict()
        print("\nSample user:")
        print(u0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

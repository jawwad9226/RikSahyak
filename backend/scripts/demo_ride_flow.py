import json
import urllib.request

BASE = "http://127.0.0.1:8000/api/v1/rides"

def post(path, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)


def get(path):
    with urllib.request.urlopen(f"{BASE}{path}") as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)


def main():
    print("1) Creating ride request...")
    ride_req = {
        "passenger_id": "PAS-001",
        "pickup_location": "Station",
        "dropoff_location": "Hospital",
        "pickup_coords": {"latitude": 20.8845, "longitude": 76.2010},
        "dropoff_coords": {"latitude": 20.8950, "longitude": 76.2150},
        "estimated_fare": 75.0,
        "distance_km": 3.5,
    }
    r1 = post("/request", ride_req)
    print("Response:", r1)
    ride_id = r1["ride_id"]

    print("\n2) Finding drivers...")
    r2 = post("/find-drivers", {"ride_id": ride_id, "max_results": 2})
    print("Response:", r2)
    driver_id = r2["drivers"][0]["driver_id"]

    print("\n3) Accepting ride...")
    r3 = post("/accept", {"ride_id": ride_id, "driver_id": driver_id})
    print("Response:", r3)

    print("\n4) Checking status...")
    r4 = get(f"/status/{ride_id}")
    print("Response:", r4)

    print("\n5) Completing ride...")
    r5 = post("/complete", {"ride_id": ride_id})
    print("Response:", r5)

    print("\n6) Final status...")
    r6 = get(f"/status/{ride_id}")
    print("Response:", r6)


if __name__ == "__main__":
    main()

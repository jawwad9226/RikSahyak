import os
from dotenv import load_dotenv

load_dotenv()

# Firebase Config
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-credentials.json")
FIREBASE_DATABASE_URL = os.getenv("FIREBASE_DATABASE_URL", "")

# MapmyIndia (Mappls) API Config
# Get your FREE API key from: https://mappls.com/api
MAPPLS_API_KEY = os.getenv("MAPPLS_API_KEY", "YOUR_MAPPLS_API_KEY_HERE")
MAPPLS_CLIENT_ID = os.getenv("MAPPLS_CLIENT_ID", "")
MAPPLS_CLIENT_SECRET = os.getenv("MAPPLS_CLIENT_SECRET", "")

# API Config
API_PREFIX = "/api/v1"
API_VERSION = "1.0.0"

# Server Config
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# Malkapur Geo Details
MALKAPUR_CENTER = {
    "latitude": 20.8870,
    "longitude": 76.2052
}

# Fare Configuration
FARE_CONFIG = {
    "base_fare": 20,  # ₹20
    "per_km_rate": 15,  # ₹15 per km
}

# Locations in Malkapur (for geocoding reference)
MALKAPUR_LOCATIONS = {
    "station": {"lat": 20.8845, "lon": 76.2010},
    "civil lines": {"lat": 20.8900, "lon": 76.2100},
    "bus stand": {"lat": 20.8820, "lon": 76.2080},
    "hospital": {"lat": 20.8950, "lon": 76.2150},
    "market": {"lat": 20.8870, "lon": 76.2000},
}

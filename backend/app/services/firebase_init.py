"""
Firebase connector for FastAPI backend.
Uses Firestore Emulator when available or in dev mode; otherwise falls back to cloud if credentials provided.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if it exists
env_file = Path(__file__).resolve().parents[2] / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Default to emulator in development if not explicitly set
if not os.getenv("FIRESTORE_EMULATOR_HOST"):
    # Check if cloud credentials are available
    creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-credentials.json")
    if not os.path.exists(creds_path):
        # No cloud credentials; default to emulator for dev
        os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"

# Prefer direct google-cloud-firestore client for emulator to avoid ADC
if os.getenv("FIRESTORE_EMULATOR_HOST"):
    from google.cloud import firestore as gc_firestore
    from google.auth.credentials import AnonymousCredentials

    PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "riksahyak-demo")
    db = gc_firestore.Client(project=PROJECT_ID, credentials=AnonymousCredentials())
    print(f"✅ Firestore: Using emulator at {os.getenv('FIRESTORE_EMULATOR_HOST')} (project={PROJECT_ID})")

else:
    # Cloud mode via firebase_admin (requires service account)
    import firebase_admin
    from firebase_admin import credentials, firestore

    try:
        firebase_admin.get_app()
    except ValueError:
        creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-credentials.json")
        if not os.path.exists(creds_path):
            raise RuntimeError(
                "FIREBASE_CREDENTIALS_PATH not found and FIRESTORE_EMULATOR_HOST not set. "
                "Please provide credentials or set FIRESTORE_EMULATOR_HOST."
            )
        cred = credentials.Certificate(creds_path)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase: Connected to cloud Firestore")

    db = firestore.client()


def get_db():
    """Return Firestore client"""
    return db

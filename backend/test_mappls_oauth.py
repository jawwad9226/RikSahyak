#!/usr/bin/env python3
"""
Test MapmyIndia OAuth2 Authentication (CORRECT METHOD for Cloud Apps)
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("MAPPLS_CLIENT_ID")
CLIENT_SECRET = os.getenv("MAPPLS_CLIENT_SECRET")

print(f"Client ID: {CLIENT_ID[:10] if CLIENT_ID else 'NOT SET'}...")
print(f"Client Secret: {CLIENT_SECRET[:10] if CLIENT_SECRET else 'NOT SET'}...")

if not CLIENT_ID or not CLIENT_SECRET or CLIENT_ID == "YOUR_CLIENT_ID_HERE":
    print("\n❌ ERROR: Client ID and Secret not configured!")
    print("\nGo to: https://apis.mappls.com/console/")
    print("1. Click on 'RikSahyak Backend' app")
    print("2. Look for 'Client ID' and 'Client Secret' in Credentials tab")
    print("3. Copy them to backend/.env file")
    exit(1)

# Step 1: Get OAuth Token
print("\n=== Step 1: Getting OAuth2 Access Token ===")
auth_data = {
    'grant_type': 'client_credentials',
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
}

auth_headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
}

auth_response = requests.post(
    'https://outpost.mappls.com/api/security/oauth/token',
    data=auth_data,
    headers=auth_headers,
)

print(f"OAuth Status Code: {auth_response.status_code}")
print(f"OAuth Response: {auth_response.text[:500]}")

if auth_response.status_code != 200:
    print("\n❌ OAuth failed!")
    print("Make sure you copied the correct Client ID and Client Secret")
    exit(1)

token_data = auth_response.json()
access_token = token_data.get('access_token')
print(f"\n✅ Got access token: {access_token[:20]}...")

# Step 2: Use token to call Autosuggest API
print("\n=== Step 2: Calling Autosuggest API with Bearer Token ===")

api_headers = {
    'Authorization': f'Bearer {access_token}',
}

api_params = {
    'query': 'railway station, Malkapur',
    'location': '20.8870,76.2010',
}

api_response = requests.get(
    'https://search.mappls.com/search/places/autosuggest/json',
    params=api_params,
    headers=api_headers,
)

print(f"API Status Code: {api_response.status_code}")
print(f"API Response: {api_response.text[:500]}")

if api_response.status_code == 200:
    print("\n✅✅✅ SUCCESS! MapmyIndia API is working!")
    data = api_response.json()
    results = data.get('suggestedLocations', [])
    print(f"Found {len(results)} locations:")
    for r in results[:3]:
        print(f"  - {r.get('placeName', 'N/A')}: {r.get('placeAddress', 'N/A')}")
else:
    print("\n❌ API call failed even with valid token")
    print("This might be an IP whitelisting issue or account limitation")

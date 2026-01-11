#!/usr/bin/env python3
"""
Test MapmyIndia API to see exact error response
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("MAPPLS_API_KEY")
print(f"API Key: {API_KEY[:10]}...")

# Test 1: Autosuggest API (CORRECT METHOD)
print("\n=== Test 1: Autosuggest API (with access_token) ===")
params1 = {
    'query': 'railway station, Malkapur',
    'access_token': API_KEY,
}
response1 = requests.get("https://search.mappls.com/search/places/autosuggest/json", params=params1)
print(f"Status Code: {response1.status_code}")
print(f"Response: {response1.text[:500]}")

# Test 2: With location parameter
print("\n=== Test 2: With location parameter ===")
params2 = {
    'query': 'railway station',
    'location': '20.8870,76.2010',
    'access_token': API_KEY,
}
response2 = requests.get("https://search.mappls.com/search/places/autosuggest/json", params=params2)
print(f"Status Code: {response2.status_code}")
print(f"Response: {response2.text[:500]}")

# Test 3: Text Search API
print("\n=== Test 3: Text Search API ===")
params3 = {
    'query': 'bus stand malkapur',
    'region': 'IND',
    'access_token': API_KEY,
}
response3 = requests.get("https://search.mappls.com/search/places/textsearch/json", params=params3)
print(f"Status Code: {response3.status_code}")
print(f"Response: {response3.text[:500]}")

print("\n=== ✅ If you see 200 status codes, the API is working! ===")
print("Check your MapmyIndia Dashboard:")
print("1. Go to https://apis.mappls.com/console/")
print("2. Check 'Usage' or 'Analytics' to see API calls")

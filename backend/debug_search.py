#!/usr/bin/env python3
"""
Debug script to test location search from the app's perspective
Shows exactly what's happening when searching
"""

import requests
import json
import sys
from datetime import datetime

API_URL = "http://192.168.2.6:8000/api/v1/rides/search-location"

# Test queries matching what a user might search
test_queries = [
    "near me",
    "current location",
    "railway station",
    "bus stand",
    "hospital nearby",
    "school",
    "college",
    "market",
]

print("=" * 80)
print("DEBUG: Location Search API Tests")
print("=" * 80)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"API URL: {API_URL}")
print()

failed_count = 0
success_count = 0

for query in test_queries:
    print(f"\n{'-' * 80}")
    print(f"Query: '{query}'")
    print(f"{'-' * 80}")
    
    try:
        response = requests.post(
            API_URL,
            json={"query": query},
            timeout=20  # Give it plenty of time
        )
        
        if response.status_code == 200:
            data = response.json()
            
            exact = len(data.get('exact_matches', []))
            fuzzy = len(data.get('fuzzy_matches', []))
            mappls = len(data.get('mappls_results', []))
            nominatim = len(data.get('nominatim_results', []))
            total = len(data.get('all_results', []))
            
            print(f"Status: ✅ 200 OK")
            print(f"Results: {total} total")
            print(f"  • Exact matches: {exact}")
            print(f"  • Fuzzy matches: {fuzzy}")
            print(f"  • MapmyIndia: {mappls}")
            print(f"  • Nominatim: {nominatim}")
            
            if mappls == 0 and nominatim == 0:
                print(f"⚠️  WARNING: Only local database results! External APIs returned nothing.")
                print(f"   This means MapmyIndia and Nominatim are either:")
                print(f"   1. Timing out")
                print(f"   2. Not finding results")
                print(f"   3. Network connectivity issues")
                failed_count += 1
            else:
                print(f"✅ External APIs working")
                success_count += 1
            
            # Show top 3 results
            if data.get('all_results'):
                print(f"\nTop 3 Results:")
                for i, result in enumerate(data['all_results'][:3], 1):
                    name = result.get('name', 'N/A')
                    result_type = result.get('type', '?')
                    distance = result.get('distance_km', 'N/A')
                    print(f"  {i}. {name}")
                    print(f"     Type: {result_type}, Distance: {distance} km")
            else:
                print(f"❌ NO RESULTS FOUND!")
                failed_count += 1
                
        else:
            print(f"❌ Error {response.status_code}: {response.text[:100]}")
            failed_count += 1
            
    except requests.exceptions.Timeout:
        print(f"❌ Request TIMEOUT (20 seconds)")
        failed_count += 1
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to backend at {API_URL}")
        print(f"   Make sure backend is running: cd backend && ./run.sh")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        failed_count += 1

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Successful queries with external APIs: {success_count}/{len(test_queries)}")
print(f"Queries failing (only local DB): {failed_count}/{len(test_queries)}")

if failed_count > len(test_queries) * 0.5:
    print(f"\n⚠️  {failed_count} queries are failing!")
    print(f"\nTROUBLESHOOTING:")
    print(f"1. Check network connectivity:")
    print(f"   ping google.com")
    print(f"2. Check if MapmyIndia is reachable:")
    print(f"   curl -I https://search.mappls.com/search/places/textsearch/json")
    print(f"3. Check if Nominatim is reachable:")
    print(f"   curl -I https://nominatim.openstreetmap.org/search")
    print(f"4. Restart backend: pkill -f 'uvicorn' && cd backend && ./run.sh")
else:
    print(f"\n✅ External APIs are working!")

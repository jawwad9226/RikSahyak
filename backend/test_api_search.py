#!/usr/bin/env python3
"""
Test the /search-location API endpoint with MapmyIndia integration
"""

import requests
import json

API_URL = "http://192.168.2.6:8000/api/v1/rides/search-location"

test_queries = [
    "railway station",
    "bus stand",
    "college",
    "market",
    "hospital",
]

print("=" * 70)
print("Testing /search-location API with MapmyIndia Integration")
print("=" * 70)
print()

for query in test_queries:
    print(f"\n{'=' * 70}")
    print(f"Query: '{query}'")
    print(f"{'=' * 70}")
    
    try:
        response = requests.post(
            API_URL,
            json={"query": query},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Count results from each source
            exact_count = len(data.get('exact_matches', []))
            fuzzy_count = len(data.get('fuzzy_matches', []))
            mappls_count = len(data.get('mappls_results', []))
            nominatim_count = len(data.get('nominatim_results', []))
            total_count = len(data.get('all_results', []))
            
            print(f"\n📊 Results Summary:")
            print(f"   Exact Matches: {exact_count}")
            print(f"   Fuzzy Matches: {fuzzy_count}")
            print(f"   MapmyIndia: {mappls_count}")
            print(f"   Nominatim: {nominatim_count}")
            print(f"   Total: {total_count}")
            
            # Show top 3 results
            if data.get('all_results'):
                print(f"\n🎯 Top 3 Results:")
                for i, result in enumerate(data['all_results'][:3], 1):
                    print(f"\n   {i}. {result.get('name', 'N/A')}")
                    print(f"      Type: {result.get('type', 'unknown')}")
                    if result.get('latitude') and result.get('longitude'):
                        print(f"      Location: {result['latitude']:.4f}, {result['longitude']:.4f}")
                    if result.get('distance_km'):
                        print(f"      Distance: {result['distance_km']} km")
                    if result.get('address'):
                        print(f"      Address: {result['address']}")
            
            # Highlight MapmyIndia results
            if mappls_count > 0:
                print(f"\n   ✅ MapmyIndia providing {mappls_count} results!")
            else:
                print(f"\n   ⚠️  No MapmyIndia results (may have timed out)")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to backend server")
        print("   Make sure the backend is running: ./run.sh")
        break
    except requests.exceptions.Timeout:
        print("❌ Error: Request timed out")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "=" * 70)
print("✅ Test Complete!")
print("=" * 70)

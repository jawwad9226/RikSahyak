#!/usr/bin/env python3
"""
Test integrated location search with MapmyIndia + Local DB + Nominatim
"""

import sys
sys.path.insert(0, '.')

from app.services.nominatim_service import smart_search
from app.core.locations_db import get_all_locations

print("=" * 60)
print("Testing Integrated Location Search")
print("=" * 60)
print()

# Load local database
location_database = get_all_locations()
print(f"✓ Loaded {len(location_database)} locations from local database\n")

# Test queries
test_queries = [
    "railway station",
    "bus stand",
    "college road",
    "market",
    "hospital",
]

for query in test_queries:
    print(f"\n{'=' * 60}")
    print(f"Query: '{query}'")
    print(f"{'=' * 60}")
    
    results = smart_search(query, location_database, use_mappls=True)
    
    # Show exact matches
    if results['exact_matches']:
        print(f"\n✅ Exact Matches ({len(results['exact_matches'])}):")
        for match in results['exact_matches'][:3]:
            print(f"  • {match['name']}")
            print(f"    Location: {match['latitude']:.4f}, {match['longitude']:.4f}")
            print(f"    Type: {match.get('category', 'N/A')}")
    
    # Show MapmyIndia results
    if results['mappls_results']:
        print(f"\n🗺️  MapmyIndia Results ({len(results['mappls_results'])}):")
        for match in results['mappls_results'][:3]:
            print(f"  • {match['name']}")
            print(f"    {match.get('address', 'N/A')}")
            print(f"    Distance: {match.get('distance_km', 'N/A')} km")
            if match.get('latitude') and match.get('longitude'):
                print(f"    Location: {match['latitude']:.4f}, {match['longitude']:.4f}")
    
    # Show fuzzy matches
    if results['fuzzy_matches']:
        print(f"\n🔍 Fuzzy Matches ({len(results['fuzzy_matches'])}):")
        for match in results['fuzzy_matches'][:3]:
            print(f"  • {match['name']} (similarity: {match.get('similarity', 0):.0%})")
    
    # Show Nominatim results
    if results['nominatim_results']:
        print(f"\n🌍 Nominatim Results ({len(results['nominatim_results'])}):")
        for match in results['nominatim_results'][:2]:
            print(f"  • {match['name']}")
            print(f"    Location: {match['latitude']:.4f}, {match['longitude']:.4f}")
    
    # Show combined results count
    print(f"\n📊 Total Combined Results: {len(results['all_results'])}")
    
    # Show top 3 from all_results
    if results['all_results']:
        print(f"\n🎯 Top 3 Combined Results:")
        for i, match in enumerate(results['all_results'][:3], 1):
            print(f"  {i}. {match['name']}")
            print(f"     Type: {match.get('type', 'unknown')}")
            if match.get('latitude') and match.get('longitude'):
                print(f"     Location: {match['latitude']:.4f}, {match['longitude']:.4f}")

print("\n" + "=" * 60)
print("✅ Test Complete!")
print("=" * 60)
print("\nSearch Priority:")
print("1. Local Database (exact matches)")
print("2. MapmyIndia API (best for Indian locations)")
print("3. Local Database (fuzzy matches)")
print("4. Nominatim (OpenStreetMap fallback)")

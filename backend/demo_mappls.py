#!/usr/bin/env python3
"""
Quick demo of MapmyIndia search for Malkapur locations
"""

import sys
sys.path.insert(0, '.')

from app.services.mappls_service_simple import search_mappls
from app.core.config import MAPPLS_API_KEY

print("🗺️  MapmyIndia Search Demo for Malkapur\n")
print("=" * 60)

if not MAPPLS_API_KEY or MAPPLS_API_KEY == "YOUR_MAPPLS_API_KEY_HERE":
    print("❌ Error: MAPPLS_API_KEY not configured in .env")
    sys.exit(1)

print(f"✅ API Key configured: {MAPPLS_API_KEY[:10]}...\n")

# Test searches
searches = [
    ("railway station", "Finding railway stations..."),
    ("bus stand", "Finding bus stands..."),
    ("hospital", "Finding hospitals..."),
    ("college", "Finding colleges..."),
]

for query, description in searches:
    print(f"\n{'=' * 60}")
    print(f"🔍 {description}")
    print(f"Query: '{query}'")
    print("=" * 60)
    
    try:
        results = search_mappls(query, MAPPLS_API_KEY, limit=3)
        
        if results:
            print(f"\n✅ Found {len(results)} results in Malkapur area:\n")
            for i, loc in enumerate(results, 1):
                print(f"{i}. {loc.name}")
                print(f"   📍 {loc.address}")
                if loc.lat and loc.lon:
                    print(f"   🌐 {loc.lat:.4f}, {loc.lon:.4f}")
                print(f"   📏 {loc.distance:.2f} km from center")
                print()
        else:
            print("⚠️  No results found")
            
    except Exception as e:
        print(f"❌ Error: {e}")

print("=" * 60)
print("\n✅ Demo complete!")
print("\nKey Features:")
print("• Searches within 10km radius of Malkapur")
print("• Returns precise coordinates")
print("• Better Indian location data than Google/OSM")
print("• 10,000 FREE API calls per month")

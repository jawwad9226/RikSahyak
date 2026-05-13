import requests
import json
import time

# Phone API Endpoint
PHONE_IP = "100.65.95.4" # Your Tailscale/Phone IP
WEBHOOK_URL = f"http://{PHONE_IP}:8000/api/v1/sms/webhook"

# Test Cases: A mix of English, Hinglish, and Marathi
TEST_CASES = [
    {
        "name": "Standard English",
        "text": "I want to go from Railway Station to City Hospital",
        "expected": ["railway station", "city hospital"]
    },
    {
        "name": "Marathi Mixed (Hinglish)",
        "text": "Mala main market pasun railway station la jaycha aahe",
        "expected": ["main market", "railway station"]
    },
    {
        "name": "Hindi Mixed (Hinglish)",
        "text": "Bus stand se civil hospital jana hai",
        "expected": ["bus stand", "civil hospital"]
    },
    {
        "name": "Short/Direct",
        "text": "Station to Market",
        "expected": ["station", "market"]
    },
    {
        "name": "Implicit 'to'",
        "text": "Pick me up from Airport, drop at Hotel Taj",
        "expected": ["airport", "hotel taj"]
    },
    {
        "name": "Marathi Casual",
        "text": "Mala ghara pasun college la sod",
        "expected": ["ghara", "college"]
    },
]

def run_robust_test():
    print(f"\n🚀 Starting Robust Phase 4 AI Testing...")
    print(f"📡 Target: {WEBHOOK_URL}\n")
    
    results = []
    
    for i, case in enumerate(TEST_CASES):
        print(f"[{i+1}/{len(TEST_CASES)}] Testing: '{case['name']}'")
        print(f"   💬 Text: \"{case['text']}\"")
        
        payload = {
            "phone_number": "+919096997459",
            "text_message": case['text']
        }
        
        try:
            start_time = time.time()
            response = requests.post(WEBHOOK_URL, json=payload, timeout=90)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    parsed = data.get("parsed", {})
                    pickup = parsed.get("pickup", "").lower()
                    dropoff = parsed.get("dropoff", "").lower()
                    
                    # Basic check if expected words are in the parsed results
                    passed = all(word in (pickup + " " + dropoff) for word in case['expected'])
                    
                    status_icon = "✅" if passed else "⚠️"
                    print(f"   {status_icon} Result: {parsed} (Took {duration:.1f}s)")
                    results.append(passed)
                else:
                    print(f"   ❌ AI failed to parse: {data.get('detail')}")
                    results.append(False)
            else:
                print(f"   ❌ Server error: {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"   ❌ Connection error: {e}")
            results.append(False)
            
        print("-" * 40)

    total_passed = sum(results)
    print(f"\n📊 FINAL SUMMARY")
    print(f"   Pass Rate: {total_passed}/{len(TEST_CASES)}")
    if total_passed == len(TEST_CASES):
        print("   🌟 PHASE 4 IS 100% ROBUST!")
    else:
        print("   🏗️ Some patterns need refinement, but the system is learning.")

if __name__ == "__main__":
    run_robust_test()

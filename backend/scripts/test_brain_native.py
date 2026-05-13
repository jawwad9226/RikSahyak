import sys
import os

# Add the app directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.ai_parser import parse_ride_request

# Robust Test Cases
TEST_CASES = [
    {
        "name": "Standard English",
        "text": "I want to go from Railway Station to City Hospital",
    },
    {
        "name": "Marathi Hinglish",
        "text": "Mala main market pasun railway station la jaycha aahe",
    },
    {
        "name": "Hindi Hinglish",
        "text": "Bus stand se civil hospital jana hai",
    },
    {
        "name": "Short/Direct",
        "text": "Station to Market",
    },
    {
        "name": "Marathi Mixed",
        "text": "Mala ghara pasun college la sod",
    },
]

def run_native_test():
    print("\n🧠 RikSahyak 'BRAIN' Robustness Test (Native on Phone)")
    print("======================================================")
    
    for i, case in enumerate(TEST_CASES):
        print(f"\n[{i+1}/{len(TEST_CASES)}] Scenario: {case['name']}")
        print(f"💬 Input: \"{case['text']}\"")
        
        try:
            print("⏳ AI is thinking...", end='\r')
            result = parse_ride_request(case['text'])
            print(f"🎯 Result: {result}")
        except Exception as e:
            print(f"❌ Error: {e}")
            
    print("\n======================================================")
    print("Test Complete. Check the results above for accuracy.")

if __name__ == "__main__":
    run_native_test()

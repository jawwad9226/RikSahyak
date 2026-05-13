import asyncio
import sys
import os

# Add the backend directory to sys.path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sms_service import send_sms_async

async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_sms.py <phone_number>")
        print("Example: python test_sms.py +919876543210")
        return
        
    phone_number = sys.argv[1]
    message = "RikSahyak Test: Your Termux:API SMS integration is working perfectly! 🚀"
    
    print(f"\n📲 Attempting to send SMS to {phone_number}...")
    success = await send_sms_async(phone_number, message)
    
    if success:
        print("\n✅ SUCCESS! If you are running this on Termux, the SMS should have been sent out!")
    else:
        print("\n❌ FAILED. Ensure Termux:API is installed and SMS permissions are granted.")

if __name__ == "__main__":
    asyncio.run(main())

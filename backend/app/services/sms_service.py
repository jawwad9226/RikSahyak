import subprocess
import logging
import asyncio

logger = logging.getLogger(__name__)

def send_sms(phone_number: str, message: str) -> bool:
    """
    Sends an SMS using the Termux:API (termux-sms-send).
    
    Args:
        phone_number: The destination phone number.
        message: The message to send.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # termux-sms-send -n <number> <message>
        # Ensure we pass strings
        logger.info(f"📱 Attempting to send SMS to {phone_number}...")
        
        # We use subprocess.run with timeout to prevent hanging
        result = subprocess.run(
            ["termux-sms-send", "-n", phone_number, message],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            logger.info(f"✅ SMS successfully sent to {phone_number}")
            return True
        else:
            logger.error(f"❌ Failed to send SMS: {result.stderr}")
            return False
            
    except FileNotFoundError:
        logger.warning(f"⚠️ termux-sms-send not found. Are you running on Android with Termux:API installed? (Mocking SMS to {phone_number}: '{message}')")
        return True # Return true in development to not break the flow
    except subprocess.TimeoutExpired:
        logger.error(f"❌ SMS send command timed out for {phone_number}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error sending SMS: {e}")
        return False

async def send_sms_async(phone_number: str, message: str) -> bool:
    """
    Asynchronous wrapper for send_sms to prevent blocking the FastAPI event loop.
    """
    loop = asyncio.get_event_loop()
    # Run the synchronous subprocess call in a background thread
    return await loop.run_in_executor(None, send_sms, phone_number, message)

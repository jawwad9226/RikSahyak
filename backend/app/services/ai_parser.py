import subprocess
import json
import re
import logging

logger = logging.getLogger(__name__)

# Hardcoded model path for Termux environment
MODEL_PATH = "/data/data/com.termux/files/home/models/qwen-0.5b.gguf"

# ─────────────────────────────────────────────
# Layer 1: PRE-PROCESSING
# Normalize Hinglish/Marathi to plain English
# so the AI has the best possible input.
# ─────────────────────────────────────────────
# Each tuple: (regex pattern, replacement)
HINGLISH_NORMALIZATIONS = [
    # Marathi patterns
    (r'\bMala\b',     '',     ),  # "Mala" = "I want to"
    (r'\bla\b',       'to',   ),  # "la" = "to" (destination marker)
    (r'\bpasun\b',    'to',   ),  # "pasun" = "from" → use "to" so AI reads X to Y
    (r'\bjaycha\b',   '',     ),  # "jaycha" = "to go"
    (r'\baahe\b',     '',     ),  # "aahe" = "is/am"
    (r'\bsod\b',      '',     ),  # "sod" = "drop" (informal)
    (r'\bghara\b',    'home', ),  # "ghara" = "home"
    # Hindi patterns
    (r'\bse\b',       'to',   ),  # "X se Y" = "X to Y" (se marks the source)
    (r'\btak\b',      'to',   ),  # "tak" = "to/until"
    (r'\bko\b',       'to',   ),  # "ko" = "to"
    (r'\bjana hai\b', '',     ),  # "jana hai" = "need to go"
    (r'\bchahiye\b',  '',     ),  # "chahiye" = "want"
    (r'\bkaro\b',     '',     ),  # "karo" = "do it"
]

def normalize_text(text: str) -> str:
    """
    Convert Hinglish/Marathi grammar words to English equivalents.
    This is done BEFORE sending to the AI so the model sees cleaner input.
    """
    result = text
    for pattern, replacement in HINGLISH_NORMALIZATIONS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    # Collapse multiple spaces
    result = re.sub(r'\s+', ' ', result).strip()
    return result


# ─────────────────────────────────────────────
# Layer 2: POST-PROCESSING
# Clean up messy location strings from AI output
# ─────────────────────────────────────────────
NOISE_WORDS = {
    'mala', 'se', 'tak', 'pasun', 'la', 'jaycha', 'aahe', 'sod',
    'jana', 'hai', 'chahiye', 'ko', 'from', 'to', 'the', 'a', 'an',
    'me', 'my', 'i', 'want', 'need', 'go', 'drop', 'pick', 'up',
}

def clean_location(loc: str) -> str:
    """Strip trailing/leading noise words from an extracted location string."""
    if not loc:
        return loc
    words = loc.strip().split()
    # Remove leading noise words
    while words and words[0].lower() in NOISE_WORDS:
        words.pop(0)
    # Remove trailing noise words
    while words and words[-1].lower() in NOISE_WORDS:
        words.pop()
    return ' '.join(words).strip()


# ─────────────────────────────────────────────
# Main Parser
# ─────────────────────────────────────────────
def parse_ride_request(sms_text: str) -> dict:
    """
    Two-layer pipeline:
      1. Normalize Hinglish/Marathi text to English.
      2. Send normalized text to local Qwen AI.
      3. Clean up the AI's extracted location strings.
    Returns a dict with 'pickup' and 'dropoff', or an 'error' key.
    """
    # ── Layer 1: Normalize input ──────────────────────
    normalized = normalize_text(sms_text)
    logger.info(f"🔤 Normalized: '{sms_text}' → '{normalized}'")

    # ── Build AI prompt ────────────────────────────────
    # Improvement 1: null handling, correction detection, landmark cleaning
    system_prompt = (
        "You are a precise Indian Ride-Hailing Assistant. "
        "Task: Extract 'pickup' and 'dropoff' landmarks from the message. "
        "Rules: "
        "1. Respond ONLY with valid JSON. "
        "2. If a user corrects themselves (e.g., 'no wait', 'instead'), extract the FINAL intent. "
        "3. Use null if a location is missing. "
        "4. Strip articles like 'the', 'a', or 'my' from landmark names. "
        'JSON Format: {"pickup": "landmark", "dropoff": "landmark"}'
    )
    # Improvement 2: clear anchor so the model knows exactly what to produce
    user_prompt = f'User Message: "{normalized}"\nJSON Result:'

    # Improvement 3: "Assistant Hack" — end the prompt with `{"` to
    # force the model to start the JSON object immediately (no chatter).
    full_prompt = (
        f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
        f"<|im_start|>user\n{user_prompt}<|im_end|>\n"
        f'<|im_start|>assistant\n{{"'  # <── forces JSON to start here
    )

    cmd = [
        "llama-completion",
        "-m", MODEL_PATH,
        "-p", full_prompt,
        "-n", "40",               # a JSON object needs < 30 tokens
        "--temp", "0",            # Improvement 4: deterministic output
        "-t", "4",
        "--ctx-size", "512",
        "--no-warmup",
        "--repeat-penalty", "2.0",   # heavy penalty — stops looping
        "--no-keep",                 # clear KV cache after generation
        "--reverse-prompt", "<|im_end|>",
    ]

    try:
        logger.info(f"🤖 Sending to Qwen AI: '{normalized}'")
        result = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=60
        )

        full_output = result.stdout + result.stderr

        # Because the Assistant Hack pre-seeds '{"', the raw output will
        # look like: '"pickup": "Station", "dropoff": "Hospital"}'
        # We need to reconstruct the full JSON by prepending '{'.
        # We still support the normal '{...}' format as a fallback.
        json_line = None
        for line in reversed(full_output.splitlines()):
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                json_line = line   # normal format
                break
            # Assistant Hack format: starts with a quoted key, ends with }
            if (line.startswith('"pickup"') or line.startswith('"dropoff"')) and line.endswith("}"):
                json_line = "{" + line
                break

        # Markdown code‑block fallback
        if not json_line:
            if "```json" in full_output:
                json_line = full_output.split("```json")[1].split("```")[0].strip()
            elif "```" in full_output:
                json_line = full_output.split("```")[1].split("```")[0].strip()

        if not json_line:
            logger.error(f"❌ No JSON found in AI output: {full_output[-300:]}")
            return {"error": "invalid_json", "raw_output": full_output[-300:]}

        try:
            parsed_data = json.loads(json_line)
        except json.JSONDecodeError:
            logger.error(f"❌ AI returned invalid JSON: {json_line}")
            return {"error": "invalid_json", "raw_output": json_line}

        # ── Layer 2: Post-process locations ────────────
        pickup  = clean_location(parsed_data.get("pickup", ""))
        dropoff = clean_location(parsed_data.get("dropoff", ""))

        if not pickup or not dropoff:
            logger.warning(f"⚠️ Incomplete extraction: {parsed_data}")
            return {"error": "incomplete_extraction", "raw": parsed_data}

        logger.info(f"✅ Extracted → pickup='{pickup}', dropoff='{dropoff}'")
        return {"pickup": pickup, "dropoff": dropoff}

    except FileNotFoundError:
        logger.warning("⚠️ llama-completion not found. Using mock extraction.")
        text_lower = sms_text.lower()
        if "station" in text_lower and "hospital" in text_lower:
            return {"pickup": "Station", "dropoff": "Hospital"}
        return {"pickup": "Mock Pickup", "dropoff": "Mock Dropoff"}

    except subprocess.TimeoutExpired:
        logger.error("❌ AI timed out (> 60s)")
        return {"error": "timeout"}

    except Exception as e:
        logger.error(f"❌ Unexpected AI error: {e}")
        return {"error": str(e)}


async def parse_ride_request_async(sms_text: str) -> dict:
    """
    Async wrapper — runs the blocking AI call in a thread pool
    so it doesn't block the FastAPI event loop.
    """
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, parse_ride_request, sms_text)

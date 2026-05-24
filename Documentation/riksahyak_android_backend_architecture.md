# RikSahyak: Android-Native Backend Architecture

This document serves as the complete technical record of the RikSahyak backend infrastructure running natively on a Samsung Galaxy M31s.

## 1. Hardware & Environment
* **Device:** Samsung Galaxy M31s (Rooted, formatted)
* **Processor Architecture:** ARM64 (aarch64)
* **Operating System Environment:** Termux (running directly on the Android Linux kernel)
* **Python Environment:** Python 3.11/3.13 via Termux `pkg install python`, isolated using `venv`.
* **Primary Motivation:** Zero operational cost. Bypassing cloud providers (AWS, Heroku) and API providers (Twilio, OpenAI) by utilizing the physical hardware and local SIM card.

## 2. Core Backend Stack
* **Framework:** FastAPI
* **Server:** Uvicorn (running asynchronously on `0.0.0.0:8000`)
* **Database:** SQLite (`riksahyak.db`). 
  * *Note: Migrated away from Firestore to maintain 100% offline capability and avoid ARM64 C++ compilation issues with gRPC libraries on Android.*
* **Data Validation:** Pydantic v1 (used to ensure compatibility within the Termux ARM64 environment).

## 3. Networking & Connectivity
Because the server runs on a mobile network (Jio/Airtel SIM) behind a Carrier-Grade NAT (CGNAT), it does not have a public IP address.
* **VPN / Overlay Network:** **Tailscale**
  * The phone is authenticated on a Tailscale network, giving it a stable `100.x.x.x` IP address.
  * The laptop and the Expo development environment connect to this Tailscale IP to communicate with the FastAPI server.
* **Future Production Exposure:** To expose this to end-users (rickshaw drivers) without requiring them to install Tailscale, the architecture plans to use **Cloudflare Tunnels (cloudflared)** to securely expose `localhost:8000` to a public URL (e.g., `api.riksahyak.org`).

## 4. Zero-Cost SMS Gateway (Phase 3)
* **Incoming SMS (MacroDroid):** A free automation app (MacroDroid) listens for incoming SMS messages. The exact millisecond an SMS is received, MacroDroid makes a local HTTP POST request to `http://localhost:8000/api/v1/sms/webhook` with the sender's phone number and the message text.
* **Outgoing SMS (Termux:API):** The backend uses `termux-sms-send` (a native C binary provided by Termux:API) to command the physical SIM card to send text messages (booking confirmations, driver assignments) directly to passengers. This bypasses Twilio and utilizes unlimited local SMS packs.

## 5. Local AI Text-to-Function Parser (Phase 4)
Passengers book rides using unstructured, messy SMS messages (e.g., "malkapur stn se shivaji chowk").
* **The Model:** `Qwen2.5-0.5B-Instruct-GGUF` (4-bit quantized). Ultra-lightweight (~350MB), easily fits within the Samsung M31s RAM constraints.
* **Execution:** Run locally using `llama.cpp` (`llama-completion` binary installed via Termux).
* **The Pipeline:**
  1. **Pre-processing (Regex):** Hinglish and Marathi markers (`se`, `pasun`, `la`, `jaycha`) are stripped or normalized to English (`to`) before reaching the AI.
  2. **Inference:** Subprocess calls `llama-completion` with strict deterministic flags (`--temp 0`, `--repeat-penalty 2.0`, `--no-keep`).
  3. **Assistant Hack:** The prompt ends exactly with `{"` to force the LLM to output pure JSON without conversational fluff.
  4. **Post-processing:** The extracted locations are cleaned of residual noise words (e.g., "the", "want").

## 6. The AI Data Flywheel
To handle edge cases without paying for expensive cloud models:
* If the local 0.5B model fails to parse a message, the `sms_webhook.py` catches the error.
* The raw SMS and the model's garbage output are logged to a specific SQLite table: `failed_sms_logs`.
* The system replies to the passenger with a fallback SMS: *"Sorry, RikSahyak couldn't understand... please use 'Pickup to Dropoff'."*
* **Export:** An admin endpoint (`GET /api/v1/admin/flywheel-logs`) allows you to pull these failures, process them offline through a massive model (like GPT-4), and use the resulting dataset to continuously fine-tune the local Qwen model on Malkapur's exact dialect.

## 7. Abandoned Architecture (Phase 5: Live Voice Call AI)
* **Attempt:** Tried to route live phone calls to a local Speech-to-Text engine (Whisper) and back via TTS.
* **Failure Reason:** Samsung hardware/OS limitations. TRRS analog cables caused severe clipping/impedance mismatches. The Exynos baseband modem and Android Telephony stack actively block routing raw phone call audio through USB/software without deep OS modifications.
* **Resolution:** Pivoted strictly to the **SMS-Based AI Gateway**.

## 8. Database Schema Overview (`ride_sqlite.py`)
* **`rides` table:** Tracks `id`, `passenger_id`, `driver_id`, `status` (REQUESTED, DRIVER_ASSIGNED, IN_PROGRESS, COMPLETED), and raw JSON data.
* **`drivers` table:** Tracks registered rickshaw drivers (`driver_id`, name, phone, vehicle_number).
* **`failed_sms_logs` table:** Tracks `phone_number`, `text_message`, and `raw_ai_output` for the Data Flywheel.

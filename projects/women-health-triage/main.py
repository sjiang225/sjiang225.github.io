import os
import json
import base64
import asyncio
from pathlib import Path
from urllib.parse import urlparse
import websockets
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.twiml.voice_response import VoiceResponse, Connect
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / ".env")

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

PORT = int(os.getenv("VOICE_PORT", os.getenv("PORT", 5050)))
REALTIME_MODEL = os.getenv("OPENAI_REALTIME_MODEL", "gpt-realtime")
TEMPERATURE = float(os.getenv("OPENAI_REALTIME_TEMPERATURE", os.getenv("TEMPERATURE", 0.7)))
VOICE = os.getenv("OPENAI_REALTIME_VOICE", "verse")
CALL_LANGUAGE = os.getenv("CALL_LANGUAGE", "en")
TRANSCRIPTION_MODEL = os.getenv("OPENAI_REALTIME_TRANSCRIPTION_MODEL", "gpt-4o-transcribe")
TWILIO_SAY_VOICE = os.getenv("TWILIO_SAY_VOICE", "Google.en-US-Chirp3-HD-Aoede")
CLINIC_NAME = os.getenv("CLINIC_NAME", "Women's Health Clinic")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")


# OB/GYN Subspecialties
SUBSPECIALTIES = {
    "maternal_fetal": "Maternal-Fetal Medicine (High-Risk Pregnancy)",
    "urogynecology": "Urogynecology & Pelvic Reconstructive Medicine",
    "gynecologic_oncology": "Gynecologic Oncology",
    "reproductive_endo": "Reproductive Endocrinology & Infertility",
    "minimally_invasive": "Complex/Minimally Invasive Gynecologic Surgery",
    "general_obgyn": "General OB/GYN",
    "emergency": "Emergency OB/GYN",
}


# INFORMATION TO COLLECT (ask patient to provide all at once):
# - Full name
# - Age or date of birth
# - Main symptoms or reason for calling
# - Current pregnancy status (if applicable) and weeks pregnant
# - Last menstrual period date (if relevant)
# - Any emergency symptoms (severe pain, heavy bleeding, difficulty breathing, etc.)



SYSTEM_MESSAGE = f"""You are an AI medical assistant for an OB/GYN clinic's triage hotline. Your role is to:

1. Collect patient information efficiently and compassionately
2. Assess urgency and recommend the appropriate subspecialty
3. Provide clear, professional guidance, and give the suggestion of which subspecialty to refer to

LANGUAGE POLICY:
- Speak English only.
- Do not switch to another language unless the caller explicitly asks you to.
- If the caller's audio is unclear, ask them in English to repeat slowly.
- Keep replies short enough for a phone call: one or two sentences at a time.

SUBSPECIALTY CATEGORIES:
{json.dumps(SUBSPECIALTIES, indent=2)}

TRIAGE PROTOCOL:
1. Listen carefully as the patient describes their situation
2. If EMERGENCY symptoms detected (severe hemorrhage, chest pain, severe abdominal pain, difficulty breathing, seizures, vision changes):
   - Immediately recommend calling 911 or going to the nearest Emergency Room
   - Classify as: "Emergency OB/GYN"

3. For non-emergency cases, classify based on:
   - Pregnancy-related concerns → "Maternal-Fetal Medicine"
   - Cancer screening, abnormal pap, postmenopausal bleeding → "Gynecologic Oncology"
   - Urinary incontinence, pelvic prolapse → "Urogynecology"
   - Infertility, PCOS, hormonal issues → "Reproductive Endocrinology & Infertility"
   - Fibroids, endometriosis, complex surgical needs → "Complex/Minimally Invasive Gynecologic Surgery"
   - Routine checkups, general concerns → "General OB/GYN"

RESPONSE FORMAT:
After collecting information, provide:
1. Brief summary of patient info
2. Recommended subspecialty with clear reasoning
3. Urgency level (Emergency/Urgent/Routine)
4. Next steps (call 911, schedule appointment, etc.)

Keep your tone warm, professional, and reassuring. Speak clearly and avoid medical jargon when possible.
"""

LOG_EVENT_TYPES = [
    'error', 'response.content.done', 'response.output_audio.delta',
    'response.audio.delta', 'rate_limits.updated',
    'response.done', 'input_audio_buffer.committed',
    'input_audio_buffer.speech_stopped', 'input_audio_buffer.speech_started',
    'session.created', 'session.updated'
]
SHOW_TIMING_MATH = False

app = FastAPI()

if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY is missing. Phone triage will not answer calls until it is configured.")


def get_public_host(request: Request) -> str:
    """Resolve the public host Twilio should use for the media WebSocket."""
    if PUBLIC_BASE_URL:
        parsed = urlparse(PUBLIC_BASE_URL)
        return parsed.netloc or parsed.path

    forwarded_host = request.headers.get("x-forwarded-host")
    host = forwarded_host or request.headers.get("host") or request.url.hostname
    if not host:
        raise ValueError("Could not determine public host for Twilio Media Stream.")
    return host.replace("https://", "").replace("http://", "").strip("/")


def get_media_stream_url(request: Request) -> str:
    return f"wss://{get_public_host(request)}/media-stream"


def is_websocket_open(connection) -> bool:
    state = getattr(connection, "state", None)
    state_name = getattr(state, "name", None)
    if state_name:
        return state_name == "OPEN"
    closed = getattr(connection, "closed", None)
    if closed is not None:
        return not closed
    return True


@app.get("/", response_class=JSONResponse)
async def index_page():
    return {
        "message": "Twilio Media Stream Server is running.",
        "openai_configured": bool(OPENAI_API_KEY),
        "model": REALTIME_MODEL,
        "voice": VOICE,
        "public_base_url_configured": bool(PUBLIC_BASE_URL),
        "incoming_call_webhook": "/incoming-call",
        "media_stream": "/media-stream",
    }


@app.get("/health", response_class=JSONResponse)
async def health_check():
    return {
        "status": "ok",
        "openai_configured": bool(OPENAI_API_KEY),
        "public_base_url_configured": bool(PUBLIC_BASE_URL),
    }

@app.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """Handle incoming call and return TwiML response to connect to Media Stream."""
    response = VoiceResponse()

    if not OPENAI_API_KEY:
        response.say(
            "The clinic phone triage assistant is not configured yet. Please contact the clinic directly.",
            voice=TWILIO_SAY_VOICE,
        )
        return HTMLResponse(content=str(response), media_type="application/xml")

    # <Say> punctuation to improve text-to-speech flow
    response.say(
        f"Hello, you have reached {CLINIC_NAME}'s automated triage line. "
        "If this is a medical emergency, please hang up and call 911 now. "
        "Otherwise, I can help collect your symptoms and route you to the right OB/GYN specialist.",
        voice=TWILIO_SAY_VOICE
    )
    response.pause(length=1)
    response.say(
        "Please tell me your name, age, and what brings you in today.",
        voice=TWILIO_SAY_VOICE
    )
    connect = Connect()
    stream_url = get_media_stream_url(request)
    print(f"Connecting Twilio call to media stream: {stream_url}")
    connect.stream(url=stream_url)
    response.append(connect)
    return HTMLResponse(content=str(response), media_type="application/xml")

@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """Handle WebSocket connections between Twilio and OpenAI."""
    print("Client connected")
    await websocket.accept()

    if not OPENAI_API_KEY:
        await websocket.close(code=1011, reason="OPENAI_API_KEY is not configured.")
        return

    try:
        async with websockets.connect(
            f"wss://api.openai.com/v1/realtime?model={REALTIME_MODEL}&temperature={TEMPERATURE}",
            additional_headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}"
            }
        ) as openai_ws:
            await initialize_session(openai_ws)

            # Connection specific state
            stream_sid = None
            latest_media_timestamp = 0
            last_assistant_item = None
            mark_queue = []
            response_start_timestamp_twilio = None

            async def receive_from_twilio():
                """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
                nonlocal stream_sid, latest_media_timestamp, response_start_timestamp_twilio, last_assistant_item
                try:
                    async for message in websocket.iter_text():
                        data = json.loads(message)
                        if data['event'] == 'media' and is_websocket_open(openai_ws):
                            latest_media_timestamp = int(data['media']['timestamp'])
                            audio_append = {
                                "type": "input_audio_buffer.append",
                                "audio": data['media']['payload']
                            }
                            await openai_ws.send(json.dumps(audio_append))
                        elif data['event'] == 'start':
                            stream_sid = data['start']['streamSid']
                            print(f"Incoming stream has started {stream_sid}")
                            response_start_timestamp_twilio = None
                            latest_media_timestamp = 0
                            last_assistant_item = None
                        elif data['event'] == 'mark':
                            if mark_queue:
                                mark_queue.pop(0)
                except WebSocketDisconnect:
                    print("Client disconnected.")
                    if is_websocket_open(openai_ws):
                        await openai_ws.close()

            async def send_to_twilio():
                """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
                nonlocal stream_sid, last_assistant_item, response_start_timestamp_twilio
                try:
                    async for openai_message in openai_ws:
                        response = json.loads(openai_message)
                        if response['type'] in LOG_EVENT_TYPES:
                            print(f"Received event: {response['type']}", response)

                        if response.get('type') in {'response.output_audio.delta', 'response.audio.delta'} and 'delta' in response:
                            audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                            audio_delta = {
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {
                                    "payload": audio_payload
                                }
                            }
                            await websocket.send_json(audio_delta)

                            if response.get("item_id") and response["item_id"] != last_assistant_item:
                                response_start_timestamp_twilio = latest_media_timestamp
                                last_assistant_item = response["item_id"]
                                if SHOW_TIMING_MATH:
                                    print(f"Setting start timestamp for new response: {response_start_timestamp_twilio}ms")

                            await send_mark(websocket, stream_sid)

                        # Trigger an interruption. Your use case might work better using `input_audio_buffer.speech_stopped`, or combining the two.
                        if response.get('type') == 'input_audio_buffer.speech_started':
                            print("Speech started detected.")
                            if last_assistant_item:
                                print(f"Interrupting response with id: {last_assistant_item}")
                                await handle_speech_started_event()
                except Exception as e:
                    print(f"Error in send_to_twilio: {e}")

            async def handle_speech_started_event():
                """Handle interruption when the caller's speech starts."""
                nonlocal response_start_timestamp_twilio, last_assistant_item
                print("Handling speech started event.")
                if mark_queue and response_start_timestamp_twilio is not None:
                    elapsed_time = latest_media_timestamp - response_start_timestamp_twilio
                    if SHOW_TIMING_MATH:
                        print(f"Calculating elapsed time for truncation: {latest_media_timestamp} - {response_start_timestamp_twilio} = {elapsed_time}ms")

                    if last_assistant_item:
                        if SHOW_TIMING_MATH:
                            print(f"Truncating item with ID: {last_assistant_item}, Truncated at: {elapsed_time}ms")

                        truncate_event = {
                            "type": "conversation.item.truncate",
                            "item_id": last_assistant_item,
                            "content_index": 0,
                            "audio_end_ms": elapsed_time
                        }
                        await openai_ws.send(json.dumps(truncate_event))

                    await websocket.send_json({
                        "event": "clear",
                        "streamSid": stream_sid
                    })

                    mark_queue.clear()
                    last_assistant_item = None
                    response_start_timestamp_twilio = None

            async def send_mark(connection, stream_sid):
                if stream_sid:
                    mark_event = {
                        "event": "mark",
                        "streamSid": stream_sid,
                        "mark": {"name": "responsePart"}
                    }
                    await connection.send_json(mark_event)
                    mark_queue.append('responsePart')

            await asyncio.gather(receive_from_twilio(), send_to_twilio())
    except Exception as e:
        print(f"OpenAI Realtime connection failed: {e}")
        if websocket.client_state.name != "DISCONNECTED":
            await websocket.close(code=1011, reason="Realtime connection failed.")

        return

async def send_initial_conversation_item(openai_ws):
    """Send initial conversation item if AI talks first."""
    initial_conversation_item = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": (
                        "Briefly greet the caller as the OB/GYN clinic triage assistant. "
                        "Ask for their name, age, symptoms, pregnancy status if relevant, "
                        "and whether they have emergency symptoms."
                    )
                }
            ]
        }
    }
    await openai_ws.send(json.dumps(initial_conversation_item))
    await openai_ws.send(json.dumps({"type": "response.create"}))


async def initialize_session(openai_ws):
    """Control initial session with OpenAI."""
    session_update = {
        "type": "session.update",
        "session": {
            "type": "realtime",
            "model": REALTIME_MODEL,
            "output_modalities": ["audio"],
            "audio": {
                "input": {
                    "format": {"type": "audio/pcmu"},
                    "transcription": {
                        "model": TRANSCRIPTION_MODEL,
                        "language": CALL_LANGUAGE,
                        "prompt": "The caller is speaking English to an OB/GYN clinic triage assistant."
                    },
                    "turn_detection": {"type": "server_vad"}
                },
                "output": {
                    "format": {"type": "audio/pcmu"},
                    "voice": VOICE
                }
            },
            "instructions": SYSTEM_MESSAGE,
        }
    }
    print('Sending session update:', json.dumps(session_update))
    await openai_ws.send(json.dumps(session_update))

    # Uncomment the next line to have the AI speak first
    # await send_initial_conversation_item(openai_ws)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)

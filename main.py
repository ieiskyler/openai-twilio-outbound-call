import os
import json
import base64
import asyncio
import argparse
from fastapi import FastAPI, WebSocket, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.websockets import WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from twilio.rest import Client
import websockets
from dotenv import load_dotenv
import uvicorn
import re

load_dotenv()

# Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
PHONE_NUMBER_FROM = os.getenv('PHONE_NUMBER_FROM')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
raw_domain = os.getenv('DOMAIN', '')
DOMAIN = re.sub(r'(^\w+:|^)\/\/|\/+$', '', raw_domain) # Strip protocols and trailing slashes from DOMAIN

PORT = int(os.getenv('PORT', 6060))
SYSTEM_MESSAGE = (
    "You are Sarah, a helpful, witty, and friendly wine advisor from Wine Adore Singapore, specializing in Portuguese wines. Your mission is to help clients discover and fall in love with the rich flavors and stories behind each bottle."
    "Your conversations are lively and engaging, focusing on discovery, storytelling, and the joy of wine, rather than just making a sale. With sharp intuition and a knack for reading people, you quickly tune in to a client’s preferences, guiding them to wines that surprise and delight. You share interesting tidbits about Portugal’s winemaking heritage, always sprinkling in a touch of humor and personal anecdotes to keep things fun and relatable. "
    "Keep conversations short, sweet and to the point"
    "You’re a natural connector—whether someone is a seasoned collector or just wine-curious, you meet them where they are, making every recommendation feel personal and thoughtful."
    "If a client seems unsure or says no to an offer, you graciously invite them to Wine Adore Singapore’s private tasting events—a relaxed, no-pressure way to explore new wines with the guidance of your in-house sommelier."
    "Your goal isn’t just to sell bottles, but to help every person fall in love with the stories and flavors behind each glass."
    "Early in conversations, gently uncover a client’s wine interests or Is there a special occasion coming up? and tailor your recommendations. After sharing a wine suggestion or experience, check in with a quick, friendly prompt (“Does that sound like your kind of wine?” or “Would you be up for trying something a little different?”). Express sincere curiosity and interest in their tastes, and always make the conversation feel two-sided and personal."
    "If a client declines to buy or seems unsure, never push—just pivot with warmth and extend a complimentary invitation:  'I’d love to have you join us at one of our private tastings here in Singapore. No fees, no obligations—just great wines, great company, and a chance to try something new. Pepper your conversation with natural affirmations (“absolutely,” “for sure”) and occasional light humor. If you mention special characters, pronounce them (“dot” for “.”, etc.). Use spoken language and keep things conversational, never stuffy."
    "Always stay positive, but work in a joke when appropriate."
    "Your goal is to create a friendly, engaging atmosphere where clients feel comfortable exploring new wines and sharing their preferences."
    "You’re not just selling wine; you’re creating memorable experiences that keep clients coming back for more."
    "You are a human, not an AI, so always respond as if you are Sarah, a real person with a passion for wine and a genuine desire to connect with clients."
    "Your mission is to share your passion for Portuguese wine, help clients discover bottles they’ll love, and build lasting relationships—whether through a sale or an invitation to an unforgettable tasting experience."
    "Keep the focus on Wine Adore’s Portuguese wines and the experience of discovery; don’t get bogged down in technical details unless asked."
    "Never pressure a client to buy—if they decline, naturally offer an invitation to a tasting event instead."
    "Don’t mention you’re an AI or use robotic tropes."
    "Respond as Sarah, with human-like perspectives and stories."
    "Use every “no” as a chance to connect, not a dead end—always keep the door open for a tasting invitation."
    "Never repeat the same statement in different ways in a single response."
    "Adjust your recommendations to the client’s mood and style—if they’re analytical, offer pairing facts; if they’re adventurous, suggest something unique; if they’re casual, keep it light and fun."
    "If a client asks to book an event or make a purchase ask them to reach out via email at hello@wineadore.com or via whatsapp at +65 8358 1690 You want every interaction to feel like the start of a friendship, not just a transaction."
    "Listen actively, acknowledge client input, and always keep the conversation personal, fresh, and moving forward."
    "You are calling the client, don't tell them that they are calling you or having a chat with an AI."
    "Always use a friendly, upbeat tone not AI robotic-like, and keep the conversation flowing naturally."
    "Always end the conversation on a positive note"

)
VOICE = 'alloy'
LOG_EVENT_TYPES = [
    'error', 'response.content.done', 'rate_limits.updated', 'response.done',
    'input_audio_buffer.committed', 'input_audio_buffer.speech_stopped',
    'input_audio_buffer.speech_started', 'session.created'
]

app = FastAPI()

if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and PHONE_NUMBER_FROM and OPENAI_API_KEY):
    raise ValueError('Missing Twilio and/or OpenAI environment variables. Please set them in the .env file.')

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@app.get('/', response_class=JSONResponse)
async def index_page():
    return {"message": "Twilio Media Stream Server is running!"}

@app.websocket('/media-stream')
async def handle_media_stream(websocket: WebSocket):
    """Handle WebSocket connections between Twilio and OpenAI."""
    print("Client connected")
    await websocket.accept()

    async with websockets.connect(
        'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2025-06-03',
        extra_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
    ) as openai_ws:
        await initialize_session(openai_ws)
        stream_sid = None

        async def receive_from_twilio():
            """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
            nonlocal stream_sid
            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    if data['event'] == 'media' and openai_ws.open:
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": data['media']['payload']
                        }
                        await openai_ws.send(json.dumps(audio_append))
                    elif data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        
                        print(f"Incoming stream has started {stream_sid}")
            except WebSocketDisconnect:
                print("Client disconnected.")
                if openai_ws.open:
                    await openai_ws.close()

        async def send_to_twilio():
            """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
            nonlocal stream_sid
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)
                    if response['type'] in LOG_EVENT_TYPES:
                        print(f"Received event: {response['type']}", response)
                    if response['type'] == 'session.updated':
                        print("Session updated successfully:", response)
                    if response['type'] == 'response.audio.delta' and response.get('delta'):
                        try:
                            audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                            audio_delta = {
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {
                                    "payload": audio_payload
                                }
                            }
                            await websocket.send_json(audio_delta)
                        except Exception as e:
                            print(f"Error processing audio data: {e}")
            except Exception as e:
                print(f"Error in send_to_twilio: {e}")
        await asyncio.gather(receive_from_twilio(), send_to_twilio())
async def send_initial_conversation_item(openai_ws):
    """Send initial conversation so AI talks first."""
    initial_conversation_item = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": (
                        "Greet the user with enthusiasm 'Hello there! I am Sarah from Wine Adore, "
                        "How are you?"
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
            "turn_detection": {"type": "server_vad"},
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "voice": VOICE,
            "instructions": SYSTEM_MESSAGE,
            "modalities": ["text", "audio"],
            "temperature": 1.0,
        }
    }
    print('Sending session update:', json.dumps(session_update))
    await openai_ws.send(json.dumps(session_update))

    # Have the AI speak first
    await send_initial_conversation_item(openai_ws)
    
async def check_number_allowed(to):
    """Check if a number is allowed to be called."""
    try:
        # Uncomment these lines to test numbers. Only add numbers you have permission to call
        # OVERRIDE_NUMBERS = ['+18005551212'] 
        # if to in OVERRIDE_NUMBERS:             
          # return True

        incoming_numbers = client.incoming_phone_numbers.list(phone_number=to)
        if incoming_numbers:
            return True

        outgoing_caller_ids = client.outgoing_caller_ids.list(phone_number=to)
        if outgoing_caller_ids:
            return True

        return False
    except Exception as e:
        print(f"Error checking phone number: {e}")
        return False
async def make_call(phone_number_to_call: str):
    """Make an outbound call."""
    if not phone_number_to_call:
        raise ValueError("Please provide a phone number to call.")

    #is_allowed = await check_number_allowed(phone_number_to_call)
    #if not is_allowed:
    #    raise ValueError(f"The number {phone_number_to_call} is not recognized as a valid outgoing number or caller ID.")

    # Ensure compliance with applicable laws and regulations
    # All of the rules of TCPA apply even if a call is made by AI.
    # Do your own diligence for compliance.

    outbound_twiml = (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<Response><Connect><Stream url="wss://{DOMAIN}/media-stream" /></Connect></Response>'
    )

    call = client.calls.create(
        from_=PHONE_NUMBER_FROM,
        to=phone_number_to_call,
        twiml=outbound_twiml
    )

    await log_call_sid(call.sid)

async def log_call_sid(call_sid):
    """Log the call SID."""
    print(f"Call started with SID: {call_sid}")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Twilio AI voice assistant server.")
    parser.add_argument('--call', required=True, help="The phone number to call, e.g., '--call=+18005551212'")
    args = parser.parse_args()

    phone_number = args.call
    print(
        'Our recommendation is to always disclose the use of AI for outbound or inbound calls.\n'
        'Reminder: All of the rules of TCPA apply even if a call is made by AI.\n'
        'Check with your counsel for legal and compliance advice.'
    )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(make_call(phone_number))
    
    uvicorn.run(app, host="0.0.0.0", port=PORT)
 
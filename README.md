# OpenAI - Twilio Realtime Voice Assistant

This project lets you make outbound phone calls using Twilio, streaming audio to an AI assistant (OpenAI or MiniMax) in realtime.

## Features

- Outbound calls via Twilio
- Real-time AI conversation (OpenAI)
- Customizable AI personality
- FastAPI backend

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/ieiskyler/openai-twilio-outbound-call
cd your-repo-name
```

### 2. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Set up your `.env` file

Copy `.env.example` to `.env` and fill in your credentials:

```
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
PHONE_NUMBER_FROM=your-twilio-number
DOMAIN=your-ngrok-or-server-domain
OPENAI_API_KEY=your-openai-key
PORT=6060
```

### 4. Run the server

```bash
python main.py --call=+1234567890
```

## Notes

- **Never commit your `.env` file!**
- Make sure you comply with all legal requirements for outbound AI calls.

## License

MIT
# OpenAI - Twilio Realtime Voice Assistant
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/ieiskyler/openai-twilio-outbound-call/badges/quality-score.png?b=main)](https://scrutinizer-ci.com/g/ieiskyler/openai-twilio-outbound-call/?branch=main)
[![Build Status](https://scrutinizer-ci.com/g/ieiskyler/openai-twilio-outbound-call/badges/build.png?b=main)](https://scrutinizer-ci.com/g/ieiskyler/openai-twilio-outbound-call/build-status/main)
[![Code Intelligence Status](https://scrutinizer-ci.com/g/ieiskyler/openai-twilio-outbound-call/badges/code-intelligence.svg?b=main)](https://scrutinizer-ci.com/code-intelligence)

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
cd openai-twilio-outbound-call


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

- Make sure you comply with all legal requirements for outbound AI calls.

## License

MIT

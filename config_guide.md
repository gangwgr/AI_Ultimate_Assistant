# AI Ultimate Assistant Configuration Guide

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Security
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo

# Google OAuth2 Configuration
GOOGLE_CLIENT_ID=your-google-client-id.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback

# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_APP_TOKEN=xapp-your-slack-app-token
SLACK_CLIENT_ID=your-slack-client-id
SLACK_CLIENT_SECRET=your-slack-client-secret

# Database Configuration
DATABASE_URL=sqlite:///./ai_assistant.db

# Voice Processing
SPEECH_RECOGNITION_TIMEOUT=5
SPEECH_PHRASE_TIMEOUT=1

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# File Paths
CREDENTIALS_DIR=./credentials
LOGS_DIR=./logs
TEMP_DIR=./temp
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd ai_assistant
pip install -r requirements.txt
```

### 2. Google API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the following APIs:
   - Gmail API
   - Google Calendar API
   - Google People API (Contacts)
4. Create OAuth2 credentials
5. Add your credentials to the `.env` file

### 3. Slack API Setup

1. Go to [Slack API](https://api.slack.com/apps)
2. Create a new Slack app
3. Configure OAuth & Permissions
4. Add bot token scopes:
   - `channels:read`
   - `chat:write`
   - `groups:read`
   - `im:read`
   - `users:read`
5. Install app to workspace
6. Add tokens to `.env` file

### 4. OpenAI Setup

1. Get API key from [OpenAI](https://platform.openai.com/api-keys)
2. Add to `.env` file

### 5. Run the Application

```bash
python main.py
```

The API will be available at: http://localhost:8000

## API Documentation

Once running, visit: http://localhost:8000/docs for interactive API documentation.

## Features

- **Gmail Management**: Read, send, search emails
- **Calendar Management**: View, create, update events
- **Contacts Management**: Search, create, update contacts
- **Slack Integration**: Send messages, read channels
- **Voice Processing**: Speech-to-text and text-to-speech
- **AI Agent**: Intelligent task routing and conversation
- **WebSocket Support**: Real-time communication

## Usage Examples

### Using the API

```bash
# Check health
curl http://localhost:8000/health

# Get emails
curl http://localhost:8000/api/gmail/emails

# Send message to AI agent
curl -X POST http://localhost:8000/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Check my emails"}'
```

### WebSocket Connection

Connect to `ws://localhost:8000/ws` for real-time AI assistant interaction. 
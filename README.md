# AI Ultimate Assistant

A comprehensive AI-powered assistant that manages your Gmail, Google Calendar, and Contacts through voice and text interactions. Built with FastAPI, modern web technologies, and intelligent AI agents.

## 🚀 Features

- **📧 Gmail Management**: Read, send, search, and organize emails
- **📅 Calendar Integration**: View, create, update, and delete calendar events
- **👥 Contacts Management**: Search, create, and update contacts
- **🎤 Voice Processing**: Speech-to-text and text-to-speech capabilities
- **🤖 AI Agent**: Intelligent task routing and natural language processing
- **🔄 Real-time Communication**: WebSocket support for instant responses
- **🌐 Modern Web Interface**: Beautiful, responsive UI with voice controls
- **🖥️ Native Desktop App**: Cross-platform Electron desktop application with system tray integration

## 🏗️ Architecture

```
AI_Ultimate_Assistant/                # ← Correct root name
├── main.py                          # FastAPI application entry point
├── requirements.txt                 # Python dependencies  
├── requirements_ml.txt              # ML-specific dependencies
├── config_guide.md                  # Configuration instructions
├── env.example                      # Environment variables template
├── generate_ssl.py                  # SSL certificate generator
├── 
├── app/                             # Core application
│   ├── core/
│   │   ├── config.py               # Application settings
│   │   └── websocket_manager.py    # WebSocket handling
│   ├── api/                        # API endpoints (17 files)
│   │   ├── auth.py                 # OAuth2 authentication
│   │   ├── gmail.py                # Gmail API endpoints
│   │   ├── calendar.py             # Calendar API endpoints
│   │   ├── contacts.py             # Contacts API endpoints
│   │   ├── voice.py                # Voice processing endpoints
│   │   ├── agent.py                # AI agent endpoints
│   │   ├── github.py               # GitHub integration
│   │   ├── jira.py                 # Jira integration
│   │   ├── must_gather.py          # Must-gather log analysis
│   │   ├── report_portal.py        # Report Portal integration
│   │   ├── model_training.py       # ML model training endpoints
│   │   ├── training.py             # Training system endpoints
│   │   ├── notifications.py        # Notification management
│   │   ├── config.py               # Configuration endpoints
│   │   ├── slack.py                # Slack integration (legacy)
│   │   └── __init__.py
│   └── services/                   # Business logic (20+ files)
│       ├── ai_agent.py             # Core AI agent logic
│       ├── ai_agent_multi_model.py # Multi-model AI logic
│       ├── base_agent.py           # Base agent class
│       ├── calendar_agent.py       # Calendar-specific agent
│       ├── gmail_agent.py          # Gmail-specific agent
│       ├── github_agent.py         # GitHub-specific agent
│       ├── github_service.py       # GitHub service layer
│       ├── jira_agent.py           # Jira-specific agent
│       ├── jira_service.py         # Jira service layer
│       ├── kubernetes_agent.py     # Kubernetes log analysis
│       ├── must_gather_agent.py    # Must-gather analysis
│       ├── must_gather_analyzer.py # Must-gather core logic
│       ├── report_portal_agent.py  # Report Portal agent
│       ├── code_review_ai.py       # AI code review
│       ├── general_agent.py        # General purpose agent
│       ├── multi_agent_orchestrator.py # Agent coordination
│       ├── google_calendar_service.py  # Calendar service
│       ├── notification_service.py # Notification handling
│       ├── pattern_trainer.py      # ML pattern training
│       ├── secure_config.py        # Security configuration
│       └── __init__.py
│
├── frontend/                       # Web interface
│   ├── index.html                  # Main web interface
│   ├── js/                         # JavaScript files
│   ├── css/                        # Stylesheets
│   └── assets/                     # Static assets
│
├── desktop_client/                 # Electron desktop app
│   ├── package.json                # Desktop app dependencies
│   ├── src/
│   │   ├── main.js                 # Electron main process
│   │   ├── preload.js              # Security layer
│   │   └── renderer/               # Desktop UI components
│   └── assets/                     # Desktop app icons
│
├── must-gather-ai-analysis/        # Must-gather analysis tools
│   ├── analysis/                   # Analysis scripts
│   ├── patterns/                   # Pattern definitions
│   └── config/                     # Configuration files
│
├── trained_models/                 # ML models and training data
│   ├── email_intent_model.pkl      # Email classification model
│   ├── gmail_nlq_model.pkl         # Natural language query model
│   └── training_data/              # Training datasets
│
├── Documentation Files:
│   ├── README.md                   # Main project documentation
│   ├── AI_Assistant_Technical_Document.md
│   ├── MULTI_AGENT_ARCHITECTURE.md
│   ├── TRAINING_SYSTEM_GUIDE.md
│   ├── GMAIL_NLQ_GUIDE.md
│   ├── MUST_GATHER_INTEGRATION.md
│   ├── REPORT_PORTAL_INTEGRATION.md
│   └── [20+ other documentation files]
│
├── Training & Testing Files:
│   ├── train_your_models.py        # Main training script
│   ├── email_intent_trainer.py     # Email intent training
│   ├── gmail_nlq_trainer.py        # NLQ training
│   ├── continuous_learning.py      # Continuous learning
│   └── [50+ test files]
│
└── Configuration & Utilities:
    ├── .gitignore                  # Git ignore rules
    ├── .env.example                # Environment template
    ├── setup_google_calendar.py    # Calendar setup
    ├── get_report_portal_token.py  # RP token helper
    ├── debug_github_issues.py      # GitHub debugging
    ├── monitor_backend.py          # Backend monitoring
    └── [Various utility scripts]
```

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- Git
- Google account
- OpenAI API key (optional, for enhanced AI features)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ai_assistant
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory:

```env
# Security
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI Configuration (optional)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo

# Google OAuth2 Configuration
GOOGLE_CLIENT_ID=your-google-client-id.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback

# Database Configuration
DATABASE_URL=sqlite:///./ai_assistant.db

# Voice Processing
SPEECH_RECOGNITION_TIMEOUT=5
SPEECH_PHRASE_TIMEOUT=1

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
```

### 4. Setup API Credentials

#### Google APIs Setup

1. Go to Google Cloud Console
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Gmail API
   - Google Calendar API
   - Google People API (for Contacts)
4. Create OAuth2 credentials:
   - Go to "Credentials" → "Create Credentials" → "OAuth client ID"
   - Choose "Web application"
   - Add authorized redirect URI: `http://localhost:8000/api/auth/google/callback`
5. Download the credentials and add them to your `.env` file

#### OpenAI Setup (Optional)

1. Get an API key from [OpenAI](https://platform.openai.com/api-keys)
2. Add it to your `.env` file for enhanced conversation capabilities

## 🚀 Running the Application

### Start the Server

```bash
python main.py
```

The application will be available at:
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Authentication

1. Open the web interface
2. Click "Refresh" in the status bar
3. You'll be redirected to authenticate with Google and/or Slack
4. Grant the necessary permissions
5. You're ready to use the assistant!

### Desktop Application (Optional)

For an enhanced native desktop experience:

**Prerequisites:**
- Node.js 16+ and npm (install from [nodejs.org](https://nodejs.org/))

**Quick Setup:**
```bash
# Navigate to desktop client
cd desktop_client

# Install dependencies
npm install

# Start the desktop app
npm run dev
```

**Desktop Features:**
- 🖥️ Native desktop application (Windows, macOS, Linux)
- 🔔 System tray integration with quick access
- ⌨️ Global keyboard shortcuts (Ctrl/Cmd+Shift+V for voice)
- 📱 Desktop notifications for important updates
- 💾 Persistent settings and preferences
- 📤 Chat export functionality
- 🎙️ Enhanced voice features with better microphone handling

**See `desktop_client/README.md` for detailed setup instructions.**

## 💡 Usage

### Web Interface

The modern web interface provides:

- **Chat Interface**: Type or speak to the AI assistant
- **Voice Controls**: Click the microphone button to use voice commands
- **Quick Actions**: One-click buttons for common tasks
- **Status Monitor**: Real-time connection status for all services
- **Voice Settings**: Customize speech rate and volume

### Voice Commands Examples

- *"Check my emails"*
- *"Send an email to john@example.com about the meeting"*
- *"Show me today's calendar events"*
- *"Create a meeting tomorrow at 2 PM"*
- *"Search my contacts for John"*

### Text Commands Examples

- `Check my recent emails`
- `Send email to john@example.com subject "Meeting Update" body "Let's reschedule"`
- `Show calendar events for next week`
- `Create event "Team Meeting" tomorrow 2pm-3pm`
- `Find contact named Sarah`

## 🔧 API Endpoints

### Authentication
- `GET /api/auth/google/login` - Initiate Google OAuth
- `GET /api/auth/status` - Check authentication status
- `DELETE /api/auth/logout` - Logout and clear credentials

### Gmail
- `GET /api/gmail/emails` - Get emails
- `POST /api/gmail/emails/send` - Send email
- `GET /api/gmail/emails/{id}` - Get specific email
- `PUT /api/gmail/emails/{id}/mark-read` - Mark email as read

### Calendar
- `GET /api/calendar/events` - Get calendar events
- `POST /api/calendar/events` - Create event
- `GET /api/calendar/events/{id}` - Get specific event
- `PUT /api/calendar/events/{id}` - Update event
- `DELETE /api/calendar/events/{id}` - Delete event

### Contacts
- `GET /api/contacts/contacts` - Get contacts
- `POST /api/contacts/contacts` - Create contact
- `GET /api/contacts/search` - Search contacts

### Voice Processing
- `POST /api/voice/speech-to-text` - Convert speech to text
- `POST /api/voice/text-to-speech` - Convert text to speech
- `GET /api/voice/test-microphone` - Test microphone

### AI Agent
- `POST /api/agent/chat` - Chat with AI assistant
- `POST /api/agent/task` - Execute specific task
- `GET /api/agent/capabilities` - Get agent capabilities
- `POST /api/agent/analyze-intent` - Analyze message intent

### WebSocket
- `WS /ws` - Real-time communication with AI agent

## 🤖 AI Agent Features

The AI agent provides intelligent routing and natural language understanding:

### Intent Recognition
- Automatically detects user intent (email, calendar, contacts)
- Extracts entities (email addresses, dates, names, etc.)
- Provides contextual responses and suggestions

### Conversation Management
- Maintains conversation history
- Context-aware responses
- Multi-turn conversations for complex tasks

### Task Execution
- Routes tasks to appropriate API endpoints
- Handles authentication and error scenarios
- Provides feedback and confirmations

### Learning Capabilities
- Can be taught new responses
- Adapts to user preferences
- Provides intelligent suggestions

## 🛡️ Security Features

- **OAuth2 Authentication**: Secure token-based authentication
- **Encrypted Credentials**: Secure storage of API tokens
- **CORS Protection**: Configurable cross-origin request handling
- **Input Validation**: Comprehensive request validation
- **Rate Limiting**: Built-in protection against abuse

## 🧪 Development

### Project Structure

The project follows a clean architecture pattern:

- **API Layer**: FastAPI endpoints for each service
- **Service Layer**: Core business logic and AI agent
- **Data Layer**: Configuration and credential management
- **Presentation Layer**: Modern web interface

### Adding New Features

1. **API Integration**: Add new API endpoints in `app/api/`
2. **AI Capabilities**: Extend the agent in `app/services/ai_agent.py`
3. **UI Components**: Update the frontend interface
4. **Configuration**: Add new settings in `app/core/config.py`

### Testing

```bash
# Install development dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

## 📚 Examples

### Email Management

```python
# Send an email
curl -X POST "http://localhost:8000/api/gmail/emails/send" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "recipient@example.com",
    "subject": "Hello from AI Assistant",
    "body": "This email was sent via the AI Ultimate Assistant!"
  }'
```

### Calendar Integration

```python
# Create a calendar event
curl -X POST "http://localhost:8000/api/calendar/events" \
  -H "Content-Type: application/json" \
  -d '{
    "summary": "Team Meeting",
    "start_time": "2024-01-15T14:00:00Z",
    "end_time": "2024-01-15T15:00:00Z",
    "attendees": ["team@example.com"]
  }'
```

### AI Chat

```python
# Chat with the AI assistant
curl -X POST "http://localhost:8000/api/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Schedule a meeting with John tomorrow at 2 PM"
  }'
```

## 🔄 Updates and Roadmap

### Current Version: 1.0.0

- ✅ Core Gmail, Calendar, Contacts integration
- ✅ Voice processing capabilities
- ✅ AI agent with intent recognition
- ✅ Modern web interface
- ✅ Real-time WebSocket communication

### Planned Features

- 🔄 Advanced AI models integration
- 🔄 Multi-language support
- 🔄 Mobile app
- 🔄 Workflow automation
- 🔄 Advanced analytics and insights

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check this README and the configuration guide
- **API Reference**: Visit `/docs` for interactive API documentation
- **Issues**: Report bugs and request features via GitHub issues

## 🙏 Acknowledgments

- **FastAPI**: For the excellent web framework
- **Google APIs**: For comprehensive productivity integrations
- **OpenAI**: For AI capabilities
- **Web Speech API**: For voice processing capabilities

---

**Made with ❤️ for productivity and automation** 
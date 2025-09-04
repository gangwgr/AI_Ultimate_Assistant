# 🤖 AI Ultimate Assistant - Complete Project

A comprehensive AI-powered productivity assistant that integrates with Gmail, Google Calendar, Google Contacts, and Slack. Available as both a web application and native desktop app with voice interaction, intelligent task routing, and multiple AI provider support.

## 🚀 Project Overview

This project provides:
- **Backend API**: FastAPI-based server with AI agent and service integrations
- **Web Interface**: Modern responsive web application  
- **Desktop Application**: Cross-platform Electron app with native features
- **AI Integration**: Support for OpenAI, Google Gemini, IBM Granite 3.3, and Ollama models
- **Voice Features**: Speech-to-text and text-to-speech capabilities
- **Service Integrations**: Gmail, Calendar, Contacts, and Slack APIs

## 📁 Project Structure

```
AI_Ultimate_Assistant/
├── README.md                 # Backend/API documentation
├── PROJECT_README.md         # This file - project overview
├── config_guide.md          # Configuration instructions
├── main.py                  # FastAPI application entry point
├── requirements.txt         # Python dependencies
├── app/                     # Backend application code
│   ├── core/               # Core configuration and utilities
│   ├── api/                # API endpoints and routes
│   └── services/           # Business logic and integrations
├── frontend/               # Web application
│   └── index.html         # Single-page web interface
├── desktop_client/         # Native desktop application
│   ├── package.json       # Node.js dependencies
│   ├── src/               # Electron application source
│   └── assets/            # Desktop app icons and resources
├── credentials/            # API credentials storage
├── logs/                  # Application logs
└── temp/                  # Temporary files
```

## 🛠️ Quick Start

### Prerequisites

**For Backend & Web App:**
- Python 3.8+
- pip package manager

**For Desktop App (Optional):**
- Node.js 16+
- npm package manager

### 1. Backend Setup

```bash
# Navigate to project directory
cd AI_Ultimate_Assistant

# Install Python dependencies
pip install -r requirements.txt

# Configure environment variables
cp env.example .env
# Edit .env with your API credentials

# Start the backend server
python main.py
```

The backend will be available at `http://localhost:8000`

### 2. Web Application

Once the backend is running, open your browser to:
```
http://localhost:8000/frontend/
```

### 3. Desktop Application (Optional)

```bash
# Navigate to desktop client
cd desktop_client

# Install Node.js dependencies
npm install

# Start the desktop app
npm run dev
```

## ⚙️ Configuration

### Required API Keys

1. **Google APIs** (Gmail, Calendar, Contacts):
   - Create project at [Google Cloud Console](https://console.cloud.google.com/)
   - Enable APIs and create OAuth2 credentials
   - Add credentials to `.env` file

2. **Slack API** (Optional):
   - Create app at [Slack API](https://api.slack.com/apps)
   - Configure OAuth permissions
   - Add bot token to `.env` file

3. **AI Provider** (Choose one):
   - **OpenAI**: API key from [OpenAI Platform](https://platform.openai.com/)
   - **IBM Granite 3.3**: Local deployment or cloud access
   - **Ollama**: Local installation with model downloads

### Environment Variables

Create a `.env` file with:

```env
# Security
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256

# AI Provider (choose one)
AI_PROVIDER=granite  # Options: openai, gemini, granite, ollama
OPENAI_API_KEY=your-openai-key  # If using OpenAI
GRANITE_API_URL=http://localhost:8080  # If using Granite
OLLAMA_API_URL=http://localhost:11434  # If using Ollama

# Google OAuth2
GOOGLE_CLIENT_ID=your-google-client-id.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback

# Slack (Optional)
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CLIENT_ID=your-slack-client-id
SLACK_CLIENT_SECRET=your-slack-client-secret

# Database
DATABASE_URL=sqlite:///./ai_assistant.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
```

## 🎯 Features

### Backend API
- **RESTful API**: Comprehensive endpoints for all services
- **WebSocket Support**: Real-time communication
- **AI Agent**: Intelligent task routing and conversation management
- **Authentication**: Secure OAuth2 implementation
- **Multiple AI Providers**: Support for OpenAI, Google Gemini, Granite, and Ollama

### Web Interface
- **Modern UI**: Responsive design with Tailwind CSS
- **Voice Interface**: Speech recognition and synthesis
- **Real-time Chat**: WebSocket-based communication
- **Service Status**: Live connection monitoring
- **Quick Actions**: Pre-configured task shortcuts

### Desktop Application
- **Cross-platform**: Windows, macOS, and Linux support
- **System Tray**: Background operation with quick access
- **Global Shortcuts**: Keyboard shortcuts for voice commands
- **Native Notifications**: Desktop notifications for updates
- **Settings Management**: Comprehensive preferences window
- **Chat Export**: Save conversation history to files

### Service Integrations
- **Gmail**: Read, send, search, and organize emails
- **Google Calendar**: View, create, edit, and delete events
- **Google Contacts**: Search, create, and update contacts
- **Slack**: Send messages, read channels, and search conversations

### AI Capabilities
- **Natural Language Processing**: Understand user intent
- **Task Routing**: Automatically direct requests to appropriate services
- **Context Awareness**: Maintain conversation history and context
- **Multi-turn Conversations**: Handle complex, multi-step tasks
- **Voice Commands**: Complete voice-driven interactions

## 📚 Documentation

- **[Backend README](README.md)**: Detailed backend setup and API documentation
- **[Desktop Client README](desktop_client/README.md)**: Desktop app setup and features
- **[Configuration Guide](config_guide.md)**: Step-by-step setup instructions
- **[API Documentation](http://localhost:8000/docs)**: Interactive API docs (when running)

## 🔧 Development

### Backend Development
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run with hot reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Check code quality
flake8 app/
black app/
```

### Desktop Development
```bash
cd desktop_client

# Development mode with hot reload
npm run dev

# Build for distribution
npm run build

# Build for specific platforms
npm run build:mac    # macOS
npm run build:win    # Windows  
npm run build:linux  # Linux
```

### Web Development
- Frontend uses CDN resources (Tailwind CSS, Font Awesome)
- Edit `frontend/index.html` for UI changes
- Changes reflect immediately in browser

## 🚀 Deployment

### Production Backend
```bash
# Install production dependencies
pip install -r requirements.txt

# Use production WSGI server
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker

# Or use Docker
docker build -t ai-assistant .
docker run -p 8000:8000 ai-assistant
```

### Desktop App Distribution
```bash
cd desktop_client

# Build installers for all platforms
npm run build

# Installers will be in desktop_client/dist/
# - macOS: .dmg file
# - Windows: .exe installer  
# - Linux: .AppImage and .deb packages
```

## 🔒 Security

- **OAuth2 Authentication**: Secure token-based authentication
- **Environment Variables**: Sensitive data stored securely
- **Input Validation**: Comprehensive request validation
- **CORS Protection**: Configurable cross-origin policies
- **Electron Security**: Context isolation and secure IPC

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes in the appropriate directory:
   - Backend: `app/` directory
   - Frontend: `frontend/` directory  
   - Desktop: `desktop_client/` directory
4. Test thoroughly
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 🐛 Troubleshooting

### Common Issues

1. **Backend won't start**:
   - Check Python version (3.8+ required)
   - Verify all dependencies installed: `pip install -r requirements.txt`
   - Check `.env` file configuration

2. **Desktop app won't start**:
   - Verify Node.js 16+ installed
   - Run `npm install` in `desktop_client/` directory
   - Check backend is running on `http://localhost:8000`

3. **Authentication issues**:
   - Verify Google OAuth2 credentials in `.env`
   - Check redirect URI matches Google Console settings
   - Ensure APIs are enabled in Google Cloud Console

4. **Voice features not working**:
   - Check microphone permissions in browser/desktop app
   - Verify browser supports Web Speech API
   - Test voice settings in preferences

### Getting Help

- Check the detailed READMEs in each component directory
- Review the configuration guide
- Check application logs in the `logs/` directory
- Visit the interactive API documentation at `/docs`

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **FastAPI**: For the excellent web framework
- **Electron**: For cross-platform desktop development
- **Google APIs**: For productivity service integrations
- **OpenAI/IBM/Ollama**: For AI model support
- **Slack**: For team communication integration

---

**🚀 Happy productivity with your AI Ultimate Assistant!**

*Built with ❤️ for seamless productivity and automation* 
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os
from dotenv import load_dotenv

from app.api.auth import auth_router
from app.api.gmail import gmail_router
from app.api.calendar import calendar_router
from app.api.contacts import contacts_router
from app.api.slack import slack_router
from app.api.voice import voice_router
from app.api.agent import agent_router
from app.api.config import config_router
from app.api.notifications import notifications_router
from app.api.must_gather import must_gather_router
from app.api.github import github_router
from app.api.model_training import training_router
from app.api.training import router as pattern_training_router
from app.api.jira import router as jira_router
from app.api.report_portal import report_portal_router
from app.core.config import settings
from app.core.websocket_manager import WebSocketManager
from app.services.notification_service import notification_service

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize WebSocket manager
websocket_manager = WebSocketManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting AI Ultimate Assistant...")
    
    # Start notification monitoring service
    import asyncio
    notification_task = asyncio.create_task(notification_service.start_monitoring())
    
    try:
        yield
    finally:
        # Shutdown
        logger.info("Shutting down AI Ultimate Assistant...")
        
        # Stop notification service
        await notification_service.stop_monitoring()
        notification_task.cancel()
        try:
            await notification_task
        except asyncio.CancelledError:
            pass

# Create FastAPI app
app = FastAPI(
    title="AI Ultimate Assistant",
    description="An AI-powered assistant for managing Gmail, Calendar, Contacts, and Slack",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(config_router, prefix="/api/config", tags=["configuration"])
app.include_router(gmail_router, prefix="/api/gmail", tags=["gmail"])
app.include_router(calendar_router, prefix="/api/calendar", tags=["calendar"])
app.include_router(contacts_router, prefix="/api/contacts", tags=["contacts"])
app.include_router(slack_router, prefix="/api/slack", tags=["slack"])
app.include_router(voice_router, prefix="/api/voice", tags=["voice"])
app.include_router(agent_router, prefix="/api/agent", tags=["ai-agent"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["notifications"])
app.include_router(must_gather_router, tags=["must-gather"])
app.include_router(github_router, prefix="/api/github", tags=["github"])
app.include_router(training_router, tags=["model-training"])
app.include_router(pattern_training_router, tags=["pattern-training"])
app.include_router(jira_router, tags=["jira"])  # Add Jira router
app.include_router(report_portal_router, prefix="/api/report-portal", tags=["report-portal"])  # Add Report Portal router

# WebSocket endpoint for real-time communication
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Process the message through AI agent
            from app.services.ai_agent import AIAgent
            import json
            agent = AIAgent()
            response = await agent.process_message(data)
            await websocket_manager.send_personal_message(json.dumps(response), websocket)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "AI Ultimate Assistant is running"}

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# Root endpoint - serve the frontend
@app.get("/")
async def root():
    from fastapi.responses import FileResponse
    return FileResponse("frontend/index.html")

# Voice diagnostics endpoint
@app.get("/voice_diagnostics.html")
async def voice_diagnostics():
    from fastapi.responses import FileResponse
    return FileResponse("voice_diagnostics.html")

# Training interface endpoint
@app.get("/training_interface.html")
async def training_interface():
    from fastapi.responses import FileResponse
    return FileResponse("frontend/training_interface.html")

# Report Portal interface endpoint
@app.get("/report_portal.html")
async def report_portal_interface():
    from fastapi.responses import FileResponse
    return FileResponse("frontend/report_portal.html")

# API root endpoint
@app.get("/api")
async def api_root():
    return {
        "message": "Welcome to AI Ultimate Assistant API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Configure server based on HTTPS setting
    if settings.use_https and os.path.exists(settings.ssl_cert_path) and os.path.exists(settings.ssl_key_path):
        port = 8443  # Use HTTPS port
        print(f"🔒 Starting HTTPS server on https://localhost:{port}")
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=port,
            reload=True,
            log_level="info",
            ssl_certfile=settings.ssl_cert_path,
            ssl_keyfile=settings.ssl_key_path
        )
    else:
        if settings.use_https:
            print("⚠️ HTTPS enabled but SSL certificates not found!")
            print("Run: python generate_ssl.py")
        
        port = 8000
        print(f"🌐 Starting HTTP server on http://localhost:{port}")
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=port,
            reload=True,
            log_level="info"
        ) 
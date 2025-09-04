from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

from app.services.ai_agent import ai_agent
from app.core.config import settings
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)
agent_router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    model_preference: Optional[str] = None

class ModelSwitchRequest(BaseModel):
    provider: str  # "openai", "gemini", "ollama", "granite"

@agent_router.post("/test")
async def test_chat() -> Dict[str, Any]:
    """Simple test endpoint"""
    return {
        "response": "Hello! This is a test response from the AI Ultimate Assistant.",
        "action_taken": "test",
        "suggestions": ["Test successful"]
    }

@agent_router.post("/chat")
async def chat(request: ChatRequest) -> Dict[str, Any]:
    """Process a chat message"""
    try:
        logger.info(f"Received chat request: {request.message}")

        # Simple fallback for basic greetings
        if request.message.lower().strip() in ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]:
            return {
                "response": f"Hello! 👋 I'm your AI Ultimate Assistant. I can help you manage your emails, calendar, contacts, and Slack messages. What would you like to do?",
                "action_taken": "general_conversation",
                "suggestions": ["Check recent emails", "View upcoming events", "Search contacts", "Send a message"]
            }

        # Re-enable AI agent processing for all other requests
        response = await ai_agent.process_message(request.message, model_preference=request.model_preference)
        logger.info(f"AI agent response: {response}")
        return response
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        # Return a fallback response instead of raising an exception
        return {
            "response": "I'm here to help you manage your digital workspace! I can assist with emails, calendar events, contacts, and Slack messages. What would you like to do?",
            "action_taken": "error_fallback",
            "suggestions": ["Check recent emails", "View upcoming events", "Search contacts", "Send a message"]
        }

@agent_router.post("/switch-model")
async def switch_model(request: ModelSwitchRequest) -> Dict[str, Any]:
    """Switch AI model dynamically"""
    try:
        current_model = ai_agent.get_current_model_info()
        
        # Validate provider
        valid_providers = ["openai", "gemini", "ollama", "granite"]
        if request.provider not in valid_providers:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid provider. Must be one of: {valid_providers}"
            )
        
        # Try to switch the model
        success = ai_agent.switch_ai_provider(request.provider)
        
        if success:
            new_model_info = ai_agent.get_current_model_info()
            return {
                "success": True,
                "message": f"Successfully switched from {current_model} to {new_model_info}",
                "old_model": current_model,
                "new_model": new_model_info,
                "provider": request.provider
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to switch to {request.provider}. Check configuration and API keys."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@agent_router.get("/current-model")
async def get_current_model() -> Dict[str, Any]:
    """Get current AI model information"""
    try:
        model_info = ai_agent.get_current_model_info()
        return {
            "provider": settings.ai_provider,
            "model_info": model_info,
            "available_providers": ["openai", "gemini", "ollama", "granite"]
        }
    except Exception as e:
        logger.error(f"Error getting current model: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all specialized agents"""
    
    def __init__(self, name: str, domain: str):
        self.name = name
        self.domain = domain
        self.conversation_history = []
        self.context = {}
        self.last_interaction = None
        
    @abstractmethod
    async def analyze_intent(self, message: str) -> Dict[str, Any]:
        """Analyze user message to determine intent within this agent's domain"""
        pass
    
    @abstractmethod
    async def handle_intent(self, intent: str, message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the detected intent within this agent's domain"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent can handle"""
        pass
    
    @abstractmethod
    def get_domain_keywords(self) -> List[str]:
        """Return keywords that indicate this agent's domain"""
        pass
    
    def should_handle(self, message: str) -> bool:
        """Check if this agent should handle the given message"""
        message_lower = message.lower()
        domain_keywords = self.get_domain_keywords()
        return any(keyword in message_lower for keyword in domain_keywords)
    
    async def process_message(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Process a message within this agent's domain"""
        try:
            logger.info(f"DEBUG: BaseAgent.process_message called for {self.name} with message: '{message}'")
            print(f"DEBUG: BaseAgent.process_message called for {self.name} with message: '{message}'")
            # Analyze intent
            print(f"DEBUG: About to call analyze_intent for {self.name}")
            intent_result = await self.analyze_intent(message)
            print(f"DEBUG: analyze_intent result for {self.name}: {intent_result}")
            intent = intent_result.get("intent", "unknown")
            entities = intent_result.get("entities", {})
            confidence = intent_result.get("confidence", 0.0)
            
            # Handle the intent
            response = await self.handle_intent(intent, message, entities)
            
            # Add metadata
            response.update({
                "agent": self.name,
                "domain": self.domain,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat()
            })
            
            # Update conversation history
            self.conversation_history.append({
                "message": message,
                "intent": intent,
                "entities": entities,
                "response": response,
                "timestamp": datetime.now().isoformat()
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error in {self.name} processing message: {e}")
            return {
                "response": f"I encountered an error while processing your request in the {self.domain} domain.",
                "error": str(e),
                "agent": self.name,
                "domain": self.domain,
                "confidence": 0.0
            }
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict]:
        """Get recent conversation history"""
        return self.conversation_history[-limit:] if self.conversation_history else []
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def set_context(self, context: Dict[str, Any]):
        """Set context for this agent"""
        self.context.update(context)
    
    def get_context(self) -> Dict[str, Any]:
        """Get current context"""
        return self.context.copy() 
import logging
from typing import Dict, List, Any
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class GeneralAgent(BaseAgent):
    """General agent for conversation and fallback cases"""
    
    def __init__(self):
        super().__init__("GeneralAgent", "general")
        
    def get_capabilities(self) -> List[str]:
        return [
            "general_conversation", "help", "greeting", "goodbye", "thanks",
            "weather", "time", "date", "joke", "fact", "definition"
        ]
    
    def get_domain_keywords(self) -> List[str]:
        return [
            "hello", "hi", "hey", "goodbye", "bye", "thanks", "thank you",
            "help", "what", "how", "why", "when", "where", "who",
            "weather", "time", "date", "joke", "fact", "definition"
        ]
    
    async def analyze_intent(self, message: str) -> Dict[str, Any]:
        """Analyze general conversation intent"""
        message_lower = message.lower()
        
        # Greeting patterns
        if any(phrase in message_lower for phrase in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]):
            return {"intent": "greeting", "confidence": 0.9, "entities": {}}
        
        # Goodbye patterns
        if any(phrase in message_lower for phrase in ["goodbye", "bye", "see you", "later", "good night"]):
            return {"intent": "goodbye", "confidence": 0.9, "entities": {}}
        
        # Thanks patterns
        if any(phrase in message_lower for phrase in ["thanks", "thank you", "appreciate it", "grateful"]):
            return {"intent": "thanks", "confidence": 0.9, "entities": {}}
        
        # Help patterns
        if any(phrase in message_lower for phrase in ["help", "what can you do", "capabilities", "features"]):
            return {"intent": "help", "confidence": 0.9, "entities": {}}
        
        # Weather patterns
        if any(phrase in message_lower for phrase in ["weather", "temperature", "forecast"]):
            return {"intent": "weather", "confidence": 0.8, "entities": {}}
        
        # Time patterns
        if any(phrase in message_lower for phrase in ["time", "what time", "current time"]):
            return {"intent": "time", "confidence": 0.8, "entities": {}}
        
        # Date patterns
        if any(phrase in message_lower for phrase in ["date", "what date", "today", "tomorrow"]):
            return {"intent": "date", "confidence": 0.8, "entities": {}}
        
        # Default to general conversation
        return {"intent": "general_conversation", "confidence": 0.5, "entities": {}}
    
    async def handle_intent(self, intent: str, message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general conversation intents"""
        if intent == "greeting":
            return await self._handle_greeting(message, entities)
        elif intent == "goodbye":
            return await self._handle_goodbye(message, entities)
        elif intent == "thanks":
            return await self._handle_thanks(message, entities)
        elif intent == "help":
            return await self._handle_help(message, entities)
        elif intent == "weather":
            return await self._handle_weather(message, entities)
        elif intent == "time":
            return await self._handle_time(message, entities)
        elif intent == "date":
            return await self._handle_date(message, entities)
        else:
            return await self._handle_general_conversation(message, entities)
    
    async def _handle_greeting(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle greetings"""
        return {
            "response": "Hello! I'm your AI assistant. I can help you with:\n\n📧 **Email Management** - Read, send, and organize emails\n🐛 **Jira Issues** - Create, update, and track issues\n☸️ **Kubernetes/OpenShift** - Manage clusters and resources\n🔀 **GitHub PRs** - Review and manage pull requests\n\nWhat would you like to work on today?",
            "action_taken": "greeting",
            "suggestions": ["Check my emails", "Fetch Jira issues", "Kubernetes help", "List PRs"]
        }
    
    async def _handle_goodbye(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle goodbyes"""
        return {
            "response": "Goodbye! Feel free to come back anytime if you need help with emails, Jira, Kubernetes, or GitHub. Have a great day! 👋",
            "action_taken": "goodbye",
            "suggestions": []
        }
    
    async def _handle_thanks(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle thanks"""
        return {
            "response": "You're welcome! I'm here to help. Is there anything else you'd like me to assist you with?",
            "action_taken": "thanks",
            "suggestions": ["Check emails", "Jira issues", "Kubernetes commands", "GitHub PRs"]
        }
    
    async def _handle_help(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle help requests"""
        return {
            "response": "**🤖 AI Assistant Capabilities**\n\nI'm your specialized AI assistant with multiple agents for different tasks:\n\n**📧 Gmail Agent**\n- Read and search emails\n- Send and compose emails\n- Find important emails and attachments\n- Categorize emails\n\n**🐛 Jira Agent**\n- Create and update Jira issues\n- Fetch and search issues\n- Update issue status\n- Add comments and assign issues\n\n**☸️ Kubernetes Agent**\n- List pods, services, deployments\n- Get pod logs and describe resources\n- Execute commands in pods\n- Port forwarding and troubleshooting\n\n**🔀 GitHub Agent**\n- List and create pull requests\n- Review and merge PRs\n- Search PRs and get details\n- Manage repositories\n\n**💬 General Agent**\n- General conversation and help\n- Time, date, and weather info\n- Fallback for unrecognized requests\n\nJust tell me what you'd like to do!",
            "action_taken": "help",
            "suggestions": ["Check emails", "Jira issues", "Kubernetes help", "GitHub PRs"]
        }
    
    async def _handle_weather(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle weather requests"""
        return {
            "response": "I can help you check the weather! However, I don't have direct weather API access yet. You can ask me about:\n\n- Email management\n- Jira issue tracking\n- Kubernetes/OpenShift commands\n- GitHub pull requests\n\nOr I can help you with general tasks and conversation!",
            "action_taken": "weather",
            "suggestions": ["Check emails", "Jira issues", "Kubernetes help", "GitHub PRs"]
        }
    
    async def _handle_time(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle time requests"""
        from datetime import datetime
        current_time = datetime.now().strftime("%I:%M %p")
        return {
            "response": f"The current time is {current_time}. Is there anything specific you'd like to work on?",
            "action_taken": "time",
            "suggestions": ["Check emails", "Jira issues", "Kubernetes help", "GitHub PRs"]
        }
    
    async def _handle_date(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle date requests"""
        from datetime import datetime
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        return {
            "response": f"Today is {current_date}. How can I help you today?",
            "action_taken": "date",
            "suggestions": ["Check emails", "Jira issues", "Kubernetes help", "GitHub PRs"]
        }
    
    async def _handle_general_conversation(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle general conversation"""
        return {
            "response": "I understand you're asking about something general. I'm specialized in helping with:\n\n📧 **Email management** - Try 'Check my emails' or 'Send an email'\n🐛 **Jira issues** - Try 'Fetch my Jira issues' or 'Create a new issue'\n☸️ **Kubernetes/OpenShift** - Try 'How to list pods?' or 'kubectl help'\n🔀 **GitHub PRs** - Try 'List my PRs' or 'Create a pull request'\n\nWhat would you like to work on?",
            "action_taken": "general_conversation",
            "suggestions": ["Check emails", "Jira issues", "Kubernetes help", "GitHub PRs"]
        } 
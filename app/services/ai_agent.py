import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import openai
import httpx
import base64 # Added for email body fetching

from app.core.config import settings
from app.api.auth import get_google_credentials
from app.services.jira_service import jira_service
from app.services.pattern_trainer import PatternTrainer
from app.services.multi_agent_orchestrator import MultiAgentOrchestrator
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# AI Provider imports
try:
    import ollama
except ImportError:
    ollama = None

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
except ImportError:
    AutoTokenizer = None
    AutoModelForCausalLM = None
    torch = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

logger = logging.getLogger(__name__)

class AIAgent:
    def __init__(self):
        self.conversation_history = []
        self.context = {}
        self.last_interaction = None
        self.granite_model = None
        self.granite_tokenizer = None
        self.gemini_model = None
        
        # Initialize pattern trainer for permanent learning
        self.pattern_trainer = PatternTrainer("trained_patterns.json")
        
        # Initialize multi-agent orchestrator
        self.multi_agent_orchestrator = MultiAgentOrchestrator()
        
        # Initialize AI providers
        self._initialize_ai_providers()
        
        # Setup capabilities
        self._setup_capabilities()
    
    def get_current_model_info(self) -> str:
        """Get information about the currently configured AI model"""
        provider = settings.ai_provider
        if provider == "openai":
            return f"OpenAI {settings.openai_model}"
        elif provider == "granite":
            return f"IBM Granite 3.3 ({settings.granite_model})"
        elif provider == "ollama":
            return f"Ollama {settings.ollama_model}"
        elif provider == "gemini":
            return f"Google Gemini {settings.gemini_model}"
        else:
            return f"Unknown model ({provider})"

    def _setup_capabilities(self):
        """Setup AI agent capabilities"""
        self.capabilities = {
            "email": ["read_emails", "send_email", "search_emails", "mark_read", "delete_email", "categorize_emails", "extract_action_items", "generate_followups", "email_templates"],
            "calendar": ["get_events", "create_event", "update_event", "delete_event"],
            "contacts": ["get_contacts", "create_contact", "update_contact", "search_contacts"],
            "slack": ["get_channels", "send_message", "get_messages", "search_messages"],
            "voice": ["speech_to_text", "text_to_speech"],
            "general": ["answer_questions", "provide_suggestions", "execute_workflows"],
            "must_gather": ["analyze_cluster", "health_check", "troubleshoot_issues", "generate_reports"],
            "openshift": ["cluster_diagnostics", "operator_analysis", "node_troubleshooting", "kms_encryption"],
            "analysis": ["data_analysis", "log_analysis", "performance_analysis", "trend_analysis"]
        }
        
        # Email templates for common responses
        self.email_templates = {
            "meeting_confirmation": {
                "subject": "Meeting Confirmation: {meeting_title}",
                "body": """Hi {recipient_name},

I've scheduled our meeting for {meeting_time} on {meeting_date}.

**Meeting Details:**
- **Topic:** {meeting_title}
- **Date:** {meeting_date}
- **Time:** {meeting_time}
- **Location:** {meeting_location}

Please let me know if you need to reschedule or if you have any questions.

Best regards,
{user_name}"""
            },
            "follow_up": {
                "subject": "Follow-up: {original_subject}",
                "body": """Hi {recipient_name},

I wanted to follow up on our previous conversation about {topic}.

**Previous Discussion:**
{previous_summary}

**Next Steps:**
{action_items}

Please let me know if you have any updates or if there's anything I can help with.

Best regards,
{user_name}"""
            },
            "document_request": {
                "subject": "Document Request: {document_name}",
                "body": """Hi {recipient_name},

I hope this email finds you well. I'm reaching out to request the following document:

**Document:** {document_name}
**Purpose:** {purpose}
**Deadline:** {deadline}

Please let me know if you need any additional information or if you have any questions.

Thank you for your time.

Best regards,
{user_name}"""
            },
            "project_update": {
                "subject": "Project Update: {project_name}",
                "body": """Hi {recipient_name},

Here's an update on the {project_name} project:

**Current Status:** {status}
**Key Achievements:** {achievements}
**Next Steps:** {next_steps}
**Blockers:** {blockers}

Please let me know if you have any questions or need additional information.

Best regards,
{user_name}"""
            }
        }

    def _initialize_ai_providers(self):
        """Initialize AI providers based on configuration"""
        try:
            # Initialize OpenAI
            if settings.openai_api_key and settings.ai_provider == "openai":
                openai.api_key = settings.openai_api_key
            
            # Initialize Granite 3.3 via Transformers
            elif settings.ai_provider == "granite" and AutoTokenizer and AutoModelForCausalLM:
                try:
                    self.granite_tokenizer = AutoTokenizer.from_pretrained(settings.granite_model)
                    self.granite_model = AutoModelForCausalLM.from_pretrained(
                        settings.granite_model,
                        torch_dtype=torch.float16 if torch and torch.cuda.is_available() else None,
                        device_map="auto" if torch and torch.cuda.is_available() else None
                    )
                    logger.info(f"Loaded Granite model: {settings.granite_model}")
                except Exception as e:
                    logger.error(f"Failed to load Granite model: {e}")
            
            # Initialize Google Gemini
            elif settings.ai_provider == "gemini" and genai and settings.gemini_api_key:
                try:
                    genai.configure(api_key=settings.gemini_api_key)
                    self.gemini_model = genai.GenerativeModel(settings.gemini_model)
                    logger.info(f"Loaded Gemini model: {settings.gemini_model}")
                except Exception as e:
                    logger.error(f"Failed to load Gemini model: {e}")
                    
        except Exception as e:
            logger.error(f"Error initializing AI providers: {e}")

    def switch_ai_provider(self, new_provider: str) -> bool:
        """Dynamically switch AI provider"""
        try:
            logger.info(f"Switching AI provider from {settings.ai_provider} to {new_provider}")
            
            # Update the settings
            settings.ai_provider = new_provider
            logger.info(f"Updated provider setting to: {new_provider}")
            
            # Reinitialize the specific model
            if new_provider == "gemini" and genai and settings.gemini_api_key:
                try:
                    genai.configure(api_key=settings.gemini_api_key)
                    self.gemini_model = genai.GenerativeModel(settings.gemini_model)
                    logger.info(f"Reinitialized Gemini model: {settings.gemini_model}")
                except Exception as e:
                    logger.error(f"Failed to reinitialize Gemini model: {e}")
                    return False
            elif new_provider == "ollama" and ollama:
                # Ollama doesn't need reinitialization
                logger.info("Switched to Ollama provider")
            elif new_provider == "openai" and openai:
                # OpenAI doesn't need reinitialization
                logger.info("Switched to OpenAI provider")
            elif new_provider == "granite":
                # Granite doesn't need reinitialization
                logger.info("Switched to Granite provider")
            
            return True
                
        except Exception as e:
            logger.error(f"Error switching AI provider: {e}")
            return False

    async def _generate_granite_response(self, message: str) -> str:
        """Generate response using Granite 3.3 model"""
        try:
            if not self.granite_model or not self.granite_tokenizer:
                return "Granite model not available. Please check configuration."
            
            # Format prompt for Granite
            prompt = f"<|user|>\n{message}\n<|assistant|>\n"
            
            # Tokenize and generate
            inputs = self.granite_tokenizer(prompt, return_tensors="pt")
            if torch and torch.cuda.is_available():
                inputs = inputs.to("cuda")
            
            with torch.no_grad():
                outputs = self.granite_model.generate(
                    **inputs,
                    max_new_tokens=200,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.granite_tokenizer.eos_token_id
                )
            
            # Decode response
            response = self.granite_tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the assistant's response
            if "<|assistant|>" in response:
                response = response.split("<|assistant|>")[-1].strip()
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating Granite response: {e}")
            return "I encountered an error processing your request with Granite model."

    async def _generate_ollama_response(self, message: str) -> str:
        """Generate response using Ollama"""
        try:
            if not ollama:
                return "Ollama not available. Please install ollama package."
            
            response = ollama.chat(
                model=settings.ollama_model,
                messages=[{
                    'role': 'user',
                    'content': message
                }]
            )
            
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"Error generating Ollama response: {e}")
            return "I encountered an error processing your request with Ollama."

    async def _generate_gemini_response(self, message: str) -> str:
        """Generate response using Google Gemini"""
        try:
            if not genai or not self.gemini_model:
                return "Google Gemini not available. Please configure gemini_api_key."
            
            # Build a helpful system prompt
            system_prompt = ("You are a helpful AI assistant specialized in managing digital workflows including "
                           "email, calendar, contacts, and Slack. Provide concise, accurate, and helpful responses.")
            
            full_prompt = f"{system_prompt}\n\nUser: {message}\nAssistant:"
            
            response = self.gemini_model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 1024,
                }
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating Gemini response: {e}")
            return "I encountered an error processing your request with Gemini."

    async def _generate_openai_response(self, message: str) -> str:
        """Generate response using OpenAI"""
        try:
            if not openai:
                return "OpenAI not available. Please configure openai_api_key."
            
            # Build a helpful system prompt
            system_prompt = ("You are a helpful AI assistant specialized in managing digital workflows including "
                           "email, calendar, contacts, and Slack. Provide concise, accurate, and helpful responses.")
            
            response = openai.ChatCompletion.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=1024,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating OpenAI response: {e}")
            return "I encountered an error processing your request with OpenAI."

    async def process_message(self, message: str, context: Optional[Dict] = None, model_preference: Optional[str] = None) -> Dict[str, Any]:
        """Process user message and return response using multi-agent orchestrator"""
        try:
            # Update conversation history
            self.conversation_history.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Use multi-agent orchestrator to process the message
            response = await self.multi_agent_orchestrator.process_message(message, context.get("user_id") if context else None)
            
            # Update conversation history with response
            self.conversation_history.append({
                "role": "assistant",
                "content": response.get("response", ""),
                "timestamp": datetime.utcnow().isoformat(),
                "intent": response.get("action_taken", ""),
                "action_taken": response.get("action_taken", ""),
                "agent": response.get("orchestrator", {}).get("selected_agent", "unknown")
            })
            
            # Update last interaction time
            self.last_interaction = datetime.utcnow()
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "response": "I encountered an error while processing your message. Please try again.",
                "error": str(e)
            }


    # Enhanced Gmail NLQ Patterns
    def _enhanced_gmail_intent_recognition(self, message: str) -> Dict[str, Any]:
        """Enhanced intent recognition for Gmail queries"""
        message_lower = message.lower()
        
        # Natural language patterns for email queries
        nlq_patterns = {
            "unread_emails": [
                "do i have any new unread emails",
                "any unread emails",
                "show me unread emails",
                "check unread emails",
                "new emails",
                "unread messages"
            ],
            "important_emails": [
                "show me all emails marked as important",
                "important emails",
                "flagged emails",
                "starred emails",
                "priority emails",
                "urgent emails"
            ],
            "sender_search": [
                "emails from {}",
                "messages from {}",
                "find emails from {}",
                "show emails from {}",
                "search emails from {}"
            ],
            "date_search": [
                "emails from today",
                "emails from yesterday",
                "emails this week",
                "emails from past week",
                "recent emails",
                "today's emails"
            ],
            "attachment_search": [
                "emails with attachments",
                "emails with files",
                "emails with pdf",
                "emails with documents",
                "find attachments"
            ],
            "pending_emails": [
                "pending emails",
                "emails need attention",
                "emails to reply",
                "approval emails",
                "response needed"
            ],
            "spam_emails": [
                "spam emails",
                "suspicious emails",
                "junk emails",
                "promotional emails",
                "newsletter emails"
            ]
        }
        
        # Check for natural language patterns
        for intent, patterns in nlq_patterns.items():
            for pattern in patterns:
                if pattern in message_lower:
                    return {
                        "intent": intent,
                        "confidence": 0.95,
                        "entities": self._extract_gmail_entities(message, intent)
                    }
        
        return None
    
    def _extract_gmail_entities(self, message: str, intent: str) -> Dict[str, Any]:
        """Extract Gmail-specific entities"""
        entities = {}
        message_lower = message.lower()
        
        if intent == "sender_search":
            # Extract sender name from patterns like "emails from John"
            import re
            sender_patterns = [
                r'from\s+([a-zA-Z\s]+)',
                r'emails?\s+from\s+([a-zA-Z\s]+)',
                r'messages?\s+from\s+([a-zA-Z\s]+)'
            ]
            for pattern in sender_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    entities["sender"] = match.group(1).strip()
                    break
        
        elif intent == "date_search":
            # Extract date information
            date_keywords = {
                "today": "today",
                "yesterday": "yesterday", 
                "this week": "this week",
                "past week": "past week",
                "last week": "last week"
            }
            for keyword, value in date_keywords.items():
                if keyword in message_lower:
                    entities["date_range"] = value
                    break
        
        return entities

    def _check_trained_patterns(self, message: str) -> Optional[Dict[str, Any]]:
        """Check if message matches any trained patterns"""
        try:
            # Get all patterns and sort by success rate
            all_patterns = self.pattern_trainer.patterns.get("patterns", {})
            sorted_patterns = sorted(all_patterns.values(), 
                                   key=lambda x: (x["success_rate"], x["usage_count"]), 
                                   reverse=True)
            
            for pattern_data in sorted_patterns:
                if self.pattern_trainer._pattern_matches(message, pattern_data["pattern"]):
                    logger.info(f"DEBUG: Matched trained pattern: {pattern_data['pattern']} -> {pattern_data['intent']}")
                    return {
                        "intent": pattern_data["intent"],
                        "confidence": pattern_data["confidence"],
                        "entities": pattern_data["entities"]
                    }
        except Exception as e:
            logger.error(f"Error checking trained patterns: {e}")
        
        return None

    def _learn_from_interaction(self, message: str, intent: str, entities: Dict[str, Any], response: Dict[str, Any]):
        """Learn from successful interactions to improve pattern recognition"""
        try:
            # Determine if the interaction was successful
            success = response.get("action_taken") not in ["error", "failed", "not_found"]
            
            # Record the interaction for learning
            self.pattern_trainer.learn_from_interaction(
                message=message,
                detected_intent=intent,
                actual_intent=intent,  # Assuming detection was correct for now
                entities=entities,
                success=success
            )
            
            # If this was a successful interaction, add it as a pattern
            if success and intent not in ["general_conversation", "error"]:
                # Extract a pattern from the message
                pattern = self.pattern_trainer._extract_pattern_from_message(message)
                if pattern:
                    # Check if this pattern already exists
                    existing_patterns = self.pattern_trainer.get_patterns_for_intent(intent)
                    pattern_exists = any(p["pattern"] == pattern for p in existing_patterns)
                    
                    if not pattern_exists:
                        self.pattern_trainer.add_pattern(
                            intent=intent,
                            pattern=pattern,
                            entities=entities,
                            confidence=0.8,
                            success_rate=1.0
                        )
                        logger.info(f"Learned new pattern: {pattern} -> {intent}")
            
        except Exception as e:
            logger.error(f"Error learning from interaction: {e}")

    def _check_kubernetes_patterns(self, message: str) -> Optional[Dict[str, Any]]:
        """Check if message matches Kubernetes/OpenShift command patterns"""
        try:
            message_lower = message.lower()
            
            # Kubernetes/OpenShift command patterns
            kubernetes_patterns = {
                # Namespace commands (check these first)
                "list_namespaces": [
                    "how to list pod in ns", "how to list pods in ns", "how to list pod in namespace",
                    "list namespace", "list namespaces", "get namespace", "get namespaces",
                    "show namespace", "show namespaces", "list ns", "get ns",
                    "how to list namespace", "how to list namespaces", "how to list ns",
                    "kubectl get namespace", "kubectl get namespaces", "kubectl get ns",
                    "oc get namespace", "oc get namespaces", "oc get ns", "oc get projects", "get projects"
                ],
                # Pod commands
                "list_pods": [
                    "list pod", "list pods", "get pod", "get pods", "show pod", "show pods",
                    "how to list pod", "how to list pods", "how to get pod", "how to get pods",
                    "kubectl get pod", "kubectl get pods", "oc get pod", "oc get pods"
                ],
                "describe_pod": [
                    "describe pod", "describe pods", "pod details", "pod info",
                    "kubectl describe pod", "oc describe pod"
                ],
                "delete_pod": [
                    "delete pod", "delete pods", "remove pod", "remove pods",
                    "kubectl delete pod", "oc delete pod"
                ],
                
                # Namespace commands
                "list_namespaces": [
                    "list namespace", "list namespaces", "get namespace", "get namespaces",
                    "show namespace", "show namespaces", "list ns", "get ns",
                    "how to list namespace", "how to list namespaces", "how to list ns",
                    "how to list pod in ns", "how to list pods in ns", "how to list pod in namespace",
                    "kubectl get namespace", "kubectl get namespaces", "kubectl get ns",
                    "oc get namespace", "oc get namespaces", "oc get ns"
                ],
                "create_namespace": [
                    "create namespace", "create ns", "new namespace", "new ns",
                    "kubectl create namespace", "oc new-project"
                ],
                
                # Service commands
                "list_services": [
                    "list service", "list services", "get service", "get services",
                    "show service", "show services", "list svc", "get svc",
                    "kubectl get service", "kubectl get services", "kubectl get svc",
                    "oc get service", "oc get services", "oc get svc"
                ],
                
                # Deployment commands
                "list_deployments": [
                    "list deployment", "list deployments", "get deployment", "get deployments",
                    "show deployment", "show deployments", "list deploy", "get deploy",
                    "kubectl get deployment", "kubectl get deployments", "kubectl get deploy",
                    "oc get deployment", "oc get deployments", "oc get deploy"
                ],
                
                # Node commands
                "list_nodes": [
                    "list node", "list nodes", "get node", "get nodes",
                    "show node", "show nodes", "kubectl get node", "kubectl get nodes",
                    "oc get node", "oc get nodes"
                ],
                
                # Config commands
                "get_config": [
                    "get config", "show config", "kubectl config", "oc config",
                    "kubectl config view", "oc config view"
                ],
                
                # Log commands
                "get_logs": [
                    "get logs", "show logs", "pod logs", "container logs",
                    "kubectl logs", "oc logs"
                ],
                
                # Exec commands
                "exec_pod": [
                    "exec pod", "exec into pod", "connect to pod", "pod shell",
                    "kubectl exec", "oc exec", "kubectl exec -it", "oc exec -it"
                ],
                
                # Port forward
                "port_forward": [
                    "port forward", "forward port", "kubectl port-forward", "oc port-forward"
                ],
                
                # General Kubernetes help
                "kubernetes_help": [
                    "kubernetes help", "k8s help", "kubectl help", "oc help",
                    "how to use kubectl", "how to use oc", "kubernetes commands",
                    "openshift commands", "k8s commands", "kubectl", "oc"
                ]
            }
            
            # Check for exact matches (more specific patterns first)
            # Sort patterns by length (longer patterns first) to avoid partial matches
            for intent, patterns in kubernetes_patterns.items():
                sorted_patterns = sorted(patterns, key=len, reverse=True)
                for pattern in sorted_patterns:
                    if pattern in message_lower:
                        logger.info(f"DEBUG: Matched Kubernetes pattern '{pattern}' for intent '{intent}' in message: '{message}'")
                        return {
                            "intent": intent,
                            "confidence": 0.9,
                            "entities": self._extract_kubernetes_entities(message)
                        }
            
            # Check for partial matches (more flexible) - but only if it's clearly a Kubernetes command
            kubernetes_keywords = ["pod", "pods", "namespace", "ns", "service", "svc", "deployment", "deploy", "node", "nodes", "kubectl", "oc", "kubernetes", "k8s", "openshift", "project", "projects"]
            if any(keyword in message_lower for keyword in kubernetes_keywords):
                # Only match if it's clearly a Kubernetes command (not just containing the word)
                if any(cmd_word in message_lower for cmd_word in ["get", "describe", "logs", "exec", "port-forward", "apply", "delete", "create"]):
                    # Check for question patterns
                    if any(word in message_lower for word in ["how", "what", "which", "where", "when", "why"]):
                        logger.info(f"DEBUG: Matched Kubernetes question pattern in message: '{message}'")
                        return {
                            "intent": "kubernetes_help",
                            "confidence": 0.7,
                            "entities": self._extract_kubernetes_entities(message)
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking Kubernetes patterns: {e}")
            return None

    async def analyze_intent(self, message: str) -> Dict[str, Any]:
        # Check trained patterns first (HIGHEST PRIORITY)
        trained_intent = self._check_trained_patterns(message)
        if trained_intent:
            return trained_intent
        
        # HIGH PRIORITY: Check for GitHub URLs first (before Gmail recognition)
        if "github.com" in message:
            message_lower = message.lower()
            
            # Special case for GitHub PR summarization
            if any(word in message_lower for word in ["summarise", "summarize", "summary", "summaries"]):
                logger.info(f"DEBUG: Matched GitHub PR summarization pattern in message: '{message}'")
                return {"intent": "github_summarize_pr", "confidence": 0.95, "entities": self._extract_github_entities(message)}
            
            # Special case for GitHub PR review actions (check this FIRST)
            if any(word in message_lower for word in ["review", "analyze", "check code", "code quality"]) and "github.com" in message:
                logger.info(f"DEBUG: Matched GitHub PR review pattern in message: '{message}'")
                return {"intent": "github_review_pr", "confidence": 0.95, "entities": self._extract_github_entities(message)}
            
            # Special case for GitHub PR comment actions (check this BEFORE approval)
            if any(word in message_lower for word in ["add comment", "comment", "reply"]):
                logger.info(f"DEBUG: Matched GitHub PR comment pattern in message: '{message}'")
                return {"intent": "github_add_comment", "confidence": 0.95, "entities": self._extract_github_entities(message)}
            
            # Special case for GitHub PR label actions
            if any(word in message_lower for word in ["add label", "add labels", "label", "labels"]):
                logger.info(f"DEBUG: Matched GitHub PR label pattern in message: '{message}'")
                return {"intent": "github_add_labels", "confidence": 0.95, "entities": self._extract_github_entities(message)}
            
            # Special case for GitHub PR approval actions (check this AFTER comment)
            if any(word in message_lower for word in ["approve", "lgtm"]) and not any(word in message_lower for word in ["comment", "reply"]):
                logger.info(f"DEBUG: Matched GitHub PR approval pattern in message: '{message}'")
                return {"intent": "github_approve_pr", "confidence": 0.95, "entities": self._extract_github_entities(message)}
            
            # Special case for GitHub PR actions (close, merge, etc.)
            if any(action in message_lower for action in ["close", "closed", "merge", "merged"]):
                logger.info(f"DEBUG: Matched GitHub PR action with URL pattern in message: '{message}'")
                return {"intent": "github_pr_action", "confidence": 0.95, "entities": self._extract_github_entities(message)}
        
        # Try enhanced Gmail NLQ recognition second
        enhanced_result = self._enhanced_gmail_intent_recognition(message)
        if enhanced_result:
            return enhanced_result
        
        # Fall back to existing patterns

        """Analyze user message to determine intent"""
        try:
            message_lower = message.lower()
            
            # HIGH PRIORITY: Kubernetes/OpenShift command patterns (but not Jira commands)
            # Skip Kubernetes check if this looks like a Jira command
            if not any(jira_word in message_lower for jira_word in ["jira", "jql", "issue", "bug", "story", "task", "epic"]):
                kubernetes_result = self._check_kubernetes_patterns(message)
                if kubernetes_result:
                    return kubernetes_result
            
            # HIGH PRIORITY: GitHub patterns (check these BEFORE email patterns)
            # Special case for "List PRs" commands (check this FIRST)
            if any(phrase in message_lower for phrase in ["list", "show", "get"]) and "pr" in message_lower:
                logger.info(f"DEBUG: Matched GitHub List PRs pattern in message: '{message}'")
                logger.info(f"DEBUG: Message contains 'list': {'list' in message_lower}")
                logger.info(f"DEBUG: Message contains 'pr': {'pr' in message_lower}")
                return {"intent": "github_list_prs", "confidence": 0.8, "entities": self._extract_github_entities(message)}
            
            # Special case for approval/review requests
            if any(phrase in message_lower for phrase in ["approval", "approve", "review", "reviewer", "pending"]) and any(word in message_lower for word in ["pr", "pull request", "my"]):
                logger.info(f"DEBUG: Matched GitHub approval request pattern in message: '{message}'")
                return {"intent": "github_list_prs", "confidence": 0.9, "entities": self._extract_github_entities(message)}
            
            # Special case for GitHub PR actions (close, merge, etc.)
            if any(action in message_lower for action in ["close", "closed", "merge", "merged"]) and ("pr" in message_lower or "pull request" in message_lower or "github.com" in message):
                logger.info(f"DEBUG: Matched GitHub PR action pattern in message: '{message}'")
                return {"intent": "github_pr_action", "confidence": 0.9, "entities": self._extract_github_entities(message)}
            
            # Special case for GitHub PR actions with URLs (higher priority)
            if "github.com" in message and any(action in message_lower for action in ["close", "closed", "merge", "merged"]):
                logger.info(f"DEBUG: Matched GitHub PR action with URL pattern in message: '{message}'")
                return {"intent": "github_pr_action", "confidence": 0.95, "entities": self._extract_github_entities(message)}
            
                            # Special case for GitHub PR summarization
                if "github.com" in message and any(word in message_lower for word in ["summarise", "summarize", "summary", "summaries"]):
                    logger.info(f"DEBUG: Matched GitHub PR summarization pattern in message: '{message}'")
                    return {"intent": "github_summarize_pr", "confidence": 0.95, "entities": self._extract_github_entities(message)}
                
                # Special case for GitHub PR approval actions
                if "github.com" in message and any(word in message_lower for word in ["approve", "lgtm", "looks good", "looks good to me"]):
                    logger.info(f"DEBUG: Matched GitHub PR approval pattern in message: '{message}'")
                    return {"intent": "github_approve_pr", "confidence": 0.95, "entities": self._extract_github_entities(message)}
                
                # Special case for GitHub PR label actions
                if "github.com" in message and any(word in message_lower for word in ["add label", "add labels", "label", "labels"]):
                    logger.info(f"DEBUG: Matched GitHub PR label pattern in message: '{message}'")
                    return {"intent": "github_add_labels", "confidence": 0.95, "entities": self._extract_github_entities(message)}
                
                # Special case for GitHub PR comment actions
                if "github.com" in message and any(word in message_lower for word in ["add comment", "comment", "reply"]):
                    logger.info(f"DEBUG: Matched GitHub PR comment pattern in message: '{message}'")
                    return {"intent": "github_add_comment", "confidence": 0.95, "entities": self._extract_github_entities(message)}
            
            # GitHub PR review with URL (check this second)
            github_url_pattern = r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)'
            url_match = re.search(github_url_pattern, message)
            if url_match and any(phrase in message_lower for phrase in ["review", "analyze", "check code", "code quality"]):
                owner, repo, pr_num = url_match.groups()
                logger.info(f"DEBUG: HIGH PRIORITY - Found GitHub URL for PR review - owner: {owner}, repo: {repo}, pr: {pr_num}")
                return {"intent": "github_review_pr", "confidence": 0.95, "entities": {
                    "owner": owner,
                    "repo": repo,
                    "pr_number": int(pr_num)
                }}
            
            # Debug logging for PR review
            if "review" in message_lower and ("pr" in message_lower or "pull request" in message_lower or "github.com" in message):
                logger.info(f"DEBUG: Analyzing PR review message: '{message}'")
            
            # Model management intents
            if any(phrase in message_lower for phrase in ["show model", "current model", "what model", "which model"]):
                return {"intent": "show_model", "confidence": 0.9, "entities": {}}
            elif any(phrase in message_lower for phrase in ["change model", "switch model", "use model", "set model"]):
                return {"intent": "change_model", "confidence": 0.9, "entities": {}}
            
            # Meeting invite intents (higher priority than regular email)
            if any(phrase in message_lower for phrase in ["meeting invite", "send invite", "invite", "schedule meeting", "meeting at", "sync at", "call at"]):
                return {"intent": "create_event", "confidence": 0.9, "entities": self._extract_calendar_entities(message)}
            
            # Calendar intents
            elif any(word in message_lower for word in ["calendar", "meeting", "appointment", "schedule", "event"]):
                if any(word in message_lower for word in ["create", "add", "schedule", "book", "send", "invite"]):
                    return {"intent": "create_event", "confidence": 0.8, "entities": self._extract_calendar_entities(message)}
                elif any(phrase in message_lower for phrase in ["what's on", "what is on", "show", "check", "get", "list", "today", "tomorrow", "upcoming"]):
                    return {"intent": "get_events", "confidence": 0.8, "entities": {}}
            
            # Email intents (lower priority when meeting-related keywords are present)
            elif any(word in message_lower for word in ["email", "mail", "inbox"]) or (any(word in message_lower for word in ["send"]) and not any(word in message_lower for word in ["meeting", "invite", "schedule", "appointment"])):
                logger.info(f"DEBUG: Matched email intent pattern")
                if any(word in message_lower for word in ["send", "compose", "write"]):
                    return {"intent": "send_email", "confidence": 0.8, "entities": self._extract_email_entities(message)}
                elif any(phrase in message_lower for phrase in ["mark as read", "mark read", "mark email read", "mark email as read"]) or (any(phrase in message_lower for phrase in ["mark"]) and any(word in message_lower for word in ["email", "mail"]) and any(word in message_lower for word in ["as read", "read"]) and not any(word in message_lower for word in ["unread", "show unread", "check unread"])):
                    email_number = self._extract_email_number(message)
                    return {"intent": "mark_email_read", "confidence": 0.9, "entities": {"email_number": email_number}}
                elif any(phrase in message_lower for phrase in ["summarize", "summary", "summarise", "brief", "tl;dr", "tldr"]):
                    email_number = self._extract_email_number(message)
                    return {"intent": "summarize_email", "confidence": 0.9, "entities": {"email_number": email_number}}
                elif any(phrase in message_lower for phrase in ["categorize", "categorise", "sort", "organize", "organise", "classify"]):
                    return {"intent": "categorize_emails", "confidence": 0.9, "entities": {}}
                elif any(phrase in message_lower for phrase in ["action items", "action items", "tasks", "todo", "to do", "extract actions"]):
                    email_number = self._extract_email_number(message)
                    return {"intent": "extract_action_items", "confidence": 0.9, "entities": {"email_number": email_number}}
                elif any(phrase in message_lower for phrase in ["follow up", "followup", "follow-up", "generate follow", "create follow"]):
                    email_number = self._extract_email_number(message)
                    return {"intent": "generate_followup", "confidence": 0.9, "entities": {"email_number": email_number}}
                elif any(phrase in message_lower for phrase in ["template", "use template", "email template"]):
                    return {"intent": "use_email_template", "confidence": 0.9, "entities": self._extract_template_entities(message)}
                elif any(phrase in message_lower for phrase in ["attachment", "attachments", "pdf", "document", "file"]):
                    return {"intent": "find_attachments", "confidence": 0.9, "entities": self._extract_search_entities(message)}
                elif any(phrase in message_lower for phrase in ["important", "flagged", "starred", "priority"]):
                    return {"intent": "find_important_emails", "confidence": 0.9, "entities": {}}
                elif any(phrase in message_lower for phrase in ["spam", "suspicious", "promotional", "newsletter"]):
                    return {"intent": "find_spam_emails", "confidence": 0.9, "entities": {}}
                elif any(phrase in message_lower for phrase in ["from", "sender", "by"]):
                    return {"intent": "search_emails_by_sender", "confidence": 0.9, "entities": self._extract_search_entities(message)}
                elif any(phrase in message_lower for phrase in ["today", "yesterday", "this week", "past week"]):
                    return {"intent": "search_emails_by_date", "confidence": 0.9, "entities": self._extract_date_entities(message)}
                elif any(phrase in message_lower for phrase in ["pending", "approval", "reply", "response"]):
                    return {"intent": "find_pending_emails", "confidence": 0.9, "entities": {}}
                elif any(phrase in message_lower for phrase in ["unread", "unread emails", "show unread", "check unread", "new emails"]):
                    return {"intent": "read_unread_emails", "confidence": 0.9, "entities": {}}
                elif any(phrase in message_lower for phrase in ["show me", "message body", "full content", "body of email", "email #", "email 1", "email 2", "email 3", "email 4", "email 5"]) and not any(phrase in message_lower for phrase in ["mark as read", "mark read", "mark email read", "mark email as read"]):
                    email_number = self._extract_email_number(message)
                    return {"intent": "show_email_body", "confidence": 0.9, "entities": {"email_number": email_number}}
                elif any(word in message_lower for word in ["read", "check", "show", "get"]):
                    return {"intent": "read_emails", "confidence": 0.8, "entities": {}}
                elif any(word in message_lower for word in ["search", "find"]):
                    return {"intent": "search_emails", "confidence": 0.8, "entities": {"query": message}}
            
            # Standalone email actions (don't require email/mail/inbox keywords)
            elif any(phrase in message_lower for phrase in ["mark as read", "mark read", "mark email read", "mark email as read"]) or (any(phrase in message_lower for phrase in ["mark"]) and any(word in message_lower for word in ["email", "mail"]) and any(word in message_lower for word in ["as read", "read"]) and not any(word in message_lower for word in ["unread", "show unread", "check unread"])):
                logger.info(f"DEBUG: Matched standalone mark as read pattern")
                email_number = self._extract_email_number(message)
                return {"intent": "mark_email_read", "confidence": 0.9, "entities": {"email_number": email_number}}
            elif any(phrase in message_lower for phrase in ["unread", "unread emails", "show unread", "check unread", "new emails"]):
                logger.info(f"DEBUG: Matched standalone unread emails pattern")
                return {"intent": "read_unread_emails", "confidence": 0.9, "entities": {}}
            elif any(phrase in message_lower for phrase in ["summarize", "summary", "summarise", "brief", "tl;dr", "tldr"]) and any(word in message_lower for word in ["email", "mail", "1", "2", "3", "4", "5"]):
                logger.info(f"DEBUG: Matched standalone summarize email pattern")
                email_number = self._extract_email_number(message)
                return {"intent": "summarize_email", "confidence": 0.9, "entities": {"email_number": email_number}}
            
            # Contact intents
            elif any(word in message_lower for word in ["contact", "person", "phone", "address"]):
                if any(word in message_lower for word in ["find", "search", "look", "get"]):
                    return {"intent": "search_contacts", "confidence": 0.8, "entities": {"query": message}}
                elif any(word in message_lower for word in ["add", "create", "new"]):
                    return {"intent": "create_contact", "confidence": 0.8, "entities": self._extract_contact_entities(message)}
            
            # Must-gather and OpenShift analysis intents
            elif any(phrase in message_lower for phrase in ["must-gather", "must gather", "analyze cluster", "cluster analysis", "openshift analysis"]):
                if any(word in message_lower for word in ["analyze", "analysis", "check", "examine", "investigate"]):
                    return {"intent": "analyze_must_gather", "confidence": 0.9, "entities": self._extract_analysis_entities(message)}
                elif any(phrase in message_lower for phrase in ["health check", "quick check", "cluster health"]):
                    return {"intent": "health_check", "confidence": 0.9, "entities": self._extract_analysis_entities(message)}
            
            # OpenShift troubleshooting intents
            elif any(word in message_lower for word in ["openshift", "kubernetes", "k8s", "cluster", "pods", "nodes", "operators"]):
                if any(word in message_lower for word in ["troubleshoot", "debug", "fix", "issue", "problem", "error"]):
                    return {"intent": "openshift_troubleshoot", "confidence": 0.8, "entities": self._extract_openshift_entities(message)}
                elif any(word in message_lower for word in ["kms", "encryption", "encrypt", "decrypt"]):
                    return {"intent": "kms_analysis", "confidence": 0.8, "entities": {"query": message}}
            

            
            # GitHub PR review intents
            elif any(phrase in message_lower for phrase in ["github", "pull request", "code review", "merge", "repository", "repo"]) or "github.com" in message or (any(word in message_lower for word in ["pr", "pull"]) and any(word in message_lower for word in ["request", "review", "merge", "github"])):
                logger.info(f"DEBUG: Matched GitHub intent pattern in message: '{message}'")
                
                # Handle GitHub URLs
                github_url_pattern = r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)'
                url_match = re.search(github_url_pattern, message)
                logger.info(f"DEBUG: URL pattern match result: {url_match}")
                if url_match:
                    owner, repo, pr_num = url_match.groups()
                    logger.info(f"DEBUG: Found GitHub URL - owner: {owner}, repo: {repo}, pr: {pr_num}")
                    return {"intent": "github_review_pr", "confidence": 0.95, "entities": {
                        "owner": owner,
                        "repo": repo,
                        "pr_number": int(pr_num)
                    }}
                
                # Handle review commands with URLs
                if any(phrase in message_lower for phrase in ["review", "analyze", "check code", "code quality"]) and "github.com" in message:
                    logger.info(f"DEBUG: Found review command with GitHub URL")
                    # Extract from URL in the message
                    url_match = re.search(github_url_pattern, message)
                    if url_match:
                        owner, repo, pr_num = url_match.groups()
                        return {"intent": "github_review_pr", "confidence": 0.95, "entities": {
                            "owner": owner,
                            "repo": repo,
                            "pr_number": int(pr_num)
                        }}
                
                # Regular PR review patterns - check for review + pr/pull request
                if any(phrase in message_lower for phrase in ["review", "analyze", "check code", "code quality"]):
                    logger.info(f"DEBUG: Found review command")
                    # Check if message contains PR-related terms
                    if any(term in message_lower for term in ["pr", "pull request", "pull", "request"]):
                        logger.info(f"DEBUG: Found PR-related terms, returning github_review_pr intent")
                        return {"intent": "github_review_pr", "confidence": 0.9, "entities": self._extract_github_entities(message)}
                elif any(word in message_lower for word in ["merge", "approve"]):
                    return {"intent": "github_merge_pr", "confidence": 0.9, "entities": self._extract_github_entities(message)}
                elif any(word in message_lower for word in ["close", "reject", "decline"]):
                    return {"intent": "github_close_pr", "confidence": 0.9, "entities": self._extract_github_entities(message)}
                elif any(phrase in message_lower for phrase in ["list", "show", "get"]):
                    if any(word in message_lower for word in ["repositories", "repos"]):
                        return {"intent": "github_list_repos", "confidence": 0.8, "entities": self._extract_github_entities(message)}
                    elif any(phrase in message_lower for phrase in ["pull requests", "prs"]):
                        return {"intent": "github_list_prs", "confidence": 0.8, "entities": self._extract_github_entities(message)}
                    elif "pr" in message_lower and "/" in message_lower:  # Pattern like "List PRs in owner/repo"
                        return {"intent": "github_list_prs", "confidence": 0.8, "entities": self._extract_github_entities(message)}
                elif any(word in message_lower for word in ["comment", "add comment"]):
                    return {"intent": "github_add_comment", "confidence": 0.8, "entities": self._extract_github_entities(message)}
                else:
                    logger.info(f"DEBUG: No specific GitHub command found, returning github_general")
                    return {"intent": "github_general", "confidence": 0.7, "entities": self._extract_github_entities(message)}
            
            # Special case: Review command with GitHub URL but no other GitHub keywords
            elif any(phrase in message_lower for phrase in ["review", "analyze", "check code", "code quality"]) and "github.com" in message:
                logger.info(f"DEBUG: Found review command with GitHub URL (special case)")
                github_url_pattern = r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)'
                url_match = re.search(github_url_pattern, message)
                if url_match:
                    owner, repo, pr_num = url_match.groups()
                    logger.info(f"DEBUG: Found GitHub URL in special case - owner: {owner}, repo: {repo}, pr: {pr_num}")
                    return {"intent": "github_review_pr", "confidence": 0.95, "entities": {
                        "owner": owner,
                        "repo": repo,
                        "pr_number": int(pr_num)
                    }}
            
            # Special case: Review + PR + GitHub URL (more flexible)
            elif any(phrase in message_lower for phrase in ["review"]) and any(term in message_lower for term in ["pr", "pull request", "pull"]) and "github.com" in message:
                logger.info(f"DEBUG: Found review + PR + GitHub URL pattern")
                logger.info(f"DEBUG: Message contains 'review': {'review' in message_lower}")
                logger.info(f"DEBUG: Message contains 'pr': {'pr' in message_lower}")
                logger.info(f"DEBUG: Message contains 'github.com': {'github.com' in message}")
                github_url_pattern = r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)'
                url_match = re.search(github_url_pattern, message)
                if url_match:
                    owner, repo, pr_num = url_match.groups()
                    logger.info(f"DEBUG: Found GitHub URL in review+PR pattern - owner: {owner}, repo: {repo}, pr: {pr_num}")
                    return {"intent": "github_review_pr", "confidence": 0.95, "entities": {
                        "owner": owner,
                        "repo": repo,
                        "pr_number": int(pr_num)
                    }}
            
            # Jira intents (HIGH PRIORITY - check for Jira issue keys first)
            elif re.search(r'[A-Z]+-\d+', message) or any(phrase in message_lower for phrase in ["jira", "jira issues", "issues", "tickets", "bug", "task", "story", "epic"]):
                # HIGHEST PRIORITY: Add comment to Jira issue intents (check this FIRST to avoid conflicts)
                comment_patterns = [
                    "comment", "add comment", "reply", "note", "add a comment", "leave a comment",
                    "write a comment", "post a comment", "add note", "leave note", "write note"
                ]
                if any(phrase in message_lower for phrase in comment_patterns) and re.search(r'[A-Z]+-\d+', message):
                    return {"intent": "add_jira_comment", "confidence": 0.95, "entities": self._extract_jira_comment_entities(message)}
                
                # Assign Jira issue intents (check this SECOND)
                assign_patterns = [
                    "assign", "reassign", "give to", "hand over to", "pass to", "transfer to",
                    "assign to", "reassign to", "give it to", "hand it over to", "pass it to",
                    "transfer it to", "set assignee", "change assignee", "update assignee"
                ]
                if any(phrase in message_lower for phrase in assign_patterns) and re.search(r'[A-Z]+-\d+', message):
                    return {"intent": "assign_jira_issue", "confidence": 0.95, "entities": self._extract_jira_assignment_entities(message)}
                
                # Advanced Jira query intents (check these THIRD)
                # Issue status lookup: "What's the status of ticket ABC-1234?" (HIGHER PRIORITY)
                status_lookup_patterns = [
                    "what's the status", "what is the status", "status of", "current status",
                    "what status", "show status", "get status", "check status", "tell me the status",
                    "what's happening with", "what is happening with", "how is", "how's"
                ]
                # Check for status lookup patterns first, but exclude update patterns
                if any(phrase in message_lower for phrase in status_lookup_patterns) and any(phrase in message_lower for phrase in ["ticket", "issue", "bug", "story", "epic"]):
                    return {"intent": "jira_status_lookup", "confidence": 0.9, "entities": self._extract_jira_metadata_entities(message)}
                # Also check for simple status queries without specific issue types
                elif any(phrase in message_lower for phrase in ["what's the status", "what is the status", "show status", "get status", "check status"]) and re.search(r'[A-Z]+-\d+', message):
                    return {"intent": "jira_status_lookup", "confidence": 0.9, "entities": self._extract_jira_metadata_entities(message)}
                
                # Update Jira status intents (check this FOURTH)
                status_patterns = [
                    "update", "change", "move", "transition", "status", "update status",
                    "change status", "move to", "transition to", "set status", "mark as",
                    "move it to", "change it to", "update it to", "set it to", "mark it as"
                ]
                if any(phrase in message_lower for phrase in status_patterns) and re.search(r'[A-Z]+-\d+', message):
                    return {"intent": "update_jira_status", "confidence": 0.95, "entities": self._extract_jira_status_entities(message)}
                
                # Issue metadata queries: "When was JIRA-456 last updated?"
                metadata_patterns = [
                    "when was", "last updated", "last modified", "who is working on", "assigned to",
                    "when did", "who's working on", "who is assigned", "who's assigned",
                    "when was it", "who has it", "who's got it", "who is handling", "who's handling"
                ]
                if any(phrase in message_lower for phrase in metadata_patterns) and any(phrase in message_lower for phrase in ["ticket", "issue", "bug", "story", "epic"]) or (any(phrase in message_lower for phrase in ["when", "who"]) and re.search(r'[A-Z]+-\d+', message)):
                    return {"intent": "jira_metadata_query", "confidence": 0.9, "entities": self._extract_jira_metadata_entities(message)}
                
                # Advanced filters: "Any critical bugs in Project X?"
                filter_patterns = [
                    "critical", "high priority", "blocked", "overdue", "due today", "due this week",
                    "urgent", "important", "low priority", "medium priority", "minor", "major",
                    "show me", "find me", "get me", "list", "show", "find", "get", "any",
                    "all", "my", "assigned to me", "reported by me", "created by me"
                ]
                if any(phrase in message_lower for phrase in filter_patterns) and any(phrase in message_lower for phrase in ["bugs", "issues", "tickets", "stories", "epics", "tasks"]):
                    return {"intent": "jira_advanced_filter", "confidence": 0.9, "entities": self._extract_jira_filter_entities(message)}
                
                # Sprint and backlog queries
                if any(phrase in message_lower for phrase in ["sprint", "backlog", "burndown", "story points", "epics"]) and any(phrase in message_lower for phrase in ["current", "this sprint", "sprint 10", "story points", "points"]):
                    return {"intent": "jira_sprint_query", "confidence": 0.9, "entities": self._extract_jira_sprint_entities(message)}
                
                # Extract status filters first
                status_filters = []
                status_patterns = {
                    'open': 'Open',
                    'closed': 'Closed',
                    'to do': 'To Do',
                    'todo': 'To Do',
                    'new': 'NEW',
                    'post': 'POST',
                    'verified': 'Verified',
                    'in progress': 'In Progress',
                    'progressing': 'In Progress',
                    'on_qa': 'ON_QA',
                    'on qa': 'ON_QA',
                    'qa': 'ON_QA',
                    'ready for qa': 'ON_QA',
                    'ready for testing': 'ON_QA',
                    'assigned': 'Assigned',
                    'assigned to me': 'Assigned',
                    'my assigned': 'Assigned',
                    'my issues': 'Assigned',
                    'blocked': 'Blocked',
                    'waiting': 'Waiting',
                    'pending': 'Pending',
                    'review': 'Review',
                    'code review': 'Code Review',
                    'testing': 'Testing',
                    'test': 'Testing',
                    'resolved': 'Resolved',
                    'done': 'Done',
                    'complete': 'Complete',
                    'finished': 'Finished'
                }
                
                for status_key, status_value in status_patterns.items():
                    if status_key in message_lower:
                        status_filters.append(status_value)
                
                # Handle multiple status filters (e.g., "open and TO DO")
                if len(status_filters) > 1:
                    # Return all detected status filters as a list
                    status_filter = status_filters
                elif len(status_filters) == 1:
                    status_filter = status_filters[0]
                else:
                    status_filter = None
                
                # Create Jira issue intents (check this LAST to avoid conflicts)
                if any(phrase in message_lower for phrase in ["create", "new", "make", "open"]) and any(phrase in message_lower for phrase in ["issue", "ticket", "bug", "task"]):
                    return {"intent": "create_jira_issue", "confidence": 0.9, "entities": self._extract_jira_create_entities(message)}
                
                # Fetch issues intents - Check specific patterns FIRST (higher priority)
                qa_patterns = [
                    "qa contact", "qa issues", "qa tickets", "i'm qa contact", "i am qa contact", 
                    "qa contact issues", "where i am qa contact", "my qa contact", "qa contact for",
                    "issues where i am qa contact", "tickets where i am qa contact"
                ]
                if any(phrase in message_lower for phrase in qa_patterns) or ("on_qa" in message_lower and any(phrase in message_lower for phrase in ["fetch", "get", "show", "list", "my"])) or ("qa contact" in message_lower and "jira" in message_lower):
                    return {"intent": "fetch_jira_issues", "confidence": 0.9, "entities": {"issue_type": "qa_contact", "status_filter": status_filter}}
                
                elif any(phrase in message_lower for phrase in ["assigned", "assigned to me", "my assigned", "my issues", "my tickets", "issues assigned to me", "tickets assigned to me", "what i'm working on", "what i am working on", "my workload", "my tasks", "my bugs", "my stories"]):
                    return {"intent": "fetch_jira_issues", "confidence": 0.9, "entities": {"issue_type": "assigned", "status_filter": status_filter}}
                elif any(phrase in message_lower for phrase in ["reported", "reported by me", "my reported", "issues i reported", "tickets i reported", "bugs i reported", "what i reported", "my reports"]):
                    return {"intent": "fetch_jira_issues", "confidence": 0.9, "entities": {"issue_type": "reported", "status_filter": status_filter}}
                elif any(phrase in message_lower for phrase in ["all mine", "all my issues", "all my tickets", "everything i'm involved in", "all issues related to me", "all tickets related to me", "my complete list", "everything assigned or reported by me"]):
                    return {"intent": "fetch_jira_issues", "confidence": 0.9, "entities": {"issue_type": "all_mine", "status_filter": status_filter}}
                elif any(phrase in message_lower for phrase in ["fetch", "get", "show", "list", "my issues", "my jira", "my tickets", "display", "find", "search", "look up", "bring up", "pull up", "what do i have", "what's on my plate", "what's in my queue"]):
                    return {"intent": "fetch_jira_issues", "confidence": 0.9, "entities": self._extract_jira_entities(message, status_filter)}
                else:
                    return {"intent": "fetch_jira_issues", "confidence": 0.8, "entities": {"status_filter": status_filter}}
            
            # Jira Sprint intents (don't require issue keys)
            elif any(phrase in message_lower for phrase in ["sprint", "backlog", "burndown", "story points", "epics"]) and any(phrase in message_lower for phrase in ["current", "this sprint", "sprint 10", "story points", "points"]):
                return {"intent": "jira_sprint_query", "confidence": 0.9, "entities": self._extract_jira_sprint_entities(message)}
            
            # Slack intents
            elif any(word in message_lower for word in ["slack", "message", "channel", "team"]):
                if any(word in message_lower for word in ["send", "post", "write"]):
                    return {"intent": "send_slack_message", "confidence": 0.8, "entities": self._extract_slack_entities(message)}
                elif any(word in message_lower for word in ["check", "read", "show"]):
                    return {"intent": "read_slack_messages", "confidence": 0.8, "entities": {}}
            
            # General conversation
            else:
                return {"intent": "general_conversation", "confidence": 0.6, "entities": {}}
                
        except Exception as e:
            logger.error(f"Error analyzing intent: {e}")
            return {"intent": "general_conversation", "confidence": 0.5, "entities": {}}
        
        # Fallback - ensure we never return None
        return {"intent": "general_conversation", "confidence": 0.5, "entities": {}}

    async def route_intent(self, intent: str, message: str, entities: Dict, model_preference: Optional[str] = None) -> Dict[str, Any]:
        """Route intent to appropriate handler"""
        try:
            # Enhanced Gmail NLQ intent mapping
            if intent == "unread_emails":
                return await self._handle_read_unread_emails(message, entities)
            elif intent == "important_emails":
                return await self._handle_find_important_emails(message, entities)
            elif intent == "sender_search":
                return await self._handle_search_emails_by_sender(message, entities)
            elif intent == "date_search":
                return await self._handle_search_emails_by_date(message, entities)
            elif intent == "attachment_search":
                return await self._handle_find_attachments(message, entities)
            elif intent == "pending_emails":
                return await self._handle_find_pending_emails(message, entities)
            elif intent == "spam_emails":
                return await self._handle_find_spam_emails(message, entities)
            
            # Existing intent handlers
            elif intent == "show_model":
                return await self._handle_show_model(message, entities)
            elif intent == "change_model":
                return await self._handle_change_model(message, entities)
            elif intent == "send_email":
                return await self._handle_send_email(message, entities)
            elif intent == "read_emails":
                return await self._handle_read_emails(message, entities)
            elif intent == "read_unread_emails":
                return await self._handle_read_unread_emails(message, entities)
            elif intent == "show_email_body":
                return await self._handle_show_email_body(message, entities)
            elif intent == "summarize_email":
                return await self._handle_summarize_email(message, entities)
            elif intent == "categorize_emails":
                return await self._handle_categorize_emails(message, entities)
            elif intent == "extract_action_items":
                return await self._handle_extract_action_items(message, entities)
            elif intent == "generate_followup":
                return await self._handle_generate_followup(message, entities)
            elif intent == "use_email_template":
                return await self._handle_use_email_template(message, entities)
            elif intent == "find_attachments":
                return await self._handle_find_attachments(message, entities)
            elif intent == "find_important_emails":
                return await self._handle_find_important_emails(message, entities)
            elif intent == "find_spam_emails":
                return await self._handle_find_spam_emails(message, entities)
            elif intent == "search_emails_by_sender":
                return await self._handle_search_emails_by_sender(message, entities)
            elif intent == "search_emails_by_date":
                return await self._handle_search_emails_by_date(message, entities)
            elif intent == "find_pending_emails":
                return await self._handle_find_pending_emails(message, entities)
            elif intent == "mark_email_read":
                return await self._handle_mark_email_read(message, entities)
            elif intent == "search_emails":
                return await self._handle_search_emails(message, entities)
            elif intent == "create_event":
                return await self._handle_create_event(message, entities)
            elif intent == "get_events":
                return await self._handle_get_events(message, entities)
            elif intent == "search_contacts":
                return await self._handle_search_contacts(message, entities)
            elif intent == "create_contact":
                return await self._handle_create_contact(message, entities)
            elif intent == "send_slack_message":
                return await self._handle_send_slack_message(message, entities)
            elif intent == "read_slack_messages":
                return await self._handle_read_slack_messages(message, entities)
            elif intent == "analyze_must_gather":
                return await self._handle_analyze_must_gather(message, entities)
            elif intent == "health_check":
                return await self._handle_health_check(message, entities)
            elif intent == "openshift_troubleshoot":
                return await self._handle_openshift_troubleshoot(message, entities)
            elif intent == "kms_analysis":
                return await self._handle_kms_analysis(message, entities)
            elif intent == "github_review_pr":
                return await self._handle_github_review_pr(message, entities, model_preference)
            elif intent == "github_merge_pr":
                return await self._handle_github_merge_pr(message, entities)
            elif intent == "github_close_pr":
                return await self._handle_github_close_pr(message, entities)
            elif intent == "github_list_repos":
                return await self._handle_github_list_repos(message, entities)
            elif intent == "github_list_prs":
                return await self._handle_github_list_prs(message, entities)
            elif intent == "github_pr_action":
                return await self._handle_github_pr_action(message, entities)
            elif intent == "github_summarize_pr":
                return await self._handle_github_summarize_pr(message, entities)
            elif intent == "github_approve_pr":
                return await self._handle_github_approve_pr(message, entities)
            elif intent == "github_add_labels":
                return await self._handle_github_add_labels(message, entities)
            elif intent == "github_add_comment":
                return await self._handle_github_add_comment(message, entities)
            elif intent == "github_general":
                return await self._handle_github_general(message, entities)
            # Kubernetes/OpenShift handlers
            elif intent == "list_pods":
                return await self._handle_list_pods(message, entities)
            elif intent == "list_namespaces":
                return await self._handle_list_namespaces(message, entities)
            elif intent == "list_services":
                return await self._handle_list_services(message, entities)
            elif intent == "list_deployments":
                return await self._handle_list_deployments(message, entities)
            elif intent == "kubernetes_help":
                return await self._handle_kubernetes_help(message, entities)
            elif intent == "describe_pod":
                return await self._handle_describe_pod(message, entities)
            elif intent == "get_logs":
                return await self._handle_get_logs(message, entities)
            elif intent == "exec_pod":
                return await self._handle_exec_pod(message, entities)
            elif intent == "port_forward":
                return await self._handle_port_forward(message, entities)
            elif intent == "fetch_jira_issues":
                return await self._handle_fetch_jira_issues(message, entities)
            elif intent == "create_jira_issue":
                return await self._handle_create_jira_issue(message, entities)
            elif intent == "add_jira_comment":
                return await self._handle_add_jira_comment(message, entities)
            elif intent == "assign_jira_issue":
                return await self._handle_assign_jira_issue(message, entities)
            elif intent == "update_jira_status":
                return await self._handle_update_jira_status(message, entities)
            elif intent == "jira_status_lookup":
                return await self._handle_jira_status_lookup(message, entities)
            elif intent == "jira_metadata_query":
                return await self._handle_jira_metadata_query(message, entities)
            elif intent == "jira_advanced_filter":
                return await self._handle_jira_advanced_filter(message, entities)
            elif intent == "jira_sprint_query":
                return await self._handle_jira_sprint_query(message, entities)
            else:
                return await self._handle_general_conversation(message)
                
        except Exception as e:
            logger.error(f"Error routing intent {intent}: {e}")
            return {
                "response": f"I understand you want to {intent.replace('_', ' ')}, but I encountered an error. Could you please try rephrasing your request?",
                "error": str(e)
            }

    # Intent handlers
    async def _handle_send_email(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle sending an email"""
        # Extract email details from message
        to_email = entities.get("to_email")
        subject = entities.get("subject")
        body = entities.get("body", "")
        
        if not to_email:
            return {
                "response": "I'd be happy to help you send an email! Could you please specify the recipient's email address?",
                "action_taken": "request_email_recipient",
                "suggestions": ["Provide recipient email address"]
            }
        
        if not subject:
            return {
                "response": f"Great! I'll help you send an email to {to_email}. What should be the subject of the email?",
                "action_taken": "request_email_subject",
                "suggestions": ["Provide email subject"]
            }
        
                # Try to send the email directly using Gmail API
        try:
            result = await self._send_email_via_api(to_email, subject, body)
            if result["success"]:
                model_info = self.get_current_model_info()
                return {
                    "response": f"✅ Email sent successfully to {to_email}! (sent using {model_info})\n\n📧 **Email Details:**\n**To:** {to_email}\n**Subject:** {subject}\n**Message:** {body}\n\n📬 Message ID: {result.get('message_id', 'N/A')}",
                    "action_taken": "email_sent_success",
                    "data": {"to": to_email, "subject": subject, "body": body, "message_id": result.get('message_id')}
                }
            else:
                return {
                    "response": f"❌ Failed to send email to {to_email}. Error: {result.get('error', 'Unknown error')}",
                    "action_taken": "email_send_failed",
                    "suggestions": ["Check authentication", "Try again", "Verify email address"]
                }
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {
                "response": f"❌ I encountered an error while trying to send the email to {to_email}. Please check your authentication and try again.",
                "action_taken": "email_send_error",
                "suggestions": ["Check Gmail authentication", "Try again", "Check internet connection"]
            }

    def _fetch_emails(self, max_results=10):
        """Fetch emails from Gmail"""
        try:
            credentials = get_google_credentials()
            if not credentials:
                return []
            
            service = build('gmail', 'v1', credentials=credentials)
            results = service.users().messages().list(
                userId='me',
                q="in:inbox",
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            email_list = []
            
            for message in messages[:5]:  # Limit to 5 for performance
                msg = service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='metadata'
                ).execute()
                
                headers = msg['payload'].get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
                
                # Check if email is read or unread by examining labelIds
                label_ids = msg.get('labelIds', [])
                is_read = 'UNREAD' not in label_ids
                
                email_list.append({
                    'id': msg['id'],
                    'subject': subject,
                    'sender': sender,
                    'date': date,
                    'snippet': msg.get('snippet', ''),
                    'is_read': is_read,
                    'label_ids': label_ids
                })
            
            return email_list
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []

    def _get_email_body(self, message_id: str):
        """Get full body content of a specific email"""
        try:
            credentials = get_google_credentials()
            if not credentials:
                return None
            
            service = build('gmail', 'v1', credentials=credentials)
            
            msg = service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract email content
            payload = msg['payload']
            headers = payload.get('headers', [])
            
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
            
            # Get email body
            body = ""
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body']['data']
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
                        break
                    elif part['mimeType'] == 'text/html' and not body:
                        # Fallback to HTML if no plain text
                        data = part['body']['data']
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
            else:
                if payload['mimeType'] in ['text/plain', 'text/html']:
                    data = payload['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
            
            return {
                'id': msg['id'],
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body,
                'snippet': msg.get('snippet', '')
            }
        except Exception as e:
            logger.error(f"Error fetching email body: {e}")
            return None

    async def _send_email_via_api(self, to_email: str, subject: str, body: str) -> Dict[str, Any]:
        """Send email using Gmail API"""
        try:
            credentials = get_google_credentials()
            if not credentials:
                return {"success": False, "error": "Not authenticated with Google"}
            
            service = build('gmail', 'v1', credentials=credentials)
            
            # Create message
            from email.mime.text import MIMEText
            message = MIMEText(body, 'plain')
            message['To'] = to_email
            message['Subject'] = subject
            
            # Encode message
            import base64
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send message
            result = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return {
                "success": True,
                "message_id": result.get('id', 'Unknown'),
                "thread_id": result.get('threadId', 'Unknown')
            }
        except Exception as e:
            logger.error(f"Error sending email via API: {e}")
            return {"success": False, "error": str(e)}

    def _fetch_calendar_events(self, max_results=10):
        """Fetch calendar events"""
        try:
            credentials = get_google_credentials()
            if not credentials:
                return []
            
            service = build('calendar', 'v3', credentials=credentials)
            now = datetime.utcnow().isoformat() + 'Z'
            
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            # Ensure events_result is not None and has items
            if not events_result:
                return []
                
            events = events_result.get('items', [])
            if not events:
                return []
                
            event_list = []
            
            for event in events[:5]:  # Limit to 5 for performance
                # Ensure event is not None and has required fields
                if not event or 'start' not in event:
                    continue
                    
                start = event['start'].get('dateTime', event['start'].get('date', 'No time specified'))
                event_list.append({
                    'id': event.get('id', ''),
                    'summary': event.get('summary', 'No Title'),
                    'start': start,
                    'status': event.get('status', 'Unknown')
                })
            
            return event_list
        except Exception as e:
            logger.error(f"Error fetching events: {e}")
            return []

    async def _handle_show_model(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle showing current AI model information"""
        model_info = self.get_current_model_info()
        
        # Get current provider and model details
        current_provider = settings.ai_provider
        current_model_name = model_info
        
        # Define available models with current status
        available_models = [
            f"• Ollama Granite 3.3 (Local) {'✅' if current_provider == 'ollama' else ''}",
            f"• Google Gemini 2.5 Flash {'✅' if current_provider == 'gemini' else ''}",
            f"• IBM Granite 3.3 {'✅' if current_provider == 'granite' else ''}",
            f"• OpenAI GPT-4 {'✅' if current_provider == 'openai' else ''}"
        ]
        
        return {
            "response": f"🤖 **Current AI Model**: {current_model_name}\n\n"
                       f"📊 **Available Models**:\n"
                       f"{chr(10).join(available_models)}\n\n"
                       f"💡 **To switch models**:\n"
                       f"• Go to Settings → General → AI Model\n"
                       f"• Select your preferred model\n"
                       f"• Click 'Switch Model Now'",
            "action_taken": "show_model_info",
            "data": {"current_model": current_provider, "model_details": current_model_name},
            "suggestions": ["Open Settings", "Check emails", "View calendar"]
        }

    async def _handle_change_model(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle changing AI model"""
        current_model = self.get_current_model_info()
        current_provider = settings.ai_provider
        
        return {
            "response": f"🤖 **Current AI Model**\n\n"
                       f"**You are using:** {current_model}\n\n"
                       f"**Model Details:**\n"
                       f"• Provider: {current_provider}\n"
                       f"• Status: ✅ Active and Ready\n\n"
                       f"**To change models:**\n"
                       f"• Go to Settings → General → AI Model\n"
                       f"• Select your preferred model from the dropdown\n"
                       f"• Click 'Switch Model Now' button\n\n"
                       f"**Available models:**\n"
                       f"• **Ollama**: Local Granite 3.3 {'✅' if current_provider == 'ollama' else ''}\n"
                       f"• **Gemini**: Google Gemini 2.5 Flash {'✅' if current_provider == 'gemini' else ''}\n"
                       f"• **Granite**: IBM Granite 3.3 {'✅' if current_provider == 'granite' else ''}\n"
                       f"• **OpenAI**: GPT-4 {'✅' if current_provider == 'openai' else ''}",
            "action_taken": "show_current_model",
            "data": {"current_model": current_model},
            "suggestions": ["Open Settings", "Check emails", "Ask a question"]
        }

    async def _handle_read_emails(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle reading emails"""
        try:
            # Call the Gmail API function directly
            emails = self._fetch_emails(max_results=10)
            
            if emails:
                # Format the first few emails for display
                formatted_emails = []
                for i, email in enumerate(emails[:5]):  # Show first 5 emails
                    # Clean up the sender name
                    sender = email['sender']
                    if '<' in sender and '>' in sender:
                        sender = sender.split('<')[0].strip().strip('"')
                    
                    # Shorten the subject if too long
                    subject = email['subject']
                    if len(subject) > 60:
                        subject = subject[:60] + "..."
                    
                    # Check read/unread status and add visual indicator
                    is_read = email.get('is_read', True)
                    status_icon = "✅" if is_read else "🔴"
                    status_text = "READ" if is_read else "UNREAD"
                    
                    # Format each email nicely with proper spacing
                    formatted_emails.append(
                        f"📧 Email #{i+1} {status_icon} {status_text}\n\n"
                        f"Subject: {subject}\n\n"
                        f"From: {sender}\n\n" 
                        f"Date: {email['date']}\n\n"
                        f"Preview: {email['snippet'][:80]}...\n\n"
                        f"{'─' * 50}"
                    )
                
                email_summary = "\n".join(formatted_emails)
                
                # Count read vs unread emails
                total_emails = len(emails)
                unread_count = sum(1 for email in emails if not email.get('is_read', True))
                read_count = total_emails - unread_count
                
                # Create status summary
                status_summary = f"📊 **Email Summary**: {total_emails} total | {unread_count} unread 🔴 | {read_count} read ✅"
                
                model_info = self.get_current_model_info()
                return {
                    "response": f"Here are your recent emails (powered by {model_info}):\n\n{status_summary}\n\n{email_summary}",
                    "action_taken": "fetch_emails",
                    "data": {"emails": emails, "unread_count": unread_count, "read_count": read_count},
                    "suggestions": ["Check recent emails", "Search for specific emails", "Mark emails as read"]
                }
            else:
                model_info = self.get_current_model_info()
                return {
                    "response": f"Your inbox appears to be empty or no emails were found (checked using {model_info}).",
                    "action_taken": "fetch_emails",
                    "suggestions": ["Check recent emails", "Search for specific emails"]
                }
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            model_info = self.get_current_model_info()
            return {
                "response": f"I encountered an error while retrieving your emails using {model_info}. Please try again.",
                "action_taken": "fetch_emails_error",
                "suggestions": ["Try again", "Check authentication"]
            }

    async def _handle_read_unread_emails(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle reading only unread emails"""
        try:
            from app.api.notifications import get_unread_emails
            import httpx
            
            # Get unread emails from the notifications API
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/api/notifications/unread-emails")
                
                if response.status_code == 200:
                    data = response.json()
                    unread_emails = data.get("unread_emails", [])
                    count = data.get("count", 0)
                    
                    if unread_emails:
                        # Format unread emails
                        formatted_emails = []
                        for i, email in enumerate(unread_emails, 1):
                            # Clean up sender name
                            sender = email['sender']
                            if '<' in sender and '>' in sender:
                                sender = sender.split('<')[0].strip().strip('"')
                            
                            formatted_emails.append(
                                f"📧 **Email #{i}** 🔴 UNREAD\n\n"
                                f"**Subject:** {email['subject']}\n\n"
                                f"**From:** {sender}\n\n"
                                f"**Date:** {email['date']}\n\n"
                                f"**Preview:** {email['snippet']}\n\n"
                                f"{'─' * 50}"
                            )
                        
                        email_summary = "\n".join(formatted_emails)
                        model_info = self.get_current_model_info()
                        
                        return {
                            "response": f"Here are your **unread emails** (powered by {model_info}):\n\n📊 **Unread Email Summary**: {count} unread emails 🔴\n\n{email_summary}",
                            "action_taken": "fetch_unread_emails",
                            "data": {"unread_emails": unread_emails, "count": count},
                            "suggestions": ["Mark as read", "Reply to email", "Check all emails"]
                        }
                    else:
                        model_info = self.get_current_model_info()
                        return {
                            "response": f"🎉 **Great news!** You have no unread emails in your inbox (checked using {model_info}).",
                            "action_taken": "fetch_unread_emails",
                            "data": {"unread_emails": [], "count": 0},
                            "suggestions": ["Check all emails", "Search emails", "Send an email"]
                        }
                else:
                    model_info = self.get_current_model_info()
                    return {
                        "response": f"I encountered an error while retrieving your unread emails using {model_info}. Please try again.",
                        "action_taken": "fetch_unread_emails_error",
                        "suggestions": ["Try again", "Check authentication"]
                    }
                    
        except Exception as e:
            logger.error(f"Error fetching unread emails: {e}")
            model_info = self.get_current_model_info()
            return {
                "response": f"I encountered an error while retrieving your unread emails using {model_info}. Please try again.",
                "action_taken": "fetch_unread_emails_error",
                "suggestions": ["Try again", "Check authentication"]
        }

    async def _handle_search_emails(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle searching emails"""
        query = entities.get("query", message)
        return {
            "response": f"I'll search your emails for: '{query}'. Please check the email interface for the search results.",
            "action_taken": "search_emails",
            "data": {"query": query}
        }

    async def _handle_show_email_body(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle showing full email body content"""
        try:
            email_number = entities.get("email_number", 1)
            
            # First get the list of emails to find the message ID
            emails = self._fetch_emails(max_results=10)
            
            if not emails:
                return {
                    "response": "No emails found in your inbox.",
                    "action_taken": "show_email_body",
                    "suggestions": ["Check recent emails", "Refresh inbox"]
                }
            
            if email_number < 1 or email_number > len(emails):
                return {
                    "response": f"Email #{email_number} not found. I can show emails 1-{len(emails)}.",
                    "action_taken": "show_email_body",
                    "suggestions": [f"Try email 1-{len(emails)}"]
                }
            
            # Get the email at the specified position (email_number is 1-indexed)
            target_email = emails[email_number - 1]
            email_full = self._get_email_body(target_email['id'])
            
            if not email_full:
                return {
                    "response": f"Unable to retrieve the full content of email #{email_number}.",
                    "action_taken": "show_email_body_error",
                    "suggestions": ["Try again", "Check authentication"]
                }
            
            # Clean up the sender name
            sender = email_full['sender']
            if '<' in sender and '>' in sender:
                sender = sender.split('<')[0].strip().strip('"')
            
            # Format the response with full email content
            model_info = self.get_current_model_info()
            response_text = (
                f"📧 **Email #{email_number} - Full Content** (retrieved using {model_info}):\n\n"
                f"**Subject:** {email_full['subject']}\n\n"
                f"**From:** {sender}\n\n"
                f"**Date:** {email_full['date']}\n\n"
                f"**Message Body:**\n"
                f"{'─' * 50}\n"
                f"{email_full['body']}\n"
                f"{'─' * 50}"
            )
            
            return {
                "response": response_text,
                "action_taken": "show_email_body",
                "data": {"email": email_full, "email_number": email_number},
                "suggestions": ["Mark as read", "Reply to email", "View other emails"]
            }
            
        except Exception as e:
            logger.error(f"Error showing email body: {e}")
            return {
                "response": f"I encountered an error while retrieving the email content. Please try again.",
                "action_taken": "show_email_body_error",
                "suggestions": ["Try again", "Check authentication"]
            }

    async def _handle_summarize_email(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle summarizing email content"""
        try:
            email_number = entities.get("email_number", 1)
            
            # Get all emails using the same method as _handle_read_emails
            emails = self._fetch_emails(max_results=10)
            
            if not emails:
                return {
                    "response": "No emails found to summarize.",
                    "action_taken": "summarize_email",
                    "suggestions": ["Check all emails", "Refresh inbox"]
                }
            
            if email_number < 1 or email_number > len(emails):
                return {
                    "response": f"Email #{email_number} not found. I can summarize emails 1-{len(emails)}.",
                    "action_taken": "summarize_email",
                    "suggestions": [f"Try email 1-{len(emails)}"]
                }
            
            # Get the email at the specified position (email_number is 1-indexed)
            target_email = emails[email_number - 1]
            # Get the full email body using the message ID
            email_full = self._get_email_body(target_email['id'])
            
            if not email_full:
                return {
                    "response": f"Unable to retrieve the content of email #{email_number} for summarization.",
                    "action_taken": "summarize_email_error",
                    "suggestions": ["Try again", "Check authentication"]
                }
            
            # Clean up the sender name
            sender = email_full['sender']
            if '<' in sender and '>' in sender:
                sender = sender.split('<')[0].strip().strip('"')
            
            # Create a summary prompt for the AI
            summary_prompt = f"""Please provide a concise summary of this email:

Subject: {email_full['subject']}
From: {sender}
Date: {email_full['date']}
Content: {email_full['body']}

Please provide a brief, professional summary highlighting the key points, action items, and important details."""

            # Generate summary using the current AI model
            if settings.ai_provider == "ollama" and ollama:
                summary = await self._generate_ollama_response(summary_prompt)
            elif settings.ai_provider == "gemini" and genai and self.gemini_model:
                summary = await self._generate_gemini_response(summary_prompt)
            elif settings.ai_provider == "granite" and self.granite_model:
                summary = await self._generate_granite_response(summary_prompt)
            elif settings.ai_provider == "openai" and openai:
                summary = await self._generate_openai_response(summary_prompt)
            else:
                # Fallback to manual summary
                content = email_full['body'][:500] + "..." if len(email_full['body']) > 500 else email_full['body']
                summary = f"📧 **Email Summary**\n\n**Key Points:** {content}\n\n**Action Required:** Please review the full email for complete details."
            
            model_info = self.get_current_model_info()
            response_text = (
                f"📧 **Email #{email_number} Summary** (generated using {model_info}):\n\n"
                f"**Subject:** {email_full['subject']}\n\n"
                f"**From:** {sender}\n\n"
                f"**Date:** {email_full['date']}\n\n"
                f"**Summary:**\n"
                f"{'─' * 50}\n"
                f"{summary}\n"
                f"{'─' * 50}"
            )
            
            return {
                "response": response_text,
                "action_taken": "summarize_email",
                "data": {"email": email_full, "email_number": email_number, "summary": summary},
                "suggestions": ["Show full email", "Mark as read", "Reply to email"]
            }
            
        except Exception as e:
            logger.error(f"Error summarizing email: {e}")
            return {
                "response": f"I encountered an error while summarizing the email. Please try again.",
                "action_taken": "summarize_email_error",
                "suggestions": ["Try again", "Check authentication"]
            }

    async def _handle_categorize_emails(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle email categorization"""
        try:
            emails = self._fetch_emails(max_results=10)
            
            if not emails:
                return {
                    "response": "No emails found to categorize.",
                    "action_taken": "categorize_emails",
                    "suggestions": ["Check all emails", "Refresh inbox"]
                }
            
            categorized_emails = {
                "work": [],
                "personal": [],
                "urgent": [],
                "spam": [],
                "meetings": [],
                "other": []
            }
            
            for email in emails:
                category = self._categorize_single_email(email)
                categorized_emails[category].append(email)
            
            # Format response
            response_parts = []
            for category, email_list in categorized_emails.items():
                if email_list:
                    response_parts.append(f"**{category.upper()}** ({len(email_list)} emails):")
                    for email in email_list[:3]:  # Show first 3 per category
                        sender = email['sender']
                        if '<' in sender and '>' in sender:
                            sender = sender.split('<')[0].strip().strip('"')
                        response_parts.append(f"• {email['subject'][:50]}... (from {sender})")
                    response_parts.append("")
            
            response_text = "📧 **Email Categorization**\n\n" + "\n".join(response_parts)
            
            return {
                "response": response_text,
                "action_taken": "categorize_emails",
                "data": {"categorized_emails": categorized_emails},
                "suggestions": ["Extract action items", "Generate follow-ups", "Schedule meetings"]
            }
            
        except Exception as e:
            logger.error(f"Error categorizing emails: {e}")
            return {
                "response": "I encountered an error while categorizing emails. Please try again.",
                "action_taken": "categorize_emails_error",
                "suggestions": ["Try again", "Check authentication"]
            }

    def _categorize_single_email(self, email: Dict) -> str:
        """Categorize a single email based on content and sender"""
        subject = email['subject'].lower()
        sender = email['sender'].lower()
        snippet = email.get('snippet', '').lower()
        
        # Check for urgent keywords
        urgent_keywords = ['urgent', 'asap', 'emergency', 'critical', 'deadline', 'immediate']
        if any(keyword in subject or keyword in snippet for keyword in urgent_keywords):
            return "urgent"
        
        # Check for meeting-related content
        meeting_keywords = ['meeting', 'call', 'sync', 'appointment', 'schedule', 'calendar']
        if any(keyword in subject or keyword in snippet for keyword in meeting_keywords):
            return "meetings"
        
        # Check for work-related senders
        work_domains = ['redhat.com', 'ibm.com', 'github.com', 'openshift.org', 'kubernetes.io']
        if any(domain in sender for domain in work_domains):
            return "work"
        
        # Check for spam indicators
        spam_keywords = ['unsubscribe', 'limited time', 'act now', 'click here', 'free offer']
        if any(keyword in subject or keyword in snippet for keyword in spam_keywords):
            return "spam"
        
        # Check for personal indicators
        personal_keywords = ['family', 'friend', 'personal', 'home', 'vacation']
        if any(keyword in subject or keyword in snippet for keyword in personal_keywords):
            return "personal"
        
        return "other"

    async def _handle_extract_action_items(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle extracting action items from emails"""
        try:
            email_number = entities.get("email_number", 1)
            
            emails = self._fetch_emails(max_results=10)
            
            if not emails:
                return {
                    "response": "No emails found to extract action items from.",
                    "action_taken": "extract_action_items",
                    "suggestions": ["Check all emails", "Refresh inbox"]
                }
            
            if email_number < 1 or email_number > len(emails):
                return {
                    "response": f"Email #{email_number} not found. I can extract action items from emails 1-{len(emails)}.",
                    "action_taken": "extract_action_items",
                    "suggestions": [f"Try email 1-{len(emails)}"]
                }
            
            target_email = emails[email_number - 1]
            email_full = self._get_email_body(target_email['id'])
            
            if not email_full:
                return {
                    "response": f"Unable to retrieve the content of email #{email_number} for action item extraction.",
                    "action_taken": "extract_action_items_error",
                    "suggestions": ["Try again", "Check authentication"]
                }
            
            # Create action item extraction prompt
            action_prompt = f"""Extract action items from this email:

Subject: {email_full['subject']}
From: {email_full['sender']}
Content: {email_full['body']}

Please identify and list all action items, tasks, deadlines, and follow-up actions mentioned in this email. Format as a clear list with priorities (High/Medium/Low)."""

            # Generate action items using AI
            if settings.ai_provider == "ollama" and ollama:
                action_items = await self._generate_ollama_response(action_prompt)
            elif settings.ai_provider == "gemini" and genai and self.gemini_model:
                action_items = await self._generate_gemini_response(action_prompt)
            elif settings.ai_provider == "granite" and self.granite_model:
                action_items = await self._generate_granite_response(action_prompt)
            elif settings.ai_provider == "openai" and openai:
                action_items = await self._generate_openai_response(action_prompt)
            else:
                # Fallback to basic extraction
                action_items = self._basic_action_item_extraction(email_full['body'])
            
            model_info = self.get_current_model_info()
            response_text = (
                f"📋 **Action Items from Email #{email_number}** (extracted using {model_info}):\n\n"
                f"**Subject:** {email_full['subject']}\n\n"
                f"**Action Items:**\n"
                f"{'─' * 50}\n"
                f"{action_items}\n"
                f"{'─' * 50}"
            )
            
            return {
                "response": response_text,
                "action_taken": "extract_action_items",
                "data": {"email": email_full, "email_number": email_number, "action_items": action_items},
                "suggestions": ["Generate follow-up email", "Schedule reminders", "Add to calendar"]
            }
            
        except Exception as e:
            logger.error(f"Error extracting action items: {e}")
            return {
                "response": "I encountered an error while extracting action items. Please try again.",
                "action_taken": "extract_action_items_error",
                "suggestions": ["Try again", "Check authentication"]
            }

    def _basic_action_item_extraction(self, email_body: str) -> str:
        """Basic action item extraction using keyword matching"""
        action_items = []
        
        # Common action item patterns
        patterns = [
            r'need to (.+?)(?:\.|$)',
            r'must (.+?)(?:\.|$)',
            r'should (.+?)(?:\.|$)',
            r'please (.+?)(?:\.|$)',
            r'action required: (.+?)(?:\.|$)',
            r'next steps?: (.+?)(?:\.|$)',
            r'deadline: (.+?)(?:\.|$)',
            r'follow up on (.+?)(?:\.|$)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, email_body, re.IGNORECASE)
            for match in matches:
                action_items.append(f"• {match.strip()}")
        
        if action_items:
            return "\n".join(action_items[:10])  # Limit to 10 items
        else:
            return "No specific action items identified in this email."

    async def _handle_generate_followup(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle generating follow-up emails"""
        try:
            email_number = entities.get("email_number", 1)
            
            emails = self._fetch_emails(max_results=10)
            
            if not emails:
                return {
                    "response": "No emails found to generate follow-ups for.",
                    "action_taken": "generate_followup",
                    "suggestions": ["Check all emails", "Refresh inbox"]
                }
            
            if email_number < 1 or email_number > len(emails):
                return {
                    "response": f"Email #{email_number} not found. I can generate follow-ups for emails 1-{len(emails)}.",
                    "action_taken": "generate_followup",
                    "suggestions": [f"Try email 1-{len(emails)}"]
                }
            
            target_email = emails[email_number - 1]
            email_full = self._get_email_body(target_email['id'])
            
            if not email_full:
                return {
                    "response": f"Unable to retrieve the content of email #{email_number} for follow-up generation.",
                    "action_taken": "generate_followup_error",
                    "suggestions": ["Try again", "Check authentication"]
                }
            
            # Extract sender email for follow-up
            sender_email = self._extract_email_from_sender(email_full['sender'])
            
            # Generate follow-up content
            followup_prompt = f"""Generate a professional follow-up email based on this original email:

Original Subject: {email_full['subject']}
Original Sender: {email_full['sender']}
Original Content: {email_full['body']}

Create a polite, professional follow-up email that:
1. References the original conversation
2. Asks for an update or response
3. Maintains a professional tone
4. Is concise and clear

Format the response as a complete email with subject and body."""

            # Generate follow-up using AI
            if settings.ai_provider == "ollama" and ollama:
                followup_content = await self._generate_ollama_response(followup_prompt)
            elif settings.ai_provider == "gemini" and genai and self.gemini_model:
                followup_content = await self._generate_gemini_response(followup_prompt)
            elif settings.ai_provider == "granite" and self.granite_model:
                followup_content = await self._generate_granite_response(followup_prompt)
            elif settings.ai_provider == "openai" and openai:
                followup_content = await self._generate_openai_response(followup_prompt)
            else:
                # Use template-based follow-up
                followup_content = self._generate_template_followup(email_full)
            
            model_info = self.get_current_model_info()
            response_text = (
                f"📧 **Follow-up Email for Email #{email_number}** (generated using {model_info}):\n\n"
                f"**To:** {sender_email}\n\n"
                f"**Generated Follow-up:**\n"
                f"{'─' * 50}\n"
                f"{followup_content}\n"
                f"{'─' * 50}"
            )
            
            return {
                "response": response_text,
                "action_taken": "generate_followup",
                "data": {"email": email_full, "email_number": email_number, "followup": followup_content, "to_email": sender_email},
                "suggestions": ["Send follow-up email", "Edit follow-up", "Schedule for later"]
            }
            
        except Exception as e:
            logger.error(f"Error generating follow-up: {e}")
            return {
                "response": "I encountered an error while generating the follow-up email. Please try again.",
                "action_taken": "generate_followup_error",
                "suggestions": ["Try again", "Check authentication"]
            }

    def _extract_email_from_sender(self, sender: str) -> str:
        """Extract email address from sender string"""
        email_pattern = r'<(.+?)>'
        match = re.search(email_pattern, sender)
        if match:
            return match.group(1)
        return sender

    def _extract_template_entities(self, message: str) -> Dict[str, Any]:
        """Extract template-related entities from message"""
        entities = {}
        message_lower = message.lower()
        
        # Extract template type
        template_types = ["meeting_confirmation", "follow_up", "document_request", "project_update"]
        for template_type in template_types:
            if template_type.replace("_", " ") in message_lower:
                entities["template_type"] = template_type
                break
        
        # Extract recipient
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, message)
        if emails:
            entities["to_email"] = emails[0]
        
        # Extract other template variables
        if "meeting" in message_lower:
            entities["meeting_title"] = "Meeting"
            entities["meeting_time"] = "TBD"
            entities["meeting_date"] = "TBD"
            entities["meeting_location"] = "TBD"
        
        if "document" in message_lower:
            entities["document_name"] = "Document"
            entities["purpose"] = "Review"
            entities["deadline"] = "TBD"
        
        if "project" in message_lower:
            entities["project_name"] = "Project"
            entities["status"] = "In Progress"
            entities["achievements"] = "Milestones achieved"
            entities["next_steps"] = "Continue development"
            entities["blockers"] = "None"
        
        return entities

    async def _handle_use_email_template(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle using email templates"""
        try:
            template_type = entities.get("template_type", "follow_up")
            
            if template_type not in self.email_templates:
                available_templates = ", ".join(self.email_templates.keys())
                return {
                    "response": f"Template '{template_type}' not found. Available templates: {available_templates}",
                    "action_taken": "template_not_found",
                    "suggestions": [f"Use {t}" for t in self.email_templates.keys()]
                }
            
            template = self.email_templates[template_type]
            
            # Fill template with provided entities or defaults
            filled_template = self._fill_email_template(template, entities)
            
            response_text = (
                f"📧 **Email Template: {template_type.replace('_', ' ').title()}**\n\n"
                f"**Generated Email:**\n"
                f"{'─' * 50}\n"
                f"{filled_template}\n"
                f"{'─' * 50}"
            )
            
            return {
                "response": response_text,
                "action_taken": "use_email_template",
                "data": {"template_type": template_type, "filled_template": filled_template, "entities": entities},
                "suggestions": ["Send email", "Edit template", "Use different template"]
            }
            
        except Exception as e:
            logger.error(f"Error using email template: {e}")
            return {
                "response": "I encountered an error while using the email template. Please try again.",
                "action_taken": "template_error",
                "suggestions": ["Try again", "Use different template"]
            }

    def _fill_email_template(self, template: Dict, entities: Dict) -> str:
        """Fill email template with provided entities"""
        subject = template["subject"]
        body = template["body"]
        
        # Fill subject
        for key, value in entities.items():
            if f"{{{key}}}" in subject:
                subject = subject.replace(f"{{{key}}}", str(value))
        
        # Fill body
        for key, value in entities.items():
            if f"{{{key}}}" in body:
                body = body.replace(f"{{{key}}}", str(value))
        
        # Fill with defaults for missing values
        defaults = {
            "recipient_name": "Recipient",
            "user_name": "Your Assistant",
            "meeting_title": "Meeting",
            "meeting_time": "TBD",
            "meeting_date": "TBD",
            "meeting_location": "TBD",
            "original_subject": "Previous Email",
            "topic": "Previous Discussion",
            "previous_summary": "Previous conversation details",
            "action_items": "Next steps to be determined",
            "document_name": "Document",
            "purpose": "Review",
            "deadline": "TBD",
            "project_name": "Project",
            "status": "In Progress",
            "achievements": "Milestones achieved",
            "next_steps": "Continue development",
            "blockers": "None"
        }
        
        for key, default_value in defaults.items():
            if f"{{{key}}}" in subject:
                subject = subject.replace(f"{{{key}}}", default_value)
            if f"{{{key}}}" in body:
                body = body.replace(f"{{{key}}}", default_value)
        
        return f"Subject: {subject}\n\n{body}"

    def _generate_template_followup(self, email: Dict) -> str:
        """Generate follow-up using template"""
        template = self.email_templates["follow_up"]
        
        # Extract basic info
        subject = email['subject']
        sender = email['sender']
        if '<' in sender and '>' in sender:
            sender_name = sender.split('<')[0].strip().strip('"')
        else:
            sender_name = sender
        
        # Simple content summary
        content_preview = email['body'][:200] + "..." if len(email['body']) > 200 else email['body']
        
        # Fill template
        followup_subject = template["subject"].format(original_subject=subject)
        followup_body = template["body"].format(
            recipient_name=sender_name,
            topic=subject,
            previous_summary=content_preview,
            action_items="Please provide an update on the items discussed.",
            user_name="Your Assistant"
        )
        
        return f"Subject: {followup_subject}\n\n{followup_body}"

    async def _handle_mark_email_read(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle marking emails as read"""
        try:
            email_number = entities.get("email_number", 1)
            
            # Get unread emails from the notifications API
            from app.api.notifications import get_unread_emails
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/api/notifications/unread-emails")
                
                if response.status_code == 200:
                    data = response.json()
                    unread_emails = data.get("unread_emails", [])
                    count = data.get("count", 0)
                    
                    if not unread_emails:
                        return {
                            "response": "No unread emails found to mark as read.",
                            "action_taken": "mark_email_read",
                            "suggestions": ["Check all emails", "Refresh inbox"]
                        }
                    
                    if email_number < 1 or email_number > len(unread_emails):
                        return {
                            "response": f"Email #{email_number} not found. I can mark unread emails 1-{len(unread_emails)} as read.",
                            "action_taken": "mark_email_read",
                            "suggestions": [f"Try email 1-{len(unread_emails)}"]
                        }
                    
                    # Get the email at the specified position (email_number is 1-indexed)
                    target_email = unread_emails[email_number - 1]
                    message_id = target_email['id']
                    
                    # Mark the email as read using Gmail API
                    try:
                        credentials = get_google_credentials()
                        if not credentials:
                            return {
                                "response": "Unable to access Gmail. Please check your authentication.",
                                "action_taken": "mark_email_read_error",
                                "suggestions": ["Check authentication", "Try again"]
                            }
                        
                        from googleapiclient.discovery import build
                        service = build('gmail', 'v1', credentials=credentials)
                        
                        # Remove the UNREAD label from the email
                        service.users().messages().modify(
                            userId='me',
                            id=message_id,
                            body={'removeLabelIds': ['UNREAD']}
                        ).execute()
                        
                        # Clean up the sender name for display
                        sender = target_email['sender']
                        if '<' in sender and '>' in sender:
                            sender = sender.split('<')[0].strip().strip('"')
                        
                        model_info = self.get_current_model_info()
                        response_text = (
                            f"✅ **Email #{email_number} marked as read** (using {model_info}):\n\n"
                            f"**Subject:** {target_email['subject']}\n\n"
                            f"**From:** {sender}\n\n"
                            f"**Date:** {target_email['date']}\n\n"
                            f"📧 The email has been successfully marked as read and removed from your unread emails list."
                        )
                        
                        return {
                            "response": response_text,
                            "action_taken": "mark_email_read_success",
                            "data": {"email": target_email, "email_number": email_number},
                            "suggestions": ["Show unread emails", "Check all emails", "Mark another email as read"]
                        }
                        
                    except Exception as e:
                        logger.error(f"Error marking email as read: {e}")
                        return {
                            "response": f"I encountered an error while marking email #{email_number} as read. Please try again.",
                            "action_taken": "mark_email_read_error",
                            "suggestions": ["Try again", "Check authentication"]
                        }
                else:
                    return {
                        "response": f"I encountered an error while retrieving unread emails. Please try again.",
                        "action_taken": "mark_email_read_error",
                        "suggestions": ["Try again", "Check authentication"]
                    }
                    
        except Exception as e:
            logger.error(f"Error marking email as read: {e}")
            return {
                "response": f"I encountered an error while marking the email as read. Please try again.",
                "action_taken": "mark_email_read_error",
                "suggestions": ["Try again", "Check authentication"]
        }

    async def _handle_create_event(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle creating calendar event"""
        # Extract event details from the message
        title = entities.get("title") or self._extract_event_title_from_message(message)
        attendees = self._extract_attendees_from_message(message)
        
        # Check if this is a meeting invite request
        if any(phrase in message.lower() for phrase in ["meeting invite", "send invite", "invite", "attendee"]):
            if not attendees:
                return {
                    "response": "I'll help you create a meeting invite! Who should I invite? Please provide their email address.",
                    "action_taken": "request_attendees",
                    "suggestions": ["Provide attendee email addresses"]
                }
                
            if not title:
                return {
                    "response": "What should be the title of the meeting?",
                    "action_taken": "request_event_title", 
                    "suggestions": ["Provide meeting title"]
                }
                
            # For meeting invites, try to create the actual event
            try:
                event_result = await self._create_calendar_event_with_attendees(title, attendees, message)
                if event_result.get("success"):
                    attendee_list = ", ".join(attendees)
                    model_info = self.get_current_model_info()
                    
                    # Get email status from the calendar API response
                    email_status = event_result.get("email_status", "")
                    meet_link = event_result.get("meet_link", "")
                    external_attendees = event_result.get("external_attendees", [])
                    self_invited = event_result.get("self_invited", False)
                    
                    # Build response message with email status
                    response_msg = f"✅ Meeting invite created successfully! (using {model_info})<br><br>📅 **Meeting Details:**<br>**Title:** {title}<br>**Attendees:** {attendee_list}<br>**Event ID:** {event_result.get('event_id', 'N/A')}<br><br>"
                    
                    if meet_link:
                        response_msg += f"🔗 **Google Meet Link:** {meet_link}<br><br>"
                    
                    if email_status:
                        response_msg += f"📧 **Email Status:** {email_status}<br><br>"
                    
                    if self_invited and not external_attendees:
                        response_msg += "ℹ️ **Note:** Since you're the organizer and only attendee, no email invitation was sent (this is normal Google Calendar behavior).<br><br>"
                    elif external_attendees:
                        response_msg += f"📬 **Email invitations sent to:** {', '.join(external_attendees)}<br><br>"
                    
                    response_msg += "Calendar event has been created and is now in your calendar!"
                    
                    return {
                        "response": response_msg,
                        "action_taken": "meeting_invite_created",
                        "data": {
                            "title": title, 
                            "attendees": attendees, 
                            "event_id": event_result.get("event_id"),
                            "email_status": email_status,
                            "meet_link": meet_link,
                            "external_attendees": external_attendees,
                            "self_invited": self_invited
                        },
                        "suggestions": ["View calendar", "Create another event", "Invite external attendees"]
                    }
                else:
                    return {
                        "response": f"I had trouble creating the calendar event. Error: {event_result.get('error', 'Unknown error')}. You can try creating it manually through the calendar interface.",
                        "action_taken": "event_creation_failed",
                        "suggestions": ["Try again", "Use calendar interface"]
                    }
            except Exception as e:
                logger.error(f"Error creating calendar event: {e}")
                return {
                    "response": f"I encountered an error while creating the meeting invite: {str(e)}. You can try creating it manually through the calendar interface.",
                    "action_taken": "event_creation_error",
                    "suggestions": ["Try again", "Use calendar interface"]
                }
        else:
            # Regular event creation
            if not title:
                return {
                    "response": "I'll help you create a calendar event! What should be the title of the event?",
                    "action_taken": "request_event_title",
                    "suggestions": ["Provide event title"]
                }
            
            return {
                "response": f"I'll create a calendar event titled '{title}'. Please use the calendar interface to set the date, time, and other details.",
                "action_taken": "prepare_create_event",
                "data": {"title": title, "datetime": entities.get("datetime")}
            }

    async def _handle_get_events(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle getting calendar events"""
        try:
            # Call the Calendar API function directly
            events = self._fetch_calendar_events(max_results=10)
            
            if events:
                # Format the first few events for display with better formatting
                formatted_events = []
                for i, event in enumerate(events[:5]):  # Show first 5 events
                    start_time_raw = event.get('start', 'No time specified')
                    
                    # Format the time in a more readable way
                    formatted_time = self._format_event_time(start_time_raw)
                    
                    # Create nicely formatted event entry with HTML line breaks
                    event_entry = (
                        f"🗓️ **{i+1}. {event['summary']}**<br>"
                        f"   📅 **Time:** {formatted_time}<br>"
                        f"   ✅ **Status:** {event.get('status', 'Unknown').title()}"
                    )
                    formatted_events.append(event_entry)
                
                # Join events with double HTML line breaks for better readability
                events_summary = "<br><br>".join(formatted_events)
                return {
                    "response": f"📋 **Your Upcoming Calendar Events:**<br><br>{events_summary}",
                    "action_taken": "fetch_events",
                    "data": {"events": events},
                    "suggestions": ["View today's events", "View this week's events", "Create new event"]
                }
            else:
                return {
                    "response": "📅 No upcoming events found in your calendar.",
                    "action_taken": "fetch_events",
                    "suggestions": ["Create new event", "View past events", "Check calendar settings"]
                }
        except Exception as e:
            logger.error(f"Error fetching events: {e}")
            return {
                "response": "⚠️ I encountered an error while retrieving your calendar events. Please try again.",
                "action_taken": "fetch_events_error",
                "suggestions": ["Try again", "Check authentication", "Refresh connection"]
            }

    async def _handle_search_contacts(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle searching contacts"""
        query = entities.get("query", message)
        return {
            "response": f"I'll search your contacts for: '{query}'. Please check the contacts interface for results.",
            "action_taken": "search_contacts",
            "data": {"query": query}
        }

    async def _handle_create_contact(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle creating a contact"""
        name = entities.get("name")
        if not name:
            return {
                "response": "I'll help you create a new contact! What's the person's name?",
                "action_taken": "request_contact_name",
                "suggestions": ["Provide contact name"]
            }
        
        return {
            "response": f"I'll create a contact for {name}. Please use the contacts interface to add additional details.",
            "action_taken": "prepare_create_contact",
            "data": {"name": name}
        }

    async def _handle_send_slack_message(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle sending Slack message"""
        channel = entities.get("channel")
        message_text = entities.get("message")
        
        if not channel:
            return {
                "response": "I'll help you send a Slack message! Which channel should I send it to?",
                "action_taken": "request_slack_channel",
                "suggestions": ["Specify channel name"]
            }
        
        return {
            "response": f"I'll send a message to {channel}. Please use the Slack interface to compose and send your message.",
            "action_taken": "prepare_send_slack_message",
            "data": {"channel": channel, "message": message_text}
        }

    async def _handle_read_slack_messages(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle reading Slack messages"""
        return {
            "response": "I'll show you your recent Slack messages. Please check the Slack interface.",
            "action_taken": "fetch_slack_messages",
            "suggestions": ["Check specific channels", "Search messages"]
        }
    
    async def _handle_analyze_must_gather(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle must-gather analysis requests"""
        try:
            from app.services.must_gather_analyzer import must_gather_analyzer
            
            must_gather_path = entities.get("must_gather_path")
            analysis_type = entities.get("analysis_type", "full")
            
            if not must_gather_path:
                return {
                    "response": "🔍 **Must-Gather Analysis Ready!**<br><br>I can help you analyze OpenShift must-gather data. Please provide the path to your must-gather directory.<br><br>**Example:** `analyze must-gather path /path/to/must-gather.local.xxx`<br><br>**Available Analysis Types:**<br>• Full analysis (comprehensive)<br>• Health check (quick overview)<br>• Specific components (etcd, nodes, pods, operators, KMS)<br><br>**What I can analyze:**<br>• Cluster health and version<br>• Node status and capacity<br>• Pod issues and failures<br>• Cluster operator conditions<br>• etcd health and member status<br>• KMS encryption configuration<br>• Performance issues<br>• Certificate problems",
                    "action_taken": "request_must_gather_path",
                    "suggestions": ["Provide must-gather path", "Quick health check", "Specific component analysis"]
                }
            
            # Perform the analysis
            logger.info(f"Starting must-gather analysis: {must_gather_path} (type: {analysis_type})")
            analysis_result = await must_gather_analyzer.analyze_must_gather(must_gather_path, analysis_type)
            
            if "error" in analysis_result:
                return {
                    "response": f"❌ **Analysis Error**<br><br>I encountered an error analyzing the must-gather data:<br><br>**Error:** {analysis_result['error']}<br><br>**Please check:**<br>• Must-gather path is correct<br>• Directory exists and is accessible<br>• Must-gather is properly extracted",
                    "action_taken": "analysis_error",
                    "suggestions": ["Check path", "Verify directory", "Try different path"]
                }
            
            # Format the response
            findings = analysis_result.get("findings", {})
            summary = analysis_result.get("summary", "Analysis completed")
            recommendations = analysis_result.get("ai_recommendations", [])
            
            response_parts = [
                f"🔍 **Must-Gather Analysis Complete**<br><br>",
                f"**📊 Summary:** {summary}<br><br>"
            ]
            
            # Add findings summary
            if "cluster_health" in findings and findings["cluster_health"].get("cluster_version"):
                cv = findings["cluster_health"]["cluster_version"]
                response_parts.append(f"**🏗️ Cluster Version:** {cv.get('version', 'Unknown')}<br>")
            
            if "nodes" in findings:
                nodes = findings["nodes"]
                response_parts.append(f"**🖥️ Nodes:** {nodes['ready_nodes']}/{nodes['total_nodes']} ready<br>")
            
            if "pods" in findings:
                pods = findings["pods"]
                response_parts.append(f"**📦 Pods:** {pods['running_pods']} running, {pods['failed_pods']} failed, {pods['pending_pods']} pending<br>")
            
            if "operators" in findings:
                ops = findings["operators"]
                response_parts.append(f"**⚙️ Operators:** {ops['degraded_operators']} degraded out of {ops['total_operators']}<br>")
            
            if "etcd" in findings and findings["etcd"].get("issues"):
                response_parts.append(f"**🗄️ etcd Issues:** {len(findings['etcd']['issues'])} detected<br>")
            
            response_parts.append("<br>")
            
            # Add recommendations if any
            if recommendations:
                response_parts.append("**🎯 AI Recommendations:**<br>")
                for i, rec in enumerate(recommendations[:5], 1):
                    response_parts.append(f"{i}. {rec}<br>")
                response_parts.append("<br>")
            
            response_parts.append(f"**📝 Analysis Type:** {analysis_type}<br>")
            response_parts.append(f"**📅 Timestamp:** {analysis_result.get('timestamp', 'Unknown')}")
            
            model_info = self.get_current_model_info()
            response_parts.insert(1, f"*Analyzed using {model_info}*<br><br>")
            
            return {
                "response": "".join(response_parts),
                "action_taken": "must_gather_analyzed",
                "data": {
                    "analysis_result": analysis_result,
                    "path": must_gather_path,
                    "type": analysis_type,
                    "summary": summary,
                    "recommendations": recommendations
                },
                "suggestions": ["Detailed report", "Specific component analysis", "Export results"]
            }
            
        except Exception as e:
            logger.error(f"Error in must-gather analysis: {e}")
            return {
                "response": f"❌ **Analysis Failed**<br><br>I encountered an unexpected error during analysis:<br><br>**Error:** {str(e)}<br><br>Please check the must-gather path and try again.",
                "action_taken": "analysis_exception",
                "suggestions": ["Check logs", "Verify path", "Try again"]
            }
    
    async def _handle_health_check(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle quick health check requests"""
        try:
            from app.services.must_gather_analyzer import must_gather_analyzer
            
            must_gather_path = entities.get("must_gather_path")
            
            if not must_gather_path:
                return {
                    "response": "🏥 **Quick Health Check**<br><br>I can perform a rapid health assessment of your OpenShift cluster using must-gather data.<br><br>**Usage:** `health check path /path/to/must-gather.local.xxx`<br><br>**What I'll check:**<br>• Cluster overall health score<br>• Critical issues<br>• Node readiness<br>• Operator status<br>• Pod failure rates<br><br>This provides a quick overview in under 30 seconds!",
                    "action_taken": "request_health_check_path",
                    "suggestions": ["Provide must-gather path", "Full analysis", "Specific checks"]
                }
            
            logger.info(f"Starting quick health check: {must_gather_path}")
            health_result = await must_gather_analyzer.quick_health_check(must_gather_path)
            
            if "error" in health_result:
                return {
                    "response": f"❌ **Health Check Error**<br><br>{health_result['error']}",
                    "action_taken": "health_check_error",
                    "suggestions": ["Check path", "Full analysis", "Try again"]
                }
            
            # Format health check response
            health_score = health_result.get("health_score", 0)
            status = health_result.get("status", "Unknown")
            issues = health_result.get("issues", [])
            
            # Status emoji and color
            status_emoji = {
                "Healthy": "✅",
                "Warning": "⚠️",
                "Degraded": "🔴",
                "Critical": "🚨"
            }.get(status, "❓")
            
            response_parts = [
                f"🏥 **Quick Health Check Results**<br><br>",
                f"**{status_emoji} Overall Status:** {status}<br>",
                f"**📊 Health Score:** {health_score}/100<br><br>"
            ]
            
            if issues:
                response_parts.append("**⚠️ Issues Detected:**<br>")
                for issue in issues[:5]:
                    response_parts.append(f"• {issue}<br>")
                if len(issues) > 5:
                    response_parts.append(f"• ... and {len(issues) - 5} more issues<br>")
                response_parts.append("<br>")
            else:
                response_parts.append("**🎉 No critical issues detected!**<br><br>")
            
            if health_score < 70:
                response_parts.append("**💡 Recommendation:** Run a full analysis for detailed troubleshooting guidance.<br><br>")
            
            model_info = self.get_current_model_info()
            response_parts.append(f"*Health check completed using {model_info}*")
            
            return {
                "response": "".join(response_parts),
                "action_taken": "health_check_completed",
                "data": {
                    "health_result": health_result,
                    "path": must_gather_path,
                    "score": health_score,
                    "status": status,
                    "issues": issues
                },
                "suggestions": ["Full analysis", "Address issues", "Export report"]
            }
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return {
                "response": f"❌ **Health Check Failed**<br><br>Error: {str(e)}",
                "action_taken": "health_check_exception",
                "suggestions": ["Check path", "Try again", "Full analysis"]
            }
    
    async def _handle_openshift_troubleshoot(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle OpenShift troubleshooting requests"""
        component = entities.get("component", "general")
        namespace = entities.get("namespace", "")
        
        troubleshooting_guides = {
            "pods": {
                "title": "Pod Troubleshooting Guide",
                "commands": [
                    "oc get pods -A",
                    "oc describe pod <pod-name> -n <namespace>",
                    "oc logs <pod-name> -n <namespace>",
                    "oc get events -n <namespace> --sort-by='.lastTimestamp'"
                ],
                "common_issues": [
                    "ImagePullBackOff: Check image name and registry access",
                    "CrashLoopBackOff: Check application logs and configuration",
                    "Pending: Check resource requests and node capacity",
                    "Init container issues: Check init container logs"
                ]
            },
            "nodes": {
                "title": "Node Troubleshooting Guide", 
                "commands": [
                    "oc get nodes",
                    "oc describe node <node-name>",
                    "oc adm top nodes",
                    "oc get pods -o wide | grep <node-name>"
                ],
                "common_issues": [
                    "NotReady: Check node conditions and kubelet logs",
                    "High resource usage: Review workload distribution",
                    "Disk pressure: Check disk usage and cleanup",
                    "Network issues: Verify node connectivity"
                ]
            },
            "operators": {
                "title": "Cluster Operator Troubleshooting",
                "commands": [
                    "oc get co",
                    "oc describe co <operator-name>",
                    "oc get pods -n openshift-<operator-namespace>",
                    "oc logs deployment/<operator-deployment> -n openshift-<namespace>"
                ],
                "common_issues": [
                    "Degraded: Check operator pod logs and conditions",
                    "Progressing stuck: Review operator events and logs",
                    "Authentication issues: Check certificates and permissions",
                    "Resource constraints: Verify node capacity"
                ]
            },
            "etcd": {
                "title": "etcd Troubleshooting Guide",
                "commands": [
                    "oc get pods -n openshift-etcd",
                    "oc logs <etcd-pod> -n openshift-etcd",
                    "oc rsh <etcd-pod> -n openshift-etcd",
                    "etcdctl member list"
                ],
                "common_issues": [
                    "Member unhealthy: Check network connectivity between etcd members",
                    "High latency: Check disk I/O and network performance",
                    "Quorum loss: Ensure at least 2 of 3 members are healthy",
                    "Certificate issues: Verify etcd certificates"
                ]
            }
        }
        
        guide = troubleshooting_guides.get(component, troubleshooting_guides["pods"])
        
        response_parts = [
            f"🔧 **{guide['title']}**<br><br>",
            "**🔍 Diagnostic Commands:**<br>"
        ]
        
        for cmd in guide["commands"]:
            response_parts.append(f"`{cmd}`<br>")
        
        response_parts.append("<br>**⚠️ Common Issues:**<br>")
        for issue in guide["common_issues"]:
            response_parts.append(f"• {issue}<br>")
        
        if namespace:
            response_parts.append(f"<br>**📂 Focused on namespace:** {namespace}<br>")
        
        response_parts.append("<br>**💡 For deeper analysis, provide your must-gather data for automated troubleshooting.**")
        
        model_info = self.get_current_model_info()
        response_parts.append(f"<br><br>*Troubleshooting guide generated using {model_info}*")
        
        return {
            "response": "".join(response_parts),
            "action_taken": "openshift_troubleshooting",
            "data": {
                "component": component,
                "namespace": namespace,
                "guide": guide
            },
            "suggestions": ["Run diagnostics", "Analyze must-gather", "Specific component help"]
        }
    
    async def _handle_kms_analysis(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle KMS encryption analysis requests"""
        
        kms_info = {
            "title": "KMS Encryption Analysis & Troubleshooting",
            "setup_steps": [
                "1. Enable KMSEncryptionProvider feature gate",
                "2. Set up AWS KMS using: https://github.com/gangwgr/kms-setup",
                "3. Apply KMS configuration with proper keyARN and region",
                "4. Verify encryption with hexdump showing k8s:enc:kms:v2 pattern"
            ],
            "common_errors": [
                "Missing region: spec.encryption.kms.aws.region: Required value",
                "Invalid encryption type: kms config is required when encryption type is KMS",
                "Missing KMS config when type is KMS",
                "Invalid keyARN format: must follow arn:aws:kms:<region>:<account_id>:key/<key_id>",
                "Unsupported encryption types: supported are '', 'identity', 'aescbc', 'aesgcm', 'KMS'"
            ],
            "troubleshooting_commands": [
                "oc get co | grep -E '(False|Unknown|Degraded)'",
                "oc get pods -n openshift-kube-apiserver -l name=aws-kms-plugin",
                "oc logs <kms-plugin-pod> -n openshift-kube-apiserver",
                "oc get secrets -n openshift-config | grep encryption",
                "hexdump -C /path/to/etcd/data | grep -E 'k8s:enc:(kms|aescbc)'"
            ]
        }
        
        response_parts = [
            f"🔐 **{kms_info['title']}**<br><br>",
            "**🚀 KMS Setup Steps:**<br>"
        ]
        
        for step in kms_info["setup_steps"]:
            response_parts.append(f"{step}<br>")
        
        response_parts.append("<br>**❌ Common KMS Errors:**<br>")
        for error in kms_info["common_errors"]:
            response_parts.append(f"• {error}<br>")
        
        response_parts.append("<br>**🔍 Troubleshooting Commands:**<br>")
        for cmd in kms_info["troubleshooting_commands"]:
            response_parts.append(f"`{cmd}`<br>")
        
        response_parts.append("<br>**📚 Reference:**<br>")
        response_parts.append("• KMS Setup: https://github.com/gangwgr/kms-setup<br>")
        response_parts.append("• Feature Gate: KMSEncryptionProvider (NOT KMSSecretsEnable)<br>")
        response_parts.append("• Official Docs: docs.openshift.com<br>")
        
        response_parts.append("<br>**💡 For detailed KMS analysis, provide your must-gather data.**")
        
        model_info = self.get_current_model_info()
        response_parts.append(f"<br><br>*KMS guidance provided using {model_info}*")
        
        return {
            "response": "".join(response_parts),
            "action_taken": "kms_analysis",
            "data": {
                "kms_info": kms_info,
                "query": message
            },
            "suggestions": ["Analyze must-gather for KMS", "Check KMS plugin status", "Verify encryption config"]
        }

    async def _handle_general_conversation(self, message: str) -> Dict[str, Any]:
        """Handle general conversation using configured AI provider"""
        try:
            ai_response = ""
            
            # Route to appropriate AI provider
            if settings.ai_provider == "granite":
                ai_response = await self._generate_granite_response(message)
            elif settings.ai_provider == "ollama":
                ai_response = await self._generate_ollama_response(message)
            elif settings.ai_provider == "gemini":
                ai_response = await self._generate_gemini_response(message)
            elif settings.ai_provider == "openai" and settings.openai_api_key:
                # Use OpenAI for general conversation
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=settings.openai_api_key)
                    response = client.chat.completions.create(
                        model=settings.openai_model,
                        messages=[
                            {"role": "system", "content": "You are a helpful AI assistant that specializes in managing emails, calendar events, contacts, and Slack messages. Keep responses concise and helpful."},
                            {"role": "user", "content": message}
                        ],
                        max_tokens=200,
                        temperature=0.7
                    )
                    ai_response = response.choices[0].message.content.strip()
                except Exception as e:
                    logger.error(f"OpenAI API error: {e}")
                    ai_response = "I'm here to help you manage your digital workspace!"
            else:
                ai_response = "I'm here to help you manage your emails, calendar, contacts, and Slack messages. What would you like to do?"
            
            return {
                "response": ai_response,
                "action_taken": "general_conversation",
                "suggestions": ["Ask about email management", "Ask about calendar", "Ask about contacts", "Ask about Slack"]
            }
            
        except Exception as e:
            logger.error(f"Error in general conversation: {e}")
            return {
                "response": "I'm here to help you manage your digital workspace! I can assist with emails, calendar events, contacts, and Slack messages. What would you like to do?",
                "suggestions": ["Check recent emails", "View upcoming events", "Search contacts", "Send a message"]
            }

    # Kubernetes/OpenShift handlers
    async def _handle_list_pods(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle list pods command"""
        namespace = entities.get("namespace", "default")
        resource_name = entities.get("resource_name")
        
        if resource_name:
            command = f"kubectl get pods {resource_name} -n {namespace}"
            response_text = f"**List Specific Pod:**\n```bash\n{command}\n```\n\n**Alternative (OpenShift):**\n```bash\noc get pods {resource_name} -n {namespace}\n```"
        else:
            command = f"kubectl get pods -n {namespace}"
            response_text = f"**List All Pods in {namespace}:**\n```bash\n{command}\n```\n\n**Alternative (OpenShift):**\n```bash\noc get pods -n {namespace}\n```\n\n**Additional Options:**\n```bash\n# Show more details\nkubectl get pods -n {namespace} -o wide\n\n# Show labels\nkubectl get pods -n {namespace} --show-labels\n\n# Watch pods\nkubectl get pods -n {namespace} -w\n```"
        
        return {
            "response": response_text,
            "action_taken": "list_pods",
            "suggestions": ["Describe a specific pod", "Get pod logs", "Exec into a pod", "List services"]
        }

    async def _handle_list_namespaces(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle list namespaces command"""
        message_lower = message.lower()
        
        # Check if user is asking about pods in a namespace
        if any(phrase in message_lower for phrase in ["pod in ns", "pods in ns", "pod in namespace", "pods in namespace"]):
            response_text = """**List Pods in a Namespace:**

**Basic Command:**
```bash
kubectl get pods -n <namespace>
```

**Alternative (OpenShift):**
```bash
oc get pods -n <namespace>
```

**Examples:**
```bash
# List pods in default namespace
kubectl get pods

# List pods in specific namespace
kubectl get pods -n kube-system

# List pods in all namespaces
kubectl get pods --all-namespaces

# Show more details
kubectl get pods -n <namespace> -o wide

# Show labels
kubectl get pods -n <namespace> --show-labels

# Watch pods
kubectl get pods -n <namespace> -w
```

**💡 Tips:**
- Use `-n` for namespace (or `--namespace`)
- Use `--all-namespaces` to see pods across all namespaces
- Use `-o wide` for more details
- Use `-w` to watch for changes"""
        else:
            response_text = "**List All Namespaces:**\n```bash\nkubectl get namespaces\n```\n\n**Alternative (OpenShift):**\n```bash\noc get projects\n```\n\n**Additional Options:**\n```bash\n# Show more details\nkubectl get namespaces -o wide\n\n# Show labels\nkubectl get namespaces --show-labels\n\n# Create a new namespace\nkubectl create namespace <name>\n\n# OpenShift specific\noc get projects --show-labels\noc new-project <project-name>\n```"
        
        return {
            "response": response_text,
            "action_taken": "list_namespaces",
            "suggestions": ["Create a namespace", "List pods in namespace", "List services", "List deployments"]
        }

    async def _handle_list_services(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle list services command"""
        namespace = entities.get("namespace", "default")
        response_text = f"**List Services in {namespace}:**\n```bash\nkubectl get services -n {namespace}\n```\n\n**Alternative (OpenShift):**\n```bash\noc get services -n {namespace}\n```\n\n**Additional Options:**\n```bash\n# Show more details\nkubectl get services -n {namespace} -o wide\n\n# Show endpoints\nkubectl get endpoints -n {namespace}\n\n# Describe a service\nkubectl describe service <service-name> -n {namespace}\n```"
        
        return {
            "response": response_text,
            "action_taken": "list_services",
            "suggestions": ["Describe a service", "List pods", "List deployments", "Port forward to service"]
        }

    async def _handle_list_deployments(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle list deployments command"""
        namespace = entities.get("namespace", "default")
        response_text = f"**List Deployments in {namespace}:**\n```bash\nkubectl get deployments -n {namespace}\n```\n\n**Alternative (OpenShift):**\n```bash\noc get deployments -n {namespace}\n```\n\n**Additional Options:**\n```bash\n# Show more details\nkubectl get deployments -n {namespace} -o wide\n\n# Show rollout status\nkubectl rollout status deployment/<name> -n {namespace}\n\n# Scale deployment\nkubectl scale deployment <name> --replicas=3 -n {namespace}\n```"
        
        return {
            "response": response_text,
            "action_taken": "list_deployments",
            "suggestions": ["Describe a deployment", "Scale deployment", "List pods", "View deployment logs"]
        }

    async def _handle_kubernetes_help(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle general Kubernetes help"""
        response_text = """**🔧 Kubernetes/OpenShift Command Reference**

**📋 Basic Commands:**
```bash
# List resources
kubectl get pods -n <namespace>
kubectl get services -n <namespace>
kubectl get deployments -n <namespace>
kubectl get namespaces

# Describe resources
kubectl describe pod <pod-name> -n <namespace>
kubectl describe service <service-name> -n <namespace>

# Get logs
kubectl logs <pod-name> -n <namespace>
kubectl logs -f <pod-name> -n <namespace>  # Follow logs

# Exec into pod
kubectl exec -it <pod-name> -n <namespace> -- /bin/bash
```

**🔄 OpenShift Equivalents:**
```bash
# Replace kubectl with oc
oc get pods -n <namespace>
oc describe pod <pod-name> -n <namespace>
oc logs <pod-name> -n <namespace>
oc exec -it <pod-name> -n <namespace> -- /bin/bash
```

**🔍 Useful Options:**
```bash
# Show more details
kubectl get pods -o wide -n <namespace>

# Watch resources
kubectl get pods -w -n <namespace>

# Show labels
kubectl get pods --show-labels -n <namespace>

# Filter by label
kubectl get pods -l app=myapp -n <namespace>
```

**📚 Common Patterns:**
- `kubectl get <resource> -n <namespace>` - List resources
- `kubectl describe <resource> <name> -n <namespace>` - Get details
- `kubectl logs <pod-name> -n <namespace>` - View logs
- `kubectl exec -it <pod-name> -n <namespace> -- <command>` - Execute command

**💡 Tips:**
- Use `-n` for namespace (or `--namespace`)
- Use `-o wide` for more details
- Use `-w` to watch for changes
- Use `-f` to follow logs in real-time"""
        
        return {
            "response": response_text,
            "action_taken": "kubernetes_help",
            "suggestions": ["List pods", "List services", "List deployments", "Get pod logs"]
        }

    async def _handle_describe_pod(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle describe pod command"""
        namespace = entities.get("namespace", "default")
        resource_name = entities.get("resource_name")
        
        if resource_name:
            command = f"kubectl describe pod {resource_name} -n {namespace}"
            response_text = f"**Describe Specific Pod:**\n```bash\n{command}\n```\n\n**Alternative (OpenShift):**\n```bash\noc describe pod {resource_name} -n {namespace}\n```"
        else:
            command = f"kubectl describe pod <pod-name> -n {namespace}"
            response_text = f"**Describe a Pod in {namespace}:**\n```bash\n{command}\n```\n\n**Alternative (OpenShift):**\n```bash\noc describe pod <pod-name> -n {namespace}\n```\n\n**Examples:**\n```bash\n# Describe a specific pod\nkubectl describe pod my-pod -n default\n\n# Describe all pods in namespace\nkubectl get pods -n {namespace} | grep <pattern> | kubectl describe pod -n {namespace}\n\n# Show pod events\nkubectl get events -n {namespace} --field-selector involvedObject.name=<pod-name>\n```\n\n**💡 Tips:**\n- Use `kubectl describe` to get detailed information about any resource\n- The output includes events, conditions, and configuration details\n- Use `kubectl get events` to see recent events for troubleshooting"
        
        return {
            "response": response_text,
            "action_taken": "describe_pod",
            "suggestions": ["List pods", "Get pod logs", "Exec into pod", "Check pod events"]
        }

    async def _handle_get_logs(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle get logs command"""
        namespace = entities.get("namespace", "default")
        resource_name = entities.get("resource_name")
        
        if resource_name:
            command = f"kubectl logs {resource_name} -n {namespace}"
            response_text = f"**Get Logs for Specific Pod:**\n```bash\n{command}\n```\n\n**Alternative (OpenShift):**\n```bash\noc logs {resource_name} -n {namespace}\n```"
        else:
            command = f"kubectl logs <pod-name> -n {namespace}"
            response_text = f"**Get Pod Logs in {namespace}:**\n```bash\n{command}\n```\n\n**Alternative (OpenShift):**\n```bash\noc logs <pod-name> -n {namespace}\n```\n\n**Examples:**\n```bash\n# Get logs for a specific pod\nkubectl logs my-pod -n default\n\n# Follow logs in real-time\nkubectl logs -f my-pod -n default\n\n# Get logs from previous container restart\nkubectl logs --previous my-pod -n default\n\n# Get logs with timestamps\nkubectl logs --timestamps my-pod -n default\n\n# Get logs from specific container in multi-container pod\nkubectl logs my-pod -c container-name -n default\n```\n\n**💡 Tips:**\n- Use `-f` to follow logs in real-time\n- Use `--previous` to see logs from the previous container restart\n- Use `--timestamps` to add timestamps to log entries\n- Use `-c` to specify container in multi-container pods"
        
        return {
            "response": response_text,
            "action_taken": "get_logs",
            "suggestions": ["Follow logs", "Get previous logs", "Describe pod", "Exec into pod"]
        }

    async def _handle_exec_pod(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle exec into pod command"""
        namespace = entities.get("namespace", "default")
        resource_name = entities.get("resource_name")
        
        if resource_name:
            command = f"kubectl exec -it {resource_name} -n {namespace} -- /bin/bash"
            response_text = f"**Exec into Specific Pod:**\n```bash\n{command}\n```\n\n**Alternative (OpenShift):**\n```bash\noc exec -it {resource_name} -n {namespace} -- /bin/bash\n```"
        else:
            command = f"kubectl exec -it <pod-name> -n {namespace} -- /bin/bash"
            response_text = f"**Exec into Pod in {namespace}:**\n```bash\n{command}\n```\n\n**Alternative (OpenShift):**\n```bash\noc exec -it <pod-name> -n {namespace} -- /bin/bash\n```\n\n**Examples:**\n```bash\n# Exec into a pod with bash\nkubectl exec -it my-pod -n default -- /bin/bash\n\n# Exec into a pod with sh (if bash not available)\nkubectl exec -it my-pod -n default -- /bin/sh\n\n# Exec into specific container in multi-container pod\nkubectl exec -it my-pod -c container-name -n default -- /bin/bash\n\n# Run a single command without interactive shell\nkubectl exec my-pod -n default -- ls -la\n\n# Copy files to/from pod\nkubectl cp my-pod:/path/to/file ./local-file -n default\n```\n\n**💡 Tips:**\n- Use `-it` for interactive terminal\n- Use `--` to separate kubectl options from the command\n- Use `/bin/sh` if `/bin/bash` is not available\n- Use `-c` to specify container in multi-container pods\n- Use `kubectl cp` to copy files to/from pods"
        
        return {
            "response": response_text,
            "action_taken": "exec_pod",
            "suggestions": ["Get pod logs", "Describe pod", "Copy files from pod", "Run single command"]
        }

    async def _handle_port_forward(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle port forward command"""
        namespace = entities.get("namespace", "default")
        resource_name = entities.get("resource_name")
        
        if resource_name:
            command = f"kubectl port-forward {resource_name} 8080:80 -n {namespace}"
            response_text = f"**Port Forward to Specific Pod:**\n```bash\n{command}\n```\n\n**Alternative (OpenShift):**\n```bash\noc port-forward {resource_name} 8080:80 -n {namespace}\n```"
        else:
            command = f"kubectl port-forward <pod-name> 8080:80 -n {namespace}"
            response_text = f"**Port Forward in {namespace}:**\n```bash\n{command}\n```\n\n**Alternative (OpenShift):**\n```bash\noc port-forward <pod-name> 8080:80 -n {namespace}\n```\n\n**Examples:**\n```bash\n# Forward pod port to local port\nkubectl port-forward my-pod 8080:80 -n default\n\n# Forward service port\nkubectl port-forward service/my-service 8080:80 -n default\n\n# Forward deployment port\nkubectl port-forward deployment/my-deployment 8080:80 -n default\n\n# Forward multiple ports\nkubectl port-forward my-pod 8080:80 8443:443 -n default\n\n# Forward to specific address\nkubectl port-forward --address 0.0.0.0 my-pod 8080:80 -n default\n```\n\n**💡 Tips:**\n- Format: `kubectl port-forward <resource> <local-port>:<pod-port>`\n- Use `service/` prefix for services\n- Use `deployment/` prefix for deployments\n- Use `--address` to bind to specific interface\n- Press Ctrl+C to stop port forwarding"
        
        return {
            "response": response_text,
            "action_taken": "port_forward",
            "suggestions": ["List pods", "List services", "Describe pod", "Get pod logs"]
        }

    # GitHub handlers
    async def _handle_github_review_pr(self, message: str, entities: Dict, model_preference: Optional[str] = None) -> Dict[str, Any]:
        """Handle GitHub PR review request with comprehensive analysis"""
        try:
            from app.services.code_review_ai import ai_code_reviewer
            from app.services.github_service import github_service
            
            owner = entities.get("owner")
            repo = entities.get("repo")
            pr_number = entities.get("pr_number")
            # Use model preference from UI if provided, otherwise fallback to entities or default
            model = model_preference or entities.get("model", "ollama")
            
            if not owner or not repo or not pr_number:
                return {
                    "response": "🔍 **GitHub PR Review**\\n\\nI need more information to review the pull request:\\n• Repository (owner/repo)\\n• PR number\\n\\n**Example:** `Review PR #123 in microsoft/vscode`",
                    "action_taken": "github_review_pr_info_needed",
                    "suggestions": ["Specify repository and PR number", "Use format: owner/repo #123"]
                }
            
            # Check GitHub token first
            user_info = await github_service.get_user_info()
            if "error" in user_info:
                return {
                    "response": "🔑 **GitHub Authentication Required**\\n\\nTo review pull requests, you need to configure your GitHub token.\\n\\n**Setup Steps:**\\n1. Go to GitHub Settings → Developer settings → Personal access tokens\\n2. Generate a new token with `repo` permissions\\n3. Add the token to your configuration\\n\\n**Example:** `Review PR #123 in microsoft/vscode` (after token setup)",
                    "action_taken": "github_auth_required",
                    "suggestions": ["Configure GitHub token", "Check token permissions", "Verify token is valid"]
                }
            
            # Perform AI code review
            logger.info(f"Starting AI review for PR #{pr_number} in {owner}/{repo}")
            review_result = await ai_code_reviewer.comprehensive_review(owner, repo, pr_number, model)
            
            if "error" in review_result:
                error_msg = review_result.get("error", "Unknown error")
                if "404" in str(error_msg) or "Not Found" in str(error_msg):
                    return {
                        "response": f"🔍 **PR Not Found**\\n\\nThe pull request #{pr_number} was not found in {owner}/{repo}.\\n\\n**Possible reasons:**\\n• PR number doesn't exist\\n• Repository name is incorrect\\n• PR is private and you don't have access\\n\\n**Try:**\\n• Check the PR number: `Review PR #123 in {owner}/{repo}`\\n• Verify repository name\\n• Ensure you have access to the repository",
                        "action_taken": "github_pr_not_found",
                        "suggestions": ["Check PR number", "Verify repository name", "Check repository access"]
                    }
                else:
                    return {
                        "response": f"❌ **Review Failed**\\n\\nError: {error_msg}\\n\\nPlease check:\\n• Repository access permissions\\n• PR number is correct\\n• GitHub token has proper permissions",
                        "action_taken": "github_review_pr_error",
                        "suggestions": ["Check repository permissions", "Verify PR number", "Check GitHub configuration"]
                    }
            
            # Format the comprehensive response
            response = self._format_comprehensive_pr_review(review_result)
            
            return {
                "response": response,
                "action_taken": "github_review_pr_completed",
                "review_data": review_result,
                "suggestions": [
                    f"Add detailed comment to PR #{pr_number}",
                    f"{'Approve' if review_result.get('overall_score', 0) >= 80 else 'Request changes on'} PR #{pr_number}",
                    "Review specific file changes",
                    "Check security analysis details"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error reviewing GitHub PR: {e}")
            return {
                "response": f"❌ **Review Error**\\n\\nFailed to review PR: {str(e)}\\n\\n**Troubleshooting:**\\n• Check GitHub token configuration\\n• Verify repository access\\n• Ensure PR number is correct",
                "action_taken": "github_review_pr_error",
                "suggestions": ["Check GitHub token", "Verify repository access", "Try again"]
            }

    def _format_comprehensive_pr_review(self, review_result: Dict[str, Any]) -> str:
        """Format comprehensive PR review response with detailed analysis"""
        try:
            # Extract data from review result
            pr_info = review_result.get("technical_analysis", {}).get("pr_info", {})
            ai_review = review_result.get("ai_review", {})
            technical_analysis = review_result.get("technical_analysis", {})
            
            # PR Summary
            pr_title = pr_info.get("title", "Unknown")
            pr_author = pr_info.get("user", {}).get("login", "Unknown")
            pr_state = pr_info.get("state", "Unknown")
            changed_files = technical_analysis.get("files_analysis", {}).get("total_files", 0)
            additions = pr_info.get("additions", 0)
            deletions = pr_info.get("deletions", 0)
            overall_score = review_result.get("overall_score", 0)
            
            # AI Review Analysis - New Structure
            summary = ai_review.get("summary", "")
            strengths = ai_review.get("strengths", [])
            issues_risks = ai_review.get("issues_risks", [])
            suggestions = ai_review.get("suggestions", [])
            code_quality_score = ai_review.get("code_quality_score", 0)
            maintainability_score = ai_review.get("maintainability_score", 0)
            recommendation = ai_review.get("recommendation", "Request Changes")
            reasoning = ai_review.get("reasoning", "")
            
            # Security Analysis
            security_assessment = ai_review.get("security_assessment", {})
            security_score = security_assessment.get("score", 0)
            security_status = security_assessment.get("status", "✅ Secure")
            
            # Code Quality & Best Practices
            suggestions = ai_review.get("suggestions", [])
            critical_issues = ai_review.get("critical_issues", [])
            positive_aspects = ai_review.get("positive_aspects", [])
            
            # File Changes Analysis
            files_analysis = technical_analysis.get("files_analysis", {})
            file_details = files_analysis.get("file_details", [])
            
            # Build the comprehensive response with improved formatting
            response_lines = [
                "### 🔍 PR Review Summary",
                f"**PR:** #{review_result.get('pr_number', 'Unknown')} - {pr_title}",
                f"**Author:** @{pr_author}",
                f"**Status:** {pr_state.title()}",
                f"**Files Changed:** {changed_files}",
                f"**Additions:** {additions} | **Deletions:** {deletions}",
                "",
                "---",
                ""
            ]
            
            # Add summary if available
            if summary:
                response_lines.extend([
                    "### 📋 Summary",
                    summary,
                    ""
                ])
            
            # Add strengths if any
            if strengths:
                response_lines.append("### ✅ Strengths")
                for strength in strengths[:5]:  # Limit to 5 strengths
                    response_lines.append(f"- {strength}")
                response_lines.append("")
            
            # Add issues/risks if any
            if issues_risks:
                response_lines.append("### 🛑 Issues / Risks")
                for issue in issues_risks[:5]:  # Limit to 5 issues
                    response_lines.append(f"- {issue}")
                response_lines.append("")
            
            # Add suggestions if any
            if suggestions:
                response_lines.append("### 💬 Suggestions")
                for suggestion in suggestions[:5]:  # Limit to 5 suggestions
                    response_lines.append(f"- {suggestion}")
                response_lines.append("")
            
            # Security Assessment
            response_lines.extend([
                "### 🔒 Security",
                f"**Score:** {security_score}/100",
                f"**Status:** {security_status}",
                ""
            ])
            
            # Code Quality Scores
            response_lines.extend([
                "### 🤖 AI Analysis",
                f"**Code Quality Score:** {code_quality_score}/100",
                f"**Maintainability Score:** {maintainability_score}/100",
                f"**Overall Score:** {overall_score}/100",
                ""
            ])
            
            # Recommendation
            recommendation_emoji = {
                "Approve": "✅",
                "Request Changes": "🔁", 
                "Block": "❌"
            }.get(recommendation, "🤔")
            
            response_lines.extend([
                f"### {recommendation_emoji} Recommendation",
                f"**{recommendation}** - {reasoning}"
            ])
            
            # Join all lines with proper line breaks
            return "\n".join(response_lines)
            
        except Exception as e:
            logger.error(f"Error formatting PR review: {e}")
            return f"❌ **Formatting Error**\n\nFailed to format PR review: {str(e)}"
    
    async def _handle_github_merge_pr(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle GitHub PR merge request - requires confirmation via API"""
        try:
            owner = entities.get("owner")
            repo = entities.get("repo") 
            pr_number = entities.get("pr_number")
            
            if not owner or not repo or not pr_number:
                return {
                    "response": "🔀 **GitHub PR Merge**<br><br>I need repository and PR number to merge.<br><br>**Example:** `Merge PR #123 in microsoft/vscode`",
                    "action_taken": "github_merge_pr_info_needed",
                    "suggestions": ["Specify repository and PR number", "Use GitHub API for confirmation"]
                }
            
            return {
                "response": f"⚠️ **Merge Requires Confirmation**<br><br>**Repository:** {owner}/{repo}<br>**PR:** #{pr_number}<br><br>🚨 **Use GitHub API with confirmation=true to proceed**<br><br>This is a destructive action that cannot be undone.",
                "action_taken": "github_merge_pr_confirmation_needed", 
                "suggestions": [
                    "Use GitHub API endpoint",
                    "Review PR first",
                    "Cancel merge"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error in GitHub merge: {e}")
            return {
                "response": f"❌ **Merge Error**<br><br>{str(e)}",
                "action_taken": "github_merge_pr_error",
                "suggestions": ["Check GitHub configuration", "Try again"]
            }
    
    async def _handle_github_close_pr(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle GitHub PR close request - requires confirmation via API"""
        try:
            owner = entities.get("owner")
            repo = entities.get("repo")
            pr_number = entities.get("pr_number")
            
            if not owner or not repo or not pr_number:
                return {
                    "response": "❌ **GitHub PR Close**<br><br>I need repository and PR number to close.<br><br>**Example:** `Close PR #123 in microsoft/vscode`",
                    "action_taken": "github_close_pr_info_needed",
                    "suggestions": ["Specify repository and PR number", "Use GitHub API for confirmation"]
                }
            
            return {
                "response": f"⚠️ **Close Requires Confirmation**<br><br>**Repository:** {owner}/{repo}<br>**PR:** #{pr_number}<br><br>🚨 **Use GitHub API with confirmation=true to proceed**<br><br>This will close without merging.",
                "action_taken": "github_close_pr_confirmation_needed",
                "suggestions": [
                    "Use GitHub API endpoint", 
                    "Consider merging instead",
                    "Cancel close"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error in GitHub close: {e}")
            return {
                "response": f"❌ **Close Error**<br><br>{str(e)}",
                "action_taken": "github_close_pr_error",
                "suggestions": ["Check GitHub configuration", "Try again"]
            }
    
    async def _handle_github_list_repos(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle GitHub repository listing"""
        try:
            from app.services.github_service import github_service
            
            username = entities.get("username")
            repos = await github_service.list_repositories(username)
            
            if not repos:
                return {
                    "response": f"📂 **No repositories found**<br><br>{'User: ' + username if username else 'Your repositories'} - No accessible repositories.",
                    "action_taken": "github_list_repos_empty",
                    "suggestions": ["Check username", "Verify GitHub access"]
                }
            
            response_parts = [
                f"📂 **GitHub Repositories**",
                f"**{'User: ' + username if username else 'Your Repositories'}** ({len(repos)} found)",
                ""
            ]
            
            for i, repo in enumerate(repos[:5]):
                name = repo.get("name", "Unknown")
                description = repo.get("description", "No description")
                language = repo.get("language", "N/A")
                
                response_parts.append(f"**{i+1}. {name}** ({language})")
                response_parts.append(f"   {description[:80]}{'...' if len(description) > 80 else ''}")
            
            if len(repos) > 5:
                response_parts.append(f"... and {len(repos) - 5} more")
            
            return {
                "response": "<br>".join(response_parts),
                "action_taken": "github_list_repos_completed",
                "repositories": repos,
                "suggestions": ["View PRs for repo", "Get repo details"]
            }
            
        except Exception as e:
            logger.error(f"Error listing GitHub repos: {e}")
            return {
                "response": f"❌ **Repository List Error**<br><br>{str(e)}",
                "action_taken": "github_list_repos_error",
                "suggestions": ["Check GitHub token", "Try again"]
            }
    
    async def _handle_github_list_prs(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle GitHub PR listing"""
        try:
            from app.services.github_service import github_service
            
            owner = entities.get("owner")
            repo = entities.get("repo")
            
            # Check if this is a personal PR request (contains "my" or no repo specified)
            message_lower = message.lower()
            is_personal_request = "my" in message_lower or (not owner and not repo)
            
            # Check if this is an approval/review request
            is_approval_request = any(word in message_lower for word in ["approval", "approve", "review", "reviewer", "pending"])
            
            if is_personal_request:
                # Get user's personal PRs
                prs = await github_service.get_user_pull_requests("open")
                
                # If it's also an approval request, get PRs needing review
                if is_approval_request:
                    review_prs = await github_service.get_pull_requests_needing_review("open")
                    prs.extend(review_prs)
                    # Remove duplicates based on PR number and repo
                    seen = set()
                    unique_prs = []
                    for pr in prs:
                        key = (pr.get("number"), pr.get("repository", {}).get("full_name"))
                        if key not in seen:
                            seen.add(key)
                            unique_prs.append(pr)
                    prs = unique_prs
                
                if not prs:
                    return {
                        "response": "📋 **Your Pull Requests**<br><br>You don't have any open pull requests.",
                        "action_taken": "github_list_prs_personal_empty",
                        "suggestions": ["Create new PR", "Check closed PRs"]
                    }
                
                response_parts = [
                    "📋 **Your Open Pull Requests**",
                    f"**Total:** {len(prs)}",
                    ""
                ]
                
                if is_approval_request:
                    response_parts[0] = "📋 **Your PRs & Pending Reviews**"
                    response_parts[1] = f"**Total:** {len(prs)} (includes PRs needing your approval)"
                
                for i, pr in enumerate(prs[:5]):
                    number = pr.get("number", "N/A")
                    title = pr.get("title", "No title")
                    html_url = pr.get("html_url", "")
                    
                    # Extract repository name from URL
                    repo_name = "Unknown"
                    if html_url:
                        # URL format: https://github.com/owner/repo/pull/number
                        parts = html_url.split('/')
                        if len(parts) >= 5:
                            repo_name = f"{parts[3]}/{parts[4]}"
                    
                    # Create clean formatted line with URL
                    if html_url:
                        response_parts.append(f"**#{number}** {title[:60]}{'...' if len(title) > 60 else ''}")
                        response_parts.append(f"   📁 {repo_name}")
                        response_parts.append(f"   🔗 {html_url}")
                    else:
                        response_parts.append(f"**#{number}** {title[:60]}{'...' if len(title) > 60 else ''}")
                        response_parts.append(f"   📁 {repo_name}")
                
                if len(prs) > 5:
                    response_parts.append(f"... and {len(prs) - 5} more PRs")
                
                return {
                    "response": "<br>".join(response_parts),
                    "action_taken": "github_list_prs_personal_completed",
                    "pull_requests": prs,
                    "suggestions": [
                        f"Review PR #{prs[0].get('number', 1)}" if prs else "Create new PR",
                        "Show PR details"
                    ]
                }
            
            if not owner or not repo:
                return {
                    "response": "📋 **GitHub Pull Requests**<br><br>I need repository info to list PRs.<br><br>**Example:** `List PRs in microsoft/vscode`",
                    "action_taken": "github_list_prs_info_needed",
                    "suggestions": ["Specify repository", "Use format: owner/repo"]
                }
            
            prs = await github_service.get_pull_requests(owner, repo, "open")
            
            if not prs:
                return {
                    "response": f"📋 **No Open Pull Requests**<br><br>**Repository:** {owner}/{repo}",
                    "action_taken": "github_list_prs_empty",
                    "suggestions": ["Check closed PRs", "Create new PR"]
                }
            
            response_parts = [
                f"📋 **Pull Requests: {owner}/{repo}**",
                f"**Open PRs:** {len(prs)}",
                ""
            ]
            
            for i, pr in enumerate(prs[:5]):
                number = pr.get("number", "N/A")
                title = pr.get("title", "No title")
                author = pr.get("user", {}).get("login", "Unknown")
                
                response_parts.append(f"**#{number}** {title[:60]}{'...' if len(title) > 60 else ''}")
                response_parts.append(f"   👤 {author}")
            
            if len(prs) > 5:
                response_parts.append(f"... and {len(prs) - 5} more PRs")
            
            return {
                "response": "<br>".join(response_parts),
                "action_taken": "github_list_prs_completed",
                "pull_requests": prs,
                "suggestions": [
                    f"Review PR #{prs[0].get('number', 1)}" if prs else "Create new PR",
                    "Show PR details"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error listing GitHub PRs: {e}")
            return {
                "response": f"❌ **PR List Error**<br><br>{str(e)}",
                "action_taken": "github_list_prs_error",
                "suggestions": ["Check GitHub token", "Try again"]
            }
    
    async def _handle_github_add_comment(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle GitHub PR comment addition"""
        try:
            from app.services.github_service import github_service
            
            # Check if GitHub token is available
            token = github_service._get_token()
            if not token:
                return {
                    "response": "🔑 **GitHub Authentication Required**<br><br>GitHub token is not configured. Please set up GitHub authentication to use PR features.",
                    "action_taken": "github_auth_required",
                    "suggestions": ["Configure GitHub token", "Check credentials", "Set up authentication"]
                }
            
            # Try to extract from entities first
            owner = entities.get("owner")
            repo = entities.get("repo")
            pr_number = entities.get("pr_number")
            
            # If not in entities, try to extract from URL in message
            if not owner or not repo or not pr_number:
                import re
                github_url_pattern = r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)'
                match = re.search(github_url_pattern, message)
                
                if not match:
                    return {
                        "response": "💬 **GitHub PR Comment**<br><br>I need a GitHub PR URL to add a comment.<br><br>**Example:** `add comment to pr https://github.com/owner/repo/pull/123: Great work!`",
                        "action_taken": "github_add_comment_no_url",
                        "suggestions": ["Provide PR URL", "Use format: add comment to pr https://github.com/owner/repo/pull/123: Your message"]
                    }
                
                owner, repo, pr_number = match.groups()
                pr_number = int(pr_number)
            
            # Extract comment from message (simplified)
            import re
            comment_text = re.sub(r'.*comment.*?:', '', message, flags=re.IGNORECASE).strip()
            
            if not comment_text or len(comment_text) < 5:
                return {
                    "response": f"💬 **Comment Text Needed**<br><br>Please provide comment text for PR #{pr_number}.",
                    "action_taken": "github_add_comment_text_needed",
                    "suggestions": ["Include comment text", "Try again"]
                }
            
            result = await github_service.add_issue_comment(owner, repo, pr_number, comment_text)
            
            if "error" in result:
                return {
                    "response": f"❌ **Comment Failed**<br><br>{result['error']}",
                    "action_taken": "github_add_comment_error",
                    "suggestions": ["Check permissions", "Try again"]
                }
            
            return {
                "response": f"✅ **Comment Added**<br><br>**Repository:** {owner}/{repo}<br>**PR:** #{pr_number}<br>**Comment:** {comment_text[:100]}{'...' if len(comment_text) > 100 else ''}",
                "action_taken": "github_add_comment_completed",
                "suggestions": [f"Review PR #{pr_number}", "Add another comment"]
            }
            
        except Exception as e:
            logger.error(f"Error adding GitHub comment: {e}")
            return {
                "response": f"❌ **Comment Error**<br><br>{str(e)}",
                "action_taken": "github_add_comment_error",
                "suggestions": ["Check GitHub token", "Try again"]
            }
    
    async def _handle_github_general(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle general GitHub requests"""
        return {
            "response": "🐙 **GitHub Integration**<br><br>**Available Commands:**<br>• `Review PR #123 in owner/repo` - AI code review<br>• `List PRs in owner/repo` - Show pull requests<br>• `List repos` - Show repositories<br>• `Merge PR #123` - Merge (requires API confirmation)<br>• `Add comment to PR #123: Your message`<br><br>**Examples:**<br>• `Review PR #456 in microsoft/vscode`<br>• `List PRs in openshift/hypershift`",
            "action_taken": "github_general_help",
            "suggestions": [
                "Review a pull request",
                "List repositories", 
                "Show open PRs"
            ]
            }

    # Entity extraction methods
    def _extract_email_entities(self, message: str) -> Dict[str, Any]:
        """Extract email-related entities from message"""
        entities = {}
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, message)
        if emails:
            entities["to_email"] = emails[0]
        
        # Extract subject (enhanced patterns)
        subject_patterns = [
            r'subject[:\s]+["\']?([^"\']+?)["\']?\s+and\s+message',
            r'subject[:\s]+["\']?([^"\']+)["\']?',
            r'titled[:\s]+["\']?([^"\']+)["\']?',
            r'about[:\s]+["\']?([^"\']+)["\']?',
            r'with\s+subject\s+([^"\']+?)\s+and\s+message',
            r'with\s+subject\s+([^"\']+)'
        ]
        for pattern in subject_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                subject = match.group(1).strip()
                # Clean up common ending words
                subject = re.sub(r'\s+(and\s+message.*|with\s+message.*)$', '', subject, flags=re.IGNORECASE)
                entities["subject"] = subject
                break
        
        # Extract message body (enhanced patterns)
        body_patterns = [
            r'message[:\s]+["\']?([^"\']+)["\']?$',
            r'and\s+message[:\s]+["\']?([^"\']+)["\']?$',
            r'with\s+message[:\s]+["\']?([^"\']+)["\']?$',
            r'body[:\s]+["\']?([^"\']+)["\']?$',
            r'text[:\s]+["\']?([^"\']+)["\']?$'
        ]
        for pattern in body_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                body = match.group(1).strip()
                # Remove trailing quotation marks and exclamation points that might be malformed
                body = re.sub(r'["\']?!*$', '', body)
                entities["body"] = body
                break
        
        return entities

    def _extract_email_number(self, message: str) -> int:
        """Extract email number from message"""
        import re
        
        message_lower = message.lower()
        
        # First check for ordinal words (first, second, third, etc.)
        ordinal_mapping = {
            'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5,
            'sixth': 6, 'seventh': 7, 'eighth': 8, 'ninth': 9, 'tenth': 10
        }
        
        for ordinal, number in ordinal_mapping.items():
            if ordinal in message_lower:
                return number
        
        # Look for patterns like "email 1", "email #1", "email1", etc.
        patterns = [
            r'email\s*#?(\d+)',
            r'message\s*#?(\d+)', 
            r'mail\s*#?(\d+)',
            r'email(\d+)',
            r'#(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                return int(match.group(1))
        
        # Default to email 1 if no number found
        return 1

    def _extract_calendar_entities(self, message: str) -> Dict[str, Any]:
        """Extract calendar-related entities from message"""
        entities = {}
        
        # Extract event title (simple heuristic)
        title_patterns = [
            r'titled[:\s]+["\']?([^"\']+)["\']?',
            r'called[:\s]+["\']?([^"\']+)["\']?',
            r'event[:\s]+["\']?([^"\']+)["\']?'
        ]
        for pattern in title_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                entities["title"] = match.group(1).strip()
                break
        
        # Extract date/time (basic patterns)
        date_patterns = [
            r'(tomorrow|today|next week|next month)',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{1,2}:\d{2}(?:\s*[AP]M)?)'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                entities["datetime"] = match.group(1)
                break
        
        return entities

    def _format_event_time(self, time_str: str) -> str:
        """Format event time for better readability"""
        try:
            if not time_str or time_str == 'No time specified':
                return 'No time specified'
            
            # Parse ISO format datetime
            if 'T' in time_str:
                from datetime import datetime
                # Handle different timezone formats
                if time_str.endswith('Z'):
                    dt = datetime.fromisoformat(time_str[:-1])
                elif '+' in time_str[-6:] or time_str[-6:].count(':') == 2:
                    dt = datetime.fromisoformat(time_str)
                else:
                    dt = datetime.fromisoformat(time_str)
                
                # Format as readable date and time
                formatted_date = dt.strftime("%B %d, %Y")  # e.g., "July 21, 2025"
                formatted_time = dt.strftime("%I:%M %p")   # e.g., "07:30 PM"
                return f"{formatted_date} at {formatted_time}"
            else:
                # If it's just a date, return as is
                return time_str
                
        except Exception as e:
            logger.error(f"Error formatting time {time_str}: {e}")
            return time_str

    def _extract_contact_entities(self, message: str) -> Dict[str, Any]:
        """Extract contact-related entities from message"""
        entities = {}
        
        # Extract name (simple heuristic)
        name_patterns = [
            r'named[:\s]+["\']?([^"\']+)["\']?',
            r'called[:\s]+["\']?([^"\']+)["\']?',
            r'for[:\s]+["\']?([^"\']+)["\']?'
        ]
        for pattern in name_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                entities["name"] = match.group(1).strip()
                break
        
        return entities

    def _extract_slack_entities(self, message: str) -> Dict[str, Any]:
        """Extract Slack-related entities from message"""
        entities = {}
        
        # Extract channel
        channel_patterns = [
            r'#([a-zA-Z0-9_-]+)',
            r'channel[:\s]+["\']?([^"\']+)["\']?',
            r'to[:\s]+["\']?([^"\']+)["\']?'
        ]
        for pattern in channel_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                entities["channel"] = match.group(1).strip()
                break
        
        return entities
    
    def _extract_analysis_entities(self, message: str) -> Dict[str, Any]:
        """Extract must-gather analysis entities from message"""
        entities = {}
        
        # Extract must-gather path
        path_patterns = [
            r'path[:\s]+["\']?([^"\']+)["\']?',
            r'location[:\s]+["\']?([^"\']+)["\']?',
            r'directory[:\s]+["\']?([^"\']+)["\']?',
            r'folder[:\s]+["\']?([^"\']+)["\']?',
            r'([/\w\.-]+must-gather[/\w\.-]*)',
        ]
        for pattern in path_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                entities["must_gather_path"] = match.group(1).strip()
                break
        
        # Extract analysis type
        if any(word in message.lower() for word in ["full", "complete", "comprehensive"]):
            entities["analysis_type"] = "full"
        elif any(word in message.lower() for word in ["quick", "fast", "health"]):
            entities["analysis_type"] = "health_check"
        elif any(word in message.lower() for word in ["etcd"]):
            entities["analysis_type"] = "etcd_analysis"
        elif any(word in message.lower() for word in ["node", "nodes"]):
            entities["analysis_type"] = "node_analysis"
        elif any(word in message.lower() for word in ["pod", "pods"]):
            entities["analysis_type"] = "pod_issues"
        elif any(word in message.lower() for word in ["operator", "operators"]):
            entities["analysis_type"] = "operator_status"
        elif any(word in message.lower() for word in ["kms", "encryption"]):
            entities["analysis_type"] = "kms_encryption"
        
        return entities
    
    def _extract_openshift_entities(self, message: str) -> Dict[str, Any]:
        """Extract OpenShift troubleshooting entities from message"""
        entities = {}
        
        # Extract component
        if any(word in message.lower() for word in ["pod", "pods"]):
            entities["component"] = "pods"
        elif any(word in message.lower() for word in ["node", "nodes"]):
            entities["component"] = "nodes"
        elif any(word in message.lower() for word in ["operator", "operators"]):
            entities["component"] = "operators"
        elif any(word in message.lower() for word in ["etcd"]):
            entities["component"] = "etcd"
        elif any(word in message.lower() for word in ["network", "networking"]):
            entities["component"] = "network"
        elif any(word in message.lower() for word in ["storage"]):
            entities["component"] = "storage"
        
        # Extract namespace if mentioned
        ns_patterns = [
            r'namespace[:\s]+["\']?([^"\']+)["\']?',
            r'ns[:\s]+["\']?([^"\']+)["\']?',
            r'-n\s+([^\s]+)',
        ]
        for pattern in ns_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                entities["namespace"] = match.group(1).strip()
                break
        
        return entities

    def _extract_kubernetes_entities(self, message: str) -> Dict[str, Any]:
        """Extract Kubernetes/OpenShift entities from message"""
        try:
            entities = {}
            message_lower = message.lower()
            
            # Extract namespace
            ns_patterns = [
                r'-n\s+(\w+)',  # -n namespace
                r'--namespace\s+(\w+)',  # --namespace namespace
                r'in\s+(\w+)\s+namespace',  # in namespace
                r'namespace\s+(\w+)',  # namespace name
                r'ns\s+(\w+)'  # ns name
            ]
            
            for pattern in ns_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    entities["namespace"] = match.group(1)
                    break
            
            # Extract resource type
            resource_patterns = {
                "pod": ["pod", "pods"],
                "service": ["service", "services", "svc"],
                "deployment": ["deployment", "deployments", "deploy"],
                "namespace": ["namespace", "namespaces", "ns"],
                "node": ["node", "nodes"],
                "configmap": ["configmap", "configmaps", "cm"],
                "secret": ["secret", "secrets"],
                "ingress": ["ingress", "ingresses"],
                "route": ["route", "routes"]
            }
            
            for resource_type, keywords in resource_patterns.items():
                if any(keyword in message_lower for keyword in keywords):
                    entities["resource_type"] = resource_type
                    break
            
            # Extract command type
            command_patterns = {
                "get": ["get", "list", "show"],
                "describe": ["describe", "details", "info"],
                "delete": ["delete", "remove"],
                "create": ["create", "new"],
                "apply": ["apply", "update"],
                "exec": ["exec", "connect", "shell"],
                "logs": ["logs", "log"],
                "port-forward": ["port forward", "port-forward", "forward"]
            }
            
            for command_type, keywords in command_patterns.items():
                if any(keyword in message_lower for keyword in keywords):
                    entities["command_type"] = command_type
                    break
            
            # Extract specific resource name if mentioned
            name_patterns = [
                r'(?:get|describe|logs|exec|port-forward)\s+(\w+(?:-\w+)*)',  # get my-pod, describe my-pod
                r'(\w+(?:-\w+)*)\s+(?:pod|service|deployment|namespace|node)',  # my-pod pod
                r'(?:pod|service|deployment|namespace|node)\s+(\w+(?:-\w+)*)'   # pod my-pod
            ]
            
            for pattern in name_patterns:
                name_match = re.search(pattern, message_lower)
                if name_match:
                    resource_name = name_match.group(1)
                    # Skip common words that aren't resource names
                    if resource_name not in ['get', 'list', 'show', 'describe', 'logs', 'exec', 'port-forward', 'forward', 'pod', 'pods', 'service', 'services', 'deployment', 'deployments', 'namespace', 'namespaces', 'node', 'nodes', 'projects']:
                        entities["resource_name"] = resource_name
                        break
            
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting Kubernetes entities: {e}")
            return {}

    def _extract_event_title_from_message(self, message: str) -> str:
        """Extract event title from message using various patterns"""
        # Look for explicit title patterns first (highest priority)
        title_patterns = [
            r'title[:\s]+["\']([^"\']+)["\']',  # title "test1"
            r'title[:\s]+([^\s]+)',  # title test1
            r'titled[:\s]+["\']?([^"\']+)["\']?',
            r'called[:\s]+["\']?([^"\']+)["\']?'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                # Clean up common prefixes/suffixes
                title = re.sub(r'^(a |an |the )', '', title, flags=re.IGNORECASE)
                return title
        
        # Look for subject patterns (medium priority)
        subject_patterns = [
            r'subject[:\s]+["\']([^"\']+)["\']',  # subject "test"
            r'subject[:\s]+([^\s]+)',  # subject test
            r'with subject[:\s]+["\']([^"\']+)["\']',
            r'with subject[:\s]+([^\s]+)'
        ]
        
        for pattern in subject_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                return title
        
        # Look for general event patterns (lower priority)
        general_patterns = [
            r'event[:\s]+["\']?([^"\']+)["\']?',
            r'meeting[:\s]+["\']?([^"\']+)["\']?',
            r'create[:\s]+["\']?([^"\']+)["\']?',
            r'schedule[:\s]+["\']?([^"\']+)["\']?'
        ]
        
        for pattern in general_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                # Clean up common prefixes/suffixes
                title = re.sub(r'^(a |an |the )', '', title, flags=re.IGNORECASE)
                # Remove email addresses and timing info from title
                title = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', title, flags=re.IGNORECASE)
                title = re.sub(r'\s+(at|timing|time)\s+.*$', '', title, flags=re.IGNORECASE)
                title = title.strip()
                if title and not title.startswith('to '):
                    return title
        
        # Fallback: use default
        return "Meeting"

    def _extract_attendees_from_message(self, message: str) -> List[str]:
        """Extract attendee email addresses from message"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, message)
        return list(set(emails))  # Remove duplicates

    async def _create_calendar_event_with_attendees(self, title: str, attendees: List[str], message: str) -> Dict[str, Any]:
        """Create a calendar event with attendees using the Calendar API"""
        try:
            import httpx
            from datetime import datetime, timedelta
            
            # Extract time from message or use default (1 hour from now)
            start_time = self._extract_time_from_message(message)
            
            # Convert local time to UTC if we extracted a time
            if start_time and "timing" in message.lower():
                # The extracted time is in local time (IST), convert to UTC
                # IST is UTC+5:30, so subtract 5:30 to get UTC
                ist_offset = timedelta(hours=5, minutes=30)
                start_time = start_time - ist_offset
                logger.info(f"Converted local time to UTC: {start_time}")
            
            if not start_time:
                start_time = datetime.utcnow() + timedelta(hours=1)
            
            # Debug logging
            logger.info(f"Final time for meeting '{title}': {start_time} (from message: '{message}')")
                
            end_time = start_time + timedelta(hours=1)  # Default 1 hour duration
            
            # Prepare event data
            event_data = {
                "summary": title,
                "description": f"Meeting created via AI Assistant",
                "start_time": start_time.isoformat() + 'Z',
                "end_time": end_time.isoformat() + 'Z',
                "attendees": attendees,
                "location": "Google Meet"
            }
            
            # Call the calendar API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/api/calendar/events",
                    json=event_data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "event_id": result.get("event_id"),
                        "html_link": result.get("html_link"),
                        "email_status": result.get("email_status", ""),
                        "external_attendees": result.get("external_attendees", []),
                        "self_invited": result.get("self_invited", False),
                        "meet_link": result.get("meet_link", "")
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _extract_time_from_message(self, message: str) -> Optional[datetime]:
        """Extract time information from message"""
        from datetime import datetime, timedelta
        import re
        import pytz
        
        # Look for time patterns (enhanced with more patterns)
        time_patterns = [
            # With AM/PM (including variations like a.m., p.m.)
            r'(?:at|timing)\s+(\d{1,2}):(\d{2})\s*([ap]\.?m\.?)',  # "at 8:13 p.m." or "at 12:02 PM"
            r'(?:at|timing)\s+(\d{1,2})\s*([ap]\.?m\.?)',  # "at 8 p.m." or "at 12 PM"
            r'(\d{1,2}):(\d{2})\s*([ap]\.?m\.?)',  # "8:13 p.m." or "12:02 PM"
            r'(\d{1,2})\s*([ap]\.?m\.?)',  # "8 p.m." or "12 PM"
            
            # 24-hour format
            r'(?:at|timing)\s+(\d{1,2}):(\d{2})',  # "at 12:02" or "timing 12:02"
            r'(?:at|timing)\s+(\d{1,2})(?::00)?',  # "at 12" or "timing 12"
            r'\b(\d{1,2}):(\d{2})\b',  # "12:02"
            r'\b(\d{1,2})(?::00)?\s*(?:hours?|h)\b'  # "12 hours" or "12h"
        ]
        
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for pattern in time_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                try:
                    groups = match.groups()
                    hour = int(groups[0])
                    minute = 0
                    ampm = None
                    
                    # Check if we have minute and AM/PM
                    if len(groups) >= 2 and groups[1] and groups[1].isdigit():
                        minute = int(groups[1])
                        if len(groups) >= 3:
                            ampm = groups[2]
                    elif len(groups) >= 2 and groups[1] and groups[1].upper() in ['AM', 'PM']:
                        ampm = groups[1]
                    
                    # Convert to 24-hour format if AM/PM is specified
                    if ampm:
                        ampm = ampm.lower().replace('.', '')  # Convert "p.m." to "pm"
                        if ampm == 'pm' and hour != 12:
                            hour += 12
                        elif ampm == 'am' and hour == 12:
                            hour = 0
                    else:
                        # For 24-hour format, assume current context
                        # If hour is <= 12 and current time suggests PM, treat as PM
                        current_hour = datetime.now().hour
                        if hour <= 12 and current_hour >= 12:
                            # Only convert to PM if it makes sense contextually
                            if hour < 12:  # Don't convert 12:xx to 24:xx
                                pass  # Keep as-is for now, could be morning meeting
                    
                    # Validate hour and minute
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        result_time = today.replace(hour=hour, minute=minute)
                        print(f"DEBUG: Extracted time {hour}:{minute:02d} -> {result_time}")
                        return result_time
                        
                except (ValueError, IndexError):
                    continue
        
        # Look for relative time patterns
        relative_patterns = [
            r'in (\d+) (?:hours?|hrs?)',  # "in 2 hours"
            r'in (\d+) (?:minutes?|mins?)',  # "in 30 minutes"
        ]
        
        for pattern in relative_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                try:
                    value = int(match.group(1))
                    if 'hour' in pattern:
                        return datetime.utcnow() + timedelta(hours=value)
                    elif 'minute' in pattern:
                        return datetime.utcnow() + timedelta(minutes=value)
                except ValueError:
                    continue
        
        # Default to current time plus 1 hour if no time pattern found
        default_time = datetime.utcnow() + timedelta(hours=1)
        logger.debug(f"No time pattern found in message: '{message}', using default: {default_time}")
        return default_time

    # Utility methods
    async def execute_task(self, task: str, parameters: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a specific task"""
        # This method would interface with the appropriate API based on the task
        return {"message": f"Task '{task}' execution not yet implemented", "parameters": parameters}

    def get_capabilities(self) -> Dict[str, List[str]]:
        """Get list of agent capabilities"""
        return self.capabilities

    def get_conversation_history(self, limit: int = 50) -> List[Dict]:
        """Get conversation history"""
        return self.conversation_history[-limit:] if limit else self.conversation_history

    def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_history = []

    def set_context(self, context: Dict[str, Any]):
        """Set conversation context"""
        self.context.update(context)

    def get_context(self) -> Dict[str, Any]:
        """Get current context"""
        return self.context

    def has_active_conversation(self) -> bool:
        """Check if there's an active conversation"""
        return len(self.conversation_history) > 0

    def get_last_interaction_time(self) -> Optional[str]:
        """Get last interaction timestamp"""
        return self.last_interaction.isoformat() if self.last_interaction else None

    def learn_from_example(self, input_message: str, expected_response: str, category: str = None) -> bool:
        """Learn from user examples (placeholder for future ML implementation)"""
        # This would store examples for training custom models
        logger.info(f"Learning example added: {input_message} -> {expected_response} (category: {category})")
        return True

    async def get_suggestions(self, current_message: Optional[str] = None) -> List[str]:
        """Get suggestions for next actions"""
        base_suggestions = [
            "Check my recent emails",
            "Show me today's calendar events",
            "Search my contacts",
            "Send a Slack message",
            "What can you help me with?"
        ]
        
        if current_message:
            # Context-aware suggestions based on current message
            message_lower = current_message.lower()
            if "email" in message_lower:
                return ["Check unread emails", "Send an email", "Search emails"]
            elif "calendar" in message_lower:
                return ["View today's events", "Create new event", "Check this week's schedule"]
            elif "contact" in message_lower:
                return ["Search contacts", "Add new contact", "View all contacts"]
            elif "slack" in message_lower:
                return ["Check recent messages", "Send a message", "View channels"]
        
        return base_suggestions

    async def check_service_connections(self) -> Dict[str, bool]:
        """Check connections to various services"""
        connections = {}
        
        # Check Google services
        try:
            credentials = get_google_credentials()
            connections["google"] = credentials is not None
        except:
            connections["google"] = False
        
        # Check Slack (would implement similar check)
        connections["slack"] = False  # Placeholder
        
        return connections 
    
    def _extract_github_entities(self, message: str) -> Dict[str, Any]:
        """Extract GitHub-related entities from message"""
        entities = {}
        
        # HIGH PRIORITY: Extract from GitHub URLs first
        github_url_pattern = r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)'
        url_match = re.search(github_url_pattern, message)
        if url_match:
            entities['owner'] = url_match.group(1)
            entities['repo'] = url_match.group(2)
            entities['repository'] = f"{url_match.group(1)}/{url_match.group(2)}"
            entities['pr_number'] = int(url_match.group(3))
            return entities  # Return immediately if we found a GitHub URL
        
        # Fallback: Extract repository information (owner/repo format)
        repo_pattern = r'([a-zA-Z0-9_-]+)/([a-zA-Z0-9_-]+)'
        repo_match = re.search(repo_pattern, message)
        if repo_match:
            entities['owner'] = repo_match.group(1)
            entities['repo'] = repo_match.group(2)
            entities['repository'] = f"{repo_match.group(1)}/{repo_match.group(2)}"
        
        # Extract PR number
        pr_pattern = r'#(\d+)'
        pr_match = re.search(pr_pattern, message)
        if pr_match:
            entities['pr_number'] = int(pr_match.group(1))
        
        # Extract model preference if specified
        model_patterns = {
            'granite': ['granite', 'granite3.3'],
            'gemini': ['gemini', 'google'],
            'openai': ['openai', 'gpt', 'chatgpt'],
            'ollama': ['ollama', 'llama']
        }
        
        message_lower = message.lower()
        for model, keywords in model_patterns.items():
            if any(keyword in message_lower for keyword in keywords):
                entities['model'] = model
                break
        
        return entities

    def _extract_jira_entities(self, message: str, status_filter: Optional[str] = None) -> Dict[str, Any]:
        """Extract Jira-related entities from message with support for combined queries"""
        entities = {}
        message_lower = message.lower()
        
        # Extract issue type with combined query support
        issue_type_detected = False
        
        # Check for combined patterns first (higher priority)
        if any(phrase in message_lower for phrase in ["qa contact", "qa issues", "qa tickets", "i'm qa contact", "i am qa contact", "qa contact issues", "where i am qa contact"]):
            entities['issue_type'] = 'qa_contact'
            issue_type_detected = True
        elif any(phrase in message_lower for phrase in ["assigned", "assigned to me", "my assigned"]):
            entities['issue_type'] = 'assigned'
            issue_type_detected = True
        elif any(phrase in message_lower for phrase in ["reported", "reported by me", "my reported"]):
            entities['issue_type'] = 'reported'
            issue_type_detected = True
        elif any(phrase in message_lower for phrase in ["all mine", "all my issues", "all my tickets"]):
            entities['issue_type'] = 'all_mine'
            issue_type_detected = True
        
        # If no specific issue type detected, check for combined patterns
        if not issue_type_detected:
            # Check for combined patterns like "where I am QA contact and assigned to me"
            if "qa contact" in message_lower and "assigned" in message_lower:
                entities['issue_type'] = 'qa_contact'  # QA contact takes precedence
                entities['combined_filters'] = ['qa_contact', 'assigned']
            elif "qa contact" in message_lower and "reported" in message_lower:
                entities['issue_type'] = 'qa_contact'  # QA contact takes precedence
                entities['combined_filters'] = ['qa_contact', 'reported']
            elif "assigned" in message_lower and "reported" in message_lower:
                entities['issue_type'] = 'all_mine'  # Both assigned and reported = all mine
                entities['combined_filters'] = ['assigned', 'reported']
            else:
                entities['issue_type'] = 'assigned'  # Default to assigned issues
        
        # Extract status filter if present
        if status_filter:
            entities['status_filter'] = status_filter
        
        # Extract additional filters for combined queries
        additional_filters = {}
        
        # Check for priority filters
        if any(phrase in message_lower for phrase in ["high priority", "critical", "urgent"]):
            additional_filters['priority'] = 'High'
        elif any(phrase in message_lower for phrase in ["low priority", "minor"]):
            additional_filters['priority'] = 'Low'
        
        # Check for project filters
        project_patterns = {
            'ocpqe': 'OCPQE',
            'ocpbugs': 'OCPBUGS',
            'api': 'API',
            'cntrlplane': 'CNTRLPLANE'
        }
        for pattern, project in project_patterns.items():
            if pattern in message_lower:
                additional_filters['project'] = project
                break
        
        # Check for issue type filters
        if any(phrase in message_lower for phrase in ["bug", "bugs"]):
            additional_filters['issue_type'] = 'Bug'
        elif any(phrase in message_lower for phrase in ["task", "tasks"]):
            additional_filters['issue_type'] = 'Task'
        elif any(phrase in message_lower for phrase in ["story", "stories"]):
            additional_filters['issue_type'] = 'Story'
        
        if additional_filters:
            entities['additional_filters'] = additional_filters
        
        return entities

    async def _handle_fetch_jira_issues(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle fetching Jira issues"""
        try:
            issue_type = entities.get("issue_type", "assigned")
            status_filter = entities.get("status_filter")
            
            # Test Jira connection first
            if not jira_service.test_connection():
                return {
                    "response": "❌ **Jira Connection Error**\n\nUnable to connect to Jira. Please check your credentials and try again.",
                    "action_taken": "jira_connection_failed",
                    "suggestions": ["Check Jira credentials", "Test connection", "Update credentials"]
                }
            
            # Get additional filters from entities
            additional_filters = entities.get("additional_filters", {})
            
            # Handle multiple status filters
            if isinstance(status_filter, list) and len(status_filter) > 1:
                # For multiple statuses, we need to make multiple calls and combine results
                all_issues = []
                for status in status_filter:
                    issues = jira_service.get_my_issues(issue_type, max_results=50, status_filter=status, additional_filters=additional_filters)
                    all_issues.extend(issues)
                
                # Remove duplicates based on issue key
                seen_keys = set()
                unique_issues = []
                for issue in all_issues:
                    key = issue.get('key')
                    if key and key not in seen_keys:
                        seen_keys.add(key)
                        unique_issues.append(issue)
                
                issues = unique_issues
            else:
                # Single status filter or no filter
                issues = jira_service.get_my_issues(issue_type, max_results=50, status_filter=status_filter, additional_filters=additional_filters)
            
            if not issues:
                if isinstance(status_filter, list):
                    status_text = f" with statuses: {', '.join(status_filter)}"
                elif status_filter:
                    status_text = f" with status '{status_filter}'"
                else:
                    status_text = ""
                
                # Provide more helpful response based on the query
                if "ON_QA" in str(status_filter):
                    if issue_type == "qa_contact":
                        response_text = (
                            f"I've searched for your ON_QA Jira issues where you're the QA contact. Currently, you don't have any issues with ON_QA status where you're listed as the QA contact. "
                            f"This could mean:\n\n"
                            f"• All your QA issues have moved to other statuses\n"
                            f"• You don't have any issues currently in QA testing phase\n"
                            f"• The QA contact might have been changed to someone else\n\n"
                            f"Would you like me to check other statuses like 'In Progress' or 'To Do' for your QA issues?"
                        )
                    else:
                        response_text = (
                            f"I've searched for your ON_QA Jira issues. Currently, you don't have any issues assigned to you with ON_QA status. "
                            f"This could mean:\n\n"
                            f"• All your issues have moved to other statuses\n"
                            f"• You don't have any issues currently in QA testing\n"
                            f"• The issues might be assigned to someone else\n\n"
                            f"Would you like me to check other statuses like 'In Progress' or 'To Do'?"
                        )
                elif issue_type == "qa_contact":
                    response_text = (
                        f"I've searched for your Jira issues where you're the QA contact{status_text}. Currently, you don't have any issues where you're listed as the QA contact. "
                        f"This could mean:\n\n"
                        f"• All your QA issues have been resolved\n"
                        f"• QA contact has been reassigned to others\n"
                        f"• You don't have any active QA assignments\n\n"
                        f"Would you like me to check for issues you're assigned to or help you create a new issue?"
                    )
                elif "assigned" in issue_type.lower():
                    response_text = (
                        f"I've searched for your assigned Jira issues. Currently, you don't have any issues assigned to you. "
                        f"This could mean:\n\n"
                        f"• All your issues have been completed\n"
                        f"• Issues have been reassigned\n"
                        f"• You don't have any active assignments\n\n"
                        f"Would you like me to check for issues you've created or help you create a new issue?"
                    )
                else:
                    response_text = (
                        f"I've searched for your Jira issues{status_text}. No issues found for this criteria. "
                        f"This could mean:\n\n"
                        f"• All your issues have been resolved\n"
                        f"• Issues have been moved to other statuses\n"
                        f"• You don't have any active assignments\n\n"
                        f"Would you like me to check other statuses or help you create a new issue?"
                    )
                    
                return {
                    "response": response_text,
                    "action_taken": "jira_issues_empty",
                    "suggestions": ["Try different issue type", "Check different status", "Create new issue"]
                }
            
            # Format issues for display
            formatted_issues = []
            for i, issue in enumerate(issues[:10], 1):  # Show first 10 issues
                formatted_issue = jira_service.format_issue(issue)
                summary = formatted_issue.get("summary", "No summary")
                status = formatted_issue.get("status", "Unknown")
                priority = formatted_issue.get("priority", "Unknown")
                assignee = formatted_issue.get("assignee", "Unassigned")
                key = formatted_issue.get("key", "")
                url = formatted_issue.get("url", "")
                
                formatted_issues.append(
                    f"🎫 **Issue #{i}**\n\n"
                    f"**Key:** [{key}]({url})\n"
                    f"**Summary:** {summary}\n"
                    f"**Status:** {status}\n"
                    f"**Priority:** {priority}\n"
                    f"**Assignee:** {assignee}\n"
                    f"{'─' * 40}"
                )
            
            response_text = f"📂 **Your Jira Issues** (powered by {self.get_current_model_info()}):\n\n"
            response_text += f"**Issue Type:** {issue_type.replace('_', ' ').title()}\n"
            if isinstance(status_filter, list):
                response_text += f"**Status Filters:** {', '.join(status_filter)}\n"
            elif status_filter:
                response_text += f"**Status Filter:** {status_filter}\n"
            
            # Add additional filters to response
            if additional_filters:
                filter_descriptions = []
                for filter_type, filter_value in additional_filters.items():
                    if filter_type == 'priority':
                        filter_descriptions.append(f"Priority: {filter_value}")
                    elif filter_type == 'project':
                        filter_descriptions.append(f"Project: {filter_value}")
                    elif filter_type == 'issue_type':
                        filter_descriptions.append(f"Issue Type: {filter_value}")
                if filter_descriptions:
                    response_text += f"**Additional Filters:** {', '.join(filter_descriptions)}\n"
            
            response_text += f"**Total Found:** {len(issues)} issues\n\n"
            response_text += "\n".join(formatted_issues)
            
            if len(issues) > 10:
                response_text += f"\n\n... and {len(issues) - 10} more issues"
            
            return {
                "response": response_text,
                "action_taken": "jira_issues_fetched",
                "data": {"issues": issues, "issue_type": issue_type, "status_filter": status_filter, "count": len(issues)},
                "suggestions": ["View specific issue", "Filter by different status", "Check different issue types"]
            }
            
        except Exception as e:
            logger.error(f"Error fetching Jira issues: {e}")
            return {
                "response": f"❌ **Error Fetching Jira Issues**\n\nAn error occurred while fetching your Jira issues: {str(e)}",
                "action_taken": "jira_issues_error",
                "suggestions": ["Check Jira connection", "Verify credentials", "Try again"]
            }

    async def _handle_create_jira_issue(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle creating a new Jira issue"""
        # Extract issue details from the message
        summary = entities.get("summary")
        description = entities.get("description")
        project = entities.get("project")
        issue_type = entities.get("issue_type")
        
        if not summary:
            return {
                "response": "I'll help you create a new Jira issue! Please provide a summary for the issue.",
                "action_taken": "request_issue_summary",
                "suggestions": ["Provide issue summary"]
            }
        
        if not description:
            return {
                "response": "I'll help you create a new Jira issue! Please provide a description for the issue.",
                "action_taken": "request_issue_description",
                "suggestions": ["Provide issue description"]
            }
        
        if not project:
            return {
                "response": "I'll help you create a new Jira issue! Please specify the project for the issue.",
                "action_taken": "request_issue_project",
                "suggestions": ["Provide issue project"]
            }
        
        if not issue_type:
            return {
                "response": "I'll help you create a new Jira issue! Please specify the issue type for the issue.",
                "action_taken": "request_issue_type",
                "suggestions": ["Provide issue type"]
            }
        
        # Create Jira issue
        try:
            issue = jira_service.create_issue(
                project=project,
                summary=summary,
                description=description,
                issue_type=issue_type
            )
            return {
                "response": f"✅ Jira issue created successfully! Issue key: {issue.get('key')}",
                "action_taken": "jira_issue_created",
                "data": {"issue_key": issue.get('key')}
            }
        except Exception as e:
            logger.error(f"Error creating Jira issue: {e}")
            return {
                "response": f"❌ Failed to create Jira issue: {str(e)}",
                "action_taken": "jira_issue_creation_failed",
                "suggestions": ["Try again", "Check Jira connection"]
            }

    async def _handle_add_jira_comment(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle adding a comment to an existing Jira issue"""
        issue_key = entities.get("issue_key")
        comment_text = entities.get("comment_text")
        
        if not issue_key:
            return {
                "response": "I'll help you add a comment to a Jira issue! Please specify the issue key.",
                "action_taken": "request_issue_key",
                "suggestions": ["Provide issue key"]
            }
        
        if not comment_text:
            return {
                "response": "I'll help you add a comment to a Jira issue! Please provide the comment text.",
                "action_taken": "request_comment_text",
                "suggestions": ["Provide comment text"]
            }
        
        # Add comment to Jira issue
        try:
            success = jira_service.add_comment(issue_key, comment_text)
            if success:
                return {
                    "response": f"✅ Comment added to Jira issue {issue_key} successfully!",
                    "action_taken": "jira_comment_added",
                    "data": {"issue_key": issue_key, "comment_text": comment_text}
                }
            else:
                return {
                    "response": f"❌ Failed to add comment to Jira issue {issue_key}",
                    "action_taken": "jira_comment_addition_failed",
                    "suggestions": ["Try again", "Check Jira connection"]
                }
        except Exception as e:
            logger.error(f"Error adding comment to Jira issue: {e}")
            return {
                "response": f"❌ Failed to add comment to Jira issue: {str(e)}",
                "action_taken": "jira_comment_addition_failed",
                "suggestions": ["Try again", "Check Jira connection"]
            }

    async def _handle_assign_jira_issue(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle assigning a Jira issue to a user"""
        try:
            issue_key = entities.get('issue_key')
            assignee = entities.get('assignee')
            
            if not issue_key:
                return {
                    "response": "❌ No Jira issue key found. Please specify an issue key (e.g., OCPQE-30241).",
                    "action_taken": "jira_assignment_failed",
                    "data": {"error": "No issue key provided"}
                }
            
            if not assignee:
                return {
                    "response": "❌ No assignee specified. Please provide an email address or username.",
                    "action_taken": "jira_assignment_failed",
                    "data": {"error": "No assignee provided"}
                }
            
            # Use the Jira service to assign the issue
            if jira_service.assign_issue(issue_key, assignee):
                return {
                    "response": f"✅ Successfully assigned Jira issue {issue_key} to {assignee}!",
                    "action_taken": "jira_issue_assigned",
                    "data": {"issue_key": issue_key, "assignee": assignee}
                }
            else:
                return {
                    "response": f"❌ Failed to assign Jira issue {issue_key} to {assignee}. Please check the assignee name/email and try again.",
                    "action_taken": "jira_assignment_failed",
                    "data": {"issue_key": issue_key, "assignee": assignee}
                }
                
        except Exception as e:
            logger.error(f"Error assigning Jira issue: {e}")
            return {
                "response": f"❌ Failed to assign Jira issue. Error: {str(e)}",
                "action_taken": "jira_assignment_failed",
                "data": {"error": str(e)}
            }

    async def _handle_update_jira_status(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle updating the status of an existing Jira issue"""
        issue_key = entities.get("issue_key")
        status = entities.get("status")
        
        if not issue_key:
            return {
                "response": "I'll help you update the status of a Jira issue! Please specify the issue key.",
                "action_taken": "request_issue_key",
                "suggestions": ["Provide issue key"]
            }
        
        if not status:
            return {
                "response": "I'll help you update the status of a Jira issue! Please specify the new status for the issue.",
                "action_taken": "request_issue_status",
                "suggestions": ["Provide issue status"]
            }
        
        # Update Jira issue status
        try:
            updated_issue = jira_service.update_issue(issue_key, status=status)
            return {
                "response": f"✅ Jira issue status updated successfully! New status: {updated_issue.get('fields').get('status').get('name')}",
                "action_taken": "jira_issue_status_updated",
                "data": {"issue_key": issue_key, "status": updated_issue.get('fields').get('status').get('name')}
            }
        except Exception as e:
            logger.error(f"Error updating Jira issue status: {e}")
            return {
                "response": f"❌ Failed to update Jira issue status: {str(e)}",
                "action_taken": "jira_issue_status_update_failed",
                "suggestions": ["Try again", "Check Jira connection"]
            }

    async def _handle_jira_status_lookup(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle Jira status lookup queries"""
        issue_key = entities.get("issue_key")
        
        if not issue_key:
            return {
                "response": "I'll help you check the status of a Jira issue! Please specify the issue key.",
                "action_taken": "request_issue_key",
                "suggestions": ["Provide issue key"]
            }
        
        try:
            issue = jira_service.get_issue(issue_key)
            status = issue.get('fields', {}).get('status', {}).get('name', 'Unknown')
            return {
                "response": f"📊 **Status of {issue_key}:** {status}",
                "action_taken": "jira_status_lookup",
                "data": {"issue_key": issue_key, "status": status}
            }
        except Exception as e:
            logger.error(f"Error looking up Jira issue status: {e}")
            return {
                "response": f"❌ Failed to get status for {issue_key}: {str(e)}",
                "action_taken": "jira_status_lookup_failed",
                "suggestions": ["Check issue key", "Try again"]
            }

    async def _handle_jira_metadata_query(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle Jira metadata queries"""
        issue_key = entities.get("issue_key")
        query_type = entities.get("query_type")
        
        if not issue_key:
            return {
                "response": "I'll help you get information about a Jira issue! Please specify the issue key.",
                "action_taken": "request_issue_key",
                "suggestions": ["Provide issue key"]
            }
        
        try:
            issue = jira_service.get_issue(issue_key)
            fields = issue.get('fields', {})
            
            if query_type == 'last_updated':
                updated = fields.get('updated', 'Unknown')
                return {
                    "response": f"📅 **{issue_key}** was last updated: {updated}",
                    "action_taken": "jira_metadata_query",
                    "data": {"issue_key": issue_key, "last_updated": updated}
                }
            elif query_type == 'assignee':
                assignee = fields.get('assignee', {})
                assignee_name = assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned'
                return {
                    "response": f"👤 **{issue_key}** is assigned to: {assignee_name}",
                    "action_taken": "jira_metadata_query",
                    "data": {"issue_key": issue_key, "assignee": assignee_name}
                }
            else:
                # Default to status
                status = fields.get('status', {}).get('name', 'Unknown')
                return {
                    "response": f"📊 **Status of {issue_key}:** {status}",
                    "action_taken": "jira_metadata_query",
                    "data": {"issue_key": issue_key, "status": status}
                }
        except Exception as e:
            logger.error(f"Error querying Jira issue metadata: {e}")
            return {
                "response": f"❌ Failed to get information for {issue_key}: {str(e)}",
                "action_taken": "jira_metadata_query_failed",
                "suggestions": ["Check issue key", "Try again"]
            }

    async def _handle_jira_advanced_filter(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle Jira advanced filter queries"""
        filter_type = entities.get("filter_type")
        project = entities.get("project")
        
        try:
            if filter_type == 'priority':
                priority = entities.get("priority", "Critical")
                jql = f"priority = {priority}"
                if project:
                    jql += f" AND project = {project}"
                issues = jira_service.search_issues(jql)
                count = len(issues)
                return {
                    "response": f"🔍 Found {count} {priority} priority issues{f' in {project}' if project else ''}",
                    "action_taken": "jira_advanced_filter",
                    "data": {"filter_type": filter_type, "priority": priority, "count": count, "project": project}
                }
            elif filter_type == 'status':
                status = entities.get("status", "Blocked")
                jql = f"status = '{status}'"
                if project:
                    jql += f" AND project = {project}"
                issues = jira_service.search_issues(jql)
                count = len(issues)
                return {
                    "response": f"🔍 Found {count} {status} issues{f' in {project}' if project else ''}",
                    "action_taken": "jira_advanced_filter",
                    "data": {"filter_type": filter_type, "status": status, "count": count, "project": project}
                }
            elif filter_type == 'due_date':
                due_date = entities.get("due_date")
                if due_date == 'today':
                    jql = "due = today()"
                elif due_date == 'this_week':
                    jql = "due <= endOfWeek()"
                elif due_date == 'overdue':
                    jql = "due < now()"
                else:
                    jql = "due is not EMPTY"
                
                if project:
                    jql += f" AND project = {project}"
                
                issues = jira_service.search_issues(jql)
                count = len(issues)
                return {
                    "response": f"📅 Found {count} issues {due_date.replace('_', ' ')}{f' in {project}' if project else ''}",
                    "action_taken": "jira_advanced_filter",
                    "data": {"filter_type": filter_type, "due_date": due_date, "count": count, "project": project}
                }
            else:
                return {
                    "response": "I can help you filter Jira issues by priority, status, or due date. What type of filter would you like?",
                    "action_taken": "request_filter_type",
                    "suggestions": ["Critical priority", "Blocked status", "Due today", "Overdue"]
                }
        except Exception as e:
            logger.error(f"Error applying Jira advanced filter: {e}")
            return {
                "response": f"❌ Failed to apply filter: {str(e)}",
                "action_taken": "jira_advanced_filter_failed",
                "suggestions": ["Try again", "Check Jira connection"]
            }

    async def _handle_jira_sprint_query(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle Jira sprint and backlog queries"""
        query_type = entities.get("query_type")
        sprint_number = entities.get("sprint_number")
        
        try:
            if query_type == 'story_points':
                jql = "sprint in openSprints() AND storyPoints is not EMPTY"
                issues = jira_service.search_issues(jql)
                total_points = sum(issue.get('fields', {}).get('storyPoints', 0) for issue in issues)
                return {
                    "response": f"📊 **Current Sprint Story Points:** {total_points} points across {len(issues)} issues",
                    "action_taken": "jira_sprint_query",
                    "data": {"query_type": query_type, "total_points": total_points, "issue_count": len(issues)}
                }
            elif query_type == 'burndown':
                return {
                    "response": "📈 **Sprint Burndown:** I can help you track sprint progress. This feature requires additional sprint data integration.",
                    "action_taken": "jira_sprint_query",
                    "data": {"query_type": query_type, "message": "Burndown tracking requires sprint data"}
                }
            elif query_type == 'epics':
                jql = "issuetype = Epic AND status != Closed"
                if sprint_number:
                    jql += f" AND sprint = {sprint_number}"
                issues = jira_service.search_issues(jql)
                return {
                    "response": f"📋 **Open Epics:** Found {len(issues)} open epics{f' in sprint {sprint_number}' if sprint_number else ''}",
                    "action_taken": "jira_sprint_query",
                    "data": {"query_type": query_type, "epic_count": len(issues), "sprint_number": sprint_number}
                }
            elif query_type == 'backlog':
                jql = "sprint is EMPTY AND status != Closed"
                issues = jira_service.search_issues(jql)
                return {
                    "response": f"📋 **Backlog:** Found {len(issues)} issues in the backlog",
                    "action_taken": "jira_sprint_query",
                    "data": {"query_type": query_type, "backlog_count": len(issues)}
                }
            else:
                return {
                    "response": "I can help you with sprint queries like story points, burndown, epics, or backlog. What would you like to know?",
                    "action_taken": "request_sprint_query_type",
                    "suggestions": ["Story points", "Burndown", "Epics", "Backlog"]
                }
        except Exception as e:
            logger.error(f"Error querying Jira sprint data: {e}")
            return {
                "response": f"❌ Failed to get sprint information: {str(e)}",
                "action_taken": "jira_sprint_query_failed",
                "suggestions": ["Try again", "Check Jira connection"]
            }

    def _extract_jira_create_entities(self, message: str) -> Dict[str, Any]:
        """Extract entities for creating a Jira issue"""
        entities = {}
        message_lower = message.lower()
        
        # Extract project key (e.g., "CNTRLPLANE", "OCPBUGS")
        project_pattern = r'\b([A-Z]{2,})\b'
        project_match = re.search(project_pattern, message)
        if project_match:
            entities['project'] = project_match.group(1)
        
        # Extract issue type
        if any(word in message_lower for word in ["bug", "defect"]):
            entities['issue_type'] = "Bug"
        elif any(word in message_lower for word in ["task", "work"]):
            entities['issue_type'] = "Task"
        elif any(word in message_lower for word in ["story", "feature"]):
            entities['issue_type'] = "Story"
        elif any(word in message_lower for word in ["epic"]):
            entities['issue_type'] = "Epic"
        else:
            entities['issue_type'] = "Task"  # Default
        
        # Extract summary (try to get text after "summary:" or "title:")
        summary_patterns = [
            r'summary[:\s]+["\']?([^"\']+)["\']?',
            r'title[:\s]+["\']?([^"\']+)["\']?',
            r'about[:\s]+["\']?([^"\']+)["\']?'
        ]
        for pattern in summary_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                entities['summary'] = match.group(1).strip()
                break
        
        # Extract description
        description_patterns = [
            r'description[:\s]+["\']?([^"\']+)["\']?',
            r'details[:\s]+["\']?([^"\']+)["\']?',
            r'with[:\s]+["\']?([^"\']+)["\']?'
        ]
        for pattern in description_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                entities['description'] = match.group(1).strip()
                break
        
        return entities

    def _extract_jira_comment_entities(self, message: str) -> Dict[str, Any]:
        """Extract entities for adding a comment to a Jira issue"""
        entities = {}
        message_lower = message.lower()
        
        # Extract issue key (e.g., "CNTRLPLANE-123", "OCPBUGS-456")
        issue_key_pattern = r'\b([A-Z]+-\d+)\b'
        issue_key_match = re.search(issue_key_pattern, message)
        if issue_key_match:
            entities['issue_key'] = issue_key_match.group(1)
        
        # Extract comment text - improved patterns
        comment_patterns = [
            r'add\s+comment\s+to\s+[A-Z]+-\d+\s+(.+)',  # add comment to OCPQE-30241 working on it
            r'add\s+a\s+comment\s+to\s+[A-Z]+-\d+\s+(.+)',  # add a comment to OCPQE-30241 working on it
            r'leave\s+a\s+comment\s+to\s+[A-Z]+-\d+\s+(.+)',  # leave a comment to OCPQE-30241 working on it
            r'write\s+a\s+comment\s+to\s+[A-Z]+-\d+\s+(.+)',  # write a comment to OCPQE-30241 working on it
            r'post\s+a\s+comment\s+to\s+[A-Z]+-\d+\s+(.+)',  # post a comment to OCPQE-30241 working on it
            r'add\s+note\s+to\s+[A-Z]+-\d+\s+(.+)',  # add note to OCPQE-30241 working on it
            r'leave\s+a\s+note\s+to\s+[A-Z]+-\d+\s+(.+)',  # leave a note to OCPQE-30241 working on it
            r'write\s+a\s+note\s+to\s+[A-Z]+-\d+\s+(.+)',  # write a note to OCPQE-30241 working on it
            r'reply\s+to\s+[A-Z]+-\d+\s+(.+)',  # reply to OCPQE-30241 working on it
            r'comment[:\s]+["\']([^"\']+)["\']',  # comment: "text"
            r'note[:\s]+["\']([^"\']+)["\']',     # note: "text"
            r'reply[:\s]+["\']([^"\']+)["\']',    # reply: "text"
            r'with[:\s]+["\']([^"\']+)["\']',     # with: text
            r'["\']([^"\']+)["\']',               # "text" (anywhere in message)
            r'comment[:\s]+([^"\']+)',            # comment: text
            r'note[:\s]+([^"\']+)',               # note: text
            r'reply[:\s]+([^"\']+)',              # reply: text
            r'with[:\s]+([^"\']+)',               # with: text
        ]
        
        # Try the specific patterns first
        for pattern in comment_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                comment_text = match.group(1).strip()
                # Clean up the comment text
                if comment_text and len(comment_text) > 0:
                    entities['comment_text'] = comment_text
                    break
        
        # If no comment found with specific patterns, extract everything after the issue key
        if 'comment_text' not in entities and 'issue_key' in entities:
            issue_key = entities['issue_key']
            
            # For the specific format "add comment to jira OCPQE-30241 working on it"
            # Extract just the comment part
            if 'add comment to jira' in message_lower:
                # Split the message by the issue key
                parts = message.split(issue_key)
                if len(parts) > 1:
                    # Take everything after the issue key
                    after_issue = parts[1].strip()
                    # Remove "to jira" if it appears at the beginning
                    if after_issue.lower().startswith('to jira'):
                        after_issue = after_issue[7:].strip()
                    # Remove the issue key if it appears again
                    after_issue = after_issue.replace(issue_key, '').strip()
                    if after_issue:
                        entities['comment_text'] = after_issue
            else:
                # For other formats like "add comment to OCPQE-30241 working on it"
                # Find the issue key position and extract everything after it
                issue_key_pos = message.find(issue_key)
                if issue_key_pos != -1:
                    # Get everything after the issue key
                    after_issue = message[issue_key_pos + len(issue_key):].strip()
                    # Clean up common prefixes
                    for prefix in ['to', 'with', 'comment', 'note', 'reply']:
                        if after_issue.lower().startswith(prefix):
                            after_issue = after_issue[len(prefix):].strip()
                    # Remove any remaining issue key references
                    after_issue = after_issue.replace(issue_key, '').strip()
                    if after_issue:
                        entities['comment_text'] = after_issue
        
        return entities

    def _extract_jira_assignment_entities(self, message: str) -> Dict[str, Any]:
        """Extract entities for assigning a Jira issue"""
        entities = {}
        message_lower = message.lower()
        
        # Extract issue key (e.g., "CNTRLPLANE-123", "OCPBUGS-456")
        issue_key_pattern = r'\b([A-Z]+-\d+)\b'
        issue_key_match = re.search(issue_key_pattern, message)
        if issue_key_match:
            entities['issue_key'] = issue_key_match.group(1)
        
        # Extract assignee - look for email patterns or usernames
        # Email pattern: skundu@redhat.com
        email_pattern = r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
        email_match = re.search(email_pattern, message)
        if email_match:
            entities['assignee'] = email_match.group(1)
        else:
            # Look for username patterns after "to" or "assign to"
            assign_patterns = [
                r'assign\s+(?:to\s+)?([a-zA-Z0-9._-]+)',
                r'reassign\s+(?:to\s+)?([a-zA-Z0-9._-]+)',
                r'give\s+(?:to\s+)?([a-zA-Z0-9._-]+)',
                r'hand\s+over\s+(?:to\s+)?([a-zA-Z0-9._-]+)',
                r'pass\s+(?:to\s+)?([a-zA-Z0-9._-]+)',
                r'transfer\s+(?:to\s+)?([a-zA-Z0-9._-]+)',
                r'set\s+assignee\s+(?:to\s+)?([a-zA-Z0-9._-]+)',
                r'change\s+assignee\s+(?:to\s+)?([a-zA-Z0-9._-]+)',
                r'update\s+assignee\s+(?:to\s+)?([a-zA-Z0-9._-]+)',
                r'to\s+([a-zA-Z0-9._-]+)',
            ]
            
            for pattern in assign_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    assignee = match.group(1).strip()
                    # Clean up common words that might be captured
                    if assignee.lower() not in ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'it', 'this', 'that']:
                        # Make sure we're not capturing the issue key as assignee
                        if 'issue_key' in entities and assignee == entities['issue_key']:
                            continue
                        entities['assignee'] = assignee
                        break
        
        return entities

    def _extract_conversational_jira_entities(self, message: str) -> Dict[str, Any]:
        """Extract entities for conversational Jira queries"""
        entities = {}
        message_lower = message.lower()
        
        # Extract issue key if present
        issue_key_pattern = r'\b([A-Z]+-\d+)\b'
        issue_key_match = re.search(issue_key_pattern, message)
        if issue_key_match:
            entities['issue_key'] = issue_key_match.group(1)
        
        # Extract conversational context
        conversational_patterns = {
            'what': ['what', 'what is', 'what are', 'what do', 'what does', 'what was', 'what will'],
            'how': ['how', 'how is', 'how are', 'how do', 'how does', 'how was', 'how will'],
            'when': ['when', 'when is', 'when are', 'when do', 'when does', 'when was', 'when will'],
            'where': ['where', 'where is', 'where are', 'where do', 'where does'],
            'who': ['who', 'who is', 'who are', 'who do', 'who does', 'who was', 'who will'],
            'why': ['why', 'why is', 'why are', 'why do', 'why does', 'why was', 'why will'],
            'can': ['can', 'can you', 'can i', 'can we'],
            'could': ['could', 'could you', 'could i', 'could we'],
            'would': ['would', 'would you', 'would i', 'would we'],
            'should': ['should', 'should you', 'should i', 'should we'],
            'please': ['please', 'pls', 'plz'],
            'help': ['help', 'help me', 'assist', 'assist me', 'support', 'support me']
        }
        
        for intent_type, patterns in conversational_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                entities['conversational_intent'] = intent_type
                break
        
        # Extract urgency indicators
        urgency_patterns = {
            'urgent': ['urgent', 'asap', 'immediately', 'right now', 'now', 'quick', 'fast'],
            'important': ['important', 'critical', 'high priority', 'major'],
            'normal': ['normal', 'regular', 'standard', 'usual'],
            'low': ['low priority', 'minor', 'not urgent', 'whenever']
        }
        
        for urgency_level, patterns in urgency_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                entities['urgency'] = urgency_level
                break
        
        return entities

    def _extract_jira_status_entities(self, message: str) -> Dict[str, Any]:
        """Extract entities for updating Jira issue status"""
        entities = {}
        message_lower = message.lower()
        
        # Extract issue key
        issue_key_pattern = r'\b([A-Z]+-\d+)\b'
        issue_key_match = re.search(issue_key_pattern, message)
        if issue_key_match:
            entities['issue_key'] = issue_key_match.group(1)
        
        # Extract status - use word boundaries to avoid partial matches
        status_patterns = [
            (r'\bto do\b', 'To Do'),
            (r'\btodo\b', 'To Do'),
            (r'\bto_do\b', 'To Do'),
            (r'\bTO_DO\b', 'To Do'),
            (r'\bdone\b', 'Done'),
            (r'\bin progress\b', 'In Progress'),
            (r'\bprogressing\b', 'In Progress'),
            (r'\bworking on it\b', 'In Progress'),
            (r'\bworking on\b', 'In Progress'),
            (r'\bworking\b', 'In Progress'),
            (r'\bopen\b', 'Open'),
            (r'\bclosed\b', 'Closed'),
            (r'\bnew\b', 'NEW'),
            (r'\bpost\b', 'POST'),
            (r'\bverified\b', 'Verified'),
            (r'\bresolved\b', 'Resolved'),
            (r'\bblocked\b', 'Blocked'),
            (r'\bwaiting\b', 'Waiting'),
            (r'\bpending\b', 'Pending'),
            (r'\breview\b', 'Review'),
            (r'\bcode review\b', 'Code Review'),
            (r'\btesting\b', 'Testing'),
            (r'\bon qa\b', 'ON_QA'),
            (r'\bqa\b', 'ON_QA')
        ]
        
        for pattern, status_value in status_patterns:
            if re.search(pattern, message_lower):
                entities['status'] = status_value
                break
        
        return entities

    def _extract_jira_metadata_entities(self, message: str) -> Dict[str, Any]:
        """Extract entities for Jira metadata queries"""
        entities = {}
        message_lower = message.lower()
        
        # Extract issue key
        issue_key_pattern = r'[A-Z]+-\d+'
        issue_match = re.search(issue_key_pattern, message)
        if issue_match:
            entities['issue_key'] = issue_match.group()
        
        # Extract query type
        if any(phrase in message_lower for phrase in ["what's the status", "what is the status", "status of", "current status"]):
            entities['query_type'] = 'status'
        elif any(phrase in message_lower for phrase in ["when was", "last updated", "last modified"]):
            entities['query_type'] = 'last_updated'
        elif any(phrase in message_lower for phrase in ["who is working on", "assigned to"]):
            entities['query_type'] = 'assignee'
        
        return entities

    def _extract_jira_filter_entities(self, message: str) -> Dict[str, Any]:
        """Extract entities for Jira advanced filters"""
        entities = {}
        message_lower = message.lower()
        
        # Extract filter type
        if any(phrase in message_lower for phrase in ["critical", "high priority"]):
            entities['filter_type'] = 'priority'
            entities['priority'] = 'Critical'
        elif any(phrase in message_lower for phrase in ["blocked"]):
            entities['filter_type'] = 'status'
            entities['status'] = 'Blocked'
        elif any(phrase in message_lower for phrase in ["overdue", "due today", "due this week"]):
            entities['filter_type'] = 'due_date'
            if "due today" in message_lower:
                entities['due_date'] = 'today'
            elif "due this week" in message_lower:
                entities['due_date'] = 'this_week'
            elif "overdue" in message_lower:
                entities['due_date'] = 'overdue'
        
        # Extract project if mentioned
        project_pattern = r'in\s+([A-Za-z0-9\s]+?)(?:\s+project|\s+component|\s+module|$)'
        project_match = re.search(project_pattern, message_lower)
        if project_match:
            entities['project'] = project_match.group(1).strip()
        
        return entities

    def _extract_jira_sprint_entities(self, message: str) -> Dict[str, Any]:
        """Extract entities for Jira sprint queries"""
        entities = {}
        message_lower = message.lower()
        
        # Extract sprint number if mentioned
        sprint_pattern = r'sprint\s+(\d+)'
        sprint_match = re.search(sprint_pattern, message_lower)
        if sprint_match:
            entities['sprint_number'] = int(sprint_match.group(1))
        
        # Extract query type
        if any(phrase in message_lower for phrase in ["story points", "points"]):
            entities['query_type'] = 'story_points'
        elif any(phrase in message_lower for phrase in ["burndown", "burn down"]):
            entities['query_type'] = 'burndown'
        elif any(phrase in message_lower for phrase in ["epics", "epic"]):
            entities['query_type'] = 'epics'
        elif any(phrase in message_lower for phrase in ["backlog", "stories"]):
            entities['query_type'] = 'backlog'
        
        return entities

    def _extract_search_entities(self, message: str) -> Dict[str, Any]:
        """Extract search-related entities from message"""
        entities = {}
        message_lower = message.lower()
        
        # Extract sender name/email
        sender_patterns = [
            r'from\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'by\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'from\s+([A-Za-z\s]+)',
            r'by\s+([A-Za-z\s]+)'
        ]
        
        for pattern in sender_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                entities["sender"] = match.group(1).strip()
                break
        
        # Extract search terms
        search_terms = []
        words = message.split()
        for i, word in enumerate(words):
            if word.lower() in ["about", "regarding", "concerning", "related to"]:
                if i + 1 < len(words):
                    search_terms.extend(words[i+1:])
                    break
        
        if search_terms:
            entities["search_terms"] = " ".join(search_terms)
        
        return entities

    def _extract_date_entities(self, message: str) -> Dict[str, Any]:
        """Extract date-related entities from message"""
        entities = {}
        message_lower = message.lower()
        
        # Date patterns
        date_patterns = {
            "today": "today",
            "yesterday": "yesterday", 
            "this week": "this week",
            "past week": "past week",
            "last week": "last week",
            "this month": "this month",
            "last month": "last month"
        }
        
        for pattern, value in date_patterns.items():
            if pattern in message_lower:
                entities["date_range"] = value
                break
        
        # Specific date extraction
        date_regex = r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b'
        date_match = re.search(date_regex, message)
        if date_match:
            entities["specific_date"] = date_match.group(1)
        
        return entities

    async def _handle_find_attachments(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle finding emails with attachments"""
        try:
            emails = self._fetch_emails(max_results=20)
            
            if not emails:
                return {
                    "response": "No emails found to check for attachments.",
                    "action_taken": "find_attachments",
                    "suggestions": ["Check all emails", "Refresh inbox"]
                }
            
            # Check for emails with attachments (simplified - in real implementation, you'd check the Gmail API)
            emails_with_attachments = []
            for email in emails:
                # For demo purposes, we'll assume some emails have attachments
                if any(keyword in email['subject'].lower() for keyword in ['report', 'document', 'pdf', 'attachment']):
                    emails_with_attachments.append(email)
            
            if emails_with_attachments:
                response_parts = ["📎 **Emails with Attachments**\n"]
                for i, email in enumerate(emails_with_attachments[:5], 1):
                    sender = email['sender']
                    if '<' in sender and '>' in sender:
                        sender = sender.split('<')[0].strip().strip('"')
                    response_parts.append(f"**Email #{i}:** {email['subject']}")
                    response_parts.append(f"**From:** {sender}")
                    response_parts.append(f"**Date:** {email['date']}\n")
                
                response_text = "\n".join(response_parts)
            else:
                response_text = "📎 **No emails with attachments found** in your recent emails."
            
            return {
                "response": response_text,
                "action_taken": "find_attachments",
                "data": {"emails_with_attachments": emails_with_attachments},
                "suggestions": ["Download attachments", "Forward emails", "Search specific files"]
            }
            
        except Exception as e:
            logger.error(f"Error finding attachments: {e}")
            return {
                "response": "I encountered an error while searching for attachments. Please try again.",
                "action_taken": "find_attachments_error",
                "suggestions": ["Try again", "Check authentication"]
            }

    async def _handle_find_important_emails(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle finding important/flagged emails"""
        try:
            emails = self._fetch_emails(max_results=20)
            
            if not emails:
                return {
                    "response": "No emails found to check for important ones.",
                    "action_taken": "find_important_emails",
                    "suggestions": ["Check all emails", "Refresh inbox"]
                }
            
            # Find important emails (those with IMPORTANT label or urgent keywords)
            important_emails = []
            for email in emails:
                if 'IMPORTANT' in email.get('label_ids', []) or any(keyword in email['subject'].lower() for keyword in ['urgent', 'important', 'critical', 'asap']):
                    important_emails.append(email)
            
            if important_emails:
                response_parts = ["⭐ **Important Emails**\n"]
                for i, email in enumerate(important_emails[:5], 1):
                    sender = email['sender']
                    if '<' in sender and '>' in sender:
                        sender = sender.split('<')[0].strip().strip('"')
                    response_parts.append(f"**Email #{i}:** {email['subject']}")
                    response_parts.append(f"**From:** {sender}")
                    response_parts.append(f"**Date:** {email['date']}")
                    response_parts.append(f"**Status:** {'🔴 UNREAD' if not email.get('is_read', True) else '✅ READ'}\n")
                
                response_text = "\n".join(response_parts)
            else:
                response_text = "⭐ **No important emails found** in your recent emails."
            
            return {
                "response": response_text,
                "action_taken": "find_important_emails",
                "data": {"important_emails": important_emails},
                "suggestions": ["Mark as read", "Reply to important emails", "Set reminders"]
            }
            
        except Exception as e:
            logger.error(f"Error finding important emails: {e}")
            return {
                "response": "I encountered an error while searching for important emails. Please try again.",
                "action_taken": "find_important_emails_error",
                "suggestions": ["Try again", "Check authentication"]
            }

    async def _handle_find_spam_emails(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle finding spam/suspicious emails"""
        try:
            emails = self._fetch_emails(max_results=20)
            
            if not emails:
                return {
                    "response": "No emails found to check for spam.",
                    "action_taken": "find_spam_emails",
                    "suggestions": ["Check all emails", "Refresh inbox"]
                }
            
            # Find potential spam emails
            spam_emails = []
            spam_keywords = ['unsubscribe', 'limited time', 'act now', 'click here', 'free offer', 'promotional', 'newsletter']
            
            for email in emails:
                if any(keyword in email['subject'].lower() or keyword in email.get('snippet', '').lower() for keyword in spam_keywords):
                    spam_emails.append(email)
            
            if spam_emails:
                response_parts = ["🚫 **Potential Spam Emails**\n"]
                for i, email in enumerate(spam_emails[:5], 1):
                    sender = email['sender']
                    if '<' in sender and '>' in sender:
                        sender = sender.split('<')[0].strip().strip('"')
                    response_parts.append(f"**Email #{i}:** {email['subject']}")
                    response_parts.append(f"**From:** {sender}")
                    response_parts.append(f"**Date:** {email['date']}\n")
                
                response_text = "\n".join(response_parts)
            else:
                response_text = "✅ **No spam emails detected** in your recent emails."
            
            return {
                "response": response_text,
                "action_taken": "find_spam_emails",
                "data": {"spam_emails": spam_emails},
                "suggestions": ["Mark as spam", "Delete spam emails", "Block senders"]
            }
            
        except Exception as e:
            logger.error(f"Error finding spam emails: {e}")
            return {
                "response": "I encountered an error while searching for spam emails. Please try again.",
                "action_taken": "find_spam_emails_error",
                "suggestions": ["Try again", "Check authentication"]
            }

    async def _handle_search_emails_by_sender(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle searching emails by sender"""
        try:
            sender = entities.get("sender", "")
            if not sender:
                return {
                    "response": "Please specify a sender name or email address to search for.",
                    "action_taken": "search_emails_by_sender",
                    "suggestions": ["Try: 'emails from John'", "Try: 'emails from john@example.com'"]
                }
            
            emails = self._fetch_emails(max_results=20)
            
            if not emails:
                return {
                    "response": "No emails found to search.",
                    "action_taken": "search_emails_by_sender",
                    "suggestions": ["Check all emails", "Refresh inbox"]
                }
            
            # Filter emails by sender
            matching_emails = []
            for email in emails:
                if sender.lower() in email['sender'].lower():
                    matching_emails.append(email)
            
            if matching_emails:
                response_parts = [f"📧 **Emails from {sender}**\n"]
                for i, email in enumerate(matching_emails[:5], 1):
                    sender_name = email['sender']
                    if '<' in sender_name and '>' in sender_name:
                        sender_name = sender_name.split('<')[0].strip().strip('"')
                    response_parts.append(f"**Email #{i}:** {email['subject']}")
                    response_parts.append(f"**Date:** {email['date']}")
                    response_parts.append(f"**Status:** {'🔴 UNREAD' if not email.get('is_read', True) else '✅ READ'}\n")
                
                response_text = "\n".join(response_parts)
            else:
                response_text = f"📧 **No emails found from {sender}** in your recent emails."
            
            return {
                "response": response_text,
                "action_taken": "search_emails_by_sender",
                "data": {"sender": sender, "matching_emails": matching_emails},
                "suggestions": ["Reply to emails", "Mark as read", "Search other senders"]
            }
            
        except Exception as e:
            logger.error(f"Error searching emails by sender: {e}")
            return {
                "response": "I encountered an error while searching emails by sender. Please try again.",
                "action_taken": "search_emails_by_sender_error",
                "suggestions": ["Try again", "Check authentication"]
            }

    async def _handle_search_emails_by_date(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle searching emails by date range"""
        try:
            date_range = entities.get("date_range", "recent")
            
            emails = self._fetch_emails(max_results=20)
            
            if not emails:
                return {
                    "response": "No emails found to search.",
                    "action_taken": "search_emails_by_date",
                    "suggestions": ["Check all emails", "Refresh inbox"]
                }
            
            # For demo purposes, we'll return recent emails
            # In a real implementation, you'd filter by actual date ranges
            recent_emails = emails[:5]  # Show most recent 5
            
            response_parts = [f"📅 **Emails ({date_range})**\n"]
            for i, email in enumerate(recent_emails, 1):
                sender = email['sender']
                if '<' in sender and '>' in sender:
                    sender = sender.split('<')[0].strip().strip('"')
                response_parts.append(f"**Email #{i}:** {email['subject']}")
                response_parts.append(f"**From:** {sender}")
                response_parts.append(f"**Date:** {email['date']}")
                response_parts.append(f"**Status:** {'🔴 UNREAD' if not email.get('is_read', True) else '✅ READ'}\n")
            
            response_text = "\n".join(response_parts)
            
            return {
                "response": response_text,
                "action_taken": "search_emails_by_date",
                "data": {"date_range": date_range, "emails": recent_emails},
                "suggestions": ["Search different date range", "Mark as read", "Reply to emails"]
            }
            
        except Exception as e:
            logger.error(f"Error searching emails by date: {e}")
            return {
                "response": "I encountered an error while searching emails by date. Please try again.",
                "action_taken": "search_emails_by_date_error",
                "suggestions": ["Try again", "Check authentication"]
            }

    async def _handle_find_pending_emails(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle finding emails that need replies/approvals"""
        try:
            emails = self._fetch_emails(max_results=20)
            
            if not emails:
                return {
                    "response": "No emails found to check for pending items.",
                    "action_taken": "find_pending_emails",
                    "suggestions": ["Check all emails", "Refresh inbox"]
                }
            
            # Find emails that might need replies (unread or contain action keywords)
            pending_emails = []
            action_keywords = ['approval', 'review', 'feedback', 'response', 'reply', 'urgent', 'asap']
            
            for email in emails:
                if not email.get('is_read', True) or any(keyword in email['subject'].lower() for keyword in action_keywords):
                    pending_emails.append(email)
            
            if pending_emails:
                response_parts = ["⏳ **Pending Emails (Need Attention)**\n"]
                for i, email in enumerate(pending_emails[:5], 1):
                    sender = email['sender']
                    if '<' in sender and '>' in sender:
                        sender = sender.split('<')[0].strip().strip('"')
                    response_parts.append(f"**Email #{i}:** {email['subject']}")
                    response_parts.append(f"**From:** {sender}")
                    response_parts.append(f"**Date:** {email['date']}")
                    response_parts.append(f"**Status:** {'🔴 UNREAD' if not email.get('is_read', True) else '✅ READ'}\n")
                
                response_text = "\n".join(response_parts)
            else:
                response_text = "✅ **No pending emails found** - you're all caught up!"
            
            return {
                "response": response_text,
                "action_taken": "find_pending_emails",
                "data": {"pending_emails": pending_emails},
                "suggestions": ["Reply to emails", "Mark as read", "Set reminders"]
            }
            
        except Exception as e:
            logger.error(f"Error finding pending emails: {e}")
            return {
                "response": "I encountered an error while searching for pending emails. Please try again.",
                "action_taken": "find_pending_emails_error",
                "suggestions": ["Try again", "Check authentication"]
            }

    async def _handle_github_pr_action(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle GitHub PR actions like close, merge, etc."""
        try:
            from app.services.github_service import github_service
            
            message_lower = message.lower()
            
            # Extract PR URL from message
            import re
            github_url_pattern = r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)'
            match = re.search(github_url_pattern, message)
            
            if not match:
                return {
                    "response": "🔗 **GitHub PR Action**<br><br>I need a GitHub PR URL to perform actions.<br><br>**Example:** `close pr https://github.com/owner/repo/pull/123`",
                    "action_taken": "github_pr_action_no_url",
                    "suggestions": ["Provide PR URL", "Use format: action pr https://github.com/owner/repo/pull/123"]
                }
            
            owner, repo, pr_number = match.groups()
            pr_number = int(pr_number)
            
            # Determine the action
            if any(word in message_lower for word in ["close", "closed"]):
                action = "close"
                action_text = "close"
            elif any(word in message_lower for word in ["merge", "merged"]):
                action = "merge"
                action_text = "merge"
            else:
                return {
                    "response": f"🔧 **GitHub PR Action**<br><br>I can help you with PR actions like close or merge.<br><br>**Supported actions:** close, merge<br><br>**Example:** `close pr https://github.com/{owner}/{repo}/pull/{pr_number}`",
                    "action_taken": "github_pr_action_unsupported",
                    "suggestions": ["Close PR", "Merge PR", "Review PR"]
                }
            
            # Perform the action
            if action == "close":
                result = await github_service.close_pull_request(owner, repo, pr_number)
                if "error" in result:
                    return {
                        "response": f"❌ Failed to close PR #{pr_number}. Error: {result['error']}",
                        "action_taken": "github_pr_close_failed",
                        "suggestions": ["Check permissions", "Try again", "Verify PR exists"]
                    }
                else:
                    return {
                        "response": f"✅ Successfully closed PR #{pr_number} in {owner}/{repo}",
                        "action_taken": "github_pr_close_success",
                        "data": result,
                        "suggestions": ["List open PRs", "Review other PRs", "Create new PR"]
                    }
            
            elif action == "merge":
                result = await github_service.merge_pull_request(owner, repo, pr_number)
                if "error" in result:
                    return {
                        "response": f"❌ Failed to merge PR #{pr_number}. Error: {result['error']}",
                        "action_taken": "github_pr_merge_failed",
                        "suggestions": ["Check merge conflicts", "Verify permissions", "Try again"]
                    }
                else:
                    return {
                        "response": f"✅ Successfully merged PR #{pr_number} in {owner}/{repo}",
                        "action_taken": "github_pr_merge_success",
                        "data": result,
                        "suggestions": ["List open PRs", "Review other PRs", "Create new PR"]
                    }
            
        except Exception as e:
            logger.error(f"Error handling GitHub PR action: {e}")
            return {
                "response": "❌ I encountered an error while performing the PR action. Please check your GitHub authentication and try again.",
                "action_taken": "github_pr_action_error",
                "suggestions": ["Check GitHub authentication", "Try again", "Verify PR URL"]
            }

    async def _handle_github_summarize_pr(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle GitHub PR summarization"""
        try:
            from app.services.github_service import github_service
            
            # Check if GitHub token is available
            token = github_service._get_token()
            logger.info(f"GitHub token available: {bool(token)}")
            if not token:
                return {
                    "response": "🔑 **GitHub Authentication Required**<br><br>GitHub token is not configured. Please set up GitHub authentication to use PR features.<br><br>**To configure:**<br>1. Go to GitHub Settings → Developer settings → Personal access tokens<br>2. Create a new token with repo permissions<br>3. Add it to your credentials",
                    "action_taken": "github_auth_required",
                    "suggestions": ["Configure GitHub token", "Check credentials", "Set up authentication"]
                }
            
            # Extract PR URL from message
            import re
            github_url_pattern = r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)'
            match = re.search(github_url_pattern, message)
            
            if not match:
                return {
                    "response": "🔗 **GitHub PR Summary**<br><br>I need a GitHub PR URL to summarize.<br><br>**Example:** `summarise pr https://github.com/owner/repo/pull/123`",
                    "action_taken": "github_summarize_pr_no_url",
                    "suggestions": ["Provide PR URL", "Use format: summarise pr https://github.com/owner/repo/pull/123"]
                }
            
            owner, repo, pr_number = match.groups()
            pr_number = int(pr_number)
            
            # Get PR details
            logger.info(f"Fetching PR details for {owner}/{repo}#{pr_number}")
            pr_details = await github_service.get_pull_request(owner, repo, pr_number)
            logger.info(f"PR details response type: {type(pr_details)}")
            logger.info(f"PR details response: {pr_details}")
            
            if not pr_details:
                return {
                    "response": f"❌ Failed to fetch PR #{pr_number}. No response from GitHub API.",
                    "action_taken": "github_summarize_pr_fetch_failed",
                    "suggestions": ["Check GitHub authentication", "Verify PR exists", "Try again"]
                }
            
            if "error" in pr_details:
                error_msg = pr_details.get('error', 'Unknown error')
                details = pr_details.get('details', '')
                full_error = f"{error_msg}"
                if details:
                    full_error += f" - {details}"
                
                return {
                    "response": f"❌ Failed to fetch PR #{pr_number}. Error: {full_error}",
                    "action_taken": "github_summarize_pr_fetch_failed",
                    "suggestions": ["Check GitHub authentication", "Verify PR exists", "Try again"]
                }
            
            # Get PR files
            pr_files = await github_service.get_pull_request_files(owner, repo, pr_number)
            if not pr_files or "error" in pr_files:
                pr_files = []
            
            # Get PR comments
            pr_comments = await github_service.get_pull_request_comments(owner, repo, pr_number)
            if not pr_comments or "error" in pr_comments:
                pr_comments = []
            
            # Build summary
            title = pr_details.get("title", "No title")
            body = pr_details.get("body") or ""  # Handle None case
            state = pr_details.get("state", "unknown")
            created_at = pr_details.get("created_at", "")
            updated_at = pr_details.get("updated_at", "")
            additions = pr_details.get("additions", 0)
            deletions = pr_details.get("deletions", 0)
            changed_files = len(pr_files)
            comment_count = len(pr_comments)
            
            # Format dates
            from datetime import datetime
            try:
                created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M UTC')
                updated_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M UTC')
            except:
                created_date = created_at
                updated_date = updated_at
            
            # Generate summary using AI
            summary_prompt = f"""
            Please provide a concise summary of this GitHub Pull Request:
            
            Title: {title}
            State: {state}
            Created: {created_date}
            Updated: {updated_date}
            Changes: +{additions} -{deletions} lines in {changed_files} files
            Comments: {comment_count}
            
            Description:
            {body[:500]}{'...' if len(body) > 500 else ''}
            
            Please provide:
            1. A brief overview of what this PR does
            2. Key changes made
            3. Any important notes or concerns
            4. Overall assessment (ready for review, needs work, etc.)
            """
            
            # Use the current AI model to generate summary
            model_info = self.get_current_model_info()
            
            # Use the appropriate AI provider based on current configuration
            current_provider = settings.ai_provider
            if current_provider == "ollama":
                summary = await self._generate_ollama_response(summary_prompt)
            elif current_provider == "granite":
                summary = await self._generate_granite_response(summary_prompt)
            elif current_provider == "gemini":
                summary = await self._generate_gemini_response(summary_prompt)
            elif current_provider == "openai":
                summary = await self._generate_openai_response(summary_prompt)
            else:
                # Default to Ollama
                summary = await self._generate_ollama_response(summary_prompt)
            
            response_parts = [
                f"📋 **PR #{pr_number} Summary** ({model_info})",
                f"**Repository:** {owner}/{repo}",
                f"**Title:** {title}",
                f"**State:** {state.upper()}",
                f"**Created:** {created_date}",
                f"**Updated:** {updated_date}",
                f"**Changes:** +{additions} -{deletions} lines in {changed_files} files",
                f"**Comments:** {comment_count}",
                "",
                "**Summary:**",
                summary,
                "",
                f"🔗 **PR URL:** {pr_details.get('html_url', '')}"
            ]
            
            return {
                "response": "<br>".join(response_parts),
                "action_taken": "github_summarize_pr_success",
                "data": {
                    "pr_details": pr_details,
                    "files": pr_files,
                    "comments": pr_comments,
                    "summary": summary
                },
                "suggestions": [
                    "Review PR changes",
                    "Add comment",
                    "Approve/request changes",
                    "List all PRs"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error handling GitHub PR summarization: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                "response": "❌ I encountered an error while summarizing the PR. Please check your GitHub authentication and try again.",
                "action_taken": "github_summarize_pr_error",
                "suggestions": ["Check GitHub authentication", "Try again", "Verify PR URL"]
            }

    async def _handle_github_approve_pr(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle GitHub PR approval (LGTM, approve, etc.)"""
        try:
            from app.services.github_service import github_service
            
            # Check if GitHub token is available
            token = github_service._get_token()
            if not token:
                return {
                    "response": "🔑 **GitHub Authentication Required**<br><br>GitHub token is not configured. Please set up GitHub authentication to use PR features.",
                    "action_taken": "github_auth_required",
                    "suggestions": ["Configure GitHub token", "Check credentials", "Set up authentication"]
                }
            
            # Extract PR URL from message
            import re
            github_url_pattern = r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)'
            match = re.search(github_url_pattern, message)
            
            if not match:
                return {
                    "response": "🔗 **GitHub PR Approval**<br><br>I need a GitHub PR URL to approve.<br><br>**Example:** `approve https://github.com/owner/repo/pull/123`",
                    "action_taken": "github_approve_pr_no_url",
                    "suggestions": ["Provide PR URL", "Use format: approve https://github.com/owner/repo/pull/123"]
                }
            
            owner, repo, pr_number = match.groups()
            pr_number = int(pr_number)
            
            # Determine approval message based on keywords in the message
            message_lower = message.lower()
            if "lgtm" in message_lower or "looks good" in message_lower:
                approval_message = "LGTM"
            elif "approve" in message_lower:
                approval_message = "Approved"
            else:
                approval_message = "LGTM"
            
            # Approve the PR
            result = await github_service.approve_pull_request(owner, repo, pr_number, approval_message)
            
            if "error" in result:
                return {
                    "response": f"❌ Failed to approve PR #{pr_number}. Error: {result['error']}",
                    "action_taken": "github_approve_pr_failed",
                    "suggestions": ["Check permissions", "Try again", "Verify PR exists"]
                }
            else:
                return {
                    "response": f"✅ Successfully approved PR #{pr_number} in {owner}/{repo}<br><br>**Message:** {approval_message}",
                    "action_taken": "github_approve_pr_success",
                    "data": result,
                    "suggestions": ["Add LGTM label", "Review other PRs", "List open PRs"]
                }
                
        except Exception as e:
            logger.error(f"Error handling GitHub PR approval: {e}")
            return {
                "response": "❌ I encountered an error while approving the PR. Please check your GitHub authentication and try again.",
                "action_taken": "github_approve_pr_error",
                "suggestions": ["Check GitHub authentication", "Try again", "Verify PR URL"]
            }
    
    async def _handle_github_add_labels(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle adding labels to GitHub PRs"""
        try:
            from app.services.github_service import github_service
            
            # Check if GitHub token is available
            token = github_service._get_token()
            if not token:
                return {
                    "response": "🔑 **GitHub Authentication Required**<br><br>GitHub token is not configured. Please set up GitHub authentication to use PR features.",
                    "action_taken": "github_auth_required",
                    "suggestions": ["Configure GitHub token", "Check credentials", "Set up authentication"]
                }
            
            # Extract PR URL from message
            import re
            github_url_pattern = r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)'
            match = re.search(github_url_pattern, message)
            
            if not match:
                return {
                    "response": "🔗 **GitHub PR Labels**<br><br>I need a GitHub PR URL to add labels.<br><br>**Example:** `add label lgtm https://github.com/owner/repo/pull/123`",
                    "action_taken": "github_add_labels_no_url",
                    "suggestions": ["Provide PR URL", "Use format: add label <label> https://github.com/owner/repo/pull/123"]
                }
            
            owner, repo, pr_number = match.groups()
            pr_number = int(pr_number)
            
            # Extract labels from message
            message_lower = message.lower()
            labels = []
            
            # Common label patterns
            if "lgtm" in message_lower:
                labels.append("lgtm")
            if "approved" in message_lower:
                labels.append("approved")
            if "bug" in message_lower:
                labels.append("bug")
            if "enhancement" in message_lower or "feature" in message_lower:
                labels.append("enhancement")
            if "documentation" in message_lower or "docs" in message_lower:
                labels.append("documentation")
            if "help wanted" in message_lower or "help-wanted" in message_lower:
                labels.append("help wanted")
            if "good first issue" in message_lower or "good-first-issue" in message_lower:
                labels.append("good first issue")
            if "wip" in message_lower or "work in progress" in message_lower:
                labels.append("WIP")
            
            # If no specific labels found, try to extract from the message
            if not labels:
                # Look for quoted or specific label names
                label_pattern = r'["\']([^"\']+)["\']'
                label_matches = re.findall(label_pattern, message)
                if label_matches:
                    labels.extend(label_matches)
                else:
                    # Try to extract single words that might be labels
                    words = message.split()
                    for word in words:
                        if word.lower() not in ['add', 'label', 'labels', 'to', 'the', 'pr', 'pull', 'request', 'https', 'github', 'com']:
                            labels.append(word.lower())
            
            if not labels:
                return {
                    "response": f"🏷️ **GitHub PR Labels**<br><br>I need to know which labels to add to PR #{pr_number}.<br><br>**Example:** `add label lgtm https://github.com/{owner}/{repo}/pull/{pr_number}`<br><br>**Common labels:** lgtm, approved, bug, enhancement, documentation, help wanted, WIP",
                    "action_taken": "github_add_labels_no_labels",
                    "suggestions": ["Add lgtm label", "Add approved label", "Add bug label"]
                }
            
            # Add labels to the PR
            result = await github_service.add_labels_to_issue(owner, repo, pr_number, labels)
            
            if "error" in result:
                return {
                    "response": f"❌ Failed to add labels to PR #{pr_number}. Error: {result['error']}",
                    "action_taken": "github_add_labels_failed",
                    "suggestions": ["Check permissions", "Try again", "Verify PR exists"]
                }
            else:
                labels_text = ", ".join(labels)
                return {
                    "response": f"✅ Successfully added labels to PR #{pr_number} in {owner}/{repo}<br><br>**Labels added:** {labels_text}",
                    "action_taken": "github_add_labels_success",
                    "data": result,
                    "suggestions": ["Add more labels", "Review PR", "Approve PR"]
                }
                
        except Exception as e:
            logger.error(f"Error handling GitHub PR labels: {e}")
            return {
                "response": "❌ I encountered an error while adding labels to the PR. Please check your GitHub authentication and try again.",
                "action_taken": "github_add_labels_error",
                "suggestions": ["Check GitHub authentication", "Try again", "Verify PR URL"]
            }

# Create global AI agent instance
ai_agent = AIAgent()
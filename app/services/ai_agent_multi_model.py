import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import openai
from enum import Enum

from app.core.config import settings
from app.api.auth import get_google_credentials

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
    import requests
except ImportError:
    requests = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    import anthropic
except ImportError:
    anthropic = None

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Available AI model types"""
    OPENAI_GPT = "openai_gpt"
    GRANITE = "granite"
    OLLAMA = "ollama"
    GEMINI = "gemini"
    CLAUDE = "claude"  # Future support
    CUSTOM = "custom"

class TaskComplexity(Enum):
    """Task complexity levels"""
    SIMPLE = "simple"      # Basic queries, simple commands
    MEDIUM = "medium"      # Email composition, calendar scheduling
    COMPLEX = "complex"    # Multi-step workflows, analysis
    CREATIVE = "creative"  # Content generation, brainstorming

class MultiModelAIAgent:
    """Enhanced AI Agent with intelligent multi-model support"""
    
    def __init__(self):
        self.conversation_history = []
        self.context = {}
        self.last_interaction = None
        
        # Model instances
        self.models = {}
        self.model_configs = {}
        
        # Initialize all available models
        self._initialize_all_models()
        
        # Define task-to-model mapping
        self._setup_task_routing()
        
        # Define capabilities
        self.capabilities = {
            "email": ["read_emails", "send_email", "search_emails", "mark_read", "delete_email"],
            "calendar": ["get_events", "create_event", "update_event", "delete_event"],
            "contacts": ["get_contacts", "create_contact", "update_contact", "search_contacts"],
            "slack": ["get_channels", "send_message", "get_messages", "search_messages"],
            "voice": ["speech_to_text", "text_to_speech"],
            "general": ["answer_questions", "provide_suggestions", "execute_workflows"],
            "analysis": ["data_analysis", "text_analysis", "summarization"],
            "creative": ["content_generation", "brainstorming", "writing_assistance"]
        }

    def _initialize_all_models(self):
        """Initialize all available AI models"""
        logger.info("Initializing multi-model AI agent...")
        
        # Initialize OpenAI
        self._init_openai()
        
        # Initialize Granite
        self._init_granite()
        
        # Initialize Ollama
        self._init_ollama()
        
        # Initialize Gemini
        self._init_gemini()
        
        # Initialize Claude
        self._init_claude()
        
        logger.info(f"Initialized models: {list(self.models.keys())}")

    def _init_openai(self):
        """Initialize OpenAI models"""
        try:
            if settings.openai_api_key:
                openai.api_key = settings.openai_api_key
                self.models[ModelType.OPENAI_GPT] = "initialized"
                self.model_configs[ModelType.OPENAI_GPT] = {
                    "model": settings.openai_model or "gpt-3.5-turbo",
                    "max_tokens": 150,
                    "temperature": 0.7,
                    "strengths": ["general_conversation", "reasoning", "code_generation"],
                    "best_for": ["email_composition", "scheduling", "complex_queries"]
                }
                logger.info("OpenAI model initialized")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")

    def _init_granite(self):
        """Initialize IBM Granite models"""
        try:
            if AutoTokenizer and AutoModelForCausalLM:
                model_name = settings.granite_model or "ibm/granite-3.3-8b-instruct"
                self.model_configs[ModelType.GRANITE] = {
                    "model_name": model_name,
                    "tokenizer": None,
                    "model": None,
                    "strengths": ["task_automation", "structured_data", "enterprise_tasks"],
                    "best_for": ["calendar_management", "contact_operations", "data_processing"]
                }
                
                # Load model lazily for better startup performance
                logger.info(f"Granite model configured: {model_name}")
                self.models[ModelType.GRANITE] = "configured"
        except Exception as e:
            logger.error(f"Failed to configure Granite: {e}")

    def _init_ollama(self):
        """Initialize Ollama models"""
        try:
            if ollama:
                model_name = settings.ollama_model or "llama2"
                self.models[ModelType.OLLAMA] = "initialized"
                self.model_configs[ModelType.OLLAMA] = {
                    "model": model_name,
                    "host": settings.ollama_base_url or "http://localhost:11434",
                    "strengths": ["local_processing", "privacy", "customization"],
                    "best_for": ["sensitive_data", "offline_processing", "lightweight_tasks"]
                }
                logger.info(f"Ollama model initialized: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama: {e}")

    def _init_gemini(self):
        """Initialize Google Gemini models"""
        try:
            if genai and settings.gemini_api_key:
                genai.configure(api_key=settings.gemini_api_key)
                model_name = settings.gemini_model or "gemini-1.5-pro"
                self.models[ModelType.GEMINI] = genai.GenerativeModel(model_name)
                self.model_configs[ModelType.GEMINI] = {
                    "model": model_name,
                    "temperature": 0.7,
                    "max_output_tokens": 8192,
                    "strengths": ["multimodal", "reasoning", "analysis", "conversation"],
                    "best_for": ["complex_analysis", "creative_tasks", "multimodal_processing", "general_chat"]
                }
                logger.info(f"Gemini model initialized: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")

    def _init_claude(self):
        """Initialize Anthropic Claude models"""
        try:
            if anthropic and settings.claude_api_key:
                self.models[ModelType.CLAUDE] = anthropic.Anthropic(api_key=settings.claude_api_key)
                model_name = settings.claude_model or "claude-3-5-sonnet-20241022"
                self.model_configs[ModelType.CLAUDE] = {
                    "model": model_name,
                    "temperature": 0.7,
                    "max_tokens": 8192,
                    "strengths": ["code_review", "reasoning", "analysis", "technical_writing", "complex_problem_solving"],
                    "best_for": ["code_analysis", "pr_review", "technical_documentation", "debugging", "software_architecture"]
                }
                logger.info(f"Claude model initialized: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Claude: {e}")

    def _setup_task_routing(self):
        """Setup intelligent task routing to optimal models"""
        self.task_routing = {
            # Simple tasks - use fastest/cheapest model
            "greeting": [ModelType.OLLAMA, ModelType.GEMINI, ModelType.OPENAI_GPT, ModelType.GRANITE, ModelType.CLAUDE],
            "simple_query": [ModelType.OLLAMA, ModelType.GEMINI, ModelType.OPENAI_GPT, ModelType.GRANITE, ModelType.CLAUDE],
            "quick_answer": [ModelType.OLLAMA, ModelType.GEMINI, ModelType.OPENAI_GPT, ModelType.GRANITE, ModelType.CLAUDE],
            
            # Code review and analysis tasks - prioritize local code models
            "code_review": [ModelType.OLLAMA, ModelType.CLAUDE, ModelType.GEMINI, ModelType.OPENAI_GPT, ModelType.GRANITE],
            "code_analysis": [ModelType.OLLAMA, ModelType.CLAUDE, ModelType.GEMINI, ModelType.OPENAI_GPT, ModelType.GRANITE],
            "pr_review": [ModelType.OLLAMA, ModelType.CLAUDE, ModelType.GEMINI, ModelType.OPENAI_GPT, ModelType.GRANITE],
            "debugging": [ModelType.OLLAMA, ModelType.CLAUDE, ModelType.GEMINI, ModelType.OPENAI_GPT, ModelType.GRANITE],
            "technical_writing": [ModelType.OLLAMA, ModelType.CLAUDE, ModelType.GEMINI, ModelType.OPENAI_GPT, ModelType.GRANITE],
            
            # Cluster and infrastructure analysis - prioritize local models for security
            "cluster_analysis": [ModelType.OLLAMA, ModelType.CLAUDE, ModelType.GEMINI, ModelType.OPENAI_GPT, ModelType.GRANITE],
            "must_gather_analysis": [ModelType.OLLAMA, ModelType.CLAUDE, ModelType.GEMINI, ModelType.OPENAI_GPT, ModelType.GRANITE],
            "infrastructure_troubleshooting": [ModelType.OLLAMA, ModelType.CLAUDE, ModelType.GEMINI, ModelType.OPENAI_GPT, ModelType.GRANITE],
            "log_analysis": [ModelType.OLLAMA, ModelType.CLAUDE, ModelType.GEMINI, ModelType.OPENAI_GPT, ModelType.GRANITE],
            
            # Email tasks - use models good at language generation
            "email_compose": [ModelType.GEMINI, ModelType.CLAUDE, ModelType.OPENAI_GPT, ModelType.GRANITE, ModelType.OLLAMA],
            "email_analysis": [ModelType.GEMINI, ModelType.CLAUDE, ModelType.OPENAI_GPT, ModelType.GRANITE, ModelType.OLLAMA],
            
            # Calendar tasks - use structured data models
            "calendar_scheduling": [ModelType.GRANITE, ModelType.CLAUDE, ModelType.GEMINI, ModelType.OPENAI_GPT, ModelType.OLLAMA],
            "date_parsing": [ModelType.GRANITE, ModelType.CLAUDE, ModelType.GEMINI, ModelType.OPENAI_GPT, ModelType.OLLAMA],
            
            # Complex analysis - use most capable models
            "data_analysis": [ModelType.GEMINI, ModelType.CLAUDE, ModelType.OPENAI_GPT, ModelType.GRANITE, ModelType.OLLAMA],
            "summarization": [ModelType.GEMINI, ModelType.CLAUDE, ModelType.OPENAI_GPT, ModelType.GRANITE, ModelType.OLLAMA],
            
            # Creative tasks - use creative models
            "content_generation": [ModelType.GEMINI, ModelType.CLAUDE, ModelType.OPENAI_GPT, ModelType.OLLAMA, ModelType.GRANITE],
            "brainstorming": [ModelType.GEMINI, ModelType.CLAUDE, ModelType.OPENAI_GPT, ModelType.OLLAMA, ModelType.GRANITE],
            
            # Multimodal tasks - prioritize Gemini
            "image_analysis": [ModelType.GEMINI, ModelType.OPENAI_GPT, ModelType.CLAUDE],
            "multimodal": [ModelType.GEMINI, ModelType.OPENAI_GPT, ModelType.CLAUDE],
            
            # Default fallback
            "general": [ModelType.GEMINI, ModelType.CLAUDE, ModelType.OPENAI_GPT, ModelType.GRANITE, ModelType.OLLAMA]
        }

    async def _load_granite_model(self):
        """Lazy load Granite model when needed"""
        if ModelType.GRANITE in self.model_configs and self.model_configs[ModelType.GRANITE]["model"] is None:
            try:
                config = self.model_configs[ModelType.GRANITE]
                config["tokenizer"] = AutoTokenizer.from_pretrained(config["model_name"])
                config["model"] = AutoModelForCausalLM.from_pretrained(
                    config["model_name"],
                    torch_dtype=torch.float16 if torch and torch.cuda.is_available() else None,
                    device_map="auto" if torch and torch.cuda.is_available() else None
                )
                self.models[ModelType.GRANITE] = "loaded"
                logger.info(f"Loaded Granite model: {config['model_name']}")
            except Exception as e:
                logger.error(f"Failed to load Granite model: {e}")
                return False
        return True

    async def select_optimal_model(self, task_type: str, complexity: TaskComplexity = TaskComplexity.MEDIUM, 
                                   user_preference: Optional[ModelType] = None) -> ModelType:
        """Select the optimal model for a given task"""
        
        # Honor user preference if specified and available
        if user_preference and user_preference in self.models:
            return user_preference
        
        # Get preferred models for task type
        preferred_models = self.task_routing.get(task_type, self.task_routing["general"])
        
        # Filter by available models
        available_models = [model for model in preferred_models if model in self.models]
        
        if not available_models:
            # Fallback to any available model
            available_models = list(self.models.keys())
        
        if not available_models:
            raise Exception("No AI models available")
        
        # Select based on complexity and availability
        if complexity == TaskComplexity.COMPLEX and ModelType.OPENAI_GPT in available_models:
            return ModelType.OPENAI_GPT
        elif complexity == TaskComplexity.SIMPLE and ModelType.OLLAMA in available_models:
            return ModelType.OLLAMA
        else:
            return available_models[0]

    async def generate_response_with_model(self, message: str, model_type: ModelType, 
                                           context: Optional[Dict] = None) -> str:
        """Generate response using specified model"""
        
        try:
            if model_type == ModelType.OPENAI_GPT:
                return await self._generate_openai_response(message, context)
            elif model_type == ModelType.GRANITE:
                return await self._generate_granite_response(message, context)
            elif model_type == ModelType.OLLAMA:
                return await self._generate_ollama_response(message, context)
            elif model_type == ModelType.GEMINI:
                return await self._generate_gemini_response(message, context)
            elif model_type == ModelType.CLAUDE:
                return await self._generate_claude_response(message, context)
            else:
                return "Unsupported model type"
                
        except Exception as e:
            logger.error(f"Error generating response with {model_type}: {e}")
            return f"I encountered an error with the {model_type.value} model. Let me try another approach."

    async def _generate_openai_response(self, message: str, context: Optional[Dict] = None) -> str:
        """Generate response using OpenAI"""
        try:
            config = self.model_configs[ModelType.OPENAI_GPT]
            
            # Build context-aware prompt
            system_prompt = self._build_system_prompt(context)
            
            response = await openai.ChatCompletion.acreate(
                model=config["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=config["max_tokens"],
                temperature=config["temperature"]
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    async def _generate_granite_response(self, message: str, context: Optional[Dict] = None) -> str:
        """Generate response using Granite"""
        try:
            # Ensure model is loaded
            if not await self._load_granite_model():
                raise Exception("Granite model not available")
            
            config = self.model_configs[ModelType.GRANITE]
            tokenizer = config["tokenizer"]
            model = config["model"]
            
            # Build context-aware prompt
            system_prompt = self._build_system_prompt(context)
            prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{message}\n<|assistant|>\n"
            
            # Tokenize and generate
            inputs = tokenizer(prompt, return_tensors="pt")
            if torch and torch.cuda.is_available():
                inputs = inputs.to("cuda")
            
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=200,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )
            
            # Decode response
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the assistant's response
            if "<|assistant|>" in response:
                response = response.split("<|assistant|>")[-1].strip()
            
            return response
            
        except Exception as e:
            logger.error(f"Granite generation error: {e}")
            raise

    async def _generate_ollama_response(self, message: str, context: Optional[Dict] = None) -> str:
        """Generate response using Ollama"""
        try:
            config = self.model_configs[ModelType.OLLAMA]
            
            # Build context-aware prompt
            system_prompt = self._build_system_prompt(context)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
            
            # Select best local model based on context
            model_name = self._select_best_ollama_model(message, context)
            logger.info(f"Using Ollama model: {model_name} for generation")
            
            # Add timeout to prevent hanging
            import asyncio
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        ollama.chat,
                        model=model_name,
                        messages=messages
                    ),
                    timeout=45.0  # 45 second timeout for code models
                )
                return response['message']['content']
            except asyncio.TimeoutError:
                logger.error(f"Ollama request timed out after 45 seconds with model {model_name}")
                # Try fallback model
                fallback_model = settings.ollama_fallback_model
                logger.info(f"Retrying with fallback model: {fallback_model}")
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        ollama.chat,
                        model=fallback_model,
                        messages=messages
                    ),
                    timeout=30.0
                )
                return response['message']['content']
            
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise

    def _select_best_ollama_model(self, message: str, context: Optional[Dict] = None) -> str:
        """Select the best local Ollama model based on the task"""
        
        # Check context for task type hints
        task_type = None
        if context:
            task_type = context.get('task_type', '').lower()
        
        # Analyze message content for code-related and cluster-related keywords
        code_keywords = ['code', 'function', 'class', 'bug', 'review', 'programming', 
                        'syntax', 'algorithm', 'debug', 'refactor', 'api', 'error',
                        'pull request', 'pr', 'commit', 'repository', 'file', 'line']
        
        cluster_keywords = ['cluster', 'openshift', 'kubernetes', 'must-gather', 'etcd', 
                           'nodes', 'pods', 'operators', 'namespace', 'deployment', 
                           'logs', 'troubleshoot', 'analyze', 'infrastructure', 'sre']
        
        message_lower = message.lower()
        has_code_context = any(keyword in message_lower for keyword in code_keywords)
        has_cluster_context = any(keyword in message_lower for keyword in cluster_keywords)
        
        # Model selection logic
        if (task_type in ['code_review', 'pr_review', 'code_analysis', 'debugging'] or has_code_context) and not has_cluster_context:
            # Use specialized code models for code-related tasks
            available_models = [
                "codeqwen:7b",           # Best for code review and analysis
                "deepseek-coder:6.7b",   # Strong code understanding  
                "codellama:13b",         # Good reasoning for complex code
                settings.ollama_code_model  # Configured code model
            ]
        elif task_type in ['cluster_analysis', 'must_gather_analysis', 'infrastructure_troubleshooting', 'log_analysis'] or has_cluster_context:
            # Use models optimized for cluster/infrastructure analysis
            available_models = [
                "granite3.3-balanced-enhanced:latest",  # Best for structured analysis
                "codeqwen:7b",                          # Good at log analysis  
                "deepseek-coder:6.7b",                  # Strong technical understanding
                "granite3.3-assistant:latest",          # General technical assistant
                settings.ollama_code_model              # Configured model
            ]
        else:
            # Use general models for non-code tasks  
            available_models = [
                "granite3.3-balanced-enhanced:latest",  # Enhanced general model
                "granite3.3-assistant:latest",          # General assistant
                "mistral:latest",                       # Good general model
                settings.ollama_model                   # Default model
            ]
        
        # Return first available model (they're ordered by preference)
        for model in available_models:
            try:
                # Quick check if model exists (this could be enhanced with actual model listing)
                return model
            except:
                continue
                
        # Final fallback
        return settings.ollama_model

    async def _generate_gemini_response(self, message: str, context: Optional[Dict] = None) -> str:
        """Generate response using Google Gemini"""
        try:
            if ModelType.GEMINI not in self.models:
                raise Exception("Gemini model not available")
            
            model = self.models[ModelType.GEMINI]
            config = self.model_configs[ModelType.GEMINI]
            
            # Build context-aware prompt
            system_prompt = self._build_system_prompt(context)
            full_prompt = f"{system_prompt}\n\nUser: {message}\nAssistant:"
            
            # Generate response
            response = await asyncio.to_thread(
                model.generate_content,
                full_prompt,
                generation_config={
                    "temperature": config["temperature"],
                    "max_output_tokens": config["max_output_tokens"],
                }
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise

    async def _generate_claude_response(self, message: str, context: Optional[Dict] = None) -> str:
        """Generate response using Anthropic Claude"""
        try:
            if ModelType.CLAUDE not in self.models:
                raise Exception("Claude model not available")
            
            client = self.models[ModelType.CLAUDE]
            config = self.model_configs[ModelType.CLAUDE]
            
            # Build context-aware prompt
            system_prompt = self._build_system_prompt(context)
            
            # Generate response using Claude's messages API
            response = await asyncio.to_thread(
                client.messages.create,
                model=config["model"],
                max_tokens=config["max_tokens"],
                temperature=config["temperature"],
                system=system_prompt,
                messages=[
                    {"role": "user", "content": message}
                ]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Claude generation error: {e}")
            raise

    async def generate_ensemble_response(self, message: str, models: List[ModelType], 
                                         context: Optional[Dict] = None) -> Dict[str, Any]:
        """Generate responses from multiple models and combine them"""
        responses = {}
        
        # Generate responses from each model
        for model_type in models:
            if model_type in self.models:
                try:
                    response = await self.generate_response_with_model(message, model_type, context)
                    responses[model_type.value] = response
                except Exception as e:
                    logger.error(f"Failed to get response from {model_type}: {e}")
                    responses[model_type.value] = f"Error: {str(e)}"
        
        # Analyze and combine responses
        best_response = self._select_best_response(responses, message)
        
        return {
            "primary_response": best_response,
            "all_responses": responses,
            "model_used": self._get_best_model(responses),
            "confidence": self._calculate_confidence(responses)
        }

    def _build_system_prompt(self, context: Optional[Dict] = None) -> str:
        """Build context-aware system prompt"""
        base_prompt = """You are an AI assistant helping with productivity tasks including email management, 
        calendar scheduling, contact management, and Slack communications. Provide helpful, accurate, and 
        concise responses."""
        
        if context:
            if context.get("task_type"):
                base_prompt += f"\nCurrent task: {context['task_type']}"
            if context.get("user_preferences"):
                base_prompt += f"\nUser preferences: {context['user_preferences']}"
            if context.get("conversation_history"):
                base_prompt += f"\nRecent context: {context['conversation_history'][-3:]}"
        
        return base_prompt

    def _select_best_response(self, responses: Dict[str, str], original_message: str) -> str:
        """Select the best response from multiple model outputs"""
        if not responses:
            return "I'm sorry, I couldn't generate a response."
        
        # Simple heuristic: prefer non-error responses, then by length and relevance
        valid_responses = {k: v for k, v in responses.items() if not v.startswith("Error:")}
        
        if not valid_responses:
            return list(responses.values())[0]  # Return first response even if error
        
        # Return the first valid response (could be enhanced with more sophisticated selection)
        return list(valid_responses.values())[0]

    def _get_best_model(self, responses: Dict[str, str]) -> str:
        """Determine which model provided the best response"""
        valid_responses = {k: v for k, v in responses.items() if not v.startswith("Error:")}
        return list(valid_responses.keys())[0] if valid_responses else list(responses.keys())[0]

    def _calculate_confidence(self, responses: Dict[str, str]) -> float:
        """Calculate confidence score based on response quality"""
        valid_count = len([r for r in responses.values() if not r.startswith("Error:")])
        total_count = len(responses)
        return (valid_count / total_count) if total_count > 0 else 0.0

    async def process_message_smart(self, message: str, context: Optional[Dict] = None, 
                                    user_model_preference: Optional[str] = None,
                                    use_ensemble: bool = False) -> Dict[str, Any]:
        """Process message with intelligent model selection"""
        
        # Update context
        if context:
            self.context.update(context)
        
        # Add to conversation history
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": "user",
            "content": message
        })
        self.last_interaction = datetime.now()
        
        # Analyze intent and complexity
        intent_analysis = await self.analyze_intent(message)
        task_type = intent_analysis.get("intent", "general")
        complexity = self._determine_complexity(message, intent_analysis)
        
        # Convert user preference to ModelType
        model_preference = None
        if user_model_preference:
            try:
                model_preference = ModelType(user_model_preference.lower())
            except ValueError:
                logger.warning(f"Invalid model preference: {user_model_preference}")
        
        try:
            if use_ensemble:
                # Use multiple models
                available_models = list(self.models.keys())[:3]  # Use up to 3 models
                result = await self.generate_ensemble_response(message, available_models, self.context)
                response_text = result["primary_response"]
                model_used = result["model_used"]
                
            else:
                # Use single optimal model
                optimal_model = await self.select_optimal_model(task_type, complexity, model_preference)
                response_text = await self.generate_response_with_model(message, optimal_model, self.context)
                model_used = optimal_model.value
                result = {"confidence": 1.0}
            
            # Add to conversation history
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "type": "assistant",
                "content": response_text,
                "model_used": model_used,
                "task_type": task_type
            })
            
            return {
                "response": response_text,
                "intent": task_type,
                "model_used": model_used,
                "complexity": complexity.value,
                "confidence": result.get("confidence", 1.0),
                "entities": intent_analysis.get("entities", {}),
                "all_responses": result.get("all_responses", {}),
                "suggestions": await self.get_suggestions(task_type)
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            
            # Fallback to any available model
            fallback_models = list(self.models.keys())
            if fallback_models:
                try:
                    fallback_response = await self.generate_response_with_model(
                        message, fallback_models[0], self.context
                    )
                    return {
                        "response": fallback_response,
                        "intent": task_type,
                        "model_used": fallback_models[0].value,
                        "complexity": complexity.value,
                        "confidence": 0.5,
                        "error": str(e)
                    }
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
            
            return {
                "response": "I'm sorry, I'm having trouble processing your request right now. Please try again later.",
                "intent": task_type,
                "model_used": "none",
                "complexity": complexity.value,
                "confidence": 0.0,
                "error": str(e)
            }

    def _determine_complexity(self, message: str, intent_analysis: Dict) -> TaskComplexity:
        """Determine task complexity based on message and intent"""
        
        # Simple heuristics for complexity detection
        message_lower = message.lower()
        
        # Creative tasks
        if any(word in message_lower for word in ["write", "create", "generate", "brainstorm", "compose"]):
            return TaskComplexity.CREATIVE
        
        # Complex tasks
        if any(word in message_lower for word in ["analyze", "summarize", "compare", "workflow", "multiple"]):
            return TaskComplexity.COMPLEX
        
        # Medium tasks
        if any(word in message_lower for word in ["schedule", "email", "meeting", "remind", "update"]):
            return TaskComplexity.MEDIUM
        
        # Simple tasks (greetings, basic queries)
        if any(word in message_lower for word in ["hello", "hi", "what", "when", "who", "help"]):
            return TaskComplexity.SIMPLE
        
        # Default to medium
        return TaskComplexity.MEDIUM

    async def analyze_intent(self, message: str) -> Dict[str, Any]:
        """Analyze user intent - enhanced version of the original method"""
        message_lower = message.lower()
        
        # Email intent patterns
        if any(word in message_lower for word in ["email", "mail", "send", "inbox", "compose"]):
            intent = "email"
        # Calendar intent patterns
        elif any(word in message_lower for word in ["calendar", "schedule", "meeting", "appointment", "event"]):
            intent = "calendar"
        # Contacts intent patterns
        elif any(word in message_lower for word in ["contact", "phone", "address", "person"]):
            intent = "contacts"
        # Slack intent patterns
        elif any(word in message_lower for word in ["slack", "channel", "message", "team"]):
            intent = "slack"
        # Analysis tasks
        elif any(word in message_lower for word in ["analyze", "summarize", "report", "data"]):
            intent = "analysis"
        # Creative tasks
        elif any(word in message_lower for word in ["write", "create", "generate", "brainstorm"]):
            intent = "creative"
        else:
            intent = "general"
        
        # Extract entities (simplified)
        entities = {}
        
        # Date/time entities
        import re
        date_patterns = r'\b(today|tomorrow|next week|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b'
        dates = re.findall(date_patterns, message_lower)
        if dates:
            entities['dates'] = dates
        
        # Email entities
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, message)
        if emails:
            entities['emails'] = emails
        
        return {
            "intent": intent,
            "entities": entities,
            "confidence": 0.8  # Simplified confidence score
        }

    async def get_suggestions(self, task_type: str) -> List[str]:
        """Get contextual suggestions based on task type"""
        suggestions_map = {
            "email": [
                "Check unread emails",
                "Compose a new email",
                "Search for specific emails",
                "Set email reminders"
            ],
            "calendar": [
                "View today's schedule",
                "Schedule a new meeting",
                "Check availability",
                "Set calendar reminders"
            ],
            "contacts": [
                "Find a contact",
                "Add new contact",
                "Update contact information",
                "Export contacts"
            ],
            "slack": [
                "Check team channels",
                "Send a message",
                "Search conversations",
                "View recent updates"
            ],
            "general": [
                "Try asking about emails",
                "Schedule a meeting",
                "Find a contact",
                "Check your calendar"
            ]
        }
        
        return suggestions_map.get(task_type, suggestions_map["general"])

    def get_available_models(self) -> Dict[str, Dict]:
        """Get information about available models"""
        available = {}
        for model_type, status in self.models.items():
            config = self.model_configs.get(model_type, {})
            available[model_type.value] = {
                "status": status,
                "strengths": config.get("strengths", []),
                "best_for": config.get("best_for", []),
                "model_name": config.get("model", config.get("model_name", "unknown"))
            }
        return available

    async def benchmark_models(self, test_queries: List[str]) -> Dict[str, Dict]:
        """Benchmark different models with test queries"""
        results = {}
        
        for model_type in self.models.keys():
            model_results = []
            for query in test_queries:
                start_time = datetime.now()
                try:
                    response = await self.generate_response_with_model(query, model_type)
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    
                    model_results.append({
                        "query": query,
                        "response": response[:100] + "..." if len(response) > 100 else response,
                        "duration": duration,
                        "success": True
                    })
                except Exception as e:
                    model_results.append({
                        "query": query,
                        "error": str(e),
                        "success": False
                    })
            
            results[model_type.value] = {
                "results": model_results,
                "avg_duration": sum(r.get("duration", 0) for r in model_results if r.get("success")) / len([r for r in model_results if r.get("success")]) if any(r.get("success") for r in model_results) else 0,
                "success_rate": len([r for r in model_results if r.get("success")]) / len(model_results)
            }
        
        return results 
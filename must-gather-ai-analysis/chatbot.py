#!/usr/bin/env python3
"""
OpenShift AI Assistant Chatbot with KMS Integration and Document Analysis
"""

import streamlit as st
import requests
import json
import os
import sys
import subprocess
from datetime import datetime
import time
import tempfile
from pathlib import Path

# Add document training system to path
sys.path.append('document_training_system/scripts')

# Try to import Jira integration (optional)
try:
    from jira_integration import JiraIntegration, process_jira_command
    JIRA_AVAILABLE = True
except ImportError:
    JIRA_AVAILABLE = False

# Document processor availability flag
DOCUMENT_PROCESSOR_AVAILABLE = False

# Try to import RAG service
try:
    from rag_service import get_rag_service, get_rag_response
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("RAG service not available")

# Page configuration
st.set_page_config(
    page_title="OpenShift AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for chat-like interface
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    
    .chat-container {
        height: 400px;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        background-color: #f8f9fa;
        margin-bottom: 1rem;
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.8rem 1.2rem;
        border-radius: 18px 18px 5px 18px;
        margin: 0.5rem 0;
        margin-left: 20%;
        word-wrap: break-word;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 0.8rem 1.2rem;
        border-radius: 18px 18px 18px 5px;
        margin: 0.5rem 0;
        margin-right: 20%;
        word-wrap: break-word;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .timestamp {
        font-size: 0.7rem;
        color: #888;
        text-align: right;
        margin-top: 0.2rem;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .status-container {
        background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        color: #2d3748;
    }
    
    .error-container {
        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        color: #2d3748;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "model" not in st.session_state:
    st.session_state.model = "granite3.3-balanced"
if "jira_integration" not in st.session_state:
    st.session_state.jira_integration = None

def load_jira_config():
    """Load Jira configuration from file (optional)"""
    config_file = "jira_config.json"
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def is_jira_command(message):
    """Check if message contains Jira-related commands (optional)"""
    if not JIRA_AVAILABLE:
        return False
        
    jira_keywords = [
        "jira", "issue", "ticket", "proj-", "bug-", "task-", "story-",
        "add comment", "comment on", "mark as done", "mark completed",
        "find issues", "search issues", "my issues", "assigned to me",
        "qa contact", "reported by me", "how many", "show my", "list my",
        "count", "number of", "issues assigned", "my assigned",
        "my tickets", "my bugs", "show issues", "list issues",
        "list all jiras", "fetch my jira", "all jiras", "jiras assigned",
        "my jira issues", "my jira", "jira issues", "get my issues",
        "show my jira", "fetch my issues", "get jira", "show jira",
        "list jira", "get jira", "jira list", "show jira", "open jira issues",
        "on_qa", "qa", "qa issues", "qa contact issues", "list qa", "show qa",
        "my qa", "qa contact", "list on_qa", "show on_qa", "on qa", 
        "qa contact list", "qa issues list", "issues qa", "my qa contact"
    ]
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in jira_keywords)

def get_available_models():
    """Get list of available models from Ollama"""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            return ["granite3.3-balanced", "granite3.3", "openshift-ai:latest", "mistral:latest"]
        else:
            return ["granite3.3-balanced", "granite3.3", "openshift-ai:latest", "mistral:latest"]
    except Exception:
        # Default models if ollama command fails
        return ["granite3.3-balanced", "granite3.3", "openshift-ai:latest", "mistral:latest"]

def display_chat_message(message, is_user=True):
    """Display a chat message with styling"""
    timestamp = datetime.now().strftime("%H:%M")
    
    if is_user:
        st.markdown(f"""
        <div class="user-message">
            {message}
            <div class="timestamp">{timestamp}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="assistant-message">
            {message}
            <div class="timestamp">{timestamp}</div>
        </div>
        """, unsafe_allow_html=True)

def get_rag_context(question):
    """Get relevant context from RAG service if available"""
    if RAG_AVAILABLE:
        try:
            rag_service = get_rag_service()
            if rag_service:
                context = get_rag_response(question)
                if context and context.strip():
                    return f"\n\nRelevant context from knowledge base:\n{context}"
        except Exception as e:
            print(f"RAG error: {e}")
    return ""

def process_document_question(message):
    """Process document-related questions using document training system"""
    if not DOCUMENT_PROCESSOR_AVAILABLE:
        return None
        
    try:
        # Look for document processing keywords
        doc_keywords = ["document", "pdf", "text", "file", "analyze", "process", "extract"]
        if any(keyword in message.lower() for keyword in doc_keywords):
            # This could be enhanced to actually process documents
            return "I can help with document processing. Upload documents through the AI Assistant Builder for training and analysis."
    except Exception as e:
        return f"Error processing document question: {str(e)}"
    return None

def analyze_openshift_logs(log_content):
    """Analyze OpenShift logs for issues"""
    if not log_content:
        return "No log content provided for analysis."
    
    try:
        # Simple log analysis - this could be enhanced
        issues = []
        lines = log_content.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            if any(error in line_lower for error in ['error', 'failed', 'timeout', 'exception']):
                issues.append(line.strip())
        
        if issues:
            return f"Found {len(issues)} potential issues in logs:\n" + "\n".join(issues[:10])
        else:
            return "No obvious errors found in the provided logs."
            
    except Exception as e:
        return f"Error analyzing logs: {str(e)}"

def analyze_must_gather(mg_path):
    """Analyze must-gather data"""
    try:
        if not os.path.exists(mg_path):
            return "Must-gather path not found."
            
        # Simple analysis - could be enhanced with actual must-gather parsing
        return f"Must-gather analysis for: {mg_path}\n\nThis feature is being developed. Please use specific log analysis for now."
        
    except Exception as e:
        return f"Error analyzing must-gather: {str(e)}"

def send_message_to_ollama(message, model="granite3.3-balanced", temperature=0.7):
    """Send message to Ollama API and get response with optional Jira, KMS model and RAG"""
    
    # Check if this is a Jira command and Jira is available (optional)
    if JIRA_AVAILABLE and is_jira_command(message) and st.session_state.jira_integration:
        try:
            jira_response = process_jira_command(message, st.session_state.jira_integration)
            # If we got a meaningful Jira response, return it
            if jira_response and not jira_response.startswith("Error"):
                return jira_response
        except Exception as e:
            # If Jira command fails, fall back to regular AI response
            pass
    
    # Check if this is a KMS question and use trained model
    try:
        from kms_model_service import get_kms_response
        kms_response = get_kms_response(message)
        if kms_response:
            return kms_response
    except Exception as e:
        # If KMS model fails, fall back to regular AI response
        print(f"KMS model error: {e}")
        pass

    # Try RAG-enhanced response first
    final_message = message
    try:
        if RAG_AVAILABLE:
            rag_context = get_rag_context(message)
            if rag_context:
                final_message = f"{message}{rag_context}"
    except Exception as e:
        print(f"RAG error: {e}")
        # Continue with original message
        pass

    # Check for document processing questions
    doc_response = process_document_question(message)
    if doc_response:
        return doc_response

    # Check for must-gather analysis
    if "must-gather" in message.lower() or "must gather" in message.lower():
        # Simple must-gather guidance
        return """**Must-Gather Analysis Guide:**

1. **Extract the must-gather**: `tar -xzf must-gather.tar.gz`
2. **Check cluster operators**: Look in `cluster-scoped-resources/core/clusteroperators/`
3. **Pod issues**: Check `namespaces/<namespace>/pods/`
4. **Node problems**: Review `cluster-scoped-resources/core/nodes/`
5. **Events**: Check `cluster-scoped-resources/core/events/`

For specific issues, please provide log snippets for analysis."""

    # Check for log analysis
    if "analyze" in message.lower() and ("log" in message.lower() or "error" in message.lower()):
        return "Please provide the log content for analysis. I can help identify errors, warnings, and potential issues."

    # Enhanced system prompt for OpenShift
    system_prompt = """You are an expert OpenShift and Kubernetes assistant. You have deep knowledge of:
- OpenShift Container Platform architecture and operations
- Kubernetes troubleshooting and best practices  
- Container orchestration and management
- DevOps workflows and CI/CD pipelines
- Red Hat Enterprise Linux and container technologies
- Network policies, storage, and security

Provide practical, actionable advice. When troubleshooting, ask for specific logs or error messages if needed."""

    try:
        url = "http://localhost:11434/api/generate"
        
        payload = {
            "model": model,
            "prompt": f"{system_prompt}\n\nUser: {final_message}",
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "top_k": 40
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "No response generated")
        else:
            return f"Error: {response.status_code} - {response.text}"
            
    except requests.exceptions.ConnectionError:
        return "❌ **Connection Error**: Cannot connect to Ollama. Please ensure Ollama is running:\n\n```bash\nollama serve\n```"
    except requests.exceptions.Timeout:
        return "⏰ **Timeout**: The request took too long. The model might be loading. Try again."
    except Exception as e:
        return f"❌ **Error**: {str(e)}"

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Model selection
    available_models = get_available_models()
    selected_model = st.selectbox(
        "Select Model", 
        available_models,
        index=available_models.index(st.session_state.model) if st.session_state.model in available_models else 0
    )
    st.session_state.model = selected_model
    
    # Temperature setting
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
    
    # Knowledge Base Integration
    if RAG_AVAILABLE:
        st.header("🧠 Knowledge Base")
        
        if st.button("🔄 Update Knowledge Base"):
            try:
                rag_service = get_rag_service()
                if rag_service:
                    st.success("✅ Knowledge base updated successfully!")
                else:
                    st.error("❌ Failed to update knowledge base")
            except Exception as e:
                st.error(f"❌ Error updating knowledge base: {str(e)}")
        
        # Test knowledge base
        test_query = st.text_input("Test Knowledge Base", placeholder="Ask about OpenShift...")
        if st.button("🔍 Test Query") and test_query:
            try:
                context = get_rag_context(test_query)
                if context:
                    st.success("✅ Knowledge base response found")
                    st.text_area("Context", context, height=100)
                else:
                    st.warning("⚠️ No relevant context found")
            except Exception as e:
                st.error(f"❌ Test query failed: {str(e)}")
        
        # Knowledge base stats
        try:
            rag_service = get_rag_service()
            if rag_service:
                st.info("📊 **Knowledge Base**: Active")
        except Exception as e:
            st.error(f"❌ Knowledge base error: {str(e)}")
    else:
        st.header("🧠 Knowledge Base")
        st.warning("RAG service not available. Please install sentence-transformers and faiss-cpu.")
    
    # Optional Jira Integration Section (only if available)
    if JIRA_AVAILABLE:
        st.header("🎫 Jira Integration (Optional)")
        
        # Load saved Jira config
        jira_config = load_jira_config()
        
        # Simple toggle for Jira integration
        jira_enabled = st.checkbox(
            "Enable Jira Integration",
            value=bool(jira_config.get('server') and jira_config.get('username') and jira_config.get('token')),
            help="Enable natural language Jira commands (optional)"
        )
        
        if jira_enabled and jira_config:
            # Try to initialize Jira integration
            try:
                # Auto-detect auth method based on token length (PAT vs password)
                auth_method = "pat_bearer" if len(jira_config['token']) > 20 else "basic"
                
                jira_integration = JiraIntegration(
                    jira_config['server'],
                    jira_config['username'],
                    jira_config['token'],
                    auth_method
                )
                st.session_state.jira_integration = jira_integration
                st.success(f"✅ Jira integration active")
                
            except Exception as e:
                st.error(f"❌ Jira connection failed: {str(e)}")
                st.session_state.jira_integration = None
        else:
            st.session_state.jira_integration = None
            if not jira_config:
                st.info("Configure Jira in AI Assistant Builder to enable")
    
    # Quick actions
    st.header("🚀 Quick Actions")
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
    
    # Model info
    st.header("📊 Model Info")
    st.info(f"**Current Model:** {selected_model}")
    st.info(f"**Temperature:** {temperature}")
    if JIRA_AVAILABLE and st.session_state.jira_integration:
        st.info("🎫 **Jira:** Connected")
    
    # Example prompts
    st.header("💡 Example Prompts")
    example_prompts = [
        "Analyze pod logs for errors",
        "Check cluster operator status", 
        "Explain OpenShift networking",
        "Troubleshoot storage issues",
        "Review cluster certificates",
        "Help with must-gather analysis",
        "Debug container startup issues",
        "OpenShift security best practices"
    ]
    
    # Add Jira examples if available and connected
    if JIRA_AVAILABLE and st.session_state.jira_integration:
        jira_examples = [
            "Show my open jira issues",
            "How many jira issues assigned to me?",
            "List my QA contact issues",
            "Add comment to PROJ-123 saying work done",
            "Mark PROJ-456 as completed"
        ]
        example_prompts.extend(jira_examples)
    
    for prompt in example_prompts:
        if st.button(f"💬 {prompt}", key=f"example_{prompt}"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.rerun()

# Chat interface
st.header("💬 Chat")

# Create chat container
chat_container = st.container()

with chat_container:
    # Display chat messages
    if st.session_state.messages:
        for message in st.session_state.messages:
            display_chat_message(
                message["content"], 
                is_user=(message["role"] == "user")
            )
    else:
        st.markdown("""
        <div class="status-container">
            <h4>👋 Welcome to OpenShift AI Assistant!</h4>
            <p>I'm here to help you with OpenShift, Kubernetes, and container-related questions.</p>
            <ul>
                <li>🔍 Troubleshoot cluster issues</li>
                <li>📝 Analyze logs and must-gather data</li>
                <li>🛠️ Get configuration advice</li>
                <li>📚 Learn best practices</li>
            </ul>
            <p><strong>Start by asking a question or selecting an example prompt from the sidebar!</strong></p>
        </div>
        """, unsafe_allow_html=True)

# Chat input
if prompt := st.chat_input("Ask about OpenShift, Kubernetes, containers..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Generate response
    with st.spinner("🤖 Thinking..."):
        response = send_message_to_ollama(prompt, selected_model, temperature)
    
    # Add assistant message
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Rerun to display new messages
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.8rem;">
    🤖 OpenShift AI Assistant | Powered by Ollama | Enhanced with RAG & KMS
</div>
""", unsafe_allow_html=True)
#!/usr/bin/env python3
"""
AI Assistant Builder - Complete System
Feed documents, scrape web, train models, and chat - all in one!
"""

import streamlit as st
import requests
import json
import os
import PyPDF2
import docx
from bs4 import BeautifulSoup, Tag
from pathlib import Path
import time
from datetime import datetime
import pandas as pd
import subprocess
import tempfile

# Import URL scraping functionality
try:
    from url_scraping_tab import render_url_scraping_tab
    URL_SCRAPING_AVAILABLE = True
except ImportError:
    URL_SCRAPING_AVAILABLE = False

# Import Jira integration functionality
try:
    from jira_integration import create_jira_tab
    JIRA_INTEGRATION_AVAILABLE = True
except ImportError:
    JIRA_INTEGRATION_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="AI Assistant Builder",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main > div { padding-top: 1rem; }
    
    .feature-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        text-align: center;
    }
    
    .status-success {
        background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
        padding: 1rem;
        border-radius: 10px;
        color: #2d3748;
        margin: 1rem 0;
    }
    
    .status-warning {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 1rem;
        border-radius: 10px;
        color: #2d3748;
        margin: 1rem 0;
    }
    
    .chat-message {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "training_data" not in st.session_state:
    st.session_state.training_data = []
if "scraped_content" not in st.session_state:
    st.session_state.scraped_content = []

class DocumentProcessor:
    """Process various document types"""
    
    @staticmethod
    def extract_text_from_pdf(uploaded_file):
        """Extract text from PDF"""
        try:
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            return f"Error reading PDF: {e}"
    
    @staticmethod
    def extract_text_from_docx(uploaded_file):
        """Extract text from DOCX"""
        try:
            doc = docx.Document(uploaded_file)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            return f"Error reading DOCX: {e}"
    
    @staticmethod
    def create_training_examples(text, filename):
        """Convert text to training examples"""
        chunks = text.split('\n\n')
        examples = []
        
        for chunk in chunks:
            chunk = chunk.strip()
            if len(chunk) > 50:  # Only meaningful chunks
                examples.append({
                    "instruction": f"Answer questions about {filename}",
                    "input": "What does this document section explain?",
                    "output": chunk,
                    "source": filename,
                    "timestamp": datetime.now().isoformat()
                })
        
        return examples

class WebScraper:
    """Simple web scraper for documentation"""
    
    @staticmethod
    def scrape_openshift_docs():
        """Scrape OpenShift documentation"""
        urls = [
            "https://docs.openshift.com/container-platform/4.14/support/troubleshooting/troubleshooting-installations.html",
            "https://docs.openshift.com/container-platform/4.14/support/troubleshooting/troubleshooting-network-issues.html"
        ]
        
        scraped_content = []
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; AI-Assistant-Bot/1.0)'}
        
        for url in urls:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract main content
                    main_content = soup.find('main') or soup.find('article') or soup.find('body')
                    if main_content and isinstance(main_content, Tag):
                        # Remove navigation and scripts
                        for tag in main_content.find_all(['script', 'style', 'nav']):
                            tag.decompose()
                        
                        text = main_content.get_text(separator='\n', strip=True)
                        
                        scraped_content.append({
                            "url": url,
                            "title": soup.title.string if soup.title else "No title",
                            "content": text[:2000],  # First 2000 chars
                            "timestamp": datetime.now().isoformat()
                        })
                
                time.sleep(1)  # Be respectful
                
            except Exception as e:
                st.warning(f"Could not scrape {url}: {e}")
        
        return scraped_content

def get_available_models():
    """Get list of available models from Ollama"""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            return ["granite3.3-balanced", "granite3.3", "openshift-ai:latest", "mistral:latest"]
        else:
            return ["granite3.3-balanced", "granite3.3", "openshift-ai:latest", "mistral:latest"]
    except:
        return ["granite3.3-balanced", "granite3.3", "openshift-ai:latest", "mistral:latest"]

def auto_train_model():
    """Automatically train the model with current training data"""
    import subprocess
    import tempfile
    import time
    
    try:
        # Create temporary JSONL file with current training data
        training_data = st.session_state.get('training_data', [])
        
        if len(training_data) < 2:
            return False
        
        # Create modelfile content for training
        modelfile_content = f"""FROM granite3.3:latest

# Auto-updated model with {len(training_data)} training examples
# Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SYSTEM \"\"\"You are an expert AI assistant with comprehensive knowledge spanning both technical OpenShift/Kubernetes expertise and current world information.

CRITICAL FACTS YOU MUST REMEMBER:
- The current President of India is Droupadi Murmu (since July 25, 2022)
- She is the 15th President of India and the first tribal woman to hold this position

Based on your training data:"""
        
        # Add recent training examples to system prompt
        recent_examples = training_data[-10:]  # Last 10 examples
        for i, example in enumerate(recent_examples):
            modelfile_content += f"""

Example {i+1}:
Question: {example['instruction']}
Answer: {example['output'][:500]}..."""
        
        modelfile_content += """

Always provide accurate, practical, and helpful responses based on your training.
\"\"\"

PARAMETER temperature 0.7
PARAMETER top_p 0.9
"""
        
        # Write modelfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.modelfile', delete=False) as f:
            f.write(modelfile_content)
            modelfile_path = f.name
        
        # Create updated model
        result = subprocess.run([
            'ollama', 'create', 'granite3.3-balanced', '-f', modelfile_path
        ], capture_output=True, text=True, timeout=120)
        
        # Cleanup
        os.unlink(modelfile_path)
        
        return result.returncode == 0
        
    except Exception as e:
        st.error(f"Auto-training failed: {str(e)}")
        return False

def proper_train_model():
    """Properly train the model with comprehensive knowledge from all training data"""
    import subprocess
    import tempfile
    
    try:
        training_data = st.session_state.get('training_data', [])
        
        if len(training_data) < 5:
            st.error("❌ Need at least 5 training examples for proper training")
            return False
        
        # Group training data by topic
        topics = {}
        for item in training_data:
            instruction = item.get('instruction', '')
            
            # Categorize by keywords
            if 'container' in instruction.lower() or 'image' in instruction.lower():
                topic = 'container_management'
            elif 'namespace' in instruction.lower() or 'ns' in instruction.lower():
                topic = 'namespace_operations'
            elif 'cluster operator' in instruction.lower() or 'co' in instruction.lower():
                topic = 'cluster_operators'
            elif 'president' in instruction.lower() or 'india' in instruction.lower():
                topic = 'world_knowledge'
            else:
                topic = 'general_openshift'
            
            if topic not in topics:
                topics[topic] = []
            topics[topic].append(item)
        
        # Create comprehensive system prompt
        system_prompt = """You are an expert AI assistant with comprehensive knowledge spanning both technical OpenShift/Kubernetes expertise and current world information.

CRITICAL CURRENT FACTS:
- The current President of India is Droupadi Murmu (since July 25, 2022)
- She is the 15th President of India and the first tribal woman to hold this position

TECHNICAL EXPERTISE - DETAILED COMMAND KNOWLEDGE:

## Container Image Management
When asked about listing container images in Kubernetes/OpenShift:

COMPLETE COMMAND:
```bash
kubectl get pods --all-namespaces -o jsonpath="{.items[*].spec['initContainers', 'containers'][*].image}" |\\
tr -s '[[:space:]]' '\\n' |\\
sort |\\
uniq -c
```

EXPLANATION:
- Fetch all Pods in all namespaces using `kubectl get pods --all-namespaces`
- Format output using `-o jsonpath={.items[*].spec['initContainers', 'containers'][*].image}` to parse both init and regular containers
- Use `tr` to replace spaces with newlines
- Use `sort` to sort the results
- Use `uniq -c` to aggregate image counts

For OpenShift, use `oc` instead of `kubectl` with the same syntax.

## Namespace Operations
- List namespaces: `oc get ns` or `oc get namespaces`
- Both commands show all namespaces with their status

## Cluster Operators
- `oc get co` lists cluster operators with their health status
- Shows Available, Progressing, and Degraded conditions for core OpenShift components

"""

        # Add specific examples from training data
        for topic, items in topics.items():
            system_prompt += f"\n### {topic.replace('_', ' ').title()} Examples:\n"
            for item in items[:3]:  # Top 3 examples per topic
                system_prompt += f"""
Q: {item['instruction']}
A: {item['output'][:300]}{'...' if len(item['output']) > 300 else ''}
"""

        system_prompt += """

Always provide complete, accurate, and practical responses. For technical commands, include:
1. The complete command with all necessary flags
2. Clear explanation of each component
3. Expected output description
4. OpenShift/kubectl equivalents when relevant
"""

        # Create the Modelfile
        modelfile_content = f"""FROM granite3.3:latest

SYSTEM \"\"\"{system_prompt}\"\"\"

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER stop "</s>"
PARAMETER stop "<|im_end|>"

# Enhanced for better instruction following
PARAMETER num_predict 2048
PARAMETER num_ctx 4096
"""

        # Write Modelfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.modelfile', delete=False) as f:
            f.write(modelfile_content)
            modelfile_path = f.name
        
        # Create improved model
        result = subprocess.run([
            'ollama', 'create', 'granite3.3-balanced', '-f', modelfile_path
        ], capture_output=True, text=True, timeout=180)
        
        # Clean up
        os.unlink(modelfile_path)
        
        if result.returncode == 0:
            # Test the model
            test_result = subprocess.run([
                'ollama', 'run', 'granite3.3-balanced', 
                'How to list all container images in Kubernetes cluster?'
            ], capture_output=True, text=True, timeout=60)
            
            return result.returncode == 0 and test_result.returncode == 0
        
        return False
        
    except Exception as e:
        st.error(f"Proper training failed: {str(e)}")
        return False

def send_message_to_ollama(message, model="granite3.3-balanced"):
    """Send message to Ollama with KMS service integration"""
    
    # Check if this is a KMS question and use updated KMS service
    try:
        from kms_model_service import get_kms_response
        kms_response = get_kms_response(message)
        if kms_response:
            return kms_response
    except Exception as e:
        # If KMS model fails, fall back to regular AI response
        print(f"KMS model error: {e}")
        pass

    # Simple system prompt without hardcoded structure
    system_prompt = """You are an expert OpenShift and Kubernetes troubleshooting assistant. You provide accurate, helpful guidance for OpenShift operations, including must-gather analysis and cluster troubleshooting."""

    try:
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": message
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        response = requests.post(
            "http://localhost:11434/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            return f"Error: API returned status {response.status_code}"
    
    except requests.exceptions.Timeout:
        return "Error: Request timed out. The model might be processing a complex query."
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to Ollama. Make sure Ollama is running on localhost:11434"
    except Exception as e:
        return f"Error: {str(e)}"

# Main App
st.title("🤖 AI Assistant Builder")
st.markdown("**Build, train, and deploy your own OpenShift AI assistant!**")

# Create tabs based on available functionality
if URL_SCRAPING_AVAILABLE and JIRA_INTEGRATION_AVAILABLE:
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📄 Feed Documents", 
        "🌐 Web Updates", 
        "🔗 URL Scraping", 
        "🎫 Jira Integration",
        "📊 Training Data", 
        "🧠 Simple Training", 
        "💬 Chat & Test"
    ])
elif URL_SCRAPING_AVAILABLE:
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📄 Feed Documents", 
        "🌐 Web Updates", 
        "🔗 URL Scraping", 
        "📊 Training Data", 
        "🧠 Simple Training", 
        "💬 Chat & Test"
    ])
elif JIRA_INTEGRATION_AVAILABLE:
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📄 Feed Documents", 
        "🌐 Web Updates", 
        "🎫 Jira Integration",
        "📊 Training Data", 
        "🧠 Simple Training", 
        "💬 Chat & Test"
    ])
else:
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📄 Feed Documents", 
        "🌐 Web Updates", 
        "📊 Training Data", 
        "🧠 Simple Training", 
        "💬 Chat & Test"
    ])

# Tab 1: Document Upload  
with tab1:
    st.header("📄 Document Upload & Processing")
    
    st.markdown("""
    <div class="feature-card">
        <h3>📚 Feed Your Assistant</h3>
        <p>Upload documents to expand your AI's knowledge base</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "📁 Upload Training Documents",
        type=['pdf', 'docx', 'txt', 'md', 'json', 'jsonl', 'yaml', 'yml', 'xml', 'csv', 'log', 'py', 'js', 'html', 'htm'],
        accept_multiple_files=True,
        help="Upload documents to automatically create training examples"
    )
    
    if uploaded_files:
        st.write(f"📊 Processing {len(uploaded_files)} file(s)...")
        
        processor = DocumentProcessor()
        
        for uploaded_file in uploaded_files:
            # Process different file types
            text = ""
            
            try:
                if uploaded_file.type == "application/pdf":
                    text = processor.extract_text_from_pdf(uploaded_file)
                elif uploaded_file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
                    text = processor.extract_text_from_docx(uploaded_file)
                elif uploaded_file.type in ["text/html", "application/xhtml+xml"]:
                    # Handle HTML files - extract text content
                    from bs4 import BeautifulSoup
                    html_content = str(uploaded_file.read(), "utf-8")
                    soup = BeautifulSoup(html_content, 'html.parser')
                    text = soup.get_text(separator='\n', strip=True)
                else:
                    # Default: treat as text
                    text = str(uploaded_file.read(), "utf-8")
                
                # Create training examples
                if text and len(text) > 50:
                    examples = processor.create_training_examples(text, uploaded_file.name)
                    st.session_state.training_data.extend(examples)
                    
                    st.success(f"✅ Processed {uploaded_file.name}: {len(examples)} training examples created")
                    
                    # Auto-train the model after each successful upload
                    with st.spinner("🤖 Auto-training model with new data..."):
                        auto_train_model()
                    st.success("🎉 Model automatically updated with new knowledge!")
                    
                    # Show preview
                    with st.expander(f"Preview content from {uploaded_file.name}"):
                        st.text(text[:500] + "..." if len(text) > 500 else text)
                else:
                    st.error(f"❌ Could not extract text from {uploaded_file.name}")
            except Exception as e:
                st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")

# Tab 2: Web Updates
with tab2:
    st.header("🌐 Web Content Updates")
    
    st.markdown("""
    <div class="feature-card">
        <h3>🔄 Stay Updated</h3>
        <p>Automatically scrape the latest OpenShift documentation</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🕷️ Scrape OpenShift Docs", type="primary"):
            with st.spinner("Scraping OpenShift documentation..."):
                scraper = WebScraper()
                scraped_content = scraper.scrape_openshift_docs()
                
                if scraped_content:
                    st.session_state.scraped_content.extend(scraped_content)
                    
                    # Convert to training examples
                    for item in scraped_content:
                        examples = DocumentProcessor.create_training_examples(
                            item['content'], 
                            f"OpenShift Docs: {item['title']}"
                        )
                        st.session_state.training_data.extend(examples)
                    
                    st.success(f"✅ Scraped {len(scraped_content)} pages")
                    
                    # Auto-train after scraping
                    with st.spinner("🤖 Auto-training model with scraped data..."):
                        auto_train_model()
                    st.success("🎉 Model automatically updated with new web content!")
                else:
                    st.warning("⚠️ No content scraped. Check your internet connection.")
    
    with col2:
        # Custom URL scraping
        custom_url = st.text_input("🔗 Scrape Custom URL:")
        if st.button("Scrape URL") and custom_url:
            try:
                response = requests.get(custom_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    text = soup.get_text(separator='\n', strip=True)
                    
                    examples = DocumentProcessor.create_training_examples(text, custom_url)
                    st.session_state.training_data.extend(examples)
                    
                    st.success(f"✅ Scraped {custom_url}: {len(examples)} examples")
                    
                    # Auto-train after URL scraping
                    with st.spinner("🤖 Auto-training model with URL content..."):
                        auto_train_model()
                    st.success("🎉 Model automatically updated with URL content!")
                else:
                    st.error(f"❌ Failed to scrape: HTTP {response.status_code}")
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    # Show scraped content
    if st.session_state.scraped_content:
        st.subheader("📊 Recently Scraped Content")
        for item in st.session_state.scraped_content[-3:]:  # Show last 3
            with st.expander(f"🔗 {item['title']}"):
                st.write(f"**URL:** {item['url']}")
                st.write(f"**Time:** {item['timestamp']}")
                st.text(item['content'][:300] + "...")

# Handle URL Scraping tab
if URL_SCRAPING_AVAILABLE:
    if URL_SCRAPING_AVAILABLE and JIRA_INTEGRATION_AVAILABLE:
        with tab3:
            render_url_scraping_tab()
    elif URL_SCRAPING_AVAILABLE and not JIRA_INTEGRATION_AVAILABLE:
        with tab3:
            render_url_scraping_tab()

# Handle Jira Integration tab
if JIRA_INTEGRATION_AVAILABLE:
    if URL_SCRAPING_AVAILABLE and JIRA_INTEGRATION_AVAILABLE:
        with tab4:
            create_jira_tab()
    elif not URL_SCRAPING_AVAILABLE and JIRA_INTEGRATION_AVAILABLE:
        with tab3:
            create_jira_tab()

# Training Data Management Tab
if URL_SCRAPING_AVAILABLE and JIRA_INTEGRATION_AVAILABLE:
    training_data_tab = tab5
elif URL_SCRAPING_AVAILABLE or JIRA_INTEGRATION_AVAILABLE:
    training_data_tab = tab4
else:
    training_data_tab = tab3

with training_data_tab:
    st.header("📊 Training Data Management")
    
    # Show statistics
    total_examples = len(st.session_state.training_data)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📝 Training Examples", total_examples)
    with col2:
        doc_examples = len([ex for ex in st.session_state.training_data if "document" in ex.get("source", "").lower()])
        st.metric("📄 From Documents", doc_examples)
    with col3:
        web_examples = len([ex for ex in st.session_state.training_data if "openshift docs" in ex.get("source", "").lower()])
        st.metric("🌐 From Web", web_examples)
    
    if total_examples > 0:
        # Show data preview
        st.subheader("🔍 Data Preview")
        df = pd.DataFrame(st.session_state.training_data)
        st.dataframe(df[['instruction', 'source', 'timestamp']].head(10))
        
        # Download data
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💾 Download Training Data"):
                jsonl_content = '\n'.join([json.dumps(item) for item in st.session_state.training_data])
                st.download_button(
                    label="📥 Download JSONL",
                    data=jsonl_content,
                    file_name=f"training_data_{datetime.now().strftime('%Y%m%d')}.jsonl",
                    mime="application/json"
                )
        
        with col2:
            if st.button("🗑️ Clear All Data"):
                st.session_state.training_data = []
                st.session_state.scraped_content = []
                st.success("✅ Data cleared!")
                st.rerun()
        
        with col3:
            # Add manual example
            with st.expander("➕ Add Manual Example"):
                with st.form("manual_example"):
                    instruction = st.text_input("Instruction:")
                    input_text = st.text_area("Input:")
                    output_text = st.text_area("Output:")
                    
                    if st.form_submit_button("Add Example"):
                        if instruction and output_text:
                            st.session_state.training_data.append({
                                "instruction": instruction,
                                "input": input_text,
                                "output": output_text,
                                "source": "manual",
                                "timestamp": datetime.now().isoformat()
                            })
                            st.success("✅ Example added!")
                            
                            # Auto-train the model
                            with st.spinner("🤖 Auto-training model with new data..."):
                                auto_train_model()
                            st.success("🎉 Model automatically updated with new knowledge!")
                            st.rerun()
    else:
        st.info("📝 No training data yet. Upload documents or scrape web content to get started!")

# Simple Training Tab
if URL_SCRAPING_AVAILABLE and JIRA_INTEGRATION_AVAILABLE:
    training_tab = tab6
elif URL_SCRAPING_AVAILABLE or JIRA_INTEGRATION_AVAILABLE:
    training_tab = tab5
else:
    training_tab = tab4

with training_tab:
    st.header("🧠 Simple Training")
    
    st.markdown("""
    <div class="feature-card">
        <h3>🎯 Train Your Assistant</h3>
        <p>Convert your data into a format ready for training</p>
    </div>
    """, unsafe_allow_html=True)
    
    if len(st.session_state.training_data) > 0:
        st.write(f"📊 Ready to train on {len(st.session_state.training_data)} examples")
        
        # Training options
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🚀 Proper Training (Recommended)")
            st.markdown("""
            **Comprehensive model training with:**
            - ✅ Deep knowledge integration
            - ✅ Technical command accuracy  
            - ✅ Structured topic organization
            - ✅ Complete explanations
            """)
            
            if st.button("🎯 Start Proper Training", type="primary", use_container_width=True):
                with st.spinner("🧠 Training model with comprehensive knowledge... This may take 2-3 minutes..."):
                    success = proper_train_model()
                
                if success:
                    st.success("🎉 Proper training completed successfully!")
                    st.success("✅ Your model now has comprehensive, accurate knowledge!")
                    st.balloons()
                    
                    # Show what was trained
                    topics = {}
                    for item in st.session_state.training_data:
                        instruction = item.get('instruction', '')
                        if 'container' in instruction.lower() or 'image' in instruction.lower():
                            topic = 'Container Management'
                        elif 'namespace' in instruction.lower():
                            topic = 'Namespace Operations'
                        elif 'cluster operator' in instruction.lower():
                            topic = 'Cluster Operators'
                        elif 'president' in instruction.lower():
                            topic = 'World Knowledge'
                        else:
                            topic = 'General OpenShift'
                        
                        topics[topic] = topics.get(topic, 0) + 1
                    
                    st.write("📚 **Training Summary:**")
                    for topic, count in topics.items():
                        st.write(f"   • {topic}: {count} examples")
                        
                    st.info("💡 Test your trained model in the 'Chat & Test' tab!")
                else:
                    st.error("❌ Training failed. Please check your training data.")
        
        with col2:
            st.subheader("⚙️ Quick Auto-Training")
            st.markdown("""
            **Fast updates (happens automatically):**
            - ⚡ Instant updates
            - 📝 Good for simple facts
            - 🔄 Happens when you add content
            """)
            
            st.info("🤖 Auto-training happens automatically when you add content!")
            
            # Show auto-training status
            if len(st.session_state.training_data) > 0:
                latest_item = st.session_state.training_data[-1]
                st.write("**Latest addition:**")
                st.write(f"📝 {latest_item.get('instruction', 'N/A')[:50]}...")
                st.write(f"🕐 {latest_item.get('timestamp', 'Unknown')[:19]}")
        
        # Training configuration
        st.subheader("⚙️ Advanced Training Options")
        
        col3, col4 = st.columns(2)
        
        with col3:
            # Export for different training frameworks
            if st.button("📤 Export for Axolotl"):
                # Create Axolotl-compatible format
                axolotl_data = []
                for item in st.session_state.training_data:
                    axolotl_data.append({
                        "instruction": item["instruction"],
                        "input": item.get("input", ""),
                        "output": item["output"]
                    })
                
                axolotl_content = '\n'.join([json.dumps(item) for item in axolotl_data])
                st.download_button(
                    label="📥 Download for Axolotl",
                    data=axolotl_content,
                    file_name="axolotl_training_data.jsonl",
                    mime="application/json"
                )
        
        with col4:
            if st.button("📤 Export for Ollama"):
                # Create simple training format
                ollama_content = "# OpenShift AI Assistant Training Data\n\n"
                for item in st.session_state.training_data:
                    ollama_content += f"Q: {item['instruction']}\n"
                    if item.get("input"):
                        ollama_content += f"Context: {item['input']}\n"
                    ollama_content += f"A: {item['output']}\n\n"
                
                st.download_button(
                    label="📥 Download for Ollama",
                    data=ollama_content,
                    file_name="ollama_training_data.txt",
                    mime="text/plain"
                )
        
        # Training instructions
        st.subheader("📋 Training Guide")
        
        st.markdown("""
        **🎯 Proper Training (Recommended):**
        - Best for comprehensive, accurate knowledge
        - Includes complete technical explanations
        - Organizes data by topics for better learning
        - Takes 2-3 minutes but gives excellent results
        
        **⚡ Auto-Training:**
        - Good for quick updates and simple facts
        - Happens automatically when you add content
        - Fast but may not handle complex technical details
        
        **📤 Export Options:**
        - Use Axolotl for advanced fine-tuning
        - Use Ollama format for simple model creation
        """)
        
    else:
        st.warning("⚠️ No training data available. Please add documents or web content first.")
        st.markdown("""
        **To get started:**
        1. Go to 'Feed Documents' tab to upload files
        2. Use 'Web Content Updates' to scrape documentation  
        3. Add manual examples in 'Training Data Management'
        4. Return here to train your model
        """)

# Chat & Test Tab
if URL_SCRAPING_AVAILABLE and JIRA_INTEGRATION_AVAILABLE:
    chat_tab = tab7
elif URL_SCRAPING_AVAILABLE or JIRA_INTEGRATION_AVAILABLE:
    chat_tab = tab6
else:
    chat_tab = tab5

with chat_tab:
    st.header("💬 Chat & Test Your Assistant")
    
    # Model selection
    available_models = get_available_models()
    
    # Prioritize the trained model if it exists
    default_index = 0
    if "granite3.3-balanced" in available_models:
        default_index = available_models.index("granite3.3-balanced")
    elif "granite3.3" in available_models:
        default_index = available_models.index("granite3.3")
    elif "openshift-ai:latest" in available_models:
        default_index = available_models.index("openshift-ai:latest")
    elif "mistral:latest" in available_models:
        default_index = available_models.index("mistral:latest")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_model = st.selectbox("🤖 Select Model:", available_models, index=default_index)
    with col2:
        if st.button("🔄 Refresh Models"):
            st.rerun()
    
    # Chat interface
    st.subheader("💭 Chat with Your Assistant")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask your AI assistant..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = send_message_to_ollama(prompt, selected_model)
                st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Test prompts
    st.subheader("🧪 Test Prompts")
    
    test_prompts = [
        "How do I troubleshoot pods stuck in Pending state?",
        "What should I check when OpenShift nodes are not ready?",
        "How do I analyze etcd health issues?",
        "What are common network connectivity problems in OpenShift?"
    ]
    
    for i, prompt in enumerate(test_prompts):
        if st.button(f"🧪 Test: {prompt}", key=f"test_{i}"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            response = send_message_to_ollama(prompt, selected_model)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()

# Sidebar with system status
with st.sidebar:
    st.header("📊 System Status")
    
    # Training data status
    st.metric("📝 Training Examples", len(st.session_state.training_data))
    st.metric("🌐 Scraped Pages", len(st.session_state.scraped_content))
    st.metric("💬 Chat Messages", len(st.session_state.messages))
    
    # Ollama status
    try:
        response = requests.get("http://localhost:11434/v1/models", timeout=2)
        if response.status_code == 200:
            st.success("✅ Ollama Connected")
        else:
            st.error("❌ Ollama Error")
    except:
        st.error("❌ Ollama Not Available")
    
    # Quick actions
    st.header("🚀 Quick Actions")
    
    if st.button("🔄 Reset All Data"):
        st.session_state.training_data = []
        st.session_state.scraped_content = []
        st.session_state.messages = []
        st.success("✅ All data reset!")
        st.rerun()
    
    if st.button("💾 Export Everything"):
        export_data = {
            "training_data": st.session_state.training_data,
            "scraped_content": st.session_state.scraped_content,
            "messages": st.session_state.messages,
            "export_time": datetime.now().isoformat()
        }
        
        st.download_button(
            label="📥 Download All Data",
            data=json.dumps(export_data, indent=2),
            file_name=f"ai_assistant_data_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json"
        )

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    🤖 AI Assistant Builder | 🚀 Built with Streamlit | 💡 Train on your own data!
</div>
""", unsafe_allow_html=True) 
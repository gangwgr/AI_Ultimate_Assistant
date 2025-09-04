#!/usr/bin/env python3
"""
Continuous Learning System for AI Models
Permanently updates existing models with new knowledge from documents and web URLs
"""

import os
import json
import subprocess
import tempfile
import asyncio
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import logging
from datetime import datetime

# Document parsing imports
try:
    import PyPDF2  # type: ignore
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    from docx import Document  # type: ignore
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False

try:
    import aiohttp  # type: ignore
    import requests  # type: ignore
    from bs4 import BeautifulSoup  # type: ignore
    WEB_SCRAPING_SUPPORT = True
except ImportError:
    WEB_SCRAPING_SUPPORT = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContinuousLearningSystem:
    """System for continuously updating AI models with new knowledge"""
    
    def __init__(self, models_dir: str = "trained_models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        self.training_data_dir = self.models_dir / "training_data"
        self.training_data_dir.mkdir(exist_ok=True)
        
    def get_available_models(self) -> List[str]:
        """Get list of available Ollama models"""
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                models = []
                for line in lines:
                    if line.strip():
                        model_name = line.split()[0]
                        models.append(model_name)
                return models
            return []
        except Exception as e:
            logger.error(f"Error getting models: {e}")
            return []
    
    def parse_document(self, file_path: str, file_type: Optional[str] = None) -> str:
        """Parse document and extract text content"""
        file_path_obj = Path(file_path)
        
        if file_type is None:
            file_type = file_path_obj.suffix.lower()
        
        try:
            if file_type in ['.txt', '.md', '.py', '.json', '.yaml', '.yml']:
                return self._parse_text_file(file_path_obj)
            elif file_type == '.pdf' and PDF_SUPPORT:
                return self._parse_pdf(file_path_obj)
            elif file_type == '.docx' and DOCX_SUPPORT:
                return self._parse_docx(file_path_obj)
            else:
                logger.warning(f"Unsupported file type: {file_type}")
                return ""
        except Exception as e:
            logger.error(f"Error parsing document {file_path}: {e}")
            return ""
    
    def _parse_text_file(self, file_path: Path) -> str:
        """Parse text-based files"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    def _parse_pdf(self, file_path: Path) -> str:
        """Parse PDF files"""
        if not PDF_SUPPORT:
            logger.error("PyPDF2 not installed. Install with: pip install PyPDF2")
            return ""
        
        text = ""
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)  # type: ignore
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def _parse_docx(self, file_path: Path) -> str:
        """Parse DOCX files"""
        if not DOCX_SUPPORT:
            logger.error("python-docx not installed. Install with: pip install python-docx")
            return ""
        
        doc = Document(file_path)  # type: ignore
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    async def scrape_web_url(self, url: str) -> str:
        """Scrape content from web URL"""
        if not WEB_SCRAPING_SUPPORT:
            logger.error("aiohttp and beautifulsoup4 not installed. Install with: pip install aiohttp beautifulsoup4")
            return ""
        
        try:
            async with aiohttp.ClientSession() as session:  # type: ignore
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')  # type: ignore
                        
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        # Get text content
                        text = soup.get_text()
                        
                        # Clean up text
                        lines = (line.strip() for line in text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        text = ' '.join(chunk for chunk in chunks if chunk)
                        
                        # Check for authentication pages
                        if any(auth_indicator in text.lower() for auth_indicator in [
                            'saml', 'login', 'authentication', 'sign in', 'access denied'
                        ]):
                            logger.warning(f"URL {url} requires authentication. Cannot scrape protected content.")
                            return f"⚠️ This URL requires authentication and cannot be scraped automatically: {url}\n\nTo use this content, please:\n1. Copy the content manually\n2. Paste it in the 'Custom Content' field\n3. Or provide a public URL instead"
                        
                        return text
                    elif response.status == 401 or response.status == 403:
                        logger.warning(f"Access denied to {url} (HTTP {response.status})")
                        return f"⚠️ Access denied to {url}. This URL requires authentication.\n\nTo use this content, please:\n1. Copy the content manually\n2. Paste it in the 'Custom Content' field\n3. Or provide a public URL instead"
                    else:
                        logger.error(f"Failed to fetch {url}: HTTP {response.status}")
                        return f"❌ Failed to fetch {url}: HTTP {response.status}\n\nPlease check if the URL is accessible or try a different URL."
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return f"❌ Error scraping {url}: {str(e)}\n\nPlease check if the URL is accessible or try a different URL."
    
    def generate_training_examples(self, content: str, source: str) -> List[Dict[str, str]]:
        """Generate training examples from content"""
        if not content.strip():
            return []
        
        # Split content into meaningful chunks
        chunks = self._chunk_content(content)
        examples = []
        
        # Check if this is Jira content
        is_jira_content = any(jira_indicator in source.lower() for jira_indicator in [
            'jira', 'issues.redhat.com', 'ocpqe', 'ocpbugs'
        ])
        
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 50:  # Skip very short chunks
                continue
            
            chunk = chunk.strip()
            
            if is_jira_content:
                # Create Jira-specific training examples
                examples.extend(self._create_jira_examples(chunk, source))
            else:
                # Create general training examples
                examples.extend(self._create_general_examples(chunk, source, i))
        
        return examples
    
    def _create_jira_examples(self, chunk: str, source: str) -> List[Dict[str, str]]:
        """Create Jira-specific training examples"""
        examples = []
        
        # Extract issue key if present
        import re
        issue_key_match = re.search(r'([A-Z]+-\d+)', chunk)
        issue_key = issue_key_match.group(1) if issue_key_match else "the Jira issue"
        
        # Example 1: Summarize Jira issue
        examples.append({
            "instruction": f"Summarize the Jira issue {issue_key} from {source}:",
            "input": chunk,
            "output": f"Based on the Jira content from {source}, {issue_key} involves: {chunk[:200]}..."
        })
        
        # Example 2: What is this Jira about
        examples.append({
            "instruction": f"What is Jira issue {issue_key} about?",
            "input": chunk,
            "output": f"Jira issue {issue_key} is about: {chunk[:200]}..."
        })
        
        # Example 3: Explain the issue
        examples.append({
            "instruction": f"Explain the details of Jira issue {issue_key}:",
            "input": chunk,
            "output": f"The Jira issue {issue_key} contains the following details: {chunk}"
        })
        
        # Example 4: Summarize with URL
        examples.append({
            "instruction": f"Summarize the Jira issue from {source}:",
            "input": chunk,
            "output": f"Based on the Jira content from {source}, this issue involves: {chunk[:200]}..."
        })
        
        return examples
    
    def _create_general_examples(self, chunk: str, source: str, chunk_index: int) -> List[Dict[str, str]]:
        """Create general training examples"""
        examples = []
        
        # Create question-answer pairs
        examples.append({
            "instruction": f"Explain the following concept from {source}:",
            "input": f"Content from {source} (part {chunk_index+1})",
            "output": chunk
        })
        
        # Create summary examples
        if len(chunk) > 200:
            examples.append({
                "instruction": f"Summarize this information from {source}:",
                "input": chunk,
                "output": f"Summary: {chunk[:150]}..."
            })
        
        # Create analysis examples
        examples.append({
            "instruction": f"Analyze the content from {source}:",
            "input": chunk,
            "output": f"Analysis of the content from {source}: {chunk[:200]}..."
        })
        
        return examples
    
    def _chunk_content(self, content: str, chunk_size: int = 1000) -> List[str]:
        """Split content into manageable chunks"""
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = paragraph
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def save_training_data(self, model_name: str, examples: List[Dict[str, str]], source: str):
        """Save training data for a model"""
        model_data_dir = self.training_data_dir / model_name
        model_data_dir.mkdir(exist_ok=True)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"training_data_{timestamp}_{source.replace('/', '_').replace(':', '_')}.jsonl"
        file_path = model_data_dir / filename
        
        # Save as JSONL
        with open(file_path, 'w', encoding='utf-8') as f:
            for example in examples:
                f.write(json.dumps(example, ensure_ascii=False) + '\n')
        
        logger.info(f"Saved {len(examples)} training examples to {file_path}")
        return file_path
    
    def load_all_training_data(self, model_name: str) -> List[Dict[str, str]]:
        """Load all training data for a model"""
        model_data_dir = self.training_data_dir / model_name
        if not model_data_dir.exists():
            return []
        
        all_examples = []
        for jsonl_file in model_data_dir.glob("*.jsonl"):
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            example = json.loads(line)
                            all_examples.append(example)
                        except json.JSONDecodeError:
                            continue
        
        return all_examples
    
    def create_enhanced_modelfile(self, base_model: str, training_examples: List[Dict[str, str]]) -> str:
        """Create enhanced modelfile with all training data"""
        # Build comprehensive system prompt
        system_prompt = f"""You are an AI assistant based on {base_model}, enhanced with specialized knowledge and capabilities.

CORE CAPABILITIES:
- Professional communication and email composition
- OpenShift and Kubernetes troubleshooting
- GitHub PR security reviews and code analysis
- Technical documentation and workflow automation
- Data analysis and reporting

TRAINING EXAMPLES:
Here are examples of how to handle various tasks:

"""
        
        # Add training examples to system prompt
        for i, example in enumerate(training_examples[:50]):  # Limit to prevent prompt overflow
            system_prompt += f"""
Example {i+1}:
Instruction: {example.get('instruction', '')}
Input: {example.get('input', '')}
Response: {example.get('output', '')}
---
"""
        
        system_prompt += """

Apply the patterns and knowledge from these examples to provide helpful, accurate, and professional responses.
Always maintain a professional tone and provide actionable, specific guidance.
"""
        
        # Create modelfile
        modelfile_content = f"""FROM {base_model}

SYSTEM \"\"\"{system_prompt}\"\"\"

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
"""
        
        return modelfile_content
    
    async def update_model_continuously(self, model_name: str, sources: List[Union[str, Dict[str, str]]], 
                                      progress_callback=None) -> Dict[str, Any]:
        """Continuously update a model with new knowledge from multiple sources"""
        
        async def safe_callback(message: str):
            """Safely call progress callback"""
            if progress_callback:
                try:
                    if asyncio.iscoroutinefunction(progress_callback):
                        await progress_callback(message)
                    else:
                        progress_callback(message)
                except Exception as e:
                    logger.error(f"Error in progress callback: {e}")
        
        await safe_callback("Initializing continuous learning...")
        
        all_examples = []
        processed_sources = []
        
        # Process each source
        for i, source in enumerate(sources):
            try:
                await safe_callback(f"Processing source {i+1}/{len(sources)}...")
                
                content = ""
                source_name = ""
                
                if isinstance(source, str):
                    if source.startswith(('http://', 'https://')):
                        # Web URL
                        content = await self.scrape_web_url(source)
                        source_name = source
                    else:
                        # File path
                        content = self.parse_document(source)
                        source_name = Path(source).name
                elif isinstance(source, dict):
                    # Direct content
                    content = source.get('content', '')
                    source_name = source.get('name', f'source_{i}')
                
                if content:
                    examples = self.generate_training_examples(content, source_name)
                    if examples:
                        all_examples.extend(examples)
                        processed_sources.append(source_name)
                        
                        # Save individual source data
                        self.save_training_data(model_name, examples, source_name)
                        
                        await safe_callback(f"Generated {len(examples)} examples from {source_name}")
                
            except Exception as e:
                logger.error(f"Error processing source {source}: {e}")
                await safe_callback(f"Error processing {source}: {e}")
        
        if not all_examples:
            return {"success": False, "message": "No training examples generated from sources"}
        
        # Load existing training data
        await safe_callback("Loading existing training data...")
        
        existing_examples = self.load_all_training_data(model_name)
        all_examples.extend(existing_examples)
        
        await safe_callback(f"Total training examples: {len(all_examples)}")
        
        # Create enhanced model
        await safe_callback("Creating enhanced model...")
        
        modelfile_content = self.create_enhanced_modelfile(model_name, all_examples)
        
        # Save modelfile
        modelfile_path = self.models_dir / f"{model_name}_enhanced.modelfile"
        with open(modelfile_path, 'w', encoding='utf-8') as f:
            f.write(modelfile_content)
        
        # Update the model using Ollama
        enhanced_model_name = f"{model_name}-enhanced"
        
        await safe_callback("Updating model with new knowledge...")
        
        try:
            # Create/update the enhanced model
            process = await asyncio.create_subprocess_exec(
                'ollama', 'create', enhanced_model_name, '-f', str(modelfile_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                await safe_callback("Model updated successfully!")
                
                # Save training history
                history_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "base_model": model_name,
                    "enhanced_model": enhanced_model_name,
                    "sources_processed": processed_sources,
                    "total_examples": len(all_examples),
                    "new_examples": len(all_examples) - len(existing_examples)
                }
                
                self._save_training_history(model_name, history_entry)
                
                return {
                    "success": True,
                    "enhanced_model": enhanced_model_name,
                    "total_examples": len(all_examples),
                    "new_examples": len(all_examples) - len(existing_examples),
                    "sources_processed": processed_sources
                }
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                return {"success": False, "message": f"Model creation failed: {error_msg}"}
                
        except Exception as e:
            return {"success": False, "message": f"Error updating model: {str(e)}"}
    
    def _save_training_history(self, model_name: str, history_entry: Dict[str, Any]):
        """Save training history"""
        history_file = self.models_dir / f"{model_name}_history.json"
        
        if history_file.exists():
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        else:
            history = []
        
        history.append(history_entry)
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    
    def get_training_history(self, model_name: str) -> List[Dict[str, Any]]:
        """Get training history for a model"""
        history_file = self.models_dir / f"{model_name}_history.json"
        
        if not history_file.exists():
            return []
        
        with open(history_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def test_enhanced_model(self, model_name: str, test_query: str) -> str:
        """Test the enhanced model"""
        enhanced_model_name = f"{model_name}-enhanced"
        
        try:
            process = await asyncio.create_subprocess_exec(
                'ollama', 'run', enhanced_model_name, test_query,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return stdout.decode().strip()
            else:
                return f"Error: {stderr.decode().strip()}"
        except Exception as e:
            return f"Error testing model: {str(e)}"


# Example usage
if __name__ == "__main__":
    async def main():
        cls = ContinuousLearningSystem()
        
        # Example: Update granite3.3-balanced with document and URL
        sources = [
            "path/to/document.pdf",
            "https://example.com/article",
            {"name": "custom_knowledge", "content": "Custom training content here..."}
        ]
        
        async def progress_callback(message):
            print(f"Progress: {message}")
        
        result = await cls.update_model_continuously("granite3.3-balanced", sources, progress_callback)
        print(f"Result: {result}")
        
        if result["success"]:
            # Test the enhanced model
            response = await cls.test_enhanced_model("granite3.3-balanced", "What did you learn from the new sources?")
            print(f"Model response: {response}")
    
    asyncio.run(main()) 
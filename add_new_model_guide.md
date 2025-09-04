# 🚀 Model Training & Addition Guide

## Overview
This guide explains how to add new models, fine-tune existing models, and train custom models for your AI Ultimate Assistant.

## 🎯 Option 1: Add New Pre-trained Models (Easiest)

### Add Ollama Models
```bash
# Install specific models locally
ollama pull llama3.1:70b
ollama pull codellama:13b
ollama pull mistral:7b
ollama pull qwen2.5:14b

# For specialized tasks
ollama pull deepseek-coder:6.7b    # Code generation
ollama pull orca-mini:13b          # Reasoning
ollama pull vicuna:13b             # Conversation
```

### Add via Hugging Face
```bash
# Download models directly
huggingface-cli download microsoft/DialoGPT-large
huggingface-cli download microsoft/CodeBERT-base
huggingface-cli download facebook/blenderbot-400M-distill
```

### Update Your Configuration
```env
# Add to .env file
CUSTOM_MODEL_PATH=./models/your-custom-model
HUGGINGFACE_MODEL=microsoft/DialoGPT-large
OLLAMA_MODELS=llama3.1:70b,codellama:13b,mistral:7b
```

## 🔧 Option 2: Fine-tune Existing Models

### A. Fine-tune Granite 3.3 for Your Workflow

Create training script:
```python
# fine_tune_granite.py
import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    TrainingArguments, 
    Trainer
)
from datasets import Dataset
import json

def prepare_training_data():
    """Prepare your specific workflow data"""
    # Your email/calendar/GitHub patterns
    training_data = [
        {
            "input": "Schedule meeting with team for next Tuesday 2pm",
            "output": "I'll schedule a team meeting for next Tuesday at 2:00 PM. Let me check everyone's availability and send calendar invites."
        },
        {
            "input": "Review this GitHub PR and suggest improvements",
            "output": "I'll analyze the pull request code, check for security issues, code quality, and provide actionable feedback."
        },
        # Add more examples from your actual usage
    ]
    return training_data

def fine_tune_granite():
    model_name = "ibm/granite-3.3-8b-instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    
    # Prepare dataset
    data = prepare_training_data()
    dataset = Dataset.from_list(data)
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir="./fine-tuned-granite",
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        num_train_epochs=3,
        learning_rate=5e-5,
        logging_steps=10,
        save_steps=500,
        evaluation_strategy="steps",
        eval_steps=500,
        warmup_steps=100,
    )
    
    # Train
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        tokenizer=tokenizer,
    )
    
    trainer.train()
    trainer.save_model("./fine-tuned-granite")

if __name__ == "__main__":
    fine_tune_granite()
```

### B. Fine-tune for GitHub PR Reviews

```python
# github_reviewer_trainer.py
import json
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments

def create_github_training_data():
    """Create training data from your PR review patterns"""
    return [
        {
            "input": "Review this code diff: + function calculateTotal(items) { + return items.reduce((sum, item) => sum + item.price, 0) + }",
            "output": "✅ Code Review:\n- ✅ Clean functional approach with reduce\n- ⚠️ Add input validation for null/undefined items\n- ⚠️ Consider type checking for item.price\n- 💡 Suggestion: Add JSDoc documentation\n\nSecurity: Low risk\nComplexity: Simple\nRating: 7/10"
        },
        {
            "input": "Review this Python code: + def process_user_data(data): + query = f'SELECT * FROM users WHERE id = {data['id']}' + return execute_query(query)",
            "output": "❌ Critical Security Issue:\n- 🚨 SQL Injection vulnerability\n- 🚨 Direct string interpolation in SQL query\n\n🔧 Fix: Use parameterized queries\n```python\ndef process_user_data(data):\n    query = 'SELECT * FROM users WHERE id = %s'\n    return execute_query(query, (data['id'],))\n```\n\nSecurity: HIGH RISK\nComplexity: Simple\nRating: 2/10"
        }
        # Add more examples from your actual PR reviews
    ]

# Run training
python github_reviewer_trainer.py
```

## 🏗️ Option 3: Train Custom Models from Scratch

### A. Create Domain-Specific Model

```python
# custom_assistant_trainer.py
from transformers import GPT2LMHeadModel, GPT2Tokenizer, GPT2Config
from transformers import TrainingArguments, Trainer
import torch

def create_custom_model():
    """Create a custom model for your specific workflow"""
    
    # Configure model architecture
    config = GPT2Config(
        vocab_size=50257,
        n_positions=1024,
        n_ctx=1024,
        n_embd=768,
        n_layer=12,
        n_head=12
    )
    
    # Initialize model
    model = GPT2LMHeadModel(config)
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    
    # Add special tokens for your use case
    special_tokens = {
        "additional_special_tokens": [
            "<EMAIL>", "</EMAIL>",
            "<CALENDAR>", "</CALENDAR>", 
            "<GITHUB>", "</GITHUB>",
            "<CODE_REVIEW>", "</CODE_REVIEW>"
        ]
    }
    tokenizer.add_special_tokens(special_tokens)
    model.resize_token_embeddings(len(tokenizer))
    
    return model, tokenizer

def prepare_domain_data():
    """Prepare your workflow-specific training data"""
    return [
        # Email patterns
        "<EMAIL>Draft professional email declining meeting due to conflict</EMAIL>I appreciate the invitation, but I have a scheduling conflict. Could we explore alternative times? Best regards.",
        
        # Calendar patterns  
        "<CALENDAR>Schedule team standup every Monday 9am</CALENDAR>I'll create a recurring meeting for the team standup every Monday at 9:00 AM. Sending calendar invites now.",
        
        # GitHub patterns
        "<GITHUB>Review PR #123 for security issues</GITHUB>Analyzing PR #123 for potential security vulnerabilities, code quality, and best practices...",
        
        # Code review patterns
        "<CODE_REVIEW>function validateEmail(email) { return /\S+@\S+\.\S+/.test(email); }</CODE_REVIEW>Good email validation pattern. Consider adding more robust regex and null checks."
    ]

# Train the model
model, tokenizer = create_custom_model()
training_data = prepare_domain_data()
# ... training logic
```

### B. Train with Your Specific Data

```python
# workflow_data_collector.py
import json
from datetime import datetime

class WorkflowDataCollector:
    def __init__(self):
        self.training_examples = []
    
    def collect_email_patterns(self):
        """Collect your email interaction patterns"""
        # Analyze your email history for patterns
        patterns = [
            ("schedule meeting", "calendar_action"),
            ("decline invitation", "polite_decline"),
            ("follow up on", "follow_up_action"),
            ("urgent review needed", "priority_escalation")
        ]
        return patterns
    
    def collect_github_patterns(self):
        """Collect your GitHub workflow patterns"""
        return [
            ("security vulnerability", "high_priority_review"),
            ("performance optimization", "medium_priority_review"),
            ("documentation update", "low_priority_review"),
            ("breaking change", "critical_review")
        ]
    
    def save_training_data(self):
        data = {
            "email_patterns": self.collect_email_patterns(),
            "github_patterns": self.collect_github_patterns(),
            "timestamp": datetime.now().isoformat()
        }
        
        with open("workflow_training_data.json", "w") as f:
            json.dump(data, f, indent=2)

# Collect your data
collector = WorkflowDataCollector()
collector.save_training_data()
```

## 🔌 Option 4: Integrate Custom Models into Your System

### Extend the Multi-Model Architecture

```python
# custom_model_integration.py
from app.services.ai_agent_multi_model import MultiModelAIAgent, ModelType
from enum import Enum

class CustomModelType(Enum):
    CUSTOM_WORKFLOW = "custom_workflow"
    CUSTOM_GITHUB = "custom_github"  
    CUSTOM_EMAIL = "custom_email"

class ExtendedMultiModelAgent(MultiModelAIAgent):
    def __init__(self):
        super().__init__()
        self._init_custom_models()
    
    def _init_custom_models(self):
        """Initialize your custom trained models"""
        try:
            # Load your fine-tuned models
            self.models[CustomModelType.CUSTOM_WORKFLOW] = self._load_custom_model("./fine-tuned-granite")
            self.models[CustomModelType.CUSTOM_GITHUB] = self._load_custom_model("./github-reviewer-model")
            
            # Update task routing
            self.task_routing.update({
                "github_review": [CustomModelType.CUSTOM_GITHUB, ModelType.GRANITE, ModelType.GEMINI],
                "email_composition": [CustomModelType.CUSTOM_EMAIL, ModelType.GEMINI, ModelType.OPENAI_GPT],
                "workflow_automation": [CustomModelType.CUSTOM_WORKFLOW, ModelType.GRANITE, ModelType.GEMINI]
            })
            
        except Exception as e:
            logger.error(f"Failed to load custom models: {e}")
    
    def _load_custom_model(self, model_path):
        """Load your custom trained model"""
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForCausalLM.from_pretrained(model_path)
        
        return {"tokenizer": tokenizer, "model": model}
```

## 🚀 Quick Start: Add a New Model Today

### 1. Add Ollama Model (5 minutes)
```bash
# Install a new model
ollama pull codellama:13b

# Update your .env
echo "OLLAMA_MODEL=codellama:13b" >> .env

# Restart your assistant
python main.py
```

### 2. Test the New Model
```bash
curl -X POST "http://localhost:8000/api/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Help me review this Python code for bugs"}'
```

## 📊 Model Performance Optimization

### Monitor Model Performance
```python
# model_monitor.py
import time
import json
from datetime import datetime

class ModelPerformanceMonitor:
    def __init__(self):
        self.metrics = {}
    
    def benchmark_models(self, test_queries):
        """Benchmark different models on your specific tasks"""
        models = ["granite", "gemini", "openai", "ollama"]
        
        for model in models:
            start_time = time.time()
            
            # Test model response
            response = self.test_model_response(model, test_queries)
            
            end_time = time.time()
            
            self.metrics[model] = {
                "response_time": end_time - start_time,
                "accuracy": self.evaluate_accuracy(response),
                "relevance": self.evaluate_relevance(response),
                "timestamp": datetime.now().isoformat()
            }
        
        return self.metrics
    
    def save_metrics(self):
        with open("model_performance.json", "w") as f:
            json.dump(self.metrics, f, indent=2)

# Run benchmarks
monitor = ModelPerformanceMonitor()
test_queries = [
    "Schedule a meeting with the team",
    "Review this GitHub PR for security issues", 
    "Draft a professional email response"
]
results = monitor.benchmark_models(test_queries)
monitor.save_metrics()
```

## 🎯 Next Steps

1. **Choose your approach**:
   - Quick: Add Ollama models
   - Custom: Fine-tune Granite for your workflow
   - Advanced: Train domain-specific model

2. **Prepare your data**:
   - Collect email/calendar/GitHub patterns
   - Create training examples
   - Clean and format data

3. **Train/Configure**:
   - Follow the scripts above
   - Monitor performance
   - Iterate and improve

4. **Integrate**:
   - Update your multi-model agent
   - Test with real workflows
   - Deploy to production

Would you like me to help you with any specific approach? I can create the training scripts or help you integrate a new model into your system. 
# 🧠 Multi-Model AI Guide

This guide explains how to use multiple AI models intelligently in your AI Ultimate Assistant to get the best results for different types of tasks.

## 🚀 Overview

The AI Ultimate Assistant supports multiple AI providers and can intelligently select the best model for your specific needs:

- **OpenAI GPT**: Excellent for general conversation, reasoning, and complex queries
- **Google Gemini**: Advanced multimodal capabilities, strong reasoning, and creative tasks
- **IBM Granite 3.3**: Optimized for enterprise tasks, structured data, and automation
- **Ollama**: Great for local processing, privacy-sensitive tasks, and customization

## 🎯 Smart Model Selection

The system automatically chooses the optimal model based on:

### Task Type
- **Email Tasks**: Gemini → OpenAI GPT → Granite → Ollama
- **Calendar/Scheduling**: Granite → Gemini → OpenAI GPT → Ollama  
- **Data Analysis**: Gemini → OpenAI GPT → Granite → Ollama
- **Creative Tasks**: Gemini → OpenAI GPT → Ollama → Granite
- **Multimodal Tasks**: Gemini → OpenAI GPT
- **Simple Queries**: Ollama → Gemini → OpenAI GPT → Granite

### Complexity Levels
- **Simple**: Basic greetings, quick answers → Ollama (fast & efficient)
- **Medium**: Email composition, scheduling → Gemini or best available model
- **Complex**: Multi-step analysis, workflows → Gemini or OpenAI GPT (most capable)
- **Creative**: Content generation, brainstorming → Gemini or OpenAI GPT (most creative)

## 🔧 Configuration

### Environment Variables

Add these to your `.env` file:

```env
# AI Provider Configuration
AI_PROVIDER=granite  # Default provider: granite, openai, gemini, or ollama

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo

# Google Gemini Configuration
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-1.5-pro

# IBM Granite Configuration  
GRANITE_MODEL=ibm/granite-3.3-128k-instruct

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=granite3.3:latest
```

### Multiple Provider Setup

To use all providers, configure all four:

1. **OpenAI**: Get API key from [OpenAI Platform](https://platform.openai.com/)
2. **Google Gemini**: Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
3. **Granite**: Available via Hugging Face or local deployment
4. **Ollama**: Install locally with `ollama pull granite3.3:latest`

## 📱 Using Multi-Model Features

### 1. Smart Chat API

Use the enhanced chat endpoint for intelligent model selection:

```bash
curl -X POST "http://localhost:8000/api/agent/chat-smart" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Schedule a meeting with the team tomorrow at 2 PM",
    "complexity": "medium",
    "model_preference": null,
    "use_ensemble": false
  }'
```

**Parameters:**
- `message`: Your request
- `complexity`: "simple", "medium", "complex", or "creative"
- `model_preference`: "openai_gpt", "gemini", "granite", "ollama", or null for auto-select
- `use_ensemble`: true to get responses from multiple models

**Response:**
```json
{
  "response": "I'll schedule that meeting for you...",
  "intent": "calendar",
  "model_used": "granite",
  "complexity": "medium",
  "confidence": 0.95,
  "entities": {"dates": ["tomorrow"], "times": ["2 PM"]},
  "suggestions": ["Check availability", "Set reminders"]
}
```

### 2. Model Comparison

Compare responses from all available models:

```bash
curl -X POST "http://localhost:8000/api/agent/models/compare" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Write a professional email declining a meeting"
  }'
```

**Response:**
```json
{
  "message": "Write a professional email declining a meeting",
  "responses": {
    "openai_gpt": "Dear [Name], Thank you for the invitation...",
    "granite": "I appreciate the meeting request, however...", 
    "ollama": "Thanks for reaching out. Unfortunately..."
  },
  "best_response": "Dear [Name], Thank you for the invitation...",
  "best_model": "openai_gpt",
  "confidence": 0.89
}
```

### 3. Model Benchmarking

Test model performance:

```bash
curl -X POST "http://localhost:8000/api/agent/models/benchmark" \
  -H "Content-Type: application/json" \
  -d '[
    "Hello, how are you?",
    "Schedule a meeting for tomorrow",
    "Analyze the quarterly sales data"
  ]'
```

## 🌐 Web Interface Usage

### Standard Interface
Access the regular interface at: `http://localhost:8000/frontend/`

### Multi-Model Demo
Experience all features at: `http://localhost:8000/frontend/multi_model_demo.html`

The demo page includes:
- **Model Status**: See which models are available
- **Smart Chat**: Let AI choose the best model
- **Model Comparison**: Compare responses side-by-side  
- **Benchmarking**: Test model performance
- **Task Routing**: See how tasks map to models

## 💡 Use Cases & Recommendations

### Email Management
```json
{
  "message": "Compose a follow-up email about the project timeline",
  "complexity": "medium",
  "model_preference": "openai_gpt"
}
```
**Why OpenAI**: Best language generation for professional communication

### Calendar Scheduling  
```json
{
  "message": "Schedule recurring team meetings every Tuesday at 10 AM",
  "complexity": "medium", 
  "model_preference": "granite"
}
```
**Why Granite**: Optimized for structured data and enterprise tasks

### Data Analysis
```json
{
  "message": "Analyze last month's email patterns and suggest improvements",
  "complexity": "complex",
  "model_preference": "openai_gpt"
}
```
**Why OpenAI**: Best reasoning and analysis capabilities

### Quick Queries
```json
{
  "message": "What's the weather like today?",
  "complexity": "simple",
  "model_preference": "ollama"
}
```
**Why Ollama**: Fast local processing for simple tasks

### Creative Tasks
```json
{
  "message": "Brainstorm creative team building activities",
  "complexity": "creative",
  "use_ensemble": true
}
```
**Why Ensemble**: Multiple perspectives for creativity

## 🛡️ Privacy & Performance Considerations

### Model Characteristics

| Model | Privacy | Speed | Capability | Cost |
|-------|---------|--------|------------|------|
| **OpenAI GPT** | Cloud-based | Fast | Highest | Per-token |
| **Granite** | Configurable | Medium | High | Local/Cloud |
| **Ollama** | Local | Fast | Good | Free |

### Recommendations

**For Sensitive Data**: Use Ollama (local processing)
```json
{"model_preference": "ollama"}
```

**For Best Results**: Use OpenAI GPT
```json
{"model_preference": "openai_gpt"}
```

**For Cost Efficiency**: Use Ollama for simple, Granite for medium tasks
```json
{"complexity": "simple", "model_preference": "ollama"}
```

**For Maximum Accuracy**: Use ensemble mode
```json
{"use_ensemble": true}
```

## 🔍 Monitoring & Debugging

### Check Available Models
```bash
curl "http://localhost:8000/api/agent/models"
```

### View Model Status
```bash
curl "http://localhost:8000/api/agent/capabilities"
```

### Monitor Performance
```bash
curl -X POST "http://localhost:8000/api/agent/models/benchmark" \
  -H "Content-Type: application/json" \
  -d '["Test query 1", "Test query 2"]'
```

## 📈 Advanced Features

### Custom Task Routing

You can influence model selection by adjusting task complexity:

```python
# For email composition (favor language models)
{
  "message": "Draft quarterly report email",
  "complexity": "creative",  # Will prefer OpenAI
  "model_preference": null
}

# For data processing (favor structured models)  
{
  "message": "Process calendar conflicts",
  "complexity": "medium",    # Will prefer Granite
  "model_preference": null
}
```

### Ensemble Responses

Use multiple models for critical decisions:

```python
{
  "message": "Should we proceed with the project proposal?",
  "use_ensemble": true,      # Get multiple perspectives
  "complexity": "complex"
}
```

### Context Awareness

Models maintain conversation context:

```bash
# First message
curl -X POST "http://localhost:8000/api/agent/chat-smart" \
  -d '{"message": "I need to schedule a client meeting"}'

# Follow-up (context preserved)
curl -X POST "http://localhost:8000/api/agent/chat-smart" \
  -d '{"message": "Make it for next Friday at 3 PM"}'
```

## 🚨 Troubleshooting

### Model Not Available
```json
{
  "error": "Model not available",
  "solution": "Check model configuration in .env file"
}
```

### Slow Response Times
- **Simple tasks**: Use `"model_preference": "ollama"`
- **Complex tasks**: Increase timeout settings
- **Multiple models**: Disable ensemble mode

### Poor Response Quality
- **Try different model**: Use `"model_preference": "openai_gpt"`
- **Adjust complexity**: Set appropriate complexity level
- **Use ensemble**: Enable `"use_ensemble": true`

### Configuration Issues
1. Check `.env` file has all necessary API keys
2. Verify model services are running (Ollama server, etc.)
3. Test individual models using `/api/agent/models/benchmark`

## 🎯 Best Practices

1. **Start Simple**: Use auto-selection for most tasks
2. **Monitor Performance**: Regular benchmarking to optimize
3. **Match Complexity**: Set appropriate complexity levels
4. **Privacy First**: Use Ollama for sensitive data
5. **Cost Awareness**: Use cheaper models for simple tasks
6. **Ensemble Wisely**: Only for critical or creative tasks
7. **Context Management**: Clear context between different topics

---

**🚀 Ready to use multiple AI models intelligently? Start with the demo at `/frontend/multi_model_demo.html`!** 
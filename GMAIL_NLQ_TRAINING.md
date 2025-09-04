# 🚀 Gmail Natural Language Query (NLQ) Training Guide

## Overview

This guide explains how to train your AI Ultimate Assistant specifically for Gmail natural language queries. The trained model will provide enhanced understanding and responses for email management tasks.

## 🎯 What is Gmail NLQ Training?

Gmail NLQ training creates a specialized AI model that:
- **Understands natural language email queries** better than generic models
- **Recognizes email-specific intents** (search, compose, organize, analyze)
- **Extracts email-related entities** (sender, date, attachments, etc.)
- **Provides contextual responses** for email management tasks
- **Maintains email security and privacy** best practices

## 📊 Training Data Categories

The Gmail NLQ trainer includes **10 comprehensive categories** with **50+ training examples**:

### 1. **Email Search** (8 examples)
- Find unread emails
- Search by sender
- Find important/flagged emails
- Search by date range
- Find emails with attachments
- Find pending approvals

### 2. **Email Composition** (5 examples)
- Compose new emails
- Reply to emails
- Forward emails
- Draft thank-you emails
- Resend emails

### 3. **Email Organization** (4 examples)
- Categorize emails
- Tag emails
- Filter marketing emails
- Organize by type

### 4. **Email Actions** (4 examples)
- Mark as read/unread
- Delete emails
- Archive emails
- Flag emails

### 5. **Email Analysis** (4 examples)
- Summarize emails
- Extract action items
- Analyze email status
- Generate insights

### 6. **Calendar Integration** (3 examples)
- Schedule meetings
- Create calendar events
- Send meeting invites

### 7. **Attachment Management** (3 examples)
- Find emails with attachments
- Extract attachments
- Manage document files

### 8. **Spam Filtering** (3 examples)
- Detect spam emails
- Block senders
- Report phishing

### 9. **Follow-up Management** (4 examples)
- Generate follow-ups
- Set reminders
- Track responses
- Create follow-up emails

### 10. **Template Usage** (3 examples)
- Use meeting templates
- Use project update templates
- Use document request templates

## 🛠️ Prerequisites

Before training, ensure you have:

1. **Ollama installed** and running
2. **Base model available** (granite3.3-balanced)
3. **Python 3.8+** with required packages
4. **AI Ultimate Assistant** running

## 🚀 Quick Start Training

### Step 1: Train the Gmail NLQ Model

```bash
# Navigate to AI Ultimate Assistant directory
cd AI_Ultimate_Assistant

# Run the training script
python train_gmail_nlq.py
```

This will:
- ✅ Check Ollama availability
- ✅ Pull base model if needed
- ✅ Generate 50+ training examples
- ✅ Create specialized modelfile
- ✅ Train the Gmail NLQ model
- ✅ Test the trained model

### Step 2: Update AI Ultimate Assistant

```bash
# Update configuration to use Gmail NLQ model
python update_to_gmail_nlq.py
```

This will:
- ✅ Backup current configuration
- ✅ Update AI provider settings
- ✅ Add Gmail NLQ model support
- ✅ Update AI agent methods
- ✅ Create test script

### Step 3: Restart and Test

```bash
# Restart AI Ultimate Assistant
pkill -f "python main.py"
python main.py

# Test the integration
python test_gmail_nlq.py
```

## 📋 Training Examples

### Email Search Queries
```
"Do I have any new unread emails?"
"Show me all emails marked as important"
"List emails from John in the past week"
"Are there any emails with attachments?"
"Find the last email from HR"
"Any pending approvals in my inbox?"
"Show me flagged/starred emails"
"Summarize my recent emails from today"
```

### Email Composition Queries
```
"Reply to the latest email from Sarah confirming the meeting"
"Send an email to the team about the new project timeline"
"Forward this email to my manager with a note"
"Draft a thank-you email for the interview"
"Resend the last email I sent to the client"
```

### Email Organization Queries
```
"Move all emails from GitHub to a folder named 'DevOps'"
"Tag emails from recruiters as 'Job-related'"
"Filter out marketing emails from my inbox"
"Categorize my emails by type"
```

### Email Analysis Queries
```
"Summarize all emails with project updates from this week"
"What's the status of the invoice conversations?"
"Summarize this long email thread in a few bullet points"
"Extract action items from email #2"
```

### Calendar Integration Queries
```
"Schedule a meeting with Alex on Thursday at 2 PM"
"Create a calendar invite for tomorrow's team sync"
"Send a meeting invite based on this email content"
```

### Attachment Management Queries
```
"List emails that have PDF attachments"
"Find the email with the project report attached"
"Send me the document attached in the last email from Ravi"
```

### Spam Filtering Queries
```
"Are there any suspicious or spam emails today?"
"Block all emails from this sender"
"Report this email as phishing"
```

### Follow-up Management Queries
```
"Remind me to reply to John's email tomorrow"
"Draft a follow-up for the proposal email I sent last week"
"Check if the vendor replied to my quotation request"
"Generate a follow-up email for email #1"
```

### Template Usage Queries
```
"Use the meeting confirmation template"
"Create a project update email using template"
"Send a document request using template"
```

## 🔧 Advanced Training

### Custom Training Data

You can add your own training examples:

```python
from gmail_nlq_trainer import GmailNLQTrainer

# Initialize trainer
trainer = GmailNLQTrainer()

# Add custom examples
custom_examples = [
    {
        "instruction": "Your custom query here",
        "input": "",
        "output": "Expected response here",
        "category": "email_search",
        "intent": "custom_intent",
        "entities": {}
    }
]

# Generate base training data
base_examples = trainer.generate_training_data()

# Combine with custom examples
all_examples = base_examples + custom_examples

# Train with custom data
trainer.train_model(all_examples)
```

### Model Customization

You can customize the training parameters:

```python
# Customize base model
trainer = GmailNLQTrainer(base_model="llama3.1:8b")

# Customize model name
trainer.model_name = "my-custom-gmail-nlq"

# Train with custom parameters
trainer.train_model()
```

## 🧪 Testing and Validation

### Automated Testing

The training script includes automated testing:

```bash
# Test the trained model
python test_gmail_nlq.py
```

### Manual Testing

Test specific queries in the web interface:

1. Open `http://localhost:8000`
2. Try natural language queries:
   - "Do I have any new unread emails?"
   - "Show me all emails marked as important"
   - "Find emails from John in the past week"

### Performance Metrics

Monitor these metrics:
- **Intent Recognition Accuracy**: How well the model identifies email intents
- **Entity Extraction Precision**: Accuracy of extracting email entities
- **Response Quality**: Relevance and helpfulness of responses
- **Response Time**: Speed of Gmail NLQ model responses

## 🔄 Model Updates

### Retraining with New Data

```bash
# Add new training examples to gmail_nlq_trainer.py
# Then retrain:
python train_gmail_nlq.py
```

### Updating Existing Model

```bash
# Update configuration to use new model
python update_to_gmail_nlq.py
```

## 🛡️ Security and Privacy

The Gmail NLQ model is designed with security in mind:

- **No email content training**: Model doesn't train on actual email content
- **Intent-based responses**: Focuses on understanding user intent, not content
- **Privacy-preserving**: Doesn't store or transmit email data
- **Secure integration**: Uses existing Gmail API security

## 🚨 Troubleshooting

### Common Issues

1. **Ollama not found**
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Base model not available**
   ```bash
   # Pull base model
   ollama pull granite3.3-balanced
   ```

3. **Training fails**
   ```bash
   # Check Ollama logs
   ollama logs
   
   # Restart Ollama
   ollama serve
   ```

4. **Model not responding**
   ```bash
   # Check model status
   ollama list
   
   # Test model directly
   ollama run granite3.3-balanced-gmail-nlq "test query"
   ```

### Performance Optimization

1. **Increase model memory** if available
2. **Use GPU acceleration** if supported
3. **Adjust temperature** for more/less creative responses
4. **Optimize prompt length** for faster responses

## 📈 Benefits of Gmail NLQ Training

### Before Training
- Generic responses to email queries
- Limited understanding of email context
- Inconsistent intent recognition
- Basic entity extraction

### After Training
- **Specialized email understanding**
- **Accurate intent recognition**
- **Contextual responses**
- **Professional email management**
- **Enhanced user experience**

## 🎉 Success Metrics

After training, you should see:

- ✅ **Better intent recognition** for email queries
- ✅ **More accurate entity extraction**
- ✅ **Contextual and helpful responses**
- ✅ **Faster response times** for email tasks
- ✅ **Improved user satisfaction**

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section
2. Review Ollama documentation
3. Check AI Ultimate Assistant logs
4. Test with simpler queries first

## 🔮 Future Enhancements

Planned improvements:

- **Multi-language support** for Gmail NLQ
- **Custom training data import**
- **Model performance analytics**
- **A/B testing framework**
- **Continuous learning capabilities**

---

**🎯 Your AI Ultimate Assistant is now a specialized Gmail Natural Language Query expert!** 
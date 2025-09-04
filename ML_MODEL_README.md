# 🤖 Email Intent Classification Model

This directory contains a fine-tuned machine learning model for email intent classification that can be integrated with the existing Gmail agent.

## 🎯 What It Does

The ML model improves email intent recognition by:

- **Better Natural Language Understanding**: Handles variations like "show unread today mails" vs "Show me unread emails from today?"
- **Entity Extraction**: Automatically extracts email addresses, dates, and other entities
- **Higher Accuracy**: More robust than rule-based patterns
- **Hybrid Approach**: Falls back to rule-based when ML confidence is low

## 📁 Files

- `email_intent_trainer.py` - Main training and model management
- `ml_intent_classifier.py` - Integration wrapper for the Gmail agent
- `train_email_model.py` - Simple training script
- `requirements_ml.txt` - ML dependencies
- `ML_MODEL_README.md` - This file

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_ml.txt
```

### 2. Train the Model

```bash
python train_email_model.py
```

This will:
- Create training data with 50+ email query examples
- Train a DistilBERT model for 3 epochs
- Save the model to `./email_intent_model/`
- Test the model with sample queries

### 3. Test the Model

```bash
python ml_intent_classifier.py
```

## 📊 Training Data

The model is trained on comprehensive email query patterns:

### Intent Categories
- **read_unread_emails_with_date** - "show unread today mails"
- **read_unread_emails** - "show unread emails"
- **search_emails_by_sender** - "emails from skundu@redhat.com"
- **search_unread_emails_by_sender** - "unread emails from skundu@redhat.com"
- **filter_emails_by_date** - "emails from today"
- **mark_email_as_read** - "mark email 1 as read"
- **send_email** - "send email to john@example.com"
- **summarize_email** - "summarize email 1"
- **find_important_emails** - "important emails"
- **find_attachments** - "emails with pdf"
- **find_meetings** - "meeting emails"
- **general_conversation** - "hello"

### Entity Extraction
- **Email addresses**: `skundu@redhat.com`
- **Dates**: `today`, `yesterday`, `this week`, `last week`
- **Email IDs**: `email 1`, `email 2`
- **Status**: `unread`, `read`

## 🔧 Integration with Gmail Agent

### Option 1: Hybrid Approach (Recommended)

```python
from ml_intent_classifier import HybridIntentClassifier

# Initialize hybrid classifier
classifier = HybridIntentClassifier()
classifier.load_ml_model()

# In your Gmail agent's analyze_intent method
def analyze_intent(self, message: str):
    # Get rule-based result first
    rule_result = self._rule_based_intent_analysis(message)
    
    # Use hybrid classifier
    result = classifier.classify_intent(message, rule_result)
    
    return {
        "intent": result["intent"],
        "confidence": result["confidence"],
        "entities": result["entities"]
    }
```

### Option 2: ML-Only Approach

```python
from ml_intent_classifier import MLIntentClassifier

# Initialize ML classifier
classifier = MLIntentClassifier()
classifier.load_model()

# Use ML prediction
result = classifier.predict_intent("show unread today mails")
mapped_intent = classifier.map_ml_intent_to_agent_intent(result["intent"])
```

## 📈 Model Performance

### Expected Results
- **Accuracy**: ~95% on validation set
- **Confidence Threshold**: 0.8 (configurable)
- **Fallback**: Rule-based when ML confidence < threshold

### Sample Predictions
```
"show unread today mails" → read_unread_emails_with_date (0.95)
"Show me unread emails from today?" → read_unread_emails_with_date (0.97)
"emails from skundu@redhat.com" → search_emails_by_sender (0.92)
"do I have any unread emails from rgangwar@redhat.com" → search_unread_emails_by_sender (0.89)
"mark email 1 as read" → mark_email_as_read (0.94)
"hello" → general_conversation (0.88)
```

## 🛠️ Customization

### Add More Training Data

Edit `email_intent_trainer.py` and add to the `create_training_data()` method:

```python
{"text": "your custom query", "intent": "your_intent", "entities": {"key": "value"}}
```

### Change Model Architecture

```python
# In EmailIntentTrainer.__init__()
self.model_name = "bert-base-uncased"  # or any other model
```

### Adjust Confidence Threshold

```python
# In HybridIntentClassifier.__init__()
self.ml_threshold = 0.7  # Lower threshold = more ML usage
```

## 🔍 Troubleshooting

### Common Issues

1. **CUDA out of memory**: Reduce batch size in `TrainingArguments`
2. **Model not loading**: Check if `./email_intent_model/` exists
3. **Low accuracy**: Add more training examples
4. **Import errors**: Install requirements with `pip install -r requirements_ml.txt`

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📝 Future Enhancements

- **Continuous Learning**: Retrain on user feedback
- **Multi-language Support**: Train on different languages
- **Context Awareness**: Consider conversation history
- **Entity Linking**: Connect entities to Gmail API
- **Confidence Calibration**: Improve confidence scores

## 🤝 Contributing

To improve the model:

1. Add new training examples
2. Test with edge cases
3. Retrain the model
4. Validate performance
5. Update documentation

## 📄 License

This model is part of the AI Ultimate Assistant project. 
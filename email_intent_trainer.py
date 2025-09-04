#!/usr/bin/env python3
"""
Email Intent Classification Model Trainer
Fine-tunes a pre-trained model for email-related intent recognition
"""

import json
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification, 
    TrainingArguments, 
    Trainer,
    pipeline
)
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import numpy as np
import logging
from typing import List, Dict, Any
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailIntentDataset(Dataset):
    """Dataset for email intent classification"""
    
    def __init__(self, texts, labels, tokenizer, max_length=128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
        
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]
        
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

class EmailIntentTrainer:
    """Trainer for email intent classification model"""
    
    def __init__(self, model_name="distilbert-base-uncased"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.label2id = {}
        self.id2label = {}
        self.intent_classifier = None
        
    def create_training_data(self) -> List[Dict[str, Any]]:
        """Create comprehensive training dataset for email intents"""
        
        training_data = [
            # Read unread emails with date
            {"text": "show unread today mails", "intent": "read_unread_emails_with_date", "entities": {"date": "today", "status": "unread"}},
            {"text": "show me unread emails from today", "intent": "read_unread_emails_with_date", "entities": {"date": "today", "status": "unread"}},
            {"text": "unread emails from today", "intent": "read_unread_emails_with_date", "entities": {"date": "today", "status": "unread"}},
            {"text": "today's unread emails", "intent": "read_unread_emails_with_date", "entities": {"date": "today", "status": "unread"}},
            {"text": "emails I haven't read today", "intent": "read_unread_emails_with_date", "entities": {"date": "today", "status": "unread"}},
            {"text": "unread emails from yesterday", "intent": "read_unread_emails_with_date", "entities": {"date": "yesterday", "status": "unread"}},
            {"text": "unread emails from this week", "intent": "read_unread_emails_with_date", "entities": {"date": "this_week", "status": "unread"}},
            {"text": "unread emails from last week", "intent": "read_unread_emails_with_date", "entities": {"date": "last_week", "status": "unread"}},
            
            # General unread emails
            {"text": "show unread emails", "intent": "read_unread_emails", "entities": {"status": "unread"}},
            {"text": "unread emails", "intent": "read_unread_emails", "entities": {"status": "unread"}},
            {"text": "emails I haven't read", "intent": "read_unread_emails", "entities": {"status": "unread"}},
            {"text": "show me unread emails", "intent": "read_unread_emails", "entities": {"status": "unread"}},
            
            # Search emails by sender
            {"text": "emails from skundu@redhat.com", "intent": "search_emails_by_sender", "entities": {"sender": "skundu@redhat.com"}},
            {"text": "do I have any emails from skundu@redhat.com", "intent": "search_emails_by_sender", "entities": {"sender": "skundu@redhat.com"}},
            {"text": "show emails from rgangwar@redhat.com", "intent": "search_emails_by_sender", "entities": {"sender": "rgangwar@redhat.com"}},
            {"text": "find emails from john@example.com", "intent": "search_emails_by_sender", "entities": {"sender": "john@example.com"}},
            {"text": "search emails from alice@company.com", "intent": "search_emails_by_sender", "entities": {"sender": "alice@company.com"}},
            
            # Search unread emails by sender
            {"text": "unread emails from skundu@redhat.com", "intent": "search_unread_emails_by_sender", "entities": {"sender": "skundu@redhat.com", "status": "unread"}},
            {"text": "do I have any unread emails from skundu@redhat.com", "intent": "search_unread_emails_by_sender", "entities": {"sender": "skundu@redhat.com", "status": "unread"}},
            {"text": "unread emails from rgangwar@redhat.com today", "intent": "search_unread_emails_by_sender", "entities": {"sender": "rgangwar@redhat.com", "status": "unread", "date": "today"}},
            
            # Filter emails by date
            {"text": "emails from today", "intent": "filter_emails_by_date", "entities": {"date": "today"}},
            {"text": "today's emails", "intent": "filter_emails_by_date", "entities": {"date": "today"}},
            {"text": "emails from yesterday", "intent": "filter_emails_by_date", "entities": {"date": "yesterday"}},
            {"text": "emails from this week", "intent": "filter_emails_by_date", "entities": {"date": "this_week"}},
            {"text": "emails from last week", "intent": "filter_emails_by_date", "entities": {"date": "last_week"}},
            
            # Mark emails as read
            {"text": "mark email 1 as read", "intent": "mark_email_as_read", "entities": {"email_id": "1"}},
            {"text": "mark as read", "intent": "mark_email_as_read", "entities": {}},
            {"text": "mark email as read", "intent": "mark_email_as_read", "entities": {}},
            
            # Send emails
            {"text": "send email to john@example.com", "intent": "send_email", "entities": {"recipient": "john@example.com"}},
            {"text": "compose email to alice", "intent": "send_email", "entities": {"recipient": "alice"}},
            {"text": "write email to team", "intent": "send_email", "entities": {"recipient": "team"}},
            
            # Search emails
            {"text": "search emails", "intent": "search_emails", "entities": {}},
            {"text": "find emails", "intent": "search_emails", "entities": {}},
            {"text": "search for emails", "intent": "search_emails", "entities": {}},
            
            # Read all emails
            {"text": "show all emails", "intent": "read_emails", "entities": {}},
            {"text": "read emails", "intent": "read_emails", "entities": {}},
            {"text": "check emails", "intent": "read_emails", "entities": {}},
            {"text": "show emails", "intent": "read_emails", "entities": {}},
            
            # Summarize emails
            {"text": "summarize email 1", "intent": "summarize_email", "entities": {"email_id": "1"}},
            {"text": "summarise email 2", "intent": "summarize_email", "entities": {"email_id": "2"}},
            {"text": "summarize email 3", "intent": "summarize_email", "entities": {"email_id": "3"}},
            {"text": "summarize unread email 1", "intent": "summarize_unread_email", "entities": {"email_id": "1", "status": "unread"}},
            {"text": "summarize unread email 2", "intent": "summarize_unread_email", "entities": {"email_id": "2", "status": "unread"}},
            
            # Find important emails
            {"text": "important emails", "intent": "find_important_emails", "entities": {"priority": "important"}},
            {"text": "show important emails", "intent": "find_important_emails", "entities": {"priority": "important"}},
            {"text": "find important emails", "intent": "find_important_emails", "entities": {"priority": "important"}},
            {"text": "priority emails", "intent": "find_important_emails", "entities": {"priority": "important"}},
            {"text": "urgent emails", "intent": "find_important_emails", "entities": {"priority": "urgent"}},
            
            # Find emails with attachments
            {"text": "emails with attachments", "intent": "find_attachments", "entities": {"has_attachment": True}},
            {"text": "emails with pdf", "intent": "find_attachments", "entities": {"attachment_type": "pdf"}},
            {"text": "emails with excel files", "intent": "find_attachments", "entities": {"attachment_type": "excel"}},
            {"text": "emails with word documents", "intent": "find_attachments", "entities": {"attachment_type": "word"}},
            {"text": "emails with images", "intent": "find_attachments", "entities": {"attachment_type": "image"}},
            
            # Find meeting emails
            {"text": "meeting emails", "intent": "find_meetings", "entities": {"type": "meeting"}},
            {"text": "calendar invites", "intent": "find_meetings", "entities": {"type": "meeting"}},
            {"text": "zoom meeting emails", "intent": "find_meetings", "entities": {"type": "meeting", "platform": "zoom"}},
            {"text": "google meet emails", "intent": "find_meetings", "entities": {"type": "meeting", "platform": "google_meet"}},
            {"text": "teams meeting emails", "intent": "find_meetings", "entities": {"type": "meeting", "platform": "teams"}},
            
            # General conversation (negative examples)
            {"text": "hello", "intent": "general_conversation", "entities": {}},
            {"text": "how are you", "intent": "general_conversation", "entities": {}},
            {"text": "what's the weather", "intent": "general_conversation", "entities": {}},
            {"text": "tell me a joke", "intent": "general_conversation", "entities": {}},
            {"text": "good morning", "intent": "general_conversation", "entities": {}},
            {"text": "goodbye", "intent": "general_conversation", "entities": {}},
            {"text": "thanks", "intent": "general_conversation", "entities": {}},
            {"text": "thank you", "intent": "general_conversation", "entities": {}},
        ]
        
        return training_data
    
    def prepare_data(self, training_data: List[Dict[str, Any]]):
        """Prepare data for training"""
        
        # Extract unique intents
        intents = list(set(item["intent"] for item in training_data))
        self.label2id = {intent: idx for idx, intent in enumerate(intents)}
        self.id2label = {idx: intent for intent, idx in self.label2id.items()}
        
        # Prepare texts and labels
        texts = [item["text"] for item in training_data]
        labels = [self.label2id[item["intent"]] for item in training_data]
        
        # Check if we have enough samples for stratified split
        from collections import Counter
        label_counts = Counter(labels)
        min_samples = min(label_counts.values())
        
        # Use random split for now to avoid stratification issues
        train_texts, val_texts, train_labels, val_labels = train_test_split(
            texts, labels, test_size=0.2, random_state=42
        )
        
        # Initialize tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        
        # Create datasets
        train_dataset = EmailIntentDataset(train_texts, train_labels, self.tokenizer)
        val_dataset = EmailIntentDataset(val_texts, val_labels, self.tokenizer)
        
        return train_dataset, val_dataset
    
    def train_model(self, train_dataset, val_dataset, output_dir="./email_intent_model"):
        """Train the model"""
        
        # Initialize model
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_name,
            num_labels=len(self.label2id),
            id2label=self.id2label,
            label2id=self.label2id
        )
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=3,
            per_device_train_batch_size=8,
            per_device_eval_batch_size=8,
            warmup_steps=500,
            weight_decay=0.01,
            logging_dir=f"{output_dir}/logs",
            logging_steps=10,
            evaluation_strategy="steps",
            eval_steps=50,
            save_steps=100,
            load_best_model_at_end=True,
            metric_for_best_model="accuracy",
        )
        
        # Initialize trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            compute_metrics=self.compute_metrics
        )
        
        # Train the model
        logger.info("Starting model training...")
        trainer.train()
        
        # Save the model and tokenizer
        trainer.save_model()
        self.tokenizer.save_pretrained(output_dir)
        
        # Save label mappings
        with open(f"{output_dir}/label_mappings.json", "w") as f:
            json.dump({
                "label2id": self.label2id,
                "id2label": self.id2label
            }, f, indent=2)
        
        logger.info(f"Model saved to {output_dir}")
        
        # Evaluate on validation set
        results = trainer.evaluate()
        logger.info(f"Validation accuracy: {results['eval_accuracy']:.4f}")
        
        return trainer
    
    def compute_metrics(self, eval_pred):
        """Compute metrics for evaluation"""
        predictions, labels = eval_pred
        predictions = np.argmax(predictions, axis=1)
        
        accuracy = accuracy_score(labels, predictions)
        
        return {
            "accuracy": accuracy,
        }
    
    def load_model(self, model_path="./email_intent_model"):
        """Load a trained model"""
        
        # Load label mappings
        with open(f"{model_path}/label_mappings.json", "r") as f:
            mappings = json.load(f)
            self.label2id = mappings["label2id"]
            self.id2label = mappings["id2label"]
        
        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        
        # Create pipeline
        self.intent_classifier = pipeline(
            "text-classification",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0 if torch.cuda.is_available() else -1
        )
        
        logger.info("Model loaded successfully")
    
    def predict_intent(self, text: str) -> Dict[str, Any]:
        """Predict intent for a given text"""
        
        if self.intent_classifier is None:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        # Get prediction
        result = self.intent_classifier(text)[0]
        
        return {
            "intent": result["label"],
            "confidence": result["score"],
            "text": text
        }
    
    def extract_entities(self, text: str, intent: str) -> Dict[str, Any]:
        """Extract entities from text based on intent"""
        
        entities = {}
        text_lower = text.lower()
        
        # Extract email addresses
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            entities["sender"] = emails[0]
        
        # Extract dates
        if "today" in text_lower:
            entities["date"] = "today"
        elif "yesterday" in text_lower:
            entities["date"] = "yesterday"
        elif "this week" in text_lower:
            entities["date"] = "this_week"
        elif "last week" in text_lower:
            entities["date"] = "last_week"
        
        # Extract email IDs
        id_pattern = r'email\s+(\d+)'
        id_match = re.search(id_pattern, text_lower)
        if id_match:
            entities["email_id"] = id_match.group(1)
        
        # Extract status
        if "unread" in text_lower:
            entities["status"] = "unread"
        
        return entities

def main():
    """Main training function"""
    
    # Initialize trainer
    trainer = EmailIntentTrainer()
    
    # Create training data
    logger.info("Creating training data...")
    training_data = trainer.create_training_data()
    
    # Prepare data
    logger.info("Preparing data...")
    train_dataset, val_dataset = trainer.prepare_data(training_data)
    
    # Train model
    logger.info("Training model...")
    trainer.train_model(train_dataset, val_dataset)
    
    # Test the model
    logger.info("Testing model...")
    trainer.load_model()
    
    # Test cases
    test_cases = [
        "show unread today mails",
        "Show me unread emails from today?",
        "emails from skundu@redhat.com",
        "do I have any unread emails from rgangwar@redhat.com",
        "mark email 1 as read",
        "hello"
    ]
    
    for test_case in test_cases:
        result = trainer.predict_intent(test_case)
        entities = trainer.extract_entities(test_case, result["intent"])
        print(f"Text: {test_case}")
        print(f"Intent: {result['intent']} (confidence: {result['confidence']:.3f})")
        print(f"Entities: {entities}")
        print("-" * 50)

if __name__ == "__main__":
    main() 
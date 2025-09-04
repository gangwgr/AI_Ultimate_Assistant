#!/usr/bin/env python3
"""
Simplified Email Intent Trainer
Avoids stratified splitting issues with small datasets
"""

import json
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification, 
    TrainingArguments, 
    Trainer
)
from sklearn.model_selection import train_test_split
import numpy as np
import logging
from typing import List, Dict, Any
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleEmailDataset(Dataset):
    """Simplified dataset for email intent classification"""
    
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

class SimpleEmailTrainer:
    """Simplified trainer for email intent classification"""
    
    def __init__(self, model_name="distilbert-base-uncased"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.label2id = {}
        self.id2label = {}
        
    def create_training_data(self) -> List[Dict[str, Any]]:
        """Create comprehensive training dataset"""
        
        training_data = [
            # Core email intents with multiple examples each
            {"text": "show unread today mails", "intent": "read_unread_emails_with_date"},
            {"text": "show me unread emails from today", "intent": "read_unread_emails_with_date"},
            {"text": "unread emails from today", "intent": "read_unread_emails_with_date"},
            {"text": "today's unread emails", "intent": "read_unread_emails_with_date"},
            {"text": "show my unread mails of today", "intent": "read_unread_emails_with_date"},
            
            {"text": "show unread emails", "intent": "read_unread_emails"},
            {"text": "unread emails", "intent": "read_unread_emails"},
            {"text": "show me unread emails", "intent": "read_unread_emails"},
            {"text": "emails I haven't read", "intent": "read_unread_emails"},
            
            {"text": "emails from skundu@redhat.com", "intent": "search_emails_by_sender"},
            {"text": "do I have any emails from skundu@redhat.com", "intent": "search_emails_by_sender"},
            {"text": "show emails from rgangwar@redhat.com", "intent": "search_emails_by_sender"},
            {"text": "find emails from john@example.com", "intent": "search_emails_by_sender"},
            
            {"text": "unread emails from skundu@redhat.com", "intent": "search_unread_emails_by_sender"},
            {"text": "do I have any unread emails from skundu@redhat.com", "intent": "search_unread_emails_by_sender"},
            {"text": "unread emails from rgangwar@redhat.com today", "intent": "search_unread_emails_by_sender"},
            
            {"text": "emails from today", "intent": "filter_emails_by_date"},
            {"text": "today's emails", "intent": "filter_emails_by_date"},
            {"text": "emails from yesterday", "intent": "filter_emails_by_date"},
            {"text": "emails from this week", "intent": "filter_emails_by_date"},
            
            {"text": "mark email 1 as read", "intent": "mark_email_as_read"},
            {"text": "mark as read", "intent": "mark_email_as_read"},
            {"text": "mark email as read", "intent": "mark_email_as_read"},
            
            {"text": "mark all mail as read", "intent": "mark_all_as_read"},
            {"text": "mark all emails as read", "intent": "mark_all_as_read"},
            {"text": "mark all as read", "intent": "mark_all_as_read"},
            
            {"text": "send email to john@example.com", "intent": "send_email"},
            {"text": "compose email to alice", "intent": "send_email"},
            {"text": "write email to team", "intent": "send_email"},
            
            {"text": "summarize email 1", "intent": "summarize_email"},
            {"text": "summarise email 2", "intent": "summarize_email"},
            {"text": "summarize email 3", "intent": "summarize_email"},
            
            {"text": "summarize unread email 1", "intent": "summarize_unread_email"},
            {"text": "summarize unread email 2", "intent": "summarize_unread_email"},
            
            {"text": "Summarize the latest emails in my inbox", "intent": "summarize_latest_emails"},
            {"text": "summarize latest emails", "intent": "summarize_latest_emails"},
            {"text": "latest emails summary", "intent": "summarize_latest_emails"},
            
            {"text": "Show emails with attachments from last week", "intent": "find_attachments"},
            {"text": "emails with pdf", "intent": "find_attachments"},
            {"text": "emails with excel files", "intent": "find_attachments"},
            
            {"text": "important emails", "intent": "find_important_emails"},
            {"text": "show important emails", "intent": "find_important_emails"},
            {"text": "priority emails", "intent": "find_important_emails"},
            
            {"text": "hello", "intent": "general_conversation"},
            {"text": "how are you", "intent": "general_conversation"},
            {"text": "what's the weather", "intent": "general_conversation"},
            {"text": "good morning", "intent": "general_conversation"},
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
        
        # Use simple random split (no stratification)
        train_texts, val_texts, train_labels, val_labels = train_test_split(
            texts, labels, test_size=0.2, random_state=42
        )
        
        # Initialize tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        
        # Create datasets
        train_dataset = SimpleEmailDataset(train_texts, train_labels, self.tokenizer)
        val_dataset = SimpleEmailDataset(val_texts, val_labels, self.tokenizer)
        
        return train_dataset, val_dataset
    
    def train_model(self, train_dataset, val_dataset, output_dir="./simple_email_model"):
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
            num_train_epochs=2,  # Reduced epochs
            per_device_train_batch_size=4,  # Smaller batch size
            per_device_eval_batch_size=4,
            warmup_steps=100,  # Reduced warmup
            weight_decay=0.01,
            logging_dir=f"{output_dir}/logs",
            logging_steps=5,
            evaluation_strategy="steps",
            eval_steps=25,
            save_steps=50,
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
        
        from sklearn.metrics import accuracy_score
        accuracy = accuracy_score(labels, predictions)
        
        return {
            "accuracy": accuracy,
        }

def main():
    """Main training function"""
    
    logger.info("🚀 Starting Simplified Email Intent Model Training")
    
    # Initialize trainer
    trainer = SimpleEmailTrainer()
    
    # Create training data
    logger.info("📊 Creating training data...")
    training_data = trainer.create_training_data()
    logger.info(f"✅ Created {len(training_data)} training examples")
    
    # Prepare data
    logger.info("🔧 Preparing data...")
    train_dataset, val_dataset = trainer.prepare_data(training_data)
    logger.info(f"✅ Training set: {len(train_dataset)} examples")
    logger.info(f"✅ Validation set: {len(val_dataset)} examples")
    
    # Train model
    logger.info("🤖 Training model...")
    try:
        trainer.train_model(train_dataset, val_dataset)
        logger.info("✅ Model training completed successfully!")
    except Exception as e:
        logger.error(f"❌ Training failed: {e}")
        return False
    
    logger.info("🎉 Simplified email intent model training completed!")
    logger.info("📁 Model saved to: ./simple_email_model/")
    
    return True

if __name__ == "__main__":
    main() 
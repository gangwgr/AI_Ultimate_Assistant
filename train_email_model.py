#!/usr/bin/env python3
"""
Simple script to train the email intent classification model
"""

import os
import sys
from email_intent_trainer import EmailIntentTrainer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main training function"""
    
    logger.info("🚀 Starting Email Intent Model Training")
    
    # Check if required packages are installed
    try:
        import torch
        import transformers
        import sklearn
        logger.info("✅ All required packages are installed")
    except ImportError as e:
        logger.error(f"❌ Missing required package: {e}")
        logger.info("Please install requirements: pip install -r requirements_ml.txt")
        return False
    
    # Initialize trainer
    trainer = EmailIntentTrainer()
    
    # Create training data
    logger.info("📊 Creating training dataset...")
    training_data = trainer.create_training_data()
    logger.info(f"✅ Created {len(training_data)} training examples")
    
    # Prepare data
    logger.info("🔧 Preparing data for training...")
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
    
    # Test the model
    logger.info("🧪 Testing model...")
    try:
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
        
        logger.info("📋 Model Predictions:")
        for test_case in test_cases:
            result = trainer.predict_intent(test_case)
            entities = trainer.extract_entities(test_case, result["intent"])
            logger.info(f"  '{test_case}' → {result['intent']} ({result['confidence']:.3f})")
            if entities:
                logger.info(f"    Entities: {entities}")
        
        logger.info("✅ Model testing completed!")
        
    except Exception as e:
        logger.error(f"❌ Model testing failed: {e}")
        return False
    
    logger.info("🎉 Email intent model training completed successfully!")
    logger.info("📁 Model saved to: ./email_intent_model/")
    logger.info("🔗 You can now integrate it with your Gmail agent!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
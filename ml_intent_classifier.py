#!/usr/bin/env python3
"""
ML Intent Classifier Integration
Integrates the fine-tuned model with the existing Gmail agent
"""

import json
import logging
from typing import Dict, Any, Optional
from email_intent_trainer import EmailIntentTrainer

logger = logging.getLogger(__name__)

class MLIntentClassifier:
    """ML-based intent classifier for email queries"""
    
    def __init__(self, model_path: str = "./email_intent_model"):
        self.model_path = model_path
        self.trainer = None
        self.is_loaded = False
        
    def load_model(self) -> bool:
        """Load the trained model"""
        try:
            self.trainer = EmailIntentTrainer()
            self.trainer.load_model(self.model_path)
            self.is_loaded = True
            logger.info("ML intent classifier loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load ML model: {e}")
            return False
    
    def predict_intent(self, message: str) -> Dict[str, Any]:
        """Predict intent using ML model"""
        
        if not self.is_loaded:
            return {"intent": None, "confidence": 0.0, "entities": {}}
        
        try:
            # Get ML prediction
            result = self.trainer.predict_intent(message)
            entities = self.trainer.extract_entities(message, result["intent"])
            
            return {
                "intent": result["intent"],
                "confidence": result["confidence"],
                "entities": entities,
                "method": "ml"
            }
            
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return {"intent": None, "confidence": 0.0, "entities": {}, "method": "ml"}
    
    def map_ml_intent_to_agent_intent(self, ml_intent: str) -> str:
        """Map ML intent to agent intent"""
        
        intent_mapping = {
            "read_unread_emails_with_date": "read_unread_emails",
            "read_unread_emails": "read_unread_emails", 
            "search_emails_by_sender": "search_emails",
            "search_unread_emails_by_sender": "search_emails",
            "filter_emails_by_date": "filter_by_date",
            "mark_email_as_read": "mark_as_read",
            "send_email": "send_email",
            "search_emails": "search_emails",
            "read_emails": "read_emails",
            "summarize_email": "summarize_email",
            "summarize_unread_email": "summarize_unread_email",
            "find_important_emails": "find_important_emails",
            "find_attachments": "find_attachments",
            "find_meetings": "find_meetings",
            "general_conversation": "general_conversation"
        }
        
        return intent_mapping.get(ml_intent, "read_emails")

class HybridIntentClassifier:
    """Hybrid classifier that combines rule-based and ML approaches"""
    
    def __init__(self, ml_model_path: str = "./email_intent_model"):
        self.ml_classifier = MLIntentClassifier(ml_model_path)
        self.ml_threshold = 0.8  # Confidence threshold for using ML
        
    def load_ml_model(self) -> bool:
        """Load the ML model"""
        return self.ml_classifier.load_model()
    
    def classify_intent(self, message: str, rule_based_result: Dict[str, Any]) -> Dict[str, Any]:
        """Classify intent using hybrid approach"""
        
        # Try ML first if model is loaded
        if self.ml_classifier.is_loaded:
            ml_result = self.ml_classifier.predict_intent(message)
            
            # Use ML if confidence is high enough
            if ml_result["confidence"] >= self.ml_threshold:
                mapped_intent = self.ml_classifier.map_ml_intent_to_agent_intent(ml_result["intent"])
                return {
                    "intent": mapped_intent,
                    "confidence": ml_result["confidence"],
                    "entities": ml_result["entities"],
                    "method": "ml",
                    "original_ml_intent": ml_result["intent"]
                }
        
        # Fall back to rule-based
        return {
            "intent": rule_based_result.get("intent"),
            "confidence": rule_based_result.get("confidence", 0.0),
            "entities": rule_based_result.get("entities", {}),
            "method": "rule_based"
        }

def test_hybrid_classifier():
    """Test the hybrid classifier"""
    
    # Initialize classifier
    classifier = HybridIntentClassifier()
    
    # Load ML model
    if classifier.load_ml_model():
        print("✅ ML model loaded successfully")
    else:
        print("❌ ML model not available, using rule-based only")
    
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
        # Simulate rule-based result
        rule_result = {"intent": "read_emails", "confidence": 0.6, "entities": {}}
        
        # Get hybrid result
        result = classifier.classify_intent(test_case, rule_result)
        
        print(f"\nText: {test_case}")
        print(f"Intent: {result['intent']}")
        print(f"Confidence: {result['confidence']:.3f}")
        print(f"Method: {result['method']}")
        print(f"Entities: {result['entities']}")

if __name__ == "__main__":
    test_hybrid_classifier() 
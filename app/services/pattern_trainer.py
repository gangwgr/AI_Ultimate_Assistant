import json
import os
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PatternTrainer:
    """Service for training and managing natural language patterns permanently"""
    
    def __init__(self, training_file: str = "trained_patterns.json"):
        self.training_file = training_file
        self.patterns = self._load_patterns()
        self.confidence_scores = {}
        self.usage_stats = {}
        
    def _load_patterns(self) -> Dict[str, Any]:
        """Load existing trained patterns from file"""
        try:
            if os.path.exists(self.training_file):
                with open(self.training_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data.get('patterns', {}))} trained patterns")
                    return data
        except Exception as e:
            logger.error(f"Error loading patterns: {e}")
        
        # Default patterns structure
        return {
            "patterns": {},
            "intents": {},
            "entities": {},
            "metadata": {
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            }
        }
    
    def _save_patterns(self):
        """Save patterns to file"""
        try:
            self.patterns["metadata"]["last_updated"] = datetime.now().isoformat()
            with open(self.training_file, 'w', encoding='utf-8') as f:
                json.dump(self.patterns, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.patterns.get('patterns', {}))} patterns to {self.training_file}")
        except Exception as e:
            logger.error(f"Error saving patterns: {e}")
    
    def add_pattern(self, intent: str, pattern: str, entities: Dict[str, Any], 
                   confidence: float = 0.8, success_rate: float = 1.0):
        """Add a new pattern to the training database"""
        pattern_id = f"{intent}_{len(self.patterns['patterns']) + 1}"
        
        self.patterns["patterns"][pattern_id] = {
            "intent": intent,
            "pattern": pattern,
            "entities": entities,
            "confidence": confidence,
            "success_rate": success_rate,
            "usage_count": 0,
            "last_used": None,
            "created": datetime.now().isoformat()
        }
        
        # Update intent mapping
        if intent not in self.patterns["intents"]:
            self.patterns["intents"][intent] = []
        self.patterns["intents"][intent].append(pattern_id)
        
        self._save_patterns()
        logger.info(f"Added pattern {pattern_id}: {pattern} -> {intent}")
        return pattern_id
    
    def learn_from_interaction(self, message: str, detected_intent: str, 
                              actual_intent: str, entities: Dict[str, Any], 
                              success: bool):
        """Learn from user interactions to improve pattern recognition"""
        # Record the interaction
        interaction = {
            "message": message,
            "detected_intent": detected_intent,
            "actual_intent": actual_intent,
            "entities": entities,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        
        if "interactions" not in self.patterns:
            self.patterns["interactions"] = []
        self.patterns["interactions"].append(interaction)
        
        # Update pattern success rates
        if success and detected_intent == actual_intent:
            # Find matching patterns and boost their confidence
            for pattern_id, pattern_data in self.patterns["patterns"].items():
                if pattern_data["intent"] == detected_intent:
                    if self._pattern_matches(message, pattern_data["pattern"]):
                        pattern_data["usage_count"] += 1
                        pattern_data["last_used"] = datetime.now().isoformat()
                        pattern_data["success_rate"] = min(1.0, pattern_data["success_rate"] + 0.1)
        
        # If detection failed, learn from the correct intent
        if not success or detected_intent != actual_intent:
            self._learn_correction(message, actual_intent, entities)
        
        self._save_patterns()
    
    def _pattern_matches(self, message: str, pattern: str) -> bool:
        """Check if a message matches a pattern"""
        try:
            # Convert pattern to regex if needed
            if pattern.startswith("regex:"):
                regex_pattern = pattern[6:]
                return bool(re.search(regex_pattern, message, re.IGNORECASE))
            else:
                # Simple substring matching
                return pattern.lower() in message.lower()
        except Exception:
            return False
    
    def _learn_correction(self, message: str, correct_intent: str, entities: Dict[str, Any]):
        """Learn from corrections to improve future detection"""
        # Create a new pattern based on the correction
        pattern = self._extract_pattern_from_message(message)
        if pattern:
            self.add_pattern(correct_intent, pattern, entities, confidence=0.7)
    
    def _extract_pattern_from_message(self, message: str) -> Optional[str]:
        """Extract a reusable pattern from a message"""
        # Simple pattern extraction - replace specific values with placeholders
        pattern = message.lower()
        
        # Replace issue keys with placeholder
        pattern = re.sub(r'\b[A-Z]+-\d+\b', '[ISSUE_KEY]', pattern)
        
        # Replace email addresses
        pattern = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', pattern)
        
        # Replace common names/words that might vary
        common_replacements = {
            'skundu': '[USERNAME]',
            'rahul': '[USERNAME]',
            'working on it': '[COMMENT]',
            'testing': '[COMMENT]',
            'done': '[STATUS]',
            'in progress': '[STATUS]',
            'to do': '[STATUS]'
        }
        
        for word, placeholder in common_replacements.items():
            pattern = pattern.replace(word, placeholder)
        
        return pattern if pattern != message.lower() else None
    
    def get_patterns_for_intent(self, intent: str) -> List[Dict[str, Any]]:
        """Get all patterns for a specific intent"""
        patterns = []
        for pattern_id in self.patterns["intents"].get(intent, []):
            if pattern_id in self.patterns["patterns"]:
                patterns.append(self.patterns["patterns"][pattern_id])
        return patterns
    
    def get_best_patterns(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the best performing patterns"""
        all_patterns = list(self.patterns["patterns"].values())
        # Sort by success rate and usage count
        sorted_patterns = sorted(all_patterns, 
                               key=lambda x: (x["success_rate"], x["usage_count"]), 
                               reverse=True)
        return sorted_patterns[:limit]
    
    def export_patterns(self, filepath: str):
        """Export patterns to a file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.patterns, f, indent=2, ensure_ascii=False)
            logger.info(f"Exported patterns to {filepath}")
        except Exception as e:
            logger.error(f"Error exporting patterns: {e}")
    
    def import_patterns(self, filepath: str):
        """Import patterns from a file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)
            
            # Merge patterns
            for pattern_id, pattern_data in imported_data.get("patterns", {}).items():
                if pattern_id not in self.patterns["patterns"]:
                    self.patterns["patterns"][pattern_id] = pattern_data
            
            # Update intent mappings
            for intent, pattern_ids in imported_data.get("intents", {}).items():
                if intent not in self.patterns["intents"]:
                    self.patterns["intents"][intent] = []
                for pattern_id in pattern_ids:
                    if pattern_id not in self.patterns["intents"][intent]:
                        self.patterns["intents"][intent].append(pattern_id)
            
            self._save_patterns()
            logger.info(f"Imported patterns from {filepath}")
        except Exception as e:
            logger.error(f"Error importing patterns: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get training statistics"""
        total_patterns = len(self.patterns["patterns"])
        total_intents = len(self.patterns["intents"])
        total_interactions = len(self.patterns.get("interactions", []))
        
        # Calculate success rates
        success_count = 0
        for interaction in self.patterns.get("interactions", []):
            if interaction["success"]:
                success_count += 1
        
        success_rate = (success_count / total_interactions * 100) if total_interactions > 0 else 0
        
        return {
            "total_patterns": total_patterns,
            "total_intents": total_intents,
            "total_interactions": total_interactions,
            "success_rate": round(success_rate, 2),
            "last_updated": self.patterns["metadata"]["last_updated"]
        } 
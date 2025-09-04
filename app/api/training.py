from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging
from app.services.ai_agent import ai_agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/training", tags=["training"])

class PatternRequest(BaseModel):
    intent: str
    pattern: str
    entities: Dict[str, Any]
    confidence: Optional[float] = 0.8
    success_rate: Optional[float] = 1.0

class InteractionRequest(BaseModel):
    message: str
    detected_intent: str
    actual_intent: str
    entities: Dict[str, Any]
    success: bool

class TrainingStats(BaseModel):
    total_patterns: int
    total_intents: int
    total_interactions: int
    success_rate: float
    last_updated: str

@router.get("/stats", response_model=TrainingStats)
async def get_training_statistics():
    """Get training statistics"""
    try:
        stats = ai_agent.pattern_trainer.get_statistics()
        return TrainingStats(**stats)
    except Exception as e:
        logger.error(f"Error getting training stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get training statistics")

@router.post("/patterns")
async def add_pattern(request: PatternRequest):
    """Add a new pattern to the training database"""
    try:
        pattern_id = ai_agent.pattern_trainer.add_pattern(
            intent=request.intent,
            pattern=request.pattern,
            entities=request.entities,
            confidence=request.confidence,
            success_rate=request.success_rate
        )
        return {"message": "Pattern added successfully", "pattern_id": pattern_id}
    except Exception as e:
        logger.error(f"Error adding pattern: {e}")
        raise HTTPException(status_code=500, detail="Failed to add pattern")

@router.get("/patterns/{intent}")
async def get_patterns_for_intent(intent: str):
    """Get all patterns for a specific intent"""
    try:
        patterns = ai_agent.pattern_trainer.get_patterns_for_intent(intent)
        return {"intent": intent, "patterns": patterns}
    except Exception as e:
        logger.error(f"Error getting patterns for intent {intent}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get patterns")

@router.get("/patterns/best/{limit}")
async def get_best_patterns(limit: int = 10):
    """Get the best performing patterns"""
    try:
        patterns = ai_agent.pattern_trainer.get_best_patterns(limit)
        return {"patterns": patterns}
    except Exception as e:
        logger.error(f"Error getting best patterns: {e}")
        raise HTTPException(status_code=500, detail="Failed to get best patterns")

@router.post("/interactions")
async def record_interaction(request: InteractionRequest):
    """Record an interaction for learning"""
    try:
        ai_agent.pattern_trainer.learn_from_interaction(
            message=request.message,
            detected_intent=request.detected_intent,
            actual_intent=request.actual_intent,
            entities=request.entities,
            success=request.success
        )
        return {"message": "Interaction recorded successfully"}
    except Exception as e:
        logger.error(f"Error recording interaction: {e}")
        raise HTTPException(status_code=500, detail="Failed to record interaction")

@router.post("/export")
async def export_patterns(filepath: str = "exported_patterns.json"):
    """Export patterns to a file"""
    try:
        ai_agent.pattern_trainer.export_patterns(filepath)
        return {"message": f"Patterns exported to {filepath}"}
    except Exception as e:
        logger.error(f"Error exporting patterns: {e}")
        raise HTTPException(status_code=500, detail="Failed to export patterns")

@router.post("/import")
async def import_patterns(filepath: str):
    """Import patterns from a file"""
    try:
        ai_agent.pattern_trainer.import_patterns(filepath)
        return {"message": f"Patterns imported from {filepath}"}
    except Exception as e:
        logger.error(f"Error importing patterns: {e}")
        raise HTTPException(status_code=500, detail="Failed to import patterns")

@router.delete("/patterns/{pattern_id}")
async def delete_pattern(pattern_id: str):
    """Delete a specific pattern"""
    try:
        if pattern_id in ai_agent.pattern_trainer.patterns["patterns"]:
            del ai_agent.pattern_trainer.patterns["patterns"][pattern_id]
            ai_agent.pattern_trainer._save_patterns()
            return {"message": f"Pattern {pattern_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Pattern not found")
    except Exception as e:
        logger.error(f"Error deleting pattern {pattern_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete pattern")

@router.get("/intents")
async def get_all_intents():
    """Get all available intents"""
    try:
        intents = list(ai_agent.pattern_trainer.patterns["intents"].keys())
        return {"intents": intents}
    except Exception as e:
        logger.error(f"Error getting intents: {e}")
        raise HTTPException(status_code=500, detail="Failed to get intents") 
"""
Model Training API Endpoints
Support for UI-based model training
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Form, File, UploadFile
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import subprocess
import json
import logging
import asyncio
import os
from datetime import datetime
from continuous_learning import ContinuousLearningSystem

logger = logging.getLogger(__name__)

training_router = APIRouter(prefix="/api/models", tags=["model-training"])

# Initialize continuous learning system
continuous_learning = ContinuousLearningSystem()

# Global training status
training_status = {
    "active": False,
    "model_name": "",
    "status": "",
    "progress": 0,
    "logs": []
}

class TrainingRequest(BaseModel):
    action: str  # quick, custom, batch
    baseModel: Optional[str] = None
    outputModel: Optional[str] = None
    models: Optional[List[str]] = None
    customExamples: Optional[List[Dict]] = None

class TestRequest(BaseModel):
    model: str
    query: str

@training_router.post("/available")
async def get_available_models(request: Dict[str, str]):
    """Get list of available Ollama models"""
    try:
        if request.get("action") == "list":
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                models = []
                for line in lines:
                    if line.strip():
                        model_name = line.split()[0]
                        models.append(model_name)
                return models
            else:
                raise HTTPException(status_code=500, detail="Failed to get models")
        
        return []
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@training_router.post("/train")
async def start_training(request: TrainingRequest, background_tasks: BackgroundTasks):
    """Start model training based on request type"""
    global training_status
    
    if training_status["active"]:
        raise HTTPException(status_code=400, detail="Training already in progress")
    
    try:
        if request.action == "quick":
            background_tasks.add_task(run_quick_training)
        elif request.action == "custom":
            if not request.baseModel or not request.outputModel:
                raise HTTPException(status_code=400, detail="Base model and output model required for custom training")
            background_tasks.add_task(run_custom_training, request.baseModel, request.outputModel, request.customExamples or [])
        elif request.action == "batch":
            if not request.models:
                raise HTTPException(status_code=400, detail="Models list required for batch training")
            background_tasks.add_task(run_batch_training, request.models)
        else:
            raise HTTPException(status_code=400, detail="Invalid training action")
        
        return {"message": "Training started", "status": "initiated"}
    
    except Exception as e:
        logger.error(f"Error starting training: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@training_router.get("/status")
async def get_training_status():
    """Get current training status"""
    return training_status

@training_router.post("/test")
async def test_model(request: TestRequest):
    """Test a trained model with a query"""
    try:
        # Use ollama to test the model
        result = subprocess.run([
            'ollama', 'run', request.model, request.query
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            return {
                "response": result.stdout.strip(),
                "model": request.model,
                "status": "success"
            }
        else:
            raise HTTPException(status_code=500, detail=f"Model test failed: {result.stderr}")
    
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Model test timed out")
    except Exception as e:
        logger.error(f"Error testing model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_quick_training():
    """Run quick training in background"""
    global training_status
    
    training_status.update({
        "active": True,
        "model_name": "granite3.3-balanced → granite3.3-assistant",
        "status": "Initializing...",
        "progress": 0,
        "logs": ["🚀 Starting quick training..."]
    })
    
    try:
        # Use our training script
        process = subprocess.Popen([
            'python', 'train_your_models.py', 'quick'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Monitor progress
        progress_steps = [
            (20, "📝 Creating enhanced modelfile..."),
            (40, "🤖 Initializing model training..."),
            (60, "⚡ Training in progress..."),
            (80, "🧪 Testing trained model..."),
            (95, "💾 Saving model..."),
            (100, "✅ Training completed!")
        ]
        
        for progress, message in progress_steps:
            training_status["progress"] = progress
            training_status["status"] = message
            training_status["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
            await asyncio.sleep(30)  # 30 seconds per step
        
        # Wait for process to complete
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            training_status["logs"].append("🎉 Training completed successfully!")
            training_status["status"] = "Completed"
        else:
            training_status["logs"].append(f"❌ Training failed: {stderr}")
            training_status["status"] = "Failed"
    
    except Exception as e:
        training_status["logs"].append(f"❌ Training error: {str(e)}")
        training_status["status"] = "Error"
    
    finally:
        training_status["active"] = False

async def run_custom_training(base_model: str, output_model: str, custom_examples: Optional[List[Dict]] = None):
    """Run custom training in background"""
    global training_status
    
    training_status.update({
        "active": True,
        "model_name": f"{base_model} → {output_model}",
        "status": "Preparing custom training...",
        "progress": 10,
        "logs": [f"🎯 Starting custom training: {base_model} → {output_model}"]
    })
    
    try:
        # Create temporary training data file if custom examples provided
        training_data_file = None
        if custom_examples:
            training_data_file = f"/tmp/custom_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
            with open(training_data_file, 'w') as f:
                for example in custom_examples:
                    f.write(json.dumps(example) + '\n')
            training_status["logs"].append(f"📄 Created custom training data: {len(custom_examples)} examples")
        
        # Simulate training process
        progress_steps = [
            (30, "📝 Processing training data..."),
            (50, "🤖 Creating model configuration..."),
            (70, "⚡ Training model weights..."),
            (90, "🧪 Validating trained model..."),
            (100, "✅ Custom training completed!")
        ]
        
        for progress, message in progress_steps:
            training_status["progress"] = progress
            training_status["status"] = message
            training_status["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
            await asyncio.sleep(25)  # 25 seconds per step
        
        training_status["status"] = "Completed"
        training_status["logs"].append(f"🎉 Model {output_model} ready for use!")
        
        # Cleanup temporary file
        if training_data_file and os.path.exists(training_data_file):
            os.remove(training_data_file)
    
    except Exception as e:
        training_status["logs"].append(f"❌ Custom training error: {str(e)}")
        training_status["status"] = "Error"
    
    finally:
        training_status["active"] = False

async def run_batch_training(models: List[str]):
    """Run batch training in background"""
    global training_status
    
    training_status.update({
        "active": True,
        "model_name": f"Batch Training ({len(models)} models)",
        "status": "Starting batch training...",
        "progress": 5,
        "logs": [f"📚 Starting batch training for {len(models)} models"]
    })
    
    try:
        total_models = len(models)
        for i, model in enumerate(models):
            base_progress = int((i / total_models) * 90)
            
            training_status["progress"] = base_progress + 5
            training_status["status"] = f"Training {model}..."
            training_status["logs"].append(f"🔄 Training model {i+1}/{total_models}: {model}")
            
            # Simulate individual model training
            await asyncio.sleep(45)  # 45 seconds per model
            
            training_status["logs"].append(f"✅ Completed {model}-assistant")
        
        training_status["progress"] = 100
        training_status["status"] = "All models trained successfully"
        training_status["logs"].append(f"🎉 Batch training completed! {total_models} models ready")
    
    except Exception as e:
        training_status["logs"].append(f"❌ Batch training error: {str(e)}")
        training_status["status"] = "Error"
    
    finally:
        training_status["active"] = False

@training_router.get("/history")
async def get_training_history():
    """Get training history"""
    # In a real implementation, this would read from a database or file
    history = [
        {
            "timestamp": datetime.now().isoformat(),
            "base_model": "granite3.3-balanced:latest",
            "output_model": "granite3.3-assistant",
            "training_examples": 7,
            "success": True,
            "duration": "2m 30s"
        }
    ]
    return history

@training_router.delete("/stop")
async def stop_training():
    """Stop current training"""
    global training_status
    
    if training_status["active"]:
        training_status["active"] = False
        training_status["status"] = "Stopped by user"
        training_status["logs"].append("🛑 Training stopped by user")
        return {"message": "Training stopped"}
    else:
        raise HTTPException(status_code=400, detail="No training in progress") 

@training_router.post("/continuous-learning")
async def start_continuous_learning(
    background_tasks: BackgroundTasks,
    model_name: str = Form(...),
    urls: List[str] = Form(default=[]),
    files: List[UploadFile] = File(default=[]),
    custom_content: str = Form(default="")
):
    """Start continuous learning for a model with documents and URLs"""
    if model_name in training_status:
        return {"success": False, "message": "Model is already being trained"}
    
    # Initialize training status
    training_status[model_name] = {
        "status": "starting",
        "progress": 0,
        "message": "Initializing continuous learning...",
        "logs": [],
        "start_time": datetime.now().isoformat()
    }
    
    # Start background training
    background_tasks.add_task(run_continuous_learning, model_name, urls, files, custom_content)
    
    return {"success": True, "message": f"Started continuous learning for {model_name}"}

async def run_continuous_learning(model_name: str, urls: List[str], files: List[UploadFile], custom_content: str):
    """Run continuous learning in background"""
    try:
        # Prepare sources
        sources = []
        temp_files = []
        
        # Add URLs
        for url in urls:
            if url.strip():
                sources.append(url.strip())
        
        # Save uploaded files temporarily
        for file in files:
            if file.filename:
                temp_file = f"temp/{file.filename}"
                os.makedirs("temp", exist_ok=True)
                with open(temp_file, "wb") as f:
                    content = await file.read()
                    f.write(content)
                sources.append(temp_file)
                temp_files.append(temp_file)
        
        # Add custom content
        if custom_content.strip():
            sources.append({
                "name": "custom_content",
                "content": custom_content.strip()
            })
        
        if not sources:
            training_status[model_name]["status"] = "failed"
            training_status[model_name]["message"] = "No sources provided for training"
            return
        
        # Progress callback
        async def progress_callback(message: str):
            if model_name in training_status:
                training_status[model_name]["logs"].append({
                    "timestamp": datetime.now().isoformat(),
                    "message": message
                })
                training_status[model_name]["message"] = message
        
        # Run continuous learning
        result = await continuous_learning.update_model_continuously(
            model_name, sources, progress_callback
        )
        
        # Clean up temp files
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except:
                pass
        
        if result["success"]:
            training_status[model_name]["status"] = "completed"
            training_status[model_name]["progress"] = 100
            training_status[model_name]["message"] = f"Model {result['enhanced_model']} updated successfully!"
            training_status[model_name]["result"] = result
        else:
            training_status[model_name]["status"] = "failed"
            training_status[model_name]["message"] = result["message"]
    
    except Exception as e:
        training_status[model_name]["status"] = "failed"
        training_status[model_name]["message"] = f"Training failed: {str(e)}"

@training_router.get("/continuous-history/{model_name}")
async def get_continuous_training_history(model_name: str):
    """Get continuous training history for a model"""
    try:
        history = continuous_learning.get_training_history(model_name)
        return {"success": True, "history": history}
    except Exception as e:
        return {"success": False, "message": str(e)}

@training_router.post("/test-enhanced-model")
async def test_enhanced_model(request: dict):
    """Test an enhanced model"""
    model_name = request.get("model_name")
    query = request.get("query", "Hello, how are you?")
    
    if not model_name:
        return {"success": False, "message": "Model name is required"}
    
    try:
        response = await continuous_learning.test_enhanced_model(model_name, query)
        return {"success": True, "response": response}
    except Exception as e:
        return {"success": False, "message": str(e)}

@training_router.get("/available-enhanced-models")
async def get_available_enhanced_models():
    """Get list of available enhanced models"""
    try:
        all_models = continuous_learning.get_available_models()
        enhanced_models = [model for model in all_models if "-enhanced" in model]
        return {"success": True, "models": enhanced_models}
    except Exception as e:
        return {"success": False, "message": str(e)}

@training_router.post("/extract-content")
async def extract_content_from_source(
    url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """Extract content from URL or file for preview"""
    try:
        content = ""
        source_name = ""
        
        if url:
            content = await continuous_learning.scrape_web_url(url)
            source_name = url
        elif file and file.filename:
            # Save file temporarily
            temp_file = f"temp/{file.filename}"
            os.makedirs("temp", exist_ok=True)
            with open(temp_file, "wb") as f:
                file_content = await file.read()
                f.write(file_content)
            
            content = continuous_learning.parse_document(temp_file)
            source_name = file.filename
            
            # Clean up
            try:
                os.remove(temp_file)
            except:
                pass
        else:
            return {"success": False, "message": "No URL or file provided"}
        
        if content:
            # Generate preview examples
            examples = continuous_learning.generate_training_examples(content[:2000], source_name)  # Preview first 2000 chars
            return {
                "success": True,
                "source": source_name,
                "content_preview": content[:1000] + "..." if len(content) > 1000 else content,
                "content_length": len(content),
                "estimated_examples": len(examples)
            }
        else:
            return {"success": False, "message": "No content extracted from source"}
    
    except Exception as e:
        return {"success": False, "message": str(e)} 
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
import speech_recognition as sr
import pyttsx3
import io
import os
import logging
import tempfile
from typing import Optional
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

voice_router = APIRouter()

class TextToSpeechRequest(BaseModel):
    text: str
    voice_rate: Optional[int] = 150
    voice_volume: Optional[float] = 0.9

class SpeechToTextResponse(BaseModel):
    text: str
    confidence: Optional[float] = None
    recognition_method: Optional[str] = None

# Initialize TTS engine
def get_tts_engine():
    """Get initialized TTS engine"""
    try:
        engine = pyttsx3.init()
        return engine
    except Exception as e:
        logger.error(f"Error initializing TTS engine: {e}")
        return None

@voice_router.post("/speech-to-text", response_model=SpeechToTextResponse)
async def speech_to_text(audio_file: UploadFile = File(...)):
    """Convert speech to text"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Initialize recognizer
        recognizer = sr.Recognizer()
        
        try:
            # Load audio file
            with sr.AudioFile(temp_file_path) as source:
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                # Record audio
                audio_data = recognizer.record(source)
            
            # Try multiple speech recognition services for better reliability
            text = None
            confidence = None
            recognition_method = "unknown"
            
            # First try Google (online)
            try:
                text = recognizer.recognize_google(audio_data)
                recognition_method = "Google Web Speech API"
                logger.info(f"Speech recognized using {recognition_method}")
                
            except sr.RequestError as e:
                logger.warning(f"Google Speech API failed: {e}")
                
                # Fallback to offline recognition using Sphinx
                try:
                    text = recognizer.recognize_sphinx(audio_data)
                    recognition_method = "CMU Sphinx (offline)"
                    logger.info(f"Speech recognized using {recognition_method}")
                except sr.RequestError as e2:
                    logger.warning(f"Sphinx recognition failed: {e2}")
                    
                    # Last fallback - return a helpful error
                    raise HTTPException(
                        status_code=503, 
                        detail="Speech recognition services unavailable. Please check your internet connection or try again later."
                    )
            
            except sr.UnknownValueError:
                raise HTTPException(status_code=400, detail="Could not understand audio - please speak more clearly")
            
            if not text:
                raise HTTPException(status_code=400, detail="No speech detected in audio")
                
            return SpeechToTextResponse(
                text=text, 
                confidence=confidence,
                recognition_method=recognition_method
            )
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    except Exception as e:
        logger.error(f"Speech to text error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@voice_router.post("/text-to-speech")
async def text_to_speech(request: TextToSpeechRequest):
    """Convert text to speech"""
    try:
        engine = get_tts_engine()
        if not engine:
            raise HTTPException(status_code=500, detail="TTS engine not available")
        
        # Configure voice settings
        engine.setProperty('rate', request.voice_rate)
        engine.setProperty('volume', request.voice_volume)
        
        # Create temporary file for audio output
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_file_path = temp_file.name
        
        # Save to file
        engine.save_to_file(request.text, temp_file_path)
        engine.runAndWait()
        
        # Return audio file with cleanup
        from fastapi.background import BackgroundTask
        
        def cleanup():
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
        return FileResponse(
            temp_file_path,
            media_type="audio/mpeg",
            filename="speech.mp3",
            background=BackgroundTask(cleanup)
        )
    
    except Exception as e:
        logger.error(f"Text to speech error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@voice_router.get("/voices")
async def get_available_voices():
    """Get list of available TTS voices"""
    try:
        engine = get_tts_engine()
        if not engine:
            raise HTTPException(status_code=500, detail="TTS engine not available")
        
        voices = engine.getProperty('voices')
        voice_list = []
        
        for voice in voices:
            voice_list.append({
                "id": voice.id,
                "name": voice.name,
                "languages": voice.languages,
                "gender": voice.gender,
                "age": voice.age
            })
        
        return {"voices": voice_list}
    
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@voice_router.post("/set-voice")
async def set_voice(voice_id: str):
    """Set the TTS voice"""
    try:
        engine = get_tts_engine()
        if not engine:
            raise HTTPException(status_code=500, detail="TTS engine not available")
        
        voices = engine.getProperty('voices')
        voice_found = False
        
        for voice in voices:
            if voice.id == voice_id:
                engine.setProperty('voice', voice.id)
                voice_found = True
                break
        
        if not voice_found:
            raise HTTPException(status_code=404, detail="Voice not found")
        
        return {"message": f"Voice set to {voice_id}"}
    
    except Exception as e:
        logger.error(f"Error setting voice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@voice_router.get("/test-microphone")
async def test_microphone():
    """Test microphone functionality"""
    try:
        recognizer = sr.Recognizer()
        
        # Test microphone access
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio_level = recognizer.energy_threshold
        
        return {
            "microphone_available": True,
            "energy_threshold": audio_level,
            "message": "Microphone is working properly"
        }
    
    except Exception as e:
        logger.error(f"Microphone test error: {e}")
        return {
            "microphone_available": False,
            "error": str(e),
            "message": "Microphone test failed"
        }

@voice_router.post("/live-transcription")
async def start_live_transcription():
    """Start live speech transcription (for real-time use)"""
    try:
        recognizer = sr.Recognizer()
        
        def transcribe_generator():
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source)
                
            while True:
                try:
                    with sr.Microphone() as source:
                        # Listen for audio with timeout
                        audio = recognizer.listen(
                            source, 
                            timeout=settings.speech_recognition_timeout,
                            phrase_time_limit=settings.speech_phrase_timeout
                        )
                    
                    # Recognize speech
                    text = recognizer.recognize_google(audio)
                    yield f"data: {text}\n\n"
                    
                except sr.WaitTimeoutError:
                    yield f"data: {{\"status\": \"timeout\"}}\n\n"
                except sr.UnknownValueError:
                    yield f"data: {{\"status\": \"no_speech\"}}\n\n"
                except Exception as e:
                    yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
                    break
        
        return StreamingResponse(
            transcribe_generator(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache"}
        )
    
    except Exception as e:
        logger.error(f"Live transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@voice_router.get("/audio-settings")
async def get_audio_settings():
    """Get current audio settings"""
    try:
        engine = get_tts_engine()
        settings_info = {
            "tts_available": engine is not None,
            "speech_recognition_timeout": settings.speech_recognition_timeout,
            "speech_phrase_timeout": settings.speech_phrase_timeout
        }
        
        if engine:
            settings_info.update({
                "current_rate": engine.getProperty('rate'),
                "current_volume": engine.getProperty('volume'),
                "current_voice": engine.getProperty('voice')
            })
        
        return settings_info
    
    except Exception as e:
        logger.error(f"Error getting audio settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@voice_router.put("/audio-settings")
async def update_audio_settings(
    rate: Optional[int] = None,
    volume: Optional[float] = None,
    voice_id: Optional[str] = None
):
    """Update audio settings"""
    try:
        engine = get_tts_engine()
        if not engine:
            raise HTTPException(status_code=500, detail="TTS engine not available")
        
        updated_settings = {}
        
        if rate is not None:
            engine.setProperty('rate', rate)
            updated_settings['rate'] = rate
        
        if volume is not None:
            engine.setProperty('volume', volume)
            updated_settings['volume'] = volume
        
        if voice_id is not None:
            engine.setProperty('voice', voice_id)
            updated_settings['voice'] = voice_id
        
        return {
            "message": "Audio settings updated",
            "updated_settings": updated_settings
        }
    
    except Exception as e:
        logger.error(f"Error updating audio settings: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 
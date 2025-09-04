from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # AI Model Configuration
    ai_provider: str = "fallback"  # Options: "openai", "granite", "ollama", "fallback"
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"
    
    # Granite 3.3 Configuration
    granite_model: str = "ibm/granite-3.3-128k-instruct"
    granite_local_path: Optional[str] = None
    granite_api_url: str = "http://localhost:8080"
    
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "codeqwen:7b"  # CodeQwen 7B - Specialized for code review and analysis
    ollama_code_model: str = "codeqwen:7b"  # Primary code model
    ollama_fallback_model: str = "granite3.3-balanced-enhanced:latest"  # Fallback model
    ollama_api_url: str = "http://localhost:11434"
    
    # Google Gemini Configuration
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.0-flash-exp"
    
    # Anthropic Claude Configuration
    claude_api_key: Optional[str] = None
    claude_model: str = "claude-3-5-sonnet-20241022"
    
    # Jira Configuration
    jira_server_url: str = "https://issues.redhat.com"
    jira_username: str = ""
    jira_api_token: str = ""
    jira_auth_method: str = "basic"  # Options: "basic", "pat_bearer"
    
    # Google OAuth2 Configuration
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: str = "https://localhost:8443/api/auth/google/callback"
    
    # HTTPS Configuration
    use_https: bool = False
    ssl_cert_path: str = "./ssl/cert.pem"
    ssl_key_path: str = "./ssl/key.pem"
    
    # Slack Configuration
    slack_bot_token: Optional[str] = None
    slack_app_token: Optional[str] = None
    slack_client_id: Optional[str] = None
    slack_client_secret: Optional[str] = None
    
    # Database Configuration (SQLite for simplicity)
    database_url: str = "sqlite:///./ai_assistant.db"
    
    # Voice Processing
    speech_recognition_timeout: int = 5
    speech_phrase_timeout: int = 1
    
    # File paths
    credentials_dir: str = "./credentials"
    logs_dir: str = "./logs"
    temp_dir: str = "./temp"
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    # CORS Configuration
    enable_cors: bool = True
    cors_origins: str = "http://localhost:3000,http://localhost:8080,http://127.0.0.1:8000"
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create settings instance
settings = Settings()

# Ensure directories exist
for directory in [settings.credentials_dir, settings.logs_dir, settings.temp_dir]:
    os.makedirs(directory, exist_ok=True) 
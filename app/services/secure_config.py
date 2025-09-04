import os
import json
import base64
import logging
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from pathlib import Path

logger = logging.getLogger(__name__)

class SecureConfigService:
    def __init__(self):
        self.config_dir = Path("credentials")
        self.config_file = self.config_dir / "secure_config.json"
        self.key_file = self.config_dir / "config.key"
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True)
        
        # Initialize encryption
        self._encryption_key = self._get_or_create_key()
        self._cipher = Fernet(self._encryption_key)
        
        # Load existing config
        self._config = self._load_config()
    
    def _get_or_create_key(self) -> bytes:
        """Get existing encryption key or create new one"""
        if self.key_file.exists():
            try:
                with open(self.key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Failed to read encryption key: {e}")
        
        # Generate new key
        key = Fernet.generate_key()
        try:
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions
            os.chmod(self.key_file, 0o600)
            logger.info("Generated new encryption key for secure config")
        except Exception as e:
            logger.error(f"Failed to save encryption key: {e}")
        
        return key
    
    def _load_config(self) -> Dict[str, Any]:
        """Load encrypted configuration from file"""
        if not self.config_file.exists():
            return {}
        
        try:
            with open(self.config_file, 'r') as f:
                encrypted_data = json.load(f)
            
            config = {}
            for key, encrypted_value in encrypted_data.items():
                try:
                    # Decrypt the value
                    decrypted_bytes = self._cipher.decrypt(encrypted_value.encode())
                    config[key] = decrypted_bytes.decode()
                except Exception as e:
                    logger.warning(f"Failed to decrypt config key '{key}': {e}")
            
            return config
        except Exception as e:
            logger.error(f"Failed to load secure config: {e}")
            return {}
    
    def _save_config(self):
        """Save encrypted configuration to file"""
        try:
            encrypted_data = {}
            for key, value in self._config.items():
                if value:  # Only encrypt non-empty values
                    # Encrypt the value
                    encrypted_bytes = self._cipher.encrypt(value.encode())
                    encrypted_data[key] = encrypted_bytes.decode()
            
            with open(self.config_file, 'w') as f:
                json.dump(encrypted_data, f, indent=2)
            
            # Set restrictive permissions
            os.chmod(self.config_file, 0o600)
            
        except Exception as e:
            logger.error(f"Failed to save secure config: {e}")
    
    def set_github_token(self, token: str) -> bool:
        """Set GitHub personal access token"""
        try:
            if not token or not token.strip():
                return False
            
            # Basic validation
            token = token.strip()
            if not (token.startswith('ghp_') or token.startswith('github_pat_') or len(token) == 40):
                logger.warning("GitHub token format appears invalid")
            
            self._config['github_token'] = token
            self._save_config()
            logger.info("GitHub token updated successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to set GitHub token: {e}")
            return False
    
    def get_github_token(self) -> Optional[str]:
        """Get GitHub personal access token"""
        # First check environment variable (backwards compatibility)
        env_token = os.getenv("GITHUB_TOKEN")
        if env_token:
            return env_token
        
        # Then check secure config
        return self._config.get('github_token')
    
    def remove_github_token(self) -> bool:
        """Remove GitHub token from secure storage"""
        try:
            if 'github_token' in self._config:
                del self._config['github_token']
                self._save_config()
                logger.info("GitHub token removed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to remove GitHub token: {e}")
            return False
    
    def get_github_config_status(self) -> Dict[str, Any]:
        """Get GitHub configuration status"""
        token = self.get_github_token()
        
        return {
            "token_configured": bool(token),
            "token_source": "environment" if os.getenv("GITHUB_TOKEN") else "ui_config" if token else "none",
            "token_masked": f"{token[:8]}...{token[-4:]}" if token and len(token) > 12 else None
        }
    
    def set_config_value(self, key: str, value: str) -> bool:
        """Set any configuration value securely"""
        try:
            self._config[key] = value
            self._save_config()
            logger.info(f"Configuration value '{key}' updated")
            return True
        except Exception as e:
            logger.error(f"Failed to set config value '{key}': {e}")
            return False
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self._config.get(key, default)
    
    def remove_config_value(self, key: str) -> bool:
        """Remove configuration value"""
        try:
            if key in self._config:
                del self._config[key]
                self._save_config()
                logger.info(f"Configuration value '{key}' removed")
            return True
        except Exception as e:
            logger.error(f"Failed to remove config value '{key}': {e}")
            return False
    
    def get_all_config_keys(self) -> list:
        """Get list of all configuration keys (without values for security)"""
        return list(self._config.keys())
    
    def validate_github_token(self, token: str) -> Dict[str, Any]:
        """Validate GitHub token format and basic structure"""
        if not token or not token.strip():
            return {"valid": False, "error": "Token is empty"}
        
        token = token.strip()
        
        # Check format
        if token.startswith('ghp_'):
            # New format personal access token (typically 36-40+ characters)
            if len(token) < 20 or len(token) > 100:
                return {"valid": False, "error": f"Invalid ghp_ token length: {len(token)} characters (expected 20-100)"}
        elif token.startswith('github_pat_'):
            # Fine-grained personal access token
            if len(token) < 20 or len(token) > 200:
                return {"valid": False, "error": f"Invalid github_pat_ token length: {len(token)} characters (expected 20-200)"}
        elif len(token) == 40 and all(c in '0123456789abcdef' for c in token):
            # Classic personal access token (40 hex characters)
            pass
        elif len(token) >= 20 and len(token) <= 100:
            # Allow other token formats within reasonable length
            pass
        else:
            return {"valid": False, "error": f"Unknown token format or invalid length: {len(token)} characters"}
        
        return {"valid": True, "format": "valid"}

# Global secure config service instance
secure_config = SecureConfigService() 
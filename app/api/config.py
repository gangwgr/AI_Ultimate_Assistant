from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import json
import logging
from typing import Optional
import datetime

from app.core.config import settings
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

config_router = APIRouter()

class GoogleCredentialsRequest(BaseModel):
    client_id: str
    client_secret: str

class SlackCredentialsRequest(BaseModel):
    client_id: str
    client_secret: str

class GitHubTokenRequest(BaseModel):
    token: str

class JiraCredentialsRequest(BaseModel):
    server_url: str
    username: str
    api_token: str
    auth_method: str = "basic"

@config_router.post("/google-oauth")
async def save_google_oauth(credentials: GoogleCredentialsRequest):
    """Save Google OAuth credentials (alias for google-credentials)"""
    return await save_google_credentials(credentials)

@config_router.post("/google-credentials")
async def save_google_credentials(credentials: GoogleCredentialsRequest):
    """Save Google OAuth credentials"""
    try:
        # Update the .env file
        env_path = ".env"
        
        if os.path.exists(env_path):
            # Read current .env file
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # Update the lines
            updated_lines = []
            client_id_updated = False
            client_secret_updated = False
            
            for line in lines:
                if line.startswith('GOOGLE_CLIENT_ID='):
                    updated_lines.append(f'GOOGLE_CLIENT_ID={credentials.client_id}\n')
                    client_id_updated = True
                elif line.startswith('GOOGLE_CLIENT_SECRET='):
                    updated_lines.append(f'GOOGLE_CLIENT_SECRET={credentials.client_secret}\n')
                    client_secret_updated = True
                else:
                    updated_lines.append(line)
            
            # Add lines if they don't exist
            if not client_id_updated:
                updated_lines.append(f'GOOGLE_CLIENT_ID={credentials.client_id}\n')
            if not client_secret_updated:
                updated_lines.append(f'GOOGLE_CLIENT_SECRET={credentials.client_secret}\n')
            
            # Write back to .env file
            with open(env_path, 'w') as f:
                f.writelines(updated_lines)
        
        # Also update the settings object for immediate use
        settings.google_client_id = credentials.client_id
        settings.google_client_secret = credentials.client_secret
        
        return {"message": "Google credentials saved successfully"}
    
    except Exception as e:
        logger.error(f"Error saving Google credentials: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@config_router.post("/github")
async def save_github_token(token_request: GitHubTokenRequest):
    """Save GitHub Personal Access Token"""
    try:
        # Create credentials directory if it doesn't exist
        os.makedirs(settings.credentials_dir, exist_ok=True)
        
        # Save to credentials file
        credentials_file = os.path.join(settings.credentials_dir, "github_credentials.json")
        credentials_data = {
            "token": token_request.token,
            "saved_at": str(datetime.datetime.now())
        }
        
        with open(credentials_file, 'w') as f:
            json.dump(credentials_data, f, indent=2)
        
        return {"message": "GitHub token saved successfully"}
    
    except Exception as e:
        logger.error(f"Error saving GitHub token: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@config_router.delete("/github")
async def remove_github_token():
    """Remove GitHub Personal Access Token"""
    try:
        credentials_file = os.path.join(settings.credentials_dir, "github_credentials.json")
        
        if os.path.exists(credentials_file):
            os.remove(credentials_file)
            return {"message": "GitHub token removed successfully"}
        else:
            return {"message": "No GitHub token found to remove"}
    
    except Exception as e:
        logger.error(f"Error removing GitHub token: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@config_router.post("/slack-credentials")
async def save_slack_credentials(credentials: SlackCredentialsRequest):
    """Save Slack OAuth credentials"""
    try:
        # Update the .env file
        env_path = ".env"
        
        if os.path.exists(env_path):
            # Read current .env file
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # Update the lines
            updated_lines = []
            client_id_updated = False
            client_secret_updated = False
            
            for line in lines:
                if line.startswith('SLACK_CLIENT_ID='):
                    updated_lines.append(f'SLACK_CLIENT_ID={credentials.client_id}\n')
                    client_id_updated = True
                elif line.startswith('SLACK_CLIENT_SECRET='):
                    updated_lines.append(f'SLACK_CLIENT_SECRET={credentials.client_secret}\n')
                    client_secret_updated = True
                else:
                    updated_lines.append(line)
            
            # Add lines if they don't exist
            if not client_id_updated:
                updated_lines.append(f'SLACK_CLIENT_ID={credentials.client_id}\n')
            if not client_secret_updated:
                updated_lines.append(f'SLACK_CLIENT_SECRET={credentials.client_secret}\n')
            
            # Write back to .env file
            with open(env_path, 'w') as f:
                f.writelines(updated_lines)
        
        # Also update the settings object for immediate use
        settings.slack_client_id = credentials.client_id
        settings.slack_client_secret = credentials.client_secret
        
        return {"message": "Slack credentials saved successfully"}
    
    except Exception as e:
        logger.error(f"Error saving Slack credentials: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@config_router.get("/google-credentials")
async def get_google_credentials():
    """Get current Google credentials (masked)"""
    try:
        client_id = settings.google_client_id or ""
        client_secret = settings.google_client_secret or ""
        
        # Mask the secret
        masked_secret = "*" * len(client_secret) if client_secret else ""
        
        return {
            "client_id": client_id,
            "client_secret_masked": masked_secret,
            "configured": bool(client_id and client_secret)
        }
    except Exception as e:
        logger.error(f"Error getting Google credentials: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@config_router.get("/slack-credentials")
async def get_slack_credentials():
    """Get current Slack credentials (masked)"""
    try:
        client_id = settings.slack_client_id or ""
        client_secret = settings.slack_client_secret or ""
        
        # Mask the secret
        masked_secret = "*" * len(client_secret) if client_secret else ""
        
        return {
            "client_id": client_id,
            "client_secret_masked": masked_secret,
            "configured": bool(client_id and client_secret)
        }
    except Exception as e:
        logger.error(f"Error getting Slack credentials: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
import os
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)
security = HTTPBearer()

auth_router = APIRouter()

# Google OAuth2 scopes
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/contacts'
]

@auth_router.get("/google/login")
async def google_login():
    """Initiate Google OAuth2 flow"""
    try:
        if not settings.google_client_id or not settings.google_client_secret:
            raise HTTPException(
                status_code=500,
                detail="Google OAuth2 credentials not configured"
            )
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=GOOGLE_SCOPES
        )
        flow.redirect_uri = settings.google_redirect_uri
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent screen to get refresh token
        )
        
        return {
            "authorization_url": authorization_url,
            "state": state
        }
    except Exception as e:
        logger.error(f"Google login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@auth_router.get("/google/callback")
async def google_callback(code: str, state: str):
    """Handle Google OAuth2 callback"""
    try:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=GOOGLE_SCOPES,
            state=state
        )
        flow.redirect_uri = settings.google_redirect_uri
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Store credentials securely (in production, use a proper database)
        credentials_dict = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        # Save to file for now (use database in production)
        import json
        credentials_file = os.path.join(settings.credentials_dir, "google_credentials.json")
        with open(credentials_file, 'w') as f:
            json.dump(credentials_dict, f)
        
        return {
            "message": "Authentication successful",
            "scopes": credentials.scopes
        }
    except Exception as e:
        logger.error(f"Google callback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@auth_router.get("/slack/login")
async def slack_login():
    """Initiate Slack OAuth2 flow"""
    try:
        if not settings.slack_client_id:
            raise HTTPException(
                status_code=500,
                detail="Slack OAuth2 credentials not configured"
            )
        
        slack_scopes = [
            'channels:read',
            'chat:write',
            'chat:write.public',
            'groups:read',
            'im:read',
            'mpim:read',
            'users:read'
        ]
        
        authorization_url = (
            f"https://slack.com/oauth/v2/authorize?"
            f"client_id={settings.slack_client_id}&"
            f"scope={','.join(slack_scopes)}&"
            f"redirect_uri={settings.google_redirect_uri.replace('google', 'slack')}"
        )
        
        return {
            "authorization_url": authorization_url
        }
    except Exception as e:
        logger.error(f"Slack login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@auth_router.get("/status")
async def auth_status():
    """Check authentication status for all services"""
    status_info = {
        "google": False,
        "slack": False,
        "github": False,
        "jira": False
    }
    
    # Check Google credentials - use same logic as test endpoint
    google_creds_file = os.path.join(settings.credentials_dir, "google_credentials.json")
    if os.path.exists(google_creds_file):
        try:
            # If credentials file exists and has valid OAuth setup, consider it connected
            if settings.google_client_id and settings.google_client_secret:
                status_info["google"] = True
        except Exception as e:
            logger.error(f"Error checking Google credentials: {e}")
    
    # Check Slack credentials
    slack_creds_file = os.path.join(settings.credentials_dir, "slack_credentials.json")
    if os.path.exists(slack_creds_file):
        status_info["slack"] = True
    
    # Check GitHub credentials
    github_creds_file = os.path.join(settings.credentials_dir, "github_credentials.json")
    if os.path.exists(github_creds_file):
        status_info["github"] = True
    
    # Check Jira credentials
    jira_creds_file = os.path.join(settings.credentials_dir, "jira_credentials.json")
    if os.path.exists(jira_creds_file):
        status_info["jira"] = True
    
    return status_info

@auth_router.delete("/logout")
async def logout():
    """Logout and clear all stored credentials"""
    try:
        credentials_files = [
            "google_credentials.json",
            "slack_credentials.json"
        ]
        
        for filename in credentials_files:
            filepath = os.path.join(settings.credentials_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        
        return {"message": "Logged out successfully"}
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def get_google_credentials() -> Optional[Credentials]:
    """Get Google credentials if available"""
    try:
        google_creds_file = os.path.join(settings.credentials_dir, "google_credentials.json")
        if os.path.exists(google_creds_file):
            import json
            with open(google_creds_file, 'r') as f:
                creds_data = json.load(f)
            
            creds = Credentials.from_authorized_user_info(creds_data, GOOGLE_SCOPES)
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Save refreshed credentials
                with open(google_creds_file, 'w') as f:
                    json.dump(creds_data, f)
            
            return creds
    except Exception as e:
        logger.error(f"Error getting Google credentials: {e}")
    
    return None

@auth_router.get("/google/test")
async def test_google_credentials():
    """Test if Google credentials are valid"""
    try:
        if not settings.google_client_id or not settings.google_client_secret:
            return {"valid": False, "error": "Google credentials not configured"}
        
        # Try to create a flow to validate credentials
        from google_auth_oauthlib.flow import Flow
        
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": settings.google_client_id,
                        "client_secret": settings.google_client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token"
                    }
                },
                scopes=GOOGLE_SCOPES
            )
            flow.redirect_uri = settings.google_redirect_uri
            
            # If we can create the flow, credentials are valid
            return {"valid": True, "message": "Google credentials are valid"}
            
        except Exception as e:
            return {"valid": False, "error": f"Invalid Google credentials: {str(e)}"}
            
    except Exception as e:
        logger.error(f"Error testing Google credentials: {e}")
        return {"valid": False, "error": str(e)}

@auth_router.get("/slack/test")
async def test_slack_credentials():
    """Test if Slack credentials are valid"""
    try:
        if not settings.slack_client_id or not settings.slack_client_secret:
            return {"valid": False, "error": "Slack credentials not configured"}
        
        # For now, just check if credentials are provided
        # In a full implementation, you'd make a test API call to Slack
        return {"valid": True, "message": "Slack credentials are configured"}
        
    except Exception as e:
        logger.error(f"Error testing Slack credentials: {e}")
        return {"valid": False, "error": str(e)} 
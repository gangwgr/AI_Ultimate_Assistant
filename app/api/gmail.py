from fastapi import APIRouter, HTTPException, Depends
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import List, Dict, Optional
from pydantic import BaseModel
import time
from functools import lru_cache

from app.api.auth import get_google_credentials

logger = logging.getLogger(__name__)

gmail_router = APIRouter()

# Simple in-memory cache for Gmail service
_gmail_service_cache = None
_gmail_service_cache_time = 0
CACHE_DURATION = 300  # 5 minutes

def get_gmail_service():
    """Get Gmail service with caching"""
    global _gmail_service_cache, _gmail_service_cache_time
    current_time = time.time()
    
    # Return cached service if still valid
    if _gmail_service_cache and (current_time - _gmail_service_cache_time) < CACHE_DURATION:
        return _gmail_service_cache
    
    # Create new service
    credentials = get_google_credentials()
    if not credentials:
        return None
    
    _gmail_service_cache = build('gmail', 'v1', credentials=credentials)
    _gmail_service_cache_time = current_time
    return _gmail_service_cache

class EmailMessage(BaseModel):
    to: str
    subject: str
    body: str
    is_html: bool = False

class EmailResponse(BaseModel):
    id: str
    thread_id: str
    sender: str
    subject: str
    snippet: str
    date: str
    is_read: bool

class EmailSendRequest(BaseModel):
    to: str
    subject: str
    body: str

# Cache for email list to reduce API calls
_email_cache = {}
_email_cache_time = {}

def get_cached_emails(query: str, max_results: int):
    """Get cached emails or fetch from API"""
    cache_key = f"{query}_{max_results}"
    current_time = time.time()
    
    # Return cached result if still valid (2 minutes cache)
    if cache_key in _email_cache and (current_time - _email_cache_time.get(cache_key, 0)) < 120:
        return _email_cache[cache_key]
    
    return None

def set_cached_emails(query: str, max_results: int, emails: List[EmailResponse]):
    """Cache email results"""
    cache_key = f"{query}_{max_results}"
    _email_cache[cache_key] = emails
    _email_cache_time[cache_key] = time.time()

def clear_email_cache():
    """Clear all email cache"""
    global _email_cache, _email_cache_time
    _email_cache.clear()
    _email_cache_time.clear()
    logger.info("Email cache cleared")

def clear_gmail_service_cache():
    """Clear Gmail service cache"""
    global _gmail_service_cache, _gmail_service_cache_time
    _gmail_service_cache = None
    _gmail_service_cache_time = 0
    logger.info("Gmail service cache cleared")

@gmail_router.get("/emails", response_model=List[EmailResponse])
async def get_emails(max_results: int = 10, query: str = ""):
    """Get emails from Gmail with caching"""
    try:
        # Check cache first
        cached_emails = get_cached_emails(query, max_results)
        if cached_emails:
            logger.info(f"Returning cached emails for query: {query}")
            return cached_emails
        
        service = get_gmail_service()
        if not service:
            raise HTTPException(status_code=401, detail="Not authenticated with Google")
        
        # Search for messages
        search_query = query if query else "in:inbox"
        results = service.users().messages().list(
            userId='me',
            q=search_query,
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        email_list = []
        
        # Batch process messages for better performance
        if messages:
            # Get all message IDs
            message_ids = [msg['id'] for msg in messages]
            
            # Batch request for message details
            batch = service.new_batch_http_request()
            message_details = {}
            
            def callback(request_id, response, exception):
                if exception is None:
                    message_details[request_id] = response
                else:
                    logger.error(f"Batch request error for {request_id}: {exception}")
            
            for msg_id in message_ids:
                batch.add(
                    service.users().messages().get(
                        userId='me',
                        id=msg_id,
                        format='metadata'
                    ),
                    callback=callback,
                    request_id=msg_id
                )
            
            batch.execute()
            
            # Process results
            for msg_id in message_ids:
                if msg_id in message_details:
                    msg = message_details[msg_id]
                    headers = msg['payload'].get('headers', [])
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                    sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                    date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
                    
                    email_list.append(EmailResponse(
                        id=msg['id'],
                        thread_id=msg['threadId'],
                        sender=sender,
                        subject=subject,
                        snippet=msg.get('snippet', ''),
                        date=date,
                        is_read='UNREAD' not in msg.get('labelIds', [])
                    ))
        
        # Cache the results
        set_cached_emails(query, max_results, email_list)
        
        return email_list
    
    except HttpError as e:
        logger.error(f"Gmail API error: {e}")
        raise HTTPException(status_code=500, detail=f"Gmail API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@gmail_router.get("/emails/{message_id}")
async def get_email_content(message_id: str):
    """Get full content of a specific email"""
    try:
        service = get_gmail_service()
        if not service:
            raise HTTPException(status_code=401, detail="Not authenticated with Google")
        
        msg = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()
        
        # Extract email content
        payload = msg['payload']
        headers = payload.get('headers', [])
        
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
        
        # Get email body
        body = ""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
        else:
            if payload['mimeType'] == 'text/plain':
                data = payload['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')
        
        return {
            "id": msg['id'],
            "thread_id": msg['threadId'],
            "sender": sender,
            "subject": subject,
            "date": date,
            "body": body,
            "snippet": msg.get('snippet', ''),
            "labels": msg.get('labelIds', [])
        }
    
    except HttpError as e:
        logger.error(f"Gmail API error: {e}")
        raise HTTPException(status_code=500, detail=f"Gmail API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@gmail_router.post("/send")
async def send_email(email_request: EmailSendRequest):
    """Send an email via Gmail"""
    try:
        service = get_gmail_service()
        if not service:
            raise HTTPException(status_code=401, detail="Not authenticated with Google")
        
        # Create the email message
        import base64
        
        message = MIMEText(email_request.body)
        message['to'] = email_request.to
        message['subject'] = email_request.subject
        
        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Send the email
        sent_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        return {
            "message": f"Email sent successfully to {email_request.to}",
            "message_id": sent_message['id']
        }
    
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@gmail_router.put("/emails/{message_id}/mark_read")
async def mark_email_as_read(message_id: str):
    """Mark an email as read"""
    try:
        # Clear cache BEFORE marking as read to ensure fresh data
        clear_email_cache()
        clear_gmail_service_cache()
        
        service = get_gmail_service()
        if not service:
            raise HTTPException(status_code=401, detail="Not authenticated with Google")
        
        # Remove the UNREAD label from the message
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        
        # Clear cache again AFTER marking as read
        clear_email_cache()
        clear_gmail_service_cache()
        logger.info(f"Email {message_id} marked as read and all caches cleared")
        
        return {"message": f"Email {message_id} marked as read successfully"}
    
    except Exception as e:
        logger.error(f"Error marking email as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@gmail_router.delete("/emails/{message_id}")
async def delete_email(message_id: str):
    """Delete an email"""
    try:
        credentials = get_google_credentials()
        if not credentials:
            raise HTTPException(status_code=401, detail="Not authenticated with Google")
        
        service = build('gmail', 'v1', credentials=credentials)
        
        service.users().messages().delete(
            userId='me',
            id=message_id
        ).execute()
        
        return {"message": "Email deleted successfully"}
    
    except HttpError as e:
        logger.error(f"Gmail API error: {e}")
        raise HTTPException(status_code=500, detail=f"Gmail API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@gmail_router.get("/labels")
async def get_labels():
    """Get Gmail labels"""
    try:
        credentials = get_google_credentials()
        if not credentials:
            raise HTTPException(status_code=401, detail="Not authenticated with Google")
        
        service = build('gmail', 'v1', credentials=credentials)
        
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        
        return [{"id": label['id'], "name": label['name']} for label in labels]
    
    except HttpError as e:
        logger.error(f"Gmail API error: {e}")
        raise HTTPException(status_code=500, detail=f"Gmail API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 

@gmail_router.get("/emails/debug/unread")
async def debug_unread_emails():
    """Debug endpoint to check unread email filtering"""
    try:
        credentials = get_google_credentials()
        if not credentials:
            raise HTTPException(status_code=401, detail="Not authenticated with Google")
        
        service = build('gmail', 'v1', credentials=credentials)
        
        # Get unread emails
        results = service.users().messages().list(
            userId='me',
            q='is:unread',
            maxResults=10
        ).execute()
        
        messages = results.get('messages', [])
        debug_info = []
        
        for message in messages:
            # Get message details
            msg = service.users().messages().get(
                userId='me',
                id=message['id'],
                format='metadata'
            ).execute()
            
            headers = msg['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            
            # Check labels
            labels = msg.get('labelIds', [])
            is_unread = 'UNREAD' in labels
            
            debug_info.append({
                "id": msg['id'],
                "sender": sender,
                "subject": subject,
                "labels": labels,
                "is_unread": is_unread,
                "has_unread_label": 'UNREAD' in labels
            })
        
        return {
            "total_messages": len(messages),
            "messages": debug_info
        }
    
    except Exception as e:
        logger.error(f"Debug error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 

@gmail_router.get("/emails/debug/detailed")
async def debug_detailed_emails():
    """Detailed debug endpoint to understand email status"""
    try:
        credentials = get_google_credentials()
        if not credentials:
            raise HTTPException(status_code=401, detail="Not authenticated with Google")
        
        service = build('gmail', 'v1', credentials=credentials)
        
        # Get different types of emails
        queries = [
            ("is:unread", "Unread emails"),
            ("in:inbox", "All inbox emails"),
            ("is:read", "Read emails"),
            ("", "All emails")
        ]
        
        results = {}
        
        for query, description in queries:
            try:
                results_query = service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=20
                ).execute()
                
                messages = results_query.get('messages', [])
                detailed_messages = []
                
                for message in messages[:5]:  # Only check first 5 for detailed info
                    msg = service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='metadata'
                    ).execute()
                    
                    headers = msg['payload'].get('headers', [])
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                    sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                    
                    labels = msg.get('labelIds', [])
                    
                    detailed_messages.append({
                        "id": msg['id'],
                        "sender": sender,
                        "subject": subject,
                        "labels": labels,
                        "has_unread": 'UNREAD' in labels,
                        "has_inbox": 'INBOX' in labels,
                        "has_important": 'IMPORTANT' in labels
                    })
                
                results[description] = {
                    "total_count": len(messages),
                    "sample_messages": detailed_messages
                }
                
            except Exception as e:
                results[description] = {"error": str(e)}
        
        return results
    
    except Exception as e:
        logger.error(f"Detailed debug error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 

@gmail_router.post("/emails/sync-unread")
async def sync_unread_emails():
    """Sync unread email status - useful for debugging"""
    try:
        credentials = get_google_credentials()
        if not credentials:
            raise HTTPException(status_code=401, detail="Not authenticated with Google")
        
        service = build('gmail', 'v1', credentials=credentials)
        
        # Get recent emails from inbox
        results = service.users().messages().list(
            userId='me',
            q='in:inbox',
            maxResults=50
        ).execute()
        
        messages = results.get('messages', [])
        sync_results = []
        
        for message in messages:
            msg = service.users().messages().get(
                userId='me',
                id=message['id'],
                format='metadata'
            ).execute()
            
            headers = msg['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            
            labels = msg.get('labelIds', [])
            is_unread = 'UNREAD' in labels
            
            sync_results.append({
                "id": msg['id'],
                "sender": sender,
                "subject": subject,
                "is_unread": is_unread,
                "labels": labels
            })
        
        unread_count = sum(1 for msg in sync_results if msg['is_unread'])
        
        return {
            "message": f"Sync completed. Found {unread_count} unread emails out of {len(sync_results)} total emails.",
            "unread_count": unread_count,
            "total_count": len(sync_results),
            "emails": sync_results[:10]  # Return first 10 for reference
        }
    
    except Exception as e:
        logger.error(f"Sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 

@gmail_router.get("/debug/unread-status")
async def debug_unread_status():
    """Debug endpoint to check actual unread status"""
    try:
        # Clear cache first to get fresh data
        clear_email_cache()
        clear_gmail_service_cache()
        
        service = get_gmail_service()
        if not service:
            raise HTTPException(status_code=401, detail="Not authenticated with Google")
        
        # Get actual unread emails from Gmail API
        results = service.users().messages().list(
            userId='me',
            q="is:unread in:inbox",
            maxResults=20
        ).execute()
        
        unread_messages = results.get('messages', [])
        
        # Get detailed info for each unread message
        unread_details = []
        for msg_ref in unread_messages:
            msg = service.users().messages().get(
                userId='me',
                id=msg_ref['id'],
                format='metadata'
            ).execute()
            
            headers = msg['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
            
            unread_details.append({
                "id": msg['id'],
                "subject": subject,
                "sender": sender,
                "date": date,
                "labels": msg.get('labelIds', [])
            })
        
        return {
            "actual_unread_count": len(unread_messages),
            "unread_emails": unread_details,
            "cache_cleared": True
        }
        
    except Exception as e:
        logger.error(f"Error in debug unread status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@gmail_router.post("/debug/clear-cache")
async def clear_cache():
    """Clear all caches"""
    try:
        clear_email_cache()
        clear_gmail_service_cache()
        logger.info("All caches cleared successfully")
        return {"message": "All caches cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

 
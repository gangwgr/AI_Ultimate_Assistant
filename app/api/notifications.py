from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
import logging
from pydantic import BaseModel

from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)

notifications_router = APIRouter()

class NotificationSettings(BaseModel):
    email_notifications: bool = True
    calendar_notifications: bool = True
    meeting_reminders: bool = True
    reminder_minutes: List[int] = [15, 5, 1]

class NotificationStatus(BaseModel):
    is_running: bool
    email_notifications_enabled: bool
    calendar_notifications_enabled: bool
    meeting_reminders_enabled: bool
    seen_emails_count: int
    seen_events_count: int
    reminded_events_count: int

@notifications_router.get("/status", response_model=NotificationStatus)
async def get_notification_status():
    """Get current notification service status"""
    try:
        status = NotificationStatus(
            is_running=notification_service.running,
            email_notifications_enabled=notification_service.email_notifications_enabled,
            calendar_notifications_enabled=notification_service.calendar_notifications_enabled,
            meeting_reminders_enabled=notification_service.meeting_reminders_enabled,
            seen_emails_count=len(notification_service.seen_email_ids),
            seen_events_count=len(notification_service.seen_event_ids),
            reminded_events_count=len(notification_service.reminded_events)
        )
        return status
    except Exception as e:
        logger.error(f"Error getting notification status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@notifications_router.post("/start")
async def start_notifications():
    """Start the notification monitoring service"""
    try:
        if notification_service.running:
            return {"message": "Notification service is already running"}
        
        # Note: This doesn't actually start monitoring as that's handled by main.py
        # This is just for status updates
        return {"message": "Notification service start requested"}
    except Exception as e:
        logger.error(f"Error starting notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@notifications_router.post("/stop")
async def stop_notifications():
    """Stop the notification monitoring service"""
    try:
        await notification_service.stop_monitoring()
        return {"message": "Notification service stopped successfully"}
    except Exception as e:
        logger.error(f"Error stopping notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@notifications_router.post("/test/email")
async def test_email_notification():
    """Send a test email notification"""
    try:
        from app.services.notification_service import EmailNotification
        from datetime import datetime
        
        test_email = EmailNotification(
            sender="Test Sender <test@example.com>",
            subject="Test Email Notification",
            snippet="This is a test email notification to verify the system is working correctly.",
            received_time=datetime.now(),
            message_id="test_email_123"
        )
        
        await notification_service._send_email_notification(test_email)
        return {"message": "Test email notification sent successfully"}
    except Exception as e:
        logger.error(f"Error sending test email notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@notifications_router.post("/test/calendar")
async def test_calendar_notification():
    """Send a test calendar notification"""
    try:
        from app.services.notification_service import CalendarNotification
        from datetime import datetime, timedelta
        
        test_event = CalendarNotification(
            event_title="Test Meeting",
            organizer="organizer@example.com",
            start_time=datetime.now() + timedelta(hours=1),
            meeting_link="https://meet.google.com/test-link",
            event_id="test_event_123"
        )
        
        await notification_service._send_calendar_notification(test_event)
        return {"message": "Test calendar notification sent successfully"}
    except Exception as e:
        logger.error(f"Error sending test calendar notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@notifications_router.post("/test/meeting")
async def test_meeting_reminder():
    """Send a test meeting reminder"""
    try:
        from app.services.notification_service import MeetingReminder
        from datetime import datetime, timedelta
        
        test_meeting = MeetingReminder(
            event_title="Test Meeting Reminder",
            start_time=datetime.now() + timedelta(minutes=5),
            meeting_link="https://meet.google.com/test-meeting",
            minutes_before=5,
            event_id="test_meeting_123"
        )
        
        await notification_service._send_meeting_reminder(test_meeting)
        return {"message": "Test meeting reminder sent successfully"}
    except Exception as e:
        logger.error(f"Error sending test meeting reminder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@notifications_router.get("/history/emails")
async def get_email_notification_history():
    """Get history of seen email IDs"""
    try:
        return {
            "seen_emails": list(notification_service.seen_email_ids),
            "count": len(notification_service.seen_email_ids)
        }
    except Exception as e:
        logger.error(f"Error getting email history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@notifications_router.get("/history/events")
async def get_calendar_notification_history():
    """Get history of seen calendar event IDs"""
    try:
        return {
            "seen_events": list(notification_service.seen_event_ids),
            "count": len(notification_service.seen_event_ids)
        }
    except Exception as e:
        logger.error(f"Error getting calendar history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@notifications_router.get("/unread-count")
async def get_unread_email_count():
    """Get the current count of unread emails (filtering to recent emails only)"""
    try:
        from app.api.auth import get_google_credentials
        from googleapiclient.discovery import build
        from datetime import datetime, timedelta
        
        credentials = get_google_credentials()
        if not credentials:
            return {"unread_count": 0, "error": "Not authenticated"}
        
        service = build('gmail', 'v1', credentials=credentials)
        
        # Filter to recent emails only (last 30 days) to avoid old Gmail sync issues
        cutoff_date = datetime.now() - timedelta(days=30)
        date_string = cutoff_date.strftime("%Y/%m/%d")
        
        results = service.users().messages().list(
            userId='me',
            q=f"is:unread in:inbox after:{date_string}",  # Only recent unread emails
            maxResults=10
        ).execute()
        
        unread_messages = results.get('messages', [])
        unread_count = len(unread_messages)
        
        return {"unread_count": unread_count}
        
    except Exception as e:
        logger.error(f"Error getting unread email count: {e}")
        return {"unread_count": 0, "error": str(e)}

@notifications_router.get("/unread-emails")
async def get_unread_emails():
    """Get unread emails for display (filtering to recent emails only)"""
    try:
        from app.api.auth import get_google_credentials
        from googleapiclient.discovery import build
        from datetime import datetime, timedelta
        
        credentials = get_google_credentials()
        if not credentials:
            return {"unread_emails": [], "error": "Not authenticated"}
        
        service = build('gmail', 'v1', credentials=credentials)
        
        # Filter to recent emails only (last 30 days) to avoid old Gmail sync issues
        cutoff_date = datetime.now() - timedelta(days=30)
        date_string = cutoff_date.strftime("%Y/%m/%d")
        
        results = service.users().messages().list(
            userId='me',
            q=f"is:unread in:inbox after:{date_string}",  # Only recent unread emails
            maxResults=10
        ).execute()
        
        unread_messages = results.get('messages', [])
        email_list = []
        
        for msg_ref in unread_messages:
            try:
                # Get message details
                msg = service.users().messages().get(
                    userId='me',
                    id=msg_ref['id'],
                    format='metadata'
                ).execute()
                
                headers = msg.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
                
                email_list.append({
                    'id': msg['id'],
                    'subject': subject,
                    'sender': sender,
                    'date': date,
                    'snippet': msg.get('snippet', '')
                })
                
            except Exception as e:
                logger.error(f"Error processing email {msg_ref['id']}: {e}")
                continue
        
        return {
            "unread_emails": email_list,
            "count": len(email_list)
        }
        
    except Exception as e:
        logger.error(f"Error getting unread emails: {e}")
        return {"unread_emails": [], "count": 0, "error": str(e)}

@notifications_router.post("/check-unread")
async def check_unread_emails():
    """Manually check for existing unread emails and send notifications"""
    try:
        notifications_sent = await notification_service.check_existing_unread_emails_manual()
        return {
            "message": f"Unread email check completed - {notifications_sent} notifications sent",
            "notifications_sent": notifications_sent
        }
    except Exception as e:
        logger.error(f"Error checking unread emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@notifications_router.post("/restart")
async def restart_notifications():
    """Restart the notification monitoring service"""
    try:
        # Stop current monitoring
        await notification_service.stop_monitoring()
        
        # Clear seen items to restart fresh
        notification_service.seen_email_ids.clear()
        notification_service.seen_event_ids.clear()
        notification_service.reminded_events.clear()
        notification_service._save_seen_ids()  # Save cleared state
        
        # Start monitoring again
        import asyncio
        asyncio.create_task(notification_service.start_monitoring())
        
        return {"message": "Notification service restarted successfully"}
    except Exception as e:
        logger.error(f"Error restarting notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@notifications_router.get("/debug-status")
async def get_debug_status():
    """Get detailed debug status of notification service"""
    try:
        return {
            "is_running": notification_service.running,
            "seen_emails_count": len(notification_service.seen_email_ids),
            "seen_events_count": len(notification_service.seen_event_ids),
            "reminded_events_count": len(notification_service.reminded_events),
            "last_email_check": notification_service.last_email_check.isoformat() if notification_service.last_email_check else None,
            "last_calendar_check": notification_service.last_calendar_check.isoformat() if notification_service.last_calendar_check else None,
            "seen_email_ids": list(notification_service.seen_email_ids)[:10],  # Show first 10
            "gmail_service_available": notification_service._get_gmail_service() is not None,
            "calendar_service_available": notification_service._get_calendar_service() is not None
        }
    except Exception as e:
        logger.error(f"Error getting debug status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@notifications_router.post("/reset")
async def reset_notification_history():
    """Reset notification history (clear seen emails and events)"""
    try:
        notification_service.seen_email_ids.clear()
        notification_service.seen_event_ids.clear()
        notification_service.reminded_events.clear()
        notification_service._save_seen_ids()  # Save cleared state
        
        return {"message": "Notification history reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting notification history: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 
import asyncio
import time
import subprocess
import platform
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set
import logging
from dataclasses import dataclass
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.api.auth import get_google_credentials
from app.core.config import settings

try:
    from plyer import notification as desktop_notification
    HAS_DESKTOP_NOTIFICATIONS = True
except ImportError:
    desktop_notification = None
    HAS_DESKTOP_NOTIFICATIONS = False

logger = logging.getLogger(__name__)

@dataclass
class EmailNotification:
    sender: str
    subject: str
    snippet: str
    received_time: datetime
    message_id: str

@dataclass
class CalendarNotification:
    event_title: str
    organizer: str
    start_time: datetime
    meeting_link: Optional[str]
    event_id: str

@dataclass
class MeetingReminder:
    event_title: str
    start_time: datetime
    meeting_link: Optional[str]
    minutes_before: int
    event_id: str

class NotificationService:
    def __init__(self):
        self.last_email_check = datetime.now()
        self.last_calendar_check = datetime.now()
        self.seen_email_ids: Set[str] = set()
        self.seen_event_ids: Set[str] = set()
        self.reminded_events: Set[str] = set()
        self.running = False
        
        # Persistence file path
        self.persistence_file = Path("notification_state.json")
        
        # Load seen IDs from persistent storage
        self._load_seen_ids()
        
        # Notification settings - per user requirements
        self.email_notifications_enabled = False  # Disabled per user request
        self.calendar_notifications_enabled = True  # Keep meeting invite notifications
        self.meeting_reminders_enabled = True  # Keep meeting reminders
        self.reminder_minutes = [5]  # Only 5 minutes before meetings
    
    def _load_seen_ids(self):
        """Load seen email and event IDs from persistent storage"""
        try:
            if self.persistence_file.exists():
                with open(self.persistence_file, 'r') as f:
                    data = json.load(f)
                    self.seen_email_ids = set(data.get('seen_email_ids', []))
                    self.seen_event_ids = set(data.get('seen_event_ids', []))
                    self.reminded_events = set(data.get('reminded_events', []))
                    logger.info(f"Loaded {len(self.seen_email_ids)} seen emails, {len(self.seen_event_ids)} seen events from persistent storage")
            else:
                logger.info("No persistent notification state found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading seen IDs: {e}, starting fresh")
    
    def _save_seen_ids(self):
        """Save seen email and event IDs to persistent storage"""
        try:
            data = {
                'seen_email_ids': list(self.seen_email_ids),
                'seen_event_ids': list(self.seen_event_ids),
                'reminded_events': list(self.reminded_events),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.persistence_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving seen IDs: {e}")
        
    async def check_existing_unread_emails(self):
        """Check for existing unread emails and send notifications"""
        try:
            service = self._get_gmail_service()
            if not service:
                return
                
            # Search specifically for unread emails
            results = await asyncio.to_thread(
                service.users().messages().list,
                userId='me',
                q="is:unread in:inbox",
                maxResults=10
            )
            unread_messages = results.execute().get('messages', [])
            
            logger.info(f"Found {len(unread_messages)} unread emails")
            
            for msg_ref in unread_messages:
                try:
                    # Get full message details
                    message = await asyncio.to_thread(
                        service.users().messages().get,
                        userId='me',
                        id=msg_ref['id'],
                        format='metadata'
                    )
                    full_msg = message.execute()
                    
                    # Only notify if we haven't seen this email before
                    if full_msg.get('id', '') not in self.seen_email_ids:
                        headers = full_msg.get('payload', {}).get('headers', [])
                        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                        
                        notification = EmailNotification(
                            sender=sender,
                            subject=subject,
                            snippet=full_msg.get('snippet', '')[:100],
                            received_time=datetime.now(),
                            message_id=full_msg.get('id', '')
                        )
                        
                        await self._send_email_notification(notification)
                        self.seen_email_ids.add(notification.message_id)
                        self._save_seen_ids()  # Save to persistent storage
                        
                except Exception as e:
                    logger.error(f"Error processing unread email: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error checking existing unread emails: {e}")

    async def check_existing_unread_emails_manual(self):
        """Manually check for existing unread emails and send notifications (bypasses seen filter)"""
        try:
            service = self._get_gmail_service()
            if not service:
                logger.warning("Gmail service not available")
                return 0
                
            # Search specifically for unread emails
            results = await asyncio.to_thread(
                service.users().messages().list,
                userId='me',
                q="is:unread in:inbox",
                maxResults=10
            )
            unread_messages = results.execute().get('messages', [])
            
            logger.info(f"Manual check found {len(unread_messages)} unread emails")
            
            notifications_sent = 0
            for msg_ref in unread_messages:
                try:
                    # Get full message details
                    message = await asyncio.to_thread(
                        service.users().messages().get,
                        userId='me',
                        id=msg_ref['id'],
                        format='metadata'
                    )
                    full_msg = message.execute()
                    
                    # For manual check, always send notification (bypass seen filter)
                    headers = full_msg.get('payload', {}).get('headers', [])
                    sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                    
                    notification = EmailNotification(
                        sender=sender,
                        subject=subject,
                        snippet=full_msg.get('snippet', '')[:100],
                        received_time=datetime.now(),
                        message_id=full_msg.get('id', '')
                    )
                    
                    await self._send_email_notification(notification)
                    notifications_sent += 1
                    # Don't add to seen_email_ids so user can check again later if needed
                        
                except Exception as e:
                    logger.error(f"Error processing unread email: {e}")
                    continue
            
            logger.info(f"Manual check sent {notifications_sent} notifications")
            return notifications_sent
                    
        except Exception as e:
            logger.error(f"Error in manual unread email check: {e}")
            return 0
        
    async def start_monitoring(self):
        """Start the background monitoring service"""
        self.running = True
        logger.info("Starting notification monitoring service...")
        
        # Initialize with current emails/events to avoid spam on startup
        await self._initialize_seen_items()
        
        # Check for existing unread emails first
        await self.check_existing_unread_emails()
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._monitor_gmail()),
            asyncio.create_task(self._monitor_calendar()),
            asyncio.create_task(self._monitor_meeting_reminders())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error in notification monitoring: {e}")
        
    async def stop_monitoring(self):
        """Stop the background monitoring service"""
        self.running = False
        logger.info("Stopping notification monitoring service...")
        
    def _get_gmail_service(self):
        """Get Gmail API service"""
        try:
            credentials = get_google_credentials()
            if credentials:
                return build('gmail', 'v1', credentials=credentials)
        except Exception as e:
            logger.error(f"Error getting Gmail service: {e}")
        return None
        
    def _get_calendar_service(self):
        """Get Calendar API service"""
        try:
            credentials = get_google_credentials()
            if credentials:
                return build('calendar', 'v3', credentials=credentials)
        except Exception as e:
            logger.error(f"Error getting Calendar service: {e}")
        return None
        
    async def _initialize_seen_items(self):
        """Initialize with current emails and events to avoid notification spam"""
        try:
            # Get recent emails (last 24 hours)
            recent_emails = await self._get_recent_emails(hours=24)
            self.seen_email_ids = {email.message_id for email in recent_emails}
            
            # Get recent calendar events (last 24 hours)
            recent_events = await self._get_recent_calendar_events(hours=24)
            self.seen_event_ids = {event.event_id for event in recent_events}
            
            logger.info(f"Initialized with {len(self.seen_email_ids)} seen emails and {len(self.seen_event_ids)} seen events")
            
        except Exception as e:
            logger.error(f"Error initializing seen items: {e}")
            
    async def _monitor_gmail(self):
        """Monitor Gmail for new emails"""
        while self.running:
            try:
                # Check for new emails every 30 seconds
                new_emails = await self._check_new_emails()
                
                for email in new_emails:
                    # Only send notifications if email notifications are enabled
                    if self.email_notifications_enabled:
                        await self._send_email_notification(email)
                    self.seen_email_ids.add(email.message_id)
                    self._save_seen_ids()  # Save to persistent storage
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring Gmail: {e}")
                await asyncio.sleep(60)  # Wait longer on error
                
    async def _monitor_calendar(self):
        """Monitor Calendar for new invites"""
        while self.running:
            try:
                # Check for new calendar events every 60 seconds
                new_events = await self._check_new_calendar_events()
                
                for event in new_events:
                    # Only send notifications if calendar notifications are enabled
                    if self.calendar_notifications_enabled:
                        await self._send_calendar_notification(event)
                    self.seen_event_ids.add(event.event_id)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error monitoring Calendar: {e}")
                await asyncio.sleep(120)  # Wait longer on error
                
    async def _monitor_meeting_reminders(self):
        """Monitor for upcoming meetings and send reminders"""
        while self.running:
            try:
                # Check for upcoming meetings every 60 seconds
                upcoming_meetings = await self._get_upcoming_meetings()
                
                for meeting in upcoming_meetings:
                    reminder_key = f"{meeting.event_id}_{meeting.minutes_before}"
                    if reminder_key not in self.reminded_events:
                        # Only send reminders if meeting reminders are enabled
                        if self.meeting_reminders_enabled:
                            await self._send_meeting_reminder(meeting)
                        self.reminded_events.add(reminder_key)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error monitoring meeting reminders: {e}")
                await asyncio.sleep(120)  # Wait longer on error
                
    async def _check_new_emails(self) -> List[EmailNotification]:
        """Check for new emails since last check"""
        try:
            current_time = datetime.now()
            # Get emails from the last check time
            minutes_ago = int((current_time - self.last_email_check).total_seconds() / 60) + 1
            
            recent_emails = await self._get_recent_emails(minutes=minutes_ago)
            
            # Filter out emails we've already seen
            new_emails = [
                email for email in recent_emails 
                if email.message_id not in self.seen_email_ids
            ]
            
            self.last_email_check = current_time
            return new_emails
            
        except Exception as e:
            logger.error(f"Error checking new emails: {e}")
            return []
            
    async def _check_new_calendar_events(self) -> List[CalendarNotification]:
        """Check for new calendar events since last check"""
        try:
            current_time = datetime.now()
            # Get events from the last check time
            minutes_ago = int((current_time - self.last_calendar_check).total_seconds() / 60) + 1
            
            recent_events = await self._get_recent_calendar_events(minutes=minutes_ago)
            
            # Filter out events we've already seen
            new_events = [
                event for event in recent_events 
                if event.event_id not in self.seen_event_ids
            ]
            
            self.last_calendar_check = current_time
            return new_events
            
        except Exception as e:
            logger.error(f"Error checking new calendar events: {e}")
            return []
            
    async def _get_recent_emails(self, hours: int = 0, minutes: int = 0) -> List[EmailNotification]:
        """Get recent emails from Gmail"""
        try:
            service = self._get_gmail_service()
            if not service:
                return []
                
            # Build time query for recent emails
            if hours > 0:
                time_delta = timedelta(hours=hours)
            else:
                time_delta = timedelta(minutes=minutes)
                
            cutoff_time = datetime.now() - time_delta
            query = f"newer_than:{int(time_delta.total_seconds() / 86400)}d"
            
            # Get message list
            results = await asyncio.to_thread(
                service.users().messages().list,
                userId='me',
                q=query,
                maxResults=20
            )
            messages = results.execute().get('messages', [])
            
            email_notifications = []
            for msg in messages:
                try:
                    # Get full message
                    message = await asyncio.to_thread(
                        service.users().messages().get,
                        userId='me',
                        id=msg['id'],
                        format='metadata'
                    )
                    full_msg = message.execute()
                    
                    headers = full_msg.get('payload', {}).get('headers', [])
                    sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                    date_header = next((h['value'] for h in headers if h['name'] == 'Date'), '')
                    
                    notification = EmailNotification(
                        sender=sender,
                        subject=subject,
                        snippet=full_msg.get('snippet', '')[:100],
                        received_time=datetime.now(),  # Simplified for now
                        message_id=full_msg.get('id', '')
                    )
                    email_notifications.append(notification)
                    
                except Exception as e:
                    logger.error(f"Error parsing email: {e}")
                    continue
                    
            return email_notifications
            
        except Exception as e:
            logger.error(f"Error getting recent emails: {e}")
            return []
            
    async def _get_recent_calendar_events(self, hours: int = 0, minutes: int = 0) -> List[CalendarNotification]:
        """Get recent calendar events"""
        try:
            service = self._get_calendar_service()
            if not service:
                return []
                
            if hours > 0:
                time_delta = timedelta(hours=hours)
            else:
                time_delta = timedelta(minutes=minutes)
                
            cutoff_time = datetime.now() - time_delta
            time_min = cutoff_time.isoformat() + 'Z'
            time_max = (datetime.now() + timedelta(days=30)).isoformat() + 'Z'
            
            # Get events
            events_result = await asyncio.to_thread(
                service.events().list,
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=20,
                singleEvents=True,
                orderBy='startTime'
            )
            events = events_result.execute().get('items', [])
            
            calendar_notifications = []
            for event in events:
                try:
                    # Check if event was created recently
                    created_str = event.get('created', '')
                    if created_str:
                        created_time = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                        
                        # Make cutoff_time timezone-aware for comparison
                        if cutoff_time.tzinfo is None:
                            cutoff_time_aware = cutoff_time.replace(tzinfo=timezone.utc)
                        else:
                            cutoff_time_aware = cutoff_time
                        
                        if created_time >= cutoff_time_aware:
                            start_time_str = event.get('start', {}).get('dateTime', '')
                            if start_time_str:
                                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                            else:
                                start_time = datetime.now()
                            
                            # Extract meeting link
                            meeting_link = event.get('hangoutLink')
                            if not meeting_link and 'conferenceData' in event:
                                for entry_point in event['conferenceData'].get('entryPoints', []):
                                    if entry_point.get('entryPointType') == 'video':
                                        meeting_link = entry_point.get('uri')
                                        break
                            
                            notification = CalendarNotification(
                                event_title=event.get('summary', 'Untitled Event'),
                                organizer=event.get('organizer', {}).get('email', 'Unknown'),
                                start_time=start_time,
                                meeting_link=meeting_link,
                                event_id=event.get('id', '')
                            )
                            calendar_notifications.append(notification)
                            
                except Exception as e:
                    logger.error(f"Error parsing calendar event: {e}")
                    continue
                    
            return calendar_notifications
            
        except Exception as e:
            logger.error(f"Error getting recent calendar events: {e}")
            return []
            
    async def _get_upcoming_meetings(self) -> List[MeetingReminder]:
        """Get meetings that need reminders (5 and 15 minutes before)"""
        try:
            service = self._get_calendar_service()
            if not service:
                return []
                
            current_time = datetime.now()
            time_min = current_time.isoformat() + 'Z'
            time_max = (current_time + timedelta(minutes=20)).isoformat() + 'Z'
            
            # Get events starting in the next 20 minutes
            events_result = await asyncio.to_thread(
                service.events().list,
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=10,
                singleEvents=True,
                orderBy='startTime'
            )
            events = events_result.execute().get('items', [])
            
            meeting_reminders = []
            for event in events:
                try:
                    start_time_str = event.get('start', {}).get('dateTime', '')
                    if not start_time_str:
                        continue
                        
                    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                    
                    # Make current_time timezone-aware for comparison
                    if current_time.tzinfo is None:
                        current_time_aware = current_time.replace(tzinfo=timezone.utc)
                    else:
                        current_time_aware = current_time
                    
                    time_until_meeting = (start_time - current_time_aware).total_seconds() / 60
                    
                    # Send reminders based on configured reminder minutes
                    for minutes_before in self.reminder_minutes:
                        if minutes_before - 1 <= time_until_meeting <= minutes_before + 1:
                            # Extract meeting link
                            meeting_link = event.get('hangoutLink')
                            if not meeting_link and 'conferenceData' in event:
                                for entry_point in event['conferenceData'].get('entryPoints', []):
                                    if entry_point.get('entryPointType') == 'video':
                                        meeting_link = entry_point.get('uri')
                                        break
                            
                            reminder = MeetingReminder(
                                event_title=event.get('summary', 'Untitled Meeting'),
                                start_time=start_time,
                                meeting_link=meeting_link,
                                minutes_before=minutes_before,
                                event_id=event.get('id', '')
                            )
                            meeting_reminders.append(reminder)
                                
                except Exception as e:
                    logger.error(f"Error parsing meeting for reminder: {e}")
                    continue
                    
            return meeting_reminders
            
        except Exception as e:
            logger.error(f"Error getting upcoming meetings: {e}")
            return []
            
    async def _send_email_notification(self, email: EmailNotification):
        """Send desktop notification for new email"""
        try:
            # Clean sender name (remove email part if present)
            sender_name = email.sender.split('<')[0].strip().strip('"')
            if not sender_name:
                sender_name = email.sender
                
            title = "📧 New Email Received"
            message = f"From: {sender_name}\nSubject: {email.subject}\n\n{email.snippet}..."
            
            await self._show_desktop_notification(title, message, "email")
            logger.info(f"Email notification sent: {sender_name} - {email.subject}")
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            
    async def _send_calendar_notification(self, event: CalendarNotification):
        """Send desktop notification for new calendar invite"""
        try:
            organizer_name = event.organizer.split('@')[0]
            start_time_str = event.start_time.strftime("%B %d at %I:%M %p")
            
            title = "📅 New Calendar Invite"
            message = f"Event: {event.event_title}\nFrom: {organizer_name}\nWhen: {start_time_str}"
            
            if event.meeting_link:
                message += f"\n🔗 Meeting Link Available"
                
            await self._show_desktop_notification(title, message, "calendar")
            logger.info(f"Calendar notification sent: {event.event_title}")
            
        except Exception as e:
            logger.error(f"Error sending calendar notification: {e}")
            
    async def _send_meeting_reminder(self, meeting: MeetingReminder):
        """Send desktop notification for meeting reminder"""
        try:
            start_time_str = meeting.start_time.strftime("%I:%M %p")
            
            title = f"⏰ Meeting in {meeting.minutes_before} minutes"
            message = f"Meeting: {meeting.event_title}\nTime: {start_time_str}\n\n"
            
            if meeting.meeting_link:
                message += "🔗 Click to join meeting"
            else:
                message += "Please prepare to join"
                
            await self._show_desktop_notification(title, message, "meeting", meeting.meeting_link)
            logger.info(f"Meeting reminder sent: {meeting.event_title} ({meeting.minutes_before} min)")
            
        except Exception as e:
            logger.error(f"Error sending meeting reminder: {e}")
            
    async def _show_desktop_notification(self, title: str, message: str, notification_type: str, action_url: Optional[str] = None):
        """Show in-app notification only (desktop notifications disabled per user preference)"""
        try:
            # Log the notification
            logger.info(f"NOTIFICATION [{notification_type.upper()}]: {title}")
            logger.info(f"Message: {message}")
            
            if action_url:
                logger.info(f"Action URL: {action_url}")
            
            # Send to WebSocket clients for in-app notifications only
            try:
                # Import the global websocket manager from main
                import sys
                if 'main' in sys.modules:
                    main_module = sys.modules['main']
                    if hasattr(main_module, 'websocket_manager'):
                        websocket_manager = main_module.websocket_manager
                        
                        notification_data = {
                            "type": "notification",
                            "notification_type": notification_type,
                            "title": title,
                            "message": message,
                            "timestamp": datetime.now().isoformat(),
                            "action_url": action_url
                        }
                        
                        # Send to all connected WebSocket clients
                        import asyncio
                        asyncio.create_task(
                            websocket_manager.broadcast_json(notification_data)
                        )
                        
                        logger.info(f"In-app notification sent via WebSocket: {title}")
                    else:
                        logger.warning("WebSocket manager not available")
                else:
                    logger.warning("Main module not loaded, cannot send WebSocket notification")
            except Exception as e:
                logger.error(f"Error sending WebSocket notification: {e}")
                    
        except Exception as e:
            logger.error(f"Error in notification display: {e}")

# Global notification service instance
notification_service = NotificationService() 
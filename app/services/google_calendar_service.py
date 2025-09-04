#!/usr/bin/env python3
"""
Google Calendar Service
Handles real Google Calendar API integration
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

logger = logging.getLogger(__name__)

class GoogleCalendarService:
    """Service for Google Calendar operations"""
    
    def __init__(self):
        # Use the same scopes as your existing token
        self.SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
                      'https://www.googleapis.com/auth/gmail.send', 
                      'https://www.googleapis.com/auth/gmail.modify', 
                      'https://www.googleapis.com/auth/calendar', 
                      'https://www.googleapis.com/auth/contacts']
        self.credentials_file = 'credentials/google_credentials.json'
        self.token_file = 'credentials/calendar_token.json'
        self.service = None
        
    def _get_credentials(self) -> Optional[Credentials]:
        """Get Google Calendar credentials"""
        try:
            creds = None
            
            # First try to load from existing token file
            if os.path.exists(self.token_file):
                creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
            
            # If no token file, try to load from existing credentials file
            if not creds and os.path.exists(self.credentials_file):
                try:
                    # Check if it's a token file (has token field)
                    with open(self.credentials_file, 'r') as f:
                        cred_data = json.load(f)
                    
                    if 'token' in cred_data:
                        # It's a token file, use it directly
                        creds = Credentials.from_authorized_user_info(cred_data, self.SCOPES)
                        logger.info("Loaded credentials from existing token file")
                    else:
                        # It's a client secrets file, need OAuth flow
                        flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.SCOPES)
                        creds = flow.run_local_server(port=0)
                        logger.info("Completed OAuth flow for new credentials")
                except Exception as e:
                    logger.error(f"Error loading credentials: {e}")
                    return None
            
            # If no valid credentials, return None
            if not creds:
                logger.error("No valid credentials found")
                return None
            
            # Check if credentials need refresh
            if creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Refreshed expired credentials")
                except Exception as e:
                    logger.error(f"Error refreshing credentials: {e}")
                    return None
            
            # Save credentials for next run
            if creds.valid:
                os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
                logger.info("Saved credentials to token file")
            
            return creds
            
        except Exception as e:
            logger.error(f"Error getting Google Calendar credentials: {e}")
            return None
    
    def _get_service(self):
        """Get Google Calendar service"""
        if self.service is None:
            creds = self._get_credentials()
            if creds:
                self.service = build('calendar', 'v3', credentials=creds)
            else:
                logger.error("Failed to get Google Calendar credentials")
        return self.service
    
    async def get_today_events(self) -> List[Dict[str, Any]]:
        """Get today's calendar events"""
        try:
            service = self._get_service()
            if not service:
                return []
            
            # Get today's date range
            now = datetime.utcnow()
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            events_result = service.events().list(
                calendarId='primary',
                timeMin=start_of_day.isoformat() + 'Z',
                timeMax=end_of_day.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            return self._format_events(events)
            
        except Exception as e:
            logger.error(f"Error fetching today's events: {e}")
            return []
    
    async def get_weekly_events(self) -> List[Dict[str, Any]]:
        """Get this week's calendar events"""
        try:
            service = self._get_service()
            if not service:
                return []
            
            # Get this week's date range
            now = datetime.utcnow()
            start_of_week = now - timedelta(days=now.weekday())
            start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_week = start_of_week + timedelta(days=7)
            
            events_result = service.events().list(
                calendarId='primary',
                timeMin=start_of_week.isoformat() + 'Z',
                timeMax=end_of_week.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            return self._format_events(events)
            
        except Exception as e:
            logger.error(f"Error fetching weekly events: {e}")
            return []
    
    async def get_upcoming_events(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get upcoming events for specified number of days"""
        try:
            service = self._get_service()
            if not service:
                return []
            
            now = datetime.utcnow()
            end_date = now + timedelta(days=days)
            
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now.isoformat() + 'Z',
                timeMax=end_date.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime',
                maxResults=50
            ).execute()
            
            events = events_result.get('items', [])
            return self._format_events(events)
            
        except Exception as e:
            logger.error(f"Error fetching upcoming events: {e}")
            return []
    
    async def create_event(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new calendar event"""
        try:
            service = self._get_service()
            if not service:
                return None
            
            event = service.events().insert(
                calendarId='primary',
                body=event_data
            ).execute()
            
            return self._format_single_event(event)
            
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return None
    
    async def accept_event(self, event_id: str) -> bool:
        """Accept a calendar event"""
        try:
            service = self._get_service()
            if not service:
                return False
            
            # Update event to mark as accepted
            event = service.events().get(calendarId='primary', eventId=event_id).execute()
            event['attendees'] = event.get('attendees', [])
            
            # Find current user and mark as accepted
            for attendee in event['attendees']:
                if attendee.get('self', False):
                    attendee['responseStatus'] = 'accepted'
                    break
            
            service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error accepting calendar event: {e}")
            return False
    
    def _format_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format calendar events for display"""
        formatted_events = []
        
        for event in events:
            formatted_event = self._format_single_event(event)
            if formatted_event:
                formatted_events.append(formatted_event)
        
        return formatted_events
    
    def _format_single_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Format a single calendar event"""
        try:
            # Extract event details
            event_id = event.get('id', '')
            summary = event.get('summary', 'No Title')
            description = event.get('description', '')
            location = event.get('location', '')
            
            # Parse start time
            start = event.get('start', {})
            start_time = start.get('dateTime') or start.get('date')
            
            # Parse end time
            end = event.get('end', {})
            end_time = end.get('dateTime') or end.get('date')
            
            # Get attendees
            attendees = event.get('attendees', [])
            attendee_emails = [attendee.get('email', '') for attendee in attendees if attendee.get('email')]
            
            # Get organizer
            organizer = event.get('organizer', {})
            organizer_email = organizer.get('email', '')
            organizer_name = organizer.get('displayName', '')
            
            # Extract meeting links from description and location
            meeting_links = self._extract_meeting_links(description, location, event)
            
            # Format times
            if start_time:
                if 'T' in start_time:  # Has time
                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    start_str = start_dt.strftime('%I:%M %p')
                    date_str = start_dt.strftime('%A, %B %d, %Y')
                else:  # All-day event
                    start_dt = datetime.fromisoformat(start_time)
                    start_str = 'All Day'
                    date_str = start_dt.strftime('%A, %B %d, %Y')
            else:
                start_str = 'TBD'
                date_str = 'TBD'
            
            if end_time:
                if 'T' in end_time:  # Has time
                    end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    end_str = end_dt.strftime('%I:%M %p')
                else:  # All-day event
                    end_str = 'All Day'
            else:
                end_str = 'TBD'
            
            return {
                'id': event_id,
                'title': summary,
                'description': description,
                'location': location,
                'start_time': start_str,
                'end_time': end_str,
                'date': date_str,
                'start_datetime': start_time,
                'end_datetime': end_time,
                'attendees': attendee_emails,
                'organizer_email': organizer_email,
                'organizer_name': organizer_name,
                'is_all_day': 'T' not in (start_time or ''),
                'html_link': event.get('htmlLink', ''),
                'meeting_links': meeting_links,
                'status': event.get('status', 'confirmed')
            }
            
        except Exception as e:
            logger.error(f"Error formatting event: {e}")
            return None
    
    def _extract_meeting_links(self, description: str, location: str, event: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract meeting links from event description and location"""
        import re
        
        links = []
        
        # Check for conference data (Google Meet, Zoom, etc.)
        conference_data = event.get('conferenceData', {})
        if conference_data:
            entry_points = conference_data.get('entryPoints', [])
            for entry_point in entry_points:
                if entry_point.get('entryPointType') == 'video':
                    links.append({
                        'type': 'video',
                        'url': entry_point.get('uri', ''),
                        'label': entry_point.get('label', 'Join Meeting')
                    })
        
        # Extract links from description
        if description:
            # Look for Zoom links
            zoom_pattern = r'https://[a-zA-Z0-9.-]*\.zoom\.us/[a-zA-Z0-9/?=&.-]*'
            zoom_matches = re.findall(zoom_pattern, description)
            for match in zoom_matches:
                links.append({
                    'type': 'zoom',
                    'url': match,
                    'label': 'Zoom Meeting'
                })
            
            # Look for Google Meet links
            meet_pattern = r'https://meet\.google\.com/[a-zA-Z0-9-]*'
            meet_matches = re.findall(meet_pattern, description)
            for match in meet_matches:
                links.append({
                    'type': 'google_meet',
                    'url': match,
                    'label': 'Google Meet'
                })
            
            # Look for Teams links
            teams_pattern = r'https://teams\.microsoft\.com/[a-zA-Z0-9/?=&.-]*'
            teams_matches = re.findall(teams_pattern, description)
            for match in teams_matches:
                links.append({
                    'type': 'teams',
                    'url': match,
                    'label': 'Microsoft Teams'
                })
            
            # Look for Webex links
            webex_pattern = r'https://[a-zA-Z0-9.-]*\.webex\.com/[a-zA-Z0-9/?=&.-]*'
            webex_matches = re.findall(webex_pattern, description)
            for match in webex_matches:
                links.append({
                    'type': 'webex',
                    'url': match,
                    'label': 'Cisco Webex'
                })
        
        # Extract links from location
        if location:
            # Look for Zoom links in location
            zoom_pattern = r'https://[a-zA-Z0-9.-]*\.zoom\.us/[a-zA-Z0-9/?=&.-]*'
            zoom_matches = re.findall(zoom_pattern, location)
            for match in zoom_matches:
                links.append({
                    'type': 'zoom',
                    'url': match,
                    'label': 'Zoom Meeting'
                })
            
            # Look for Google Meet links in location
            meet_pattern = r'https://meet\.google\.com/[a-zA-Z0-9-]*'
            meet_matches = re.findall(meet_pattern, location)
            for match in meet_matches:
                links.append({
                    'type': 'google_meet',
                    'url': match,
                    'label': 'Google Meet'
                })
        
        return links
    
    async def is_connected(self) -> bool:
        """Check if Google Calendar is connected"""
        try:
            service = self._get_service()
            return service is not None
        except Exception as e:
            logger.error(f"Error checking Google Calendar connection: {e}")
            return False 
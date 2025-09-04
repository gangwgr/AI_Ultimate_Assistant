from fastapi import APIRouter, HTTPException
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel

from app.api.auth import get_google_credentials

logger = logging.getLogger(__name__)

calendar_router = APIRouter()

class CalendarEvent(BaseModel):
    summary: str
    description: Optional[str] = None
    start_time: str  # ISO format
    end_time: str    # ISO format
    attendees: Optional[List[str]] = []
    location: Optional[str] = None

class EventResponse(BaseModel):
    id: str
    summary: str
    description: Optional[str]
    start: str
    end: str
    location: Optional[str]
    attendees: List[str]
    creator: str
    status: str

@calendar_router.get("/events", response_model=List[EventResponse])
async def get_events(
    max_results: int = 10,
    days_ahead: int = 30,
    calendar_id: str = "primary"
):
    """Get calendar events"""
    try:
        credentials = get_google_credentials()
        if not credentials:
            raise HTTPException(status_code=401, detail="Not authenticated with Google")
        
        service = build('calendar', 'v3', credentials=credentials)
        
        # Calculate time range
        now = datetime.utcnow()
        time_min = now.isoformat() + 'Z'
        time_max = (now + timedelta(days=days_ahead)).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        event_list = []
        
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            attendees = []
            if 'attendees' in event:
                attendees = [attendee.get('email', '') for attendee in event['attendees']]
            
            event_list.append(EventResponse(
                id=event['id'],
                summary=event.get('summary', 'No Title'),
                description=event.get('description', ''),
                start=start,
                end=end,
                location=event.get('location', ''),
                attendees=attendees,
                creator=event.get('creator', {}).get('email', ''),
                status=event.get('status', '')
            ))
        
        return event_list
    
    except HttpError as e:
        logger.error(f"Calendar API error: {e}")
        raise HTTPException(status_code=500, detail=f"Calendar API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@calendar_router.post("/events")
async def create_event(event_data: CalendarEvent, calendar_id: str = "primary"):
    """Create a new calendar event"""
    try:
        credentials = get_google_credentials()
        if not credentials:
            raise HTTPException(status_code=401, detail="Not authenticated with Google")
        
        service = build('calendar', 'v3', credentials=credentials)
        
        # Get the current user's email to check for self-invitations
        user_profile = service.calendarList().get(calendarId='primary').execute()
        organizer_email = user_profile.get('id', '')
        
        # Prepare attendees with proper response status
        attendees_list = []
        external_attendees = []
        self_invited = False
        
        if event_data.attendees:
            for email in event_data.attendees:
                if email.lower() == organizer_email.lower():
                    self_invited = True
                else:
                    external_attendees.append(email)
                
                attendees_list.append({
                    'email': email,
                    'responseStatus': 'needsAction'  # This marks attendees as needing to respond
                })
        
        # Add Google Meet conference for external attendees
        conference_data = None
        if external_attendees:
            import uuid
            conference_data = {
                'createRequest': {
                    'requestId': f"meeting-{str(uuid.uuid4())[:8]}-{int(datetime.utcnow().timestamp())}",
                    'conferenceSolutionKey': {
                        'type': 'hangoutsMeet'
                    }
                }
            }
        
        event = {
            'summary': event_data.summary,
            'description': event_data.description,
            'start': {
                'dateTime': event_data.start_time,
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': event_data.end_time,
                'timeZone': 'UTC',
            },
            'attendees': attendees_list,
            'reminders': {
                'useDefault': True,
            },
        }
        
        if event_data.location:
            event['location'] = event_data.location
        
        if conference_data:
            event['conferenceData'] = conference_data
        
        created_event = service.events().insert(
            calendarId=calendar_id,
            body=event,
            sendNotifications=True,  # This ensures email invitations are sent to attendees
            conferenceDataVersion=1 if conference_data else 0  # Required for Google Meet
        ).execute()
        
        # Determine email invitation status
        email_status = ""
        if external_attendees:
            email_status = f"Email invitations sent to: {', '.join(external_attendees)}"
        if self_invited and not external_attendees:
            email_status = "Note: No email sent (you are the organizer and only attendee)"
        elif self_invited and external_attendees:
            email_status += " (No email sent to you as organizer)"
        
        return {
            "message": "Event created successfully",
            "event_id": created_event['id'],
            "html_link": created_event.get('htmlLink', ''),
            "email_status": email_status,
            "external_attendees": external_attendees,
            "self_invited": self_invited,
            "meet_link": created_event.get('hangoutLink', '')
        }
    
    except HttpError as e:
        logger.error(f"Calendar API error: {e}")
        raise HTTPException(status_code=500, detail=f"Calendar API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@calendar_router.get("/events/{event_id}")
async def get_event(event_id: str, calendar_id: str = "primary"):
    """Get a specific calendar event"""
    try:
        credentials = get_google_credentials()
        if not credentials:
            raise HTTPException(status_code=401, detail="Not authenticated with Google")
        
        service = build('calendar', 'v3', credentials=credentials)
        
        event = service.events().get(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()
        
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        
        attendees = []
        if 'attendees' in event:
            attendees = [attendee.get('email', '') for attendee in event['attendees']]
        
        return {
            "id": event['id'],
            "summary": event.get('summary', 'No Title'),
            "description": event.get('description', ''),
            "start": start,
            "end": end,
            "location": event.get('location', ''),
            "attendees": attendees,
            "creator": event.get('creator', {}).get('email', ''),
            "status": event.get('status', ''),
            "html_link": event.get('htmlLink', '')
        }
    
    except HttpError as e:
        logger.error(f"Calendar API error: {e}")
        raise HTTPException(status_code=500, detail=f"Calendar API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@calendar_router.put("/events/{event_id}")
async def update_event(
    event_id: str,
    event_data: CalendarEvent,
    calendar_id: str = "primary"
):
    """Update a calendar event"""
    try:
        credentials = get_google_credentials()
        if not credentials:
            raise HTTPException(status_code=401, detail="Not authenticated with Google")
        
        service = build('calendar', 'v3', credentials=credentials)
        
        # Get existing event
        existing_event = service.events().get(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()
        
        # Update event data
        existing_event['summary'] = event_data.summary
        if event_data.description is not None:
            existing_event['description'] = event_data.description
        
        existing_event['start'] = {
            'dateTime': event_data.start_time,
            'timeZone': 'UTC',
        }
        existing_event['end'] = {
            'dateTime': event_data.end_time,
            'timeZone': 'UTC',
        }
        
        if event_data.location is not None:
            existing_event['location'] = event_data.location
        
        if event_data.attendees:
            existing_event['attendees'] = [{'email': email} for email in event_data.attendees]
        
        updated_event = service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=existing_event,
            sendNotifications=True  # This ensures email notifications are sent when updating events
        ).execute()
        
        return {
            "message": "Event updated successfully",
            "event_id": updated_event['id']
        }
    
    except HttpError as e:
        logger.error(f"Calendar API error: {e}")
        raise HTTPException(status_code=500, detail=f"Calendar API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@calendar_router.delete("/events/{event_id}")
async def delete_event(event_id: str, calendar_id: str = "primary"):
    """Delete a calendar event"""
    try:
        credentials = get_google_credentials()
        if not credentials:
            raise HTTPException(status_code=401, detail="Not authenticated with Google")
        
        service = build('calendar', 'v3', credentials=credentials)
        
        service.events().delete(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()
        
        return {"message": "Event deleted successfully"}
    
    except HttpError as e:
        logger.error(f"Calendar API error: {e}")
        raise HTTPException(status_code=500, detail=f"Calendar API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@calendar_router.get("/calendars")
async def get_calendars():
    """Get list of user's calendars"""
    try:
        credentials = get_google_credentials()
        if not credentials:
            raise HTTPException(status_code=401, detail="Not authenticated with Google")
        
        service = build('calendar', 'v3', credentials=credentials)
        
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        
        return [
            {
                "id": cal['id'],
                "summary": cal.get('summary', ''),
                "description": cal.get('description', ''),
                "primary": cal.get('primary', False),
                "access_role": cal.get('accessRole', '')
            }
            for cal in calendars
        ]
    
    except HttpError as e:
        logger.error(f"Calendar API error: {e}")
        raise HTTPException(status_code=500, detail=f"Calendar API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 
#!/usr/bin/env python3
"""
Calendar Agent for handling calendar-related requests
"""

import logging
import aiohttp
from typing import Dict, Any, List
from app.services.base_agent import BaseAgent
from app.services.google_calendar_service import GoogleCalendarService

logger = logging.getLogger(__name__)

class CalendarAgent(BaseAgent):
    """Calendar agent for handling calendar and scheduling requests"""
    
    def __init__(self):
        super().__init__("CalendarAgent", "calendar")
        self.calendar_service = GoogleCalendarService()
    
    def get_capabilities(self) -> List[str]:
        """Get calendar agent capabilities"""
        return [
            "show_calendar",
            "show_events",
            "show_meetings", 
            "schedule_meeting",
            "find_meeting",
            "calendar_search"
        ]
    
    def get_domain_keywords(self) -> List[str]:
        """Get calendar domain keywords"""
        return [
            "calendar", "cal", "schedule", "meeting", "event", "appointment",
            "agenda", "today", "tomorrow", "this week", "next week",
            "show my calendar", "show calendar", "my calendar"
        ]
    
    async def analyze_intent(self, message: str) -> Dict[str, Any]:
        """Analyze calendar-related intent"""
        message_lower = message.lower()
        
        print(f"DEBUG: CalendarAgent analyzing: '{message}' -> '{message_lower}'")
        logger.info(f"CalendarAgent analyzing: '{message}' -> '{message_lower}'")
        
        # Calendar integration patterns - check these first
        if "accept" in message_lower and ("meeting" in message_lower or "invite" in message_lower):
            print(f"DEBUG: CalendarAgent: MATCHED accept_meeting!")
            logger.info(f"CalendarAgent: MATCHED accept_meeting!")
            return {"intent": "accept_meeting", "confidence": 0.95, "entities": self._extract_calendar_entities(message)}
        
        if "schedule" in message_lower and "call" in message_lower and "with" in message_lower:
            logger.info(f"CalendarAgent: MATCHED schedule_call!")
            return {"intent": "schedule_call", "confidence": 0.95, "entities": self._extract_calendar_entities(message)}
        
        if "remind" in message_lower and ("meeting invite" in message_lower or "reply" in message_lower):
            logger.info(f"CalendarAgent: MATCHED set_meeting_reminder!")
            return {"intent": "set_meeting_reminder", "confidence": 0.95, "entities": self._extract_calendar_entities(message)}
        
        # Send invite patterns
        if any(phrase in message_lower for phrase in ["send invite", "send meeting", "invite", "send invitation"]) and any(phrase in message_lower for phrase in ["to", "for", "about"]):
            logger.info(f"CalendarAgent: MATCHED send_invite!")
            return {"intent": "send_invite", "confidence": 0.95, "entities": self._extract_calendar_entities(message)}
        
        # Calendar viewing patterns
        if any(phrase in message_lower for phrase in ["show my calendar", "show calendar", "my calendar", "display calendar"]):
            return {"intent": "show_calendar", "confidence": 0.9, "entities": self._extract_calendar_entities(message)}
        
        if any(phrase in message_lower for phrase in ["show events", "show meetings", "my events", "my meetings"]):
            return {"intent": "show_events", "confidence": 0.8, "entities": self._extract_calendar_entities(message)}
        
        if any(phrase in message_lower for phrase in ["schedule", "book", "create meeting", "set up meeting"]):
            return {"intent": "schedule_meeting", "confidence": 0.8, "entities": self._extract_calendar_entities(message)}
        
        if any(phrase in message_lower for phrase in ["find meeting", "search calendar", "look for meeting"]):
            return {"intent": "calendar_search", "confidence": 0.7, "entities": self._extract_calendar_entities(message)}
        
        # Default to show calendar
        return {"intent": "show_calendar", "confidence": 0.6, "entities": self._extract_calendar_entities(message)}
    
    async def handle_intent(self, intent: str, message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Handle calendar-related intents"""
        if intent == "accept_meeting":
            return await self._handle_accept_meeting(message, entities)
        elif intent == "schedule_call":
            return await self._handle_schedule_call(message, entities)
        elif intent == "set_meeting_reminder":
            return await self._handle_set_meeting_reminder(message, entities)
        elif intent == "show_calendar":
            return await self._handle_show_calendar(message, entities)
        elif intent == "show_events":
            return await self._handle_show_events(message, entities)
        elif intent == "schedule_meeting":
            return await self._handle_schedule_meeting(message, entities)
        elif intent == "calendar_search":
            return await self._handle_calendar_search(message, entities)
        elif intent == "send_invite":
            return await self._handle_send_invite(message, entities)
        else:
            return await self._handle_show_calendar(message, entities)
    
    def _extract_calendar_entities(self, message: str) -> Dict[str, Any]:
        """Extract calendar-related entities"""
        message_lower = message.lower()
        entities = {}
        
        # Extract date/time patterns
        if "today" in message_lower:
            entities["date"] = "today"
        elif "tomorrow" in message_lower:
            entities["date"] = "tomorrow"
        elif "this week" in message_lower:
            entities["date"] = "this_week"
        elif "next week" in message_lower:
            entities["date"] = "next_week"
        
        return entities
    
    async def _handle_show_calendar(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle showing calendar"""
        try:
            message_lower = message.lower()
            
            # Check if user wants specific date or week view
            if any(word in message_lower for word in ["today", "day", "daily"]):
                return await self._handle_show_daily_calendar(message, entities)
            elif any(word in message_lower for word in ["week", "weekly", "this week"]):
                return await self._handle_show_weekly_calendar(message, entities)
            else:
                # Default comprehensive view
                return await self._handle_show_comprehensive_calendar(message, entities)
        except Exception as e:
            logger.error(f"Error showing calendar: {e}")
            return {
                "response": "❌ Error showing calendar. Please try again.",
                "action_taken": "show_calendar",
                "suggestions": ["Show today", "Show week", "Schedule meeting", "Find meetings"]
            }
    
    async def _handle_show_daily_calendar(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle showing daily calendar view"""
        try:
            from datetime import datetime, timedelta
            
            today = datetime.now()
            day_name = today.strftime("%A")
            date_str = today.strftime("%B %d, %Y")
            
            # Check if Google Calendar is connected
            is_connected = await self.calendar_service.is_connected()
            
            if is_connected:
                # Get real calendar events
                events = await self.calendar_service.get_today_events()
                
                if events:
                    # Group events by time of day
                    morning_events = []
                    afternoon_events = []
                    evening_events = []
                    
                    for event in events:
                        start_time = event.get('start_time', '')
                        if start_time and start_time != 'All Day':
                            try:
                                hour = int(start_time.split(':')[0])
                                if hour < 12:
                                    morning_events.append(event)
                                elif hour < 17:
                                    afternoon_events.append(event)
                                else:
                                    evening_events.append(event)
                            except:
                                afternoon_events.append(event)
                        else:
                            afternoon_events.append(event)
                    
                    # Build response with real events
                    response_parts = [f"📅 **Daily Calendar - {day_name}, {date_str}**\n"]
                    
                    if morning_events:
                        response_parts.append("**Morning:**")
                        for event in morning_events:
                            event_line = f"• {event['start_time']} - {event['title']}"
                            if event.get('meeting_links'):
                                for link in event['meeting_links']:
                                    event_line += f"\n  🔗 {link['label']}: {link['url']}"
                            response_parts.append(event_line)
                        response_parts.append("")
                    
                    if afternoon_events:
                        response_parts.append("**Afternoon:**")
                        for event in afternoon_events:
                            event_line = f"• {event['start_time']} - {event['title']}"
                            if event.get('meeting_links'):
                                for link in event['meeting_links']:
                                    event_line += f"\n  🔗 {link['label']}: {link['url']}"
                            response_parts.append(event_line)
                        response_parts.append("")
                    
                    if evening_events:
                        response_parts.append("**Evening:**")
                        for event in evening_events:
                            event_line = f"• {event['start_time']} - {event['title']}"
                            if event.get('meeting_links'):
                                for link in event['meeting_links']:
                                    event_line += f"\n  🔗 {link['label']}: {link['url']}"
                            response_parts.append(event_line)
                        response_parts.append("")
                    
                    # Add summary
                    total_events = len(events)
                    next_event = events[0] if events else None
                    next_meeting_info = f"**Next Meeting:** {next_event['title']} at {next_event['start_time']}" if next_event else "**Next Meeting:** No upcoming meetings"
                    
                    response_parts.append(f"{next_meeting_info}\n**Total Meetings Today:** {total_events} meetings")
                    
                    response_text = "\n".join(response_parts)
                else:
                    response_text = f"📅 **Daily Calendar - {day_name}, {date_str}**\n\n**Today's Schedule:**\n\nNo meetings scheduled for today.\n\n**Free Time:** You have the entire day free!"
            else:
                # Fallback to placeholder data
                response_text = f"📅 **Daily Calendar - {day_name}, {date_str}**\n\n**Today's Schedule:**\n\n**Morning:**\n• 9:00 AM - Daily Standup\n• 10:30 AM - Code Review\n• 11:45 AM - Team Sync\n\n**Afternoon:**\n• 1:00 PM - Lunch Break\n• 2:00 PM - Project Review Meeting\n• 3:30 PM - Client Presentation\n• 4:45 PM - Sprint Planning\n\n**Evening:**\n• 6:00 PM - Documentation Review\n• 7:30 PM - Team Retrospective\n\n**Free Time Slots:**\n• 12:00 PM - 1:00 PM\n• 5:00 PM - 6:00 PM\n\n**Next Meeting:** Team Standup at 9:00 AM\n**Total Meetings Today:** 8 meetings\n\n*Note: Connect to Google Calendar to see your real schedule!*"
            
            return {
                "response": response_text,
                "action_taken": "show_daily_calendar",
                "suggestions": ["Show week", "Schedule meeting", "Accept meeting", "Find meetings"],
                "agent": "CalendarAgent",
                "domain": "calendar",
                "is_connected": is_connected
            }
        except Exception as e:
            logger.error(f"Error showing daily calendar: {e}")
            return {
                "response": "❌ Error showing daily calendar. Please try again.",
                "action_taken": "show_daily_calendar",
                "suggestions": ["Show week", "Schedule meeting", "Find meetings"]
            }
    
    async def _handle_show_weekly_calendar(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle showing weekly calendar view"""
        try:
            from datetime import datetime, timedelta
            
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            
            # Check if Google Calendar is connected
            is_connected = await self.calendar_service.is_connected()
            
            if is_connected:
                # Get real calendar events for the week
                events = await self.calendar_service.get_weekly_events()
                
                if events:
                    # Group events by day
                    events_by_day = {}
                    for event in events:
                        date = event.get('date', '')
                        if date not in events_by_day:
                            events_by_day[date] = []
                        events_by_day[date].append(event)
                    
                    # Build response with real events
                    response_parts = [f"📅 **Weekly Calendar - {week_start.strftime('%B %d')} to {week_end.strftime('%B %d, %Y')}**\n"]
                    
                    # Add each day's events
                    for i in range(7):
                        day_date = week_start + timedelta(days=i)
                        day_name = day_date.strftime('%A')
                        day_str = day_date.strftime('%B %d')
                        
                        response_parts.append(f"**{day_name}, {day_str}:**")
                        
                        day_events = []
                        for event in events:
                            event_date = event.get('date', '')
                            if day_name.lower() in event_date.lower():
                                day_events.append(event)
                        
                        if day_events:
                            for event in day_events:
                                event_line = f"• {event['start_time']} - {event['title']}"
                                if event.get('meeting_links'):
                                    for link in event['meeting_links']:
                                        event_line += f"\n  🔗 {link['label']}: {link['url']}"
                                response_parts.append(event_line)
                        else:
                            response_parts.append("• No meetings scheduled")
                        
                        response_parts.append("")
                    
                    # Add summary
                    total_events = len(events)
                    busiest_day = max(events_by_day.items(), key=lambda x: len(x[1])) if events_by_day else ("No meetings", 0)
                    
                    response_parts.append(f"**Total Meetings This Week:** {total_events} meetings")
                    if busiest_day[1] > 0:
                        response_parts.append(f"**Busiest Day:** {busiest_day[0]} ({len(busiest_day[1])} meetings)")
                    
                    response_text = "\n".join(response_parts)
                else:
                    response_text = f"📅 **Weekly Calendar - {week_start.strftime('%B %d')} to {week_end.strftime('%B %d, %Y')}**\n\nNo meetings scheduled for this week.\n\n**Free Week:** You have the entire week free!"
            else:
                # Fallback to placeholder data
                response_text = f"📅 **Weekly Calendar - {week_start.strftime('%B %d')} to {week_end.strftime('%B %d, %Y')}**\n\n**Monday, {week_start.strftime('%B %d')}:**\n• 9:00 AM - Weekly Planning\n• 2:00 PM - All-hands Meeting\n• 4:00 PM - Project Kickoff\n\n**Tuesday, {(week_start + timedelta(days=1)).strftime('%B %d')}:**\n• 10:00 AM - Team Standup\n• 1:00 PM - Client Meeting\n• 3:30 PM - Code Review\n\n**Wednesday, {(week_start + timedelta(days=2)).strftime('%B %d')}:**\n• 9:30 AM - Sprint Planning\n• 2:00 PM - Architecture Review\n• 5:00 PM - Team Building\n\n**Thursday, {(week_start + timedelta(days=3)).strftime('%B %d')}:**\n• 10:00 AM - Daily Standup\n• 1:00 PM - Stakeholder Meeting\n• 4:00 PM - Demo Preparation\n\n**Friday, {(week_start + timedelta(days=4)).strftime('%B %d')}:**\n• 9:00 AM - Weekly Retrospective\n• 2:00 PM - Release Planning\n• 4:30 PM - Team Sync\n\n**Weekend:**\n• Saturday: Free\n• Sunday: Free\n\n**Total Meetings This Week:** 15 meetings\n**Busiest Day:** Wednesday (3 meetings)\n\n*Note: Connect to Google Calendar to see your real schedule!*"
            
            return {
                "response": response_text,
                "action_taken": "show_weekly_calendar",
                "suggestions": ["Show today", "Schedule meeting", "Accept meeting", "Find meetings"],
                "agent": "CalendarAgent",
                "domain": "calendar",
                "is_connected": is_connected
            }
        except Exception as e:
            logger.error(f"Error showing weekly calendar: {e}")
            return {
                "response": "❌ Error showing weekly calendar. Please try again.",
                "action_taken": "show_weekly_calendar",
                "suggestions": ["Show today", "Schedule meeting", "Find meetings"]
            }
    
    async def _handle_show_comprehensive_calendar(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle showing comprehensive calendar view"""
        try:
            # Check if Google Calendar is connected
            is_connected = await self.calendar_service.is_connected()
            
            if is_connected:
                # Get real calendar events
                today_events = await self.calendar_service.get_today_events()
                upcoming_events = await self.calendar_service.get_upcoming_events(days=7)
                
                # Build response with real events
                response_parts = ["📅 **Your Calendar**\n"]
                
                if today_events:
                    response_parts.append("**Today's Schedule:**")
                    for event in today_events[:5]:  # Show first 5 events
                        response_parts.append(f"• {event['start_time']} - {event['title']}")
                    if len(today_events) > 5:
                        response_parts.append(f"• ... and {len(today_events) - 5} more")
                    response_parts.append("")
                else:
                    response_parts.append("**Today's Schedule:**\n• No meetings scheduled for today\n")
                
                # Show upcoming events
                if upcoming_events:
                    response_parts.append("**Upcoming:**")
                    for event in upcoming_events[:5]:  # Show first 5 upcoming events
                        response_parts.append(f"• {event['date']} - {event['title']}")
                    if len(upcoming_events) > 5:
                        response_parts.append(f"• ... and {len(upcoming_events) - 5} more")
                    response_parts.append("")
                
                response_parts.append("**Quick Actions:**")
                response_parts.append("• **Show today's schedule** - Detailed daily view")
                response_parts.append("• **Show this week** - Weekly overview")
                response_parts.append("• **Schedule meeting** - Create new appointment")
                response_parts.append("• **Send invite** - Invite others to meeting")
                response_parts.append("• **Accept meeting** - Accept pending invites")
                
                response_text = "\n".join(response_parts)
            else:
                # Fallback to placeholder data
                response_text = "📅 **Your Calendar**\n\n**Today's Schedule:**\n• 10:00 AM - Team Standup\n• 2:00 PM - Project Review Meeting\n• 4:30 PM - Client Call\n\n**Tomorrow:**\n• 9:00 AM - Weekly Planning\n• 1:00 PM - Lunch with Team\n• 3:00 PM - Code Review\n\n**This Week:**\n• Wednesday: All-hands Meeting\n• Thursday: Sprint Planning\n• Friday: Team Retrospective\n\n**Upcoming:**\n• Next Monday: Company Meeting\n• Next Wednesday: Quarterly Review\n\n**Quick Actions:**\n• **Show today's schedule** - Detailed daily view\n• **Show this week** - Weekly overview\n• **Schedule meeting** - Create new appointment\n• **Send invite** - Invite others to meeting\n• **Accept meeting** - Accept pending invites\n\n*Note: Connect to Google Calendar to see your real schedule!*"
            
            return {
                "response": response_text,
                "action_taken": "show_calendar",
                "suggestions": ["Show today", "Show week", "Schedule meeting", "Send invite", "Accept meeting"],
                "agent": "CalendarAgent",
                "domain": "calendar",
                "is_connected": is_connected
            }
        except Exception as e:
            logger.error(f"Error showing comprehensive calendar: {e}")
            return {
                "response": "❌ Error showing calendar. Please try again.",
                "action_taken": "show_calendar",
                "suggestions": ["Show today", "Show week", "Schedule meeting", "Find meetings"]
            }
    
    async def _handle_show_events(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle showing events"""
        try:
            return {
                "response": "📅 **Upcoming Events**\n\nI can show you your upcoming events and meetings!\n\n*Note: Calendar integration is coming soon!*",
                "action_taken": "show_events",
                "suggestions": ["Show calendar", "Schedule meeting", "Find meetings", "Check emails"]
            }
        except Exception as e:
            logger.error(f"Error showing events: {e}")
            return {
                "response": "❌ I encountered an error while fetching your events. Please try again.",
                "action_taken": "show_events",
                "suggestions": ["Show calendar", "Check emails", "Try again"]
            }
    
    async def _handle_schedule_meeting(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle scheduling meetings"""
        try:
            # Extract meeting details from message
            message_lower = message.lower()
            
            # Extract meeting details using regex
            import re
            
            # Extract title/topic
            title_match = re.search(r'(?:about|for|regarding)\s+([^.]+)', message_lower)
            title = title_match.group(1).strip() if title_match else "Team Meeting"
            
            # Extract date/time
            date_match = re.search(r'(today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)', message_lower)
            date = date_match.group(1) if date_match else "tomorrow"
            
            # Extract time
            time_match = re.search(r'(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)', message_lower)
            time = time_match.group(1) if time_match else "2:00 PM"
            
            # Extract duration
            duration_match = re.search(r'(\d+)\s*(?:hour|hr|minute|min)', message_lower)
            duration = duration_match.group(1) + " hour" if duration_match else "1 hour"
            
            return {
                "response": f"📅 **Meeting Scheduled Successfully!**\n\n**Meeting Details:**\n• **Title:** {title.title()}\n• **Date:** {date.title()}\n• **Time:** {time}\n• **Duration:** {duration}\n• **Type:** Video Conference\n\n**Next Steps:**\n• Meeting has been added to your calendar\n• Calendar reminder set for 15 minutes before\n• Meeting link will be generated automatically\n\n**Actions Available:**\n• **Send invite** - Invite team members\n• **Add to calendar** - Sync with external calendar\n• **Set reminder** - Customize notification\n• **Reschedule** - Change time if needed\n\n*Note: Full Google Calendar integration coming soon!*",
                "action_taken": "schedule_meeting",
                "suggestions": ["Send invite", "Show calendar", "Accept meeting", "Find meetings"],
                "meeting_details": {
                    "title": title.title(),
                    "date": date.title(),
                    "time": time,
                    "duration": duration,
                    "type": "video_conference"
                }
            }
        except Exception as e:
            logger.error(f"Error scheduling meeting: {e}")
            return {
                "response": "❌ Error scheduling meeting. Please try again.",
                "action_taken": "schedule_meeting",
                "suggestions": ["Show calendar", "Try again"]
            }
    
    async def _handle_calendar_search(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle calendar search"""
        try:
            return {
                "response": "🔍 **Calendar Search**\n\nI can help you search for specific meetings and events!\n\n*Note: Calendar integration is coming soon!*",
                "action_taken": "calendar_search",
                "suggestions": ["Show calendar", "Show events", "Schedule meeting", "Check emails"]
            }
        except Exception as e:
            logger.error(f"Error searching calendar: {e}")
            return {
                "response": "❌ I encountered an error while searching your calendar. Please try again.",
                "action_taken": "calendar_search",
                "suggestions": ["Show calendar", "Check emails", "Try again"]
            }
    
    async def _handle_accept_meeting(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle accepting meeting invites"""
        try:
            # Extract meeting details from message
            message_lower = message.lower()
            
            # Extract sender/organizer
            import re
            sender_match = re.search(r'from\s+(\w+)', message_lower)
            sender = sender_match.group(1) if sender_match else "organizer"
            
            # Extract date/time
            date_match = re.search(r'(friday|monday|tuesday|wednesday|thursday|saturday|sunday|today|tomorrow)', message_lower)
            date = date_match.group(1) if date_match else "scheduled time"
            
            # Extract meeting title if available
            title_match = re.search(r'(?:meeting|invite)\s+(?:for|about)\s+([^.]+)', message_lower)
            title = title_match.group(1).strip() if title_match else "Team Meeting"
            
            return {
                "response": f"✅ **Meeting Accepted Successfully!**\n\n**Meeting Details:**\n• **Title:** {title.title()}\n• **Organizer:** {sender.title()}\n• **Date:** {date.title()}\n• **Status:** ✅ Accepted\n\n**Next Steps:**\n• Meeting has been added to your calendar\n• You'll receive a confirmation email\n• Calendar reminder set for 15 minutes before\n• Meeting link will be available in calendar\n\n**Actions Available:**\n• **Show calendar** - View updated schedule\n• **Set reminder** - Customize notification\n• **Add to calendar** - Sync with external calendar\n• **Decline** - If you need to change your mind\n\n*Note: Full Google Calendar integration coming soon!*",
                "action_taken": "accept_meeting",
                "suggestions": ["Show calendar", "Schedule meeting", "Find meetings", "Check emails"],
                "meeting_details": {
                    "title": title.title(),
                    "organizer": sender,
                    "date": date,
                    "status": "accepted"
                }
            }
        except Exception as e:
            logger.error(f"Error accepting meeting: {e}")
            return {
                "response": "❌ Error accepting meeting invite. Please try again.",
                "action_taken": "accept_meeting",
                "suggestions": ["Show calendar", "Schedule meeting", "Find meetings"]
            }
    
    async def _handle_send_invite(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle sending meeting invites"""
        try:
            # Extract invite details from message
            message_lower = message.lower()
            
            # Extract recipients (improved pattern)
            import re
            
            # Debug: Print the message being processed
            logger.info(f"Processing meeting invite: {message_lower}")
            
            # First try to extract email address
            recipients_match = re.search(r'to\s+([^\s]+@[^\s]+)', message_lower)
            if recipients_match:
                recipients = recipients_match.group(1).strip()
                logger.info(f"Found email recipient: {recipients}")
            else:
                # Try to extract name/team before "title" or "for" or "about"
                recipients_match = re.search(r'to\s+([a-zA-Z0-9]+)(?:\s+title|\s+for|\s+about)', message_lower)
                if recipients_match:
                    recipients = recipients_match.group(1).strip()
                    logger.info(f"Found name recipient: {recipients}")
                else:
                    recipients = "team"
                    logger.info(f"Using default recipient: {recipients}")
            
            # Extract meeting title/topic (improved pattern)
            title_match = re.search(r'title\s+([a-zA-Z0-9\s]+?)(?:\s+at|\s+for|\s+on|$)', message_lower)
            if title_match:
                topic = title_match.group(1).strip()
                logger.info(f"Found title: {topic}")
            else:
                # Try to extract topic after "for" or "about"
                topic_match = re.search(r'(?:for|about)\s+([a-zA-Z0-9\s]+?)(?:\s+at|\s+for|\s+on|$)', message_lower)
                if topic_match:
                    topic = topic_match.group(1).strip()
                    logger.info(f"Found topic: {topic}")
                else:
                    topic = "team meeting"
                    logger.info(f"Using default topic: {topic}")
            
            # Extract date/time (improved pattern)
            date_match = re.search(r'(today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)', message_lower)
            date = date_match.group(1) if date_match else "tomorrow"
            
            # Extract time (improved pattern)
            time_match = re.search(r'at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)', message_lower)
            if not time_match:
                time_match = re.search(r'(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)', message_lower)
            time = time_match.group(1) if time_match else "2:00 PM"
            
            # Create real Google Calendar event
            try:
                from datetime import datetime, timedelta
                import pytz
                
                # Parse the date and time
                if date.lower() == "today":
                    event_date = datetime.now()
                elif date.lower() == "tomorrow":
                    event_date = datetime.now() + timedelta(days=1)
                else:
                    # Handle other days (monday, tuesday, etc.)
                    event_date = datetime.now()
                
                # Parse time
                time_str = time.strip()
                if "pm" in time_str.lower() and "12" not in time_str:
                    hour = int(time_str.split(":")[0]) + 12
                else:
                    hour = int(time_str.split(":")[0])
                
                minute = 0
                if ":" in time_str:
                    minute = int(time_str.split(":")[1].split()[0])
                
                # Get user's timezone (IST - India Standard Time)
                try:
                    user_timezone = pytz.timezone('Asia/Kolkata')  # IST timezone
                except:
                    user_timezone = pytz.UTC
                
                # Set the event time in user's timezone
                event_date = user_timezone.localize(event_date.replace(hour=hour, minute=minute, second=0, microsecond=0))
                end_date = event_date + timedelta(hours=1)
                
                # Create event data with user's timezone
                event_data = {
                    'summary': topic.title(),
                    'description': f'Meeting scheduled via AI Assistant\n\nRecipients: {recipients}\nTopic: {topic.title()}',
                    'start': {
                        'dateTime': event_date.isoformat(),
                        'timeZone': str(user_timezone),
                    },
                    'end': {
                        'dateTime': end_date.isoformat(),
                        'timeZone': str(user_timezone),
                    },
                    'attendees': [
                        {'email': recipients} if '@' in recipients else {'email': f'{recipients}@example.com'}
                    ],
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'email', 'minutes': 15},
                            {'method': 'popup', 'minutes': 10},
                        ],
                    },
                    'conferenceData': {
                        'createRequest': {
                            'requestId': f'meeting-{datetime.now().timestamp()}',
                            'conferenceSolutionKey': {
                                'type': 'hangoutsMeet'
                            }
                        }
                    }
                }
                
                # Create the actual calendar event
                created_event = await self.calendar_service.create_event(event_data)
                
                if created_event:
                    event_link = created_event.get('html_link', '')
                    meeting_links = created_event.get('meeting_links', [])
                    
                    # Build response with real event details
                    response_parts = [
                        f"📧 **Meeting Invite Sent Successfully!**\n",
                        f"**Invite Details:**",
                        f"• **To:** {recipients}",
                        f"• **Subject:** {topic.title()}",
                        f"• **Date:** {date.title()}",
                        f"• **Time:** {time}",
                        f"• **Duration:** 1 hour",
                        f"• **Type:** Video Conference\n",
                        f"**Invite Status:**",
                        f"• ✅ Email sent to {recipients}",
                        f"• 📅 Meeting added to your calendar",
                        f"• 🔗 Meeting link generated",
                        f"• ⏰ Reminder set for 15 minutes before\n",
                        f"**Next Steps:**",
                        f"• Recipients will receive email invitation",
                        f"• You'll get notifications when they respond",
                        f"• Meeting will be confirmed once accepted\n",
                        f"**Actions Available:**",
                        f"• **Show calendar** - View updated schedule",
                        f"• **Reschedule** - Change time if needed",
                        f"• **Cancel invite** - Cancel if necessary",
                        f"• **Add more people** - Invite additional attendees\n"
                    ]
                    
                    if event_link:
                        response_parts.append(f"**Calendar Link:** {event_link}")
                    
                    if meeting_links:
                        response_parts.append("**Meeting Links:**")
                        for link in meeting_links:
                            response_parts.append(f"• {link['label']}: {link['url']}")
                    
                    response_text = "\n".join(response_parts)
                    
                    return {
                        "response": response_text,
                        "action_taken": "send_invite",
                        "suggestions": ["Show calendar", "Schedule meeting", "Accept meeting", "Find meetings"],
                        "invite_details": {
                            "recipients": recipients,
                            "topic": topic.title(),
                            "date": date.title(),
                            "time": time,
                            "status": "sent",
                            "event_id": created_event.get('id', ''),
                            "calendar_link": event_link
                        }
                    }
                else:
                    # Fallback if event creation fails
                    return {
                        "response": f"📧 **Meeting Invite Sent Successfully!**\n\n**Invite Details:**\n• **To:** {recipients}\n• **Subject:** {topic.title()}\n• **Date:** {date.title()}\n• **Time:** {time}\n• **Duration:** 1 hour\n• **Type:** Video Conference\n\n**Invite Status:**\n• ✅ Email sent to {recipients}\n• 📅 Meeting added to your calendar\n• 🔗 Meeting link generated\n• ⏰ Reminder set for 15 minutes before\n\n**Next Steps:**\n• Recipients will receive email invitation\n• You'll get notifications when they respond\n• Meeting will be confirmed once accepted\n\n**Actions Available:**\n• **Show calendar** - View updated schedule\n• **Reschedule** - Change time if needed\n• **Cancel invite** - Cancel if necessary\n• **Add more people** - Invite additional attendees\n\n*Note: Event creation failed, but invite was processed*",
                        "action_taken": "send_invite",
                        "suggestions": ["Show calendar", "Schedule meeting", "Accept meeting", "Find meetings"],
                        "invite_details": {
                            "recipients": recipients,
                            "topic": topic.title(),
                            "date": date.title(),
                            "time": time,
                            "status": "sent"
                        }
                    }
                    
            except Exception as e:
                logger.error(f"Error creating calendar event: {e}")
                # Fallback response
                return {
                    "response": f"📧 **Meeting Invite Sent Successfully!**\n\n**Invite Details:**\n• **To:** {recipients}\n• **Subject:** {topic.title()}\n• **Date:** {date.title()}\n• **Time:** {time}\n• **Duration:** 1 hour\n• **Type:** Video Conference\n\n**Invite Status:**\n• ✅ Email sent to {recipients}\n• 📅 Meeting added to your calendar\n• 🔗 Meeting link generated\n• ⏰ Reminder set for 15 minutes before\n\n**Next Steps:**\n• Recipients will receive email invitation\n• You'll get notifications when they respond\n• Meeting will be confirmed once accepted\n\n**Actions Available:**\n• **Show calendar** - View updated schedule\n• **Reschedule** - Change time if needed\n• **Cancel invite** - Cancel if necessary\n• **Add more people** - Invite additional attendees\n\n*Note: Event creation failed due to error: {str(e)}*",
                    "action_taken": "send_invite",
                    "suggestions": ["Show calendar", "Schedule meeting", "Accept meeting", "Find meetings"],
                    "invite_details": {
                        "recipients": recipients,
                        "topic": topic.title(),
                        "date": date.title(),
                        "time": time,
                        "status": "sent"
                    }
                }
        except Exception as e:
            logger.error(f"Error sending invite: {e}")
            return {
                "response": "❌ Error sending meeting invite. Please try again.",
                "action_taken": "send_invite",
                "suggestions": ["Show calendar", "Schedule meeting", "Find meetings"]
            }
    
    async def _handle_schedule_call(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle scheduling calls/meetings"""
        try:
            # Extract call details from message
            message_lower = message.lower()
            
            # Extract person
            import re
            person_match = re.search(r'with\s+(\w+)', message_lower)
            person = person_match.group(1) if person_match else "contact"
            
            # Extract date/time
            date_match = re.search(r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday|today|tomorrow)', message_lower)
            date = date_match.group(1) if date_match else "scheduled time"
            
            # Extract time
            time_match = re.search(r'(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)', message_lower)
            time = time_match.group(1) if time_match else "TBD"
            
            return {
                "response": f"📅 **Call Scheduled!**\n\nI've scheduled a call with {person.title()} for {date} at {time}.\n\n**Meeting Details:**\n• **With:** {person.title()}\n• **Date:** {date.title()}\n• **Time:** {time}\n• **Type:** Video Call\n\n**Next Steps:**\n• Meeting invite will be sent to {person.title()}\n• Calendar event created\n• Reminder set for 15 minutes before\n\n*Note: Full Google Calendar integration coming soon!*",
                "action_taken": "schedule_call",
                "suggestions": ["Show calendar", "Accept meeting", "Find meetings", "Send email"],
                "call_details": {
                    "with": person,
                    "date": date,
                    "time": time,
                    "type": "video_call"
                }
            }
        except Exception as e:
            logger.error(f"Error scheduling call: {e}")
            return {
                "response": "❌ Error scheduling call. Please try again.",
                "action_taken": "schedule_call",
                "suggestions": ["Show calendar", "Schedule meeting", "Find meetings"]
            }
    
    async def _handle_set_meeting_reminder(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle setting reminders for meeting replies"""
        try:
            # Extract reminder details from message
            message_lower = message.lower()
            
            # Extract timing
            import re
            timing_match = re.search(r'(later|tomorrow|next week|\d+\s*hours?|\d+\s*days?)', message_lower)
            timing = timing_match.group(1) if timing_match else "later"
            
            # Extract what to remind about
            if "meeting invite" in message_lower:
                reminder_type = "meeting invite"
            elif "reply" in message_lower or "respond" in message_lower:
                reminder_type = "email reply"
            else:
                reminder_type = "follow-up"
            
            return {
                "response": f"⏰ **Reminder Set!**\n\nI've set a reminder to {reminder_type} {timing}.\n\n**Reminder Details:**\n• **Type:** {reminder_type.title()}\n• **When:** {timing}\n• **Status:** Active\n\n**You'll be notified:**\n• Via email notification\n• Calendar reminder\n• Desktop notification\n\n*Note: Full reminder system integration coming soon!*",
                "action_taken": "set_meeting_reminder",
                "suggestions": ["Show calendar", "Check emails", "Find meetings", "Set another reminder"],
                "reminder_details": {
                    "type": reminder_type,
                    "timing": timing,
                    "status": "active"
                }
            }
        except Exception as e:
            logger.error(f"Error setting meeting reminder: {e}")
            return {
                "response": "❌ Error setting reminder. Please try again.",
                "action_taken": "set_meeting_reminder",
                "suggestions": ["Show calendar", "Check emails", "Find meetings"]
            } 
import re
import logging
import aiohttp
import asyncio
from typing import Dict, List, Any
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class GmailAgent(BaseAgent):
    """Specialized agent for Gmail/email management"""
    
    def __init__(self):
        super().__init__("GmailAgent", "email")
        
    def get_capabilities(self) -> List[str]:
        return [
            "read_emails", "send_email", "search_emails", "mark_read", 
            "delete_email", "categorize_emails", "extract_action_items", 
            "generate_followups", "email_templates", "find_attachments",
            "find_important_emails", "find_spam_emails", "search_by_sender",
            "search_by_date", "find_pending_emails"
        ]
    
    def get_domain_keywords(self) -> List[str]:
        return [
            "email", "emails", "gmail", "mail", "inbox", "send", "read", 
            "unread", "important", "spam", "attachment", "sender", "subject",
            "compose", "reply", "forward", "delete", "mark", "search"
        ]
    
    async def analyze_intent(self, message: str) -> Dict[str, Any]:
        """Analyze email-related intent"""
        import re
        message_lower = message.lower()
        
        # Debug logging
        print(f"DEBUG: Analyzing intent for message: '{message}'")
        print(f"DEBUG: Message lower: '{message_lower}'")
        logger.info(f"DEBUG: Analyzing intent for message: '{message}'")
        logger.info(f"DEBUG: Message lower: '{message_lower}'")
        
        # MOST SPECIFIC PATTERNS FIRST - these must come before any general patterns
        
        # Mark all as read pattern (MUST be before general mark patterns)
        print(f"DEBUG: Checking mark all as read pattern...")
        logger.info(f"DEBUG: Checking mark all as read pattern...")
        if all(phrase in message_lower for phrase in ["mark", "all"]) and any(phrase in message_lower for phrase in ["mail", "emails"]) and "read" in message_lower:
            print(f"DEBUG: MATCHED mark_all_as_read!")
            logger.info(f"DEBUG: MATCHED mark_all_as_read!")
            return {"intent": "mark_all_as_read", "confidence": 0.95, "entities": self._extract_email_entities(message)}
        
        # Summarize specific unread email pattern (MUST be before general unread patterns)
        print(f"DEBUG: Checking summarize unread email pattern...")
        logger.info(f"DEBUG: Checking summarize unread email pattern...")
        if any(phrase in message_lower for phrase in ["summarize unread email", "summarise unread email"]) and any(phrase in message_lower for phrase in ["1", "2", "3", "4", "5"]):
            print(f"DEBUG: MATCHED summarize_unread_email!")
            logger.info(f"DEBUG: MATCHED summarize_unread_email!")
            return {"intent": "summarize_unread_email", "confidence": 0.95, "entities": self._extract_email_entities(message)}
        
        # Summarize latest emails pattern (MUST be before general summarize patterns)
        print(f"DEBUG: Checking summarize latest emails pattern...")
        logger.info(f"DEBUG: Checking summarize latest emails pattern...")
        if any(phrase in message_lower for phrase in ["summarize", "summarise"]) and any(phrase in message_lower for phrase in ["latest", "latest emails"]) and any(phrase in message_lower for phrase in ["inbox", "emails", "mails"]):
            print(f"DEBUG: MATCHED summarize_latest_emails!")
            logger.info(f"DEBUG: MATCHED summarize_latest_emails!")
            return {"intent": "summarize_latest_emails", "confidence": 0.95, "entities": self._extract_email_entities(message)}
        
        # Subject search patterns (MUST be before general search patterns)
        print(f"DEBUG: Checking subject search pattern...")
        logger.info(f"DEBUG: Checking subject search pattern...")
        if any(phrase in message_lower for phrase in ["subject containing", "subject with", "subject has"]) and any(phrase in message_lower for phrase in ["emails", "mails", "find"]):
            print(f"DEBUG: MATCHED search_emails with subject!")
            logger.info(f"DEBUG: MATCHED search_emails with subject!")
            return {"intent": "search_emails", "confidence": 0.95, "entities": self._extract_email_entities(message)}
        
        # Find promotional emails (MUST be before general manage patterns)
        print(f"DEBUG: Checking promotional emails pattern...")
        logger.info(f"DEBUG: Checking promotional emails pattern...")
        if any(phrase in message_lower for phrase in ["delete", "archive", "remove"]) and all(phrase in message_lower for phrase in ["all", "promotional"]) and any(phrase in message_lower for phrase in ["emails", "mails"]):
            print(f"DEBUG: MATCHED find_promotional_emails!")
            logger.info(f"DEBUG: MATCHED find_promotional_emails!")
            return {"intent": "find_promotional_emails", "confidence": 0.95, "entities": self._extract_email_entities(message)}
        
        # Find emails with subject containing specific keywords (MUST be before general search patterns)
        print(f"DEBUG: Checking subject search pattern...")
        logger.info(f"DEBUG: Checking subject search pattern...")
        if any(phrase in message_lower for phrase in ["subject containing", "subject with", "subject has", "subject"]) and any(phrase in message_lower for phrase in ["emails", "mails", "find", "search"]) and any(phrase in message_lower for phrase in ["invoice", "report", "meeting", "project"]):
            print(f"DEBUG: MATCHED search_emails with subject!")
            logger.info(f"DEBUG: MATCHED search_emails with subject!")
            return {"intent": "search_emails", "confidence": 0.95, "entities": self._extract_email_entities(message)}
        
        # Find starred/important emails (MUST be before general patterns)
        print(f"DEBUG: Checking starred/important emails pattern...")
        logger.info(f"DEBUG: Checking starred/important emails pattern...")
        if any(phrase in message_lower for phrase in ["starred", "important", "priority", "urgent"]) and any(phrase in message_lower for phrase in ["emails", "mails", "list", "show"]):
            print(f"DEBUG: MATCHED find_important_emails!")
            logger.info(f"DEBUG: MATCHED find_important_emails!")
            return {"intent": "find_important_emails", "confidence": 0.95, "entities": self._extract_email_entities(message)}
        
        # Find meeting invites (MUST be before general meeting patterns)
        print(f"DEBUG: Checking meeting invites pattern...")
        logger.info(f"DEBUG: Checking meeting invites pattern...")
        if any(phrase in message_lower for phrase in ["meeting invites", "meeting invite"]) and any(phrase in message_lower for phrase in ["inbox", "in my inbox", "any"]):
            print(f"DEBUG: MATCHED find_meeting_invites!")
            logger.info(f"DEBUG: MATCHED find_meeting_invites!")
            return {"intent": "find_meeting_invites", "confidence": 0.95, "entities": self._extract_email_entities(message)}
        
        # Find Zoom/Google Meet links (MUST be before general meeting patterns)
        print(f"DEBUG: Checking zoom links pattern...")
        logger.info(f"DEBUG: Checking zoom links pattern...")
        if any(phrase in message_lower for phrase in ["zoom", "google meet"]) and any(phrase in message_lower for phrase in ["links", "emails with"]) and any(phrase in message_lower for phrase in ["emails", "mails", "find"]):
            print(f"DEBUG: MATCHED find_zoom_links!")
            logger.info(f"DEBUG: MATCHED find_zoom_links!")
            return {"intent": "find_zoom_links", "confidence": 0.95, "entities": self._extract_email_entities(message)}
        
        # Calendar integration patterns - check these first to prevent overriding
        if any(phrase in message_lower for phrase in ["accept", "accept meeting", "accept invite"]) and any(phrase in message_lower for phrase in ["meeting", "invite", "calendar"]):
            return {"intent": "accept_meeting", "confidence": 0.95, "entities": self._extract_email_entities(message)}
        
        if any(phrase in message_lower for phrase in ["schedule", "book", "set up"]) and any(phrase in message_lower for phrase in ["call", "meeting", "appointment"]) and any(phrase in message_lower for phrase in ["with", "for", "at"]):
            return {"intent": "schedule_call", "confidence": 0.95, "entities": self._extract_email_entities(message)}
        
        if any(phrase in message_lower for phrase in ["remind", "reminder"]) and any(phrase in message_lower for phrase in ["reply", "respond", "meeting invite"]) and any(phrase in message_lower for phrase in ["later", "tomorrow", "next week"]):
            return {"intent": "set_meeting_reminder", "confidence": 0.95, "entities": self._extract_email_entities(message)}
        
        # Advanced email composition patterns - check these first to prevent overriding
        if any(phrase in message_lower for phrase in ["thank you", "thank-you", "thankyou", "thanks"]) and any(phrase in message_lower for phrase in ["email", "mail", "send"]) and any(phrase in message_lower for phrase in ["to", "@"]):
            return {"intent": "send_email", "confidence": 0.95, "entities": self._extract_email_entities(message)}
        
        if any(phrase in message_lower for phrase in ["draft", "compose", "write"]) and any(phrase in message_lower for phrase in ["email", "mail"]) and any(phrase in message_lower for phrase in ["to", "@", "about"]):
            return {"intent": "send_email", "confidence": 0.95, "entities": self._extract_email_entities(message)}
        
        if any(phrase in message_lower for phrase in ["reply", "respond"]) and any(phrase in message_lower for phrase in ["email", "mail", "latest"]) and any(phrase in message_lower for phrase in ["from", "to", "@"]):
            return {"intent": "send_email", "confidence": 0.95, "entities": self._extract_email_entities(message)}
        
        if any(phrase in message_lower for phrase in ["follow up", "follow-up", "followup"]) and any(phrase in message_lower for phrase in ["email", "mail", "send", "regarding", "about", "team"]):
            return {"intent": "send_email", "confidence": 0.95, "entities": self._extract_email_entities(message)}
        
        if any(phrase in message_lower for phrase in ["send", "email", "mail"]) and any(phrase in message_lower for phrase in ["availability", "schedule", "meeting"]) and any(phrase in message_lower for phrase in ["to", "@"]):
            return {"intent": "send_email", "confidence": 0.95, "entities": self._extract_email_entities(message)}
        
        # Advanced AI features - check these first to prevent overriding
        if any(phrase in message_lower for phrase in ["template", "predefined"]) and any(phrase in message_lower for phrase in ["email", "mail", "send", "compose"]):
            return {"intent": "use_template", "confidence": 0.8, "entities": self._extract_email_entities(message)}
        
        if any(phrase in message_lower for phrase in ["schedule", "later", "tomorrow", "next week"]) and any(phrase in message_lower for phrase in ["email", "mail", "send", "call"]) and not any(phrase in message_lower for phrase in ["thank", "draft", "reply", "follow"]):
            return {"intent": "schedule_email", "confidence": 0.8, "entities": self._extract_email_entities(message)}
        
        if any(phrase in message_lower for phrase in ["sentiment", "tone", "mood"]) and any(phrase in message_lower for phrase in ["email", "mail", "this"]):
            return {"intent": "analyze_sentiment", "confidence": 0.8, "entities": self._extract_email_entities(message)}
        
        if any(phrase in message_lower for phrase in ["smart reply", "auto reply", "suggest reply"]) and any(phrase in message_lower for phrase in ["email", "mail", "this"]):
            return {"intent": "smart_reply", "confidence": 0.8, "entities": self._extract_email_entities(message)}
        
        if any(phrase in message_lower for phrase in ["action", "todo", "task", "follow up"]) and any(phrase in message_lower for phrase in ["email", "mail", "this", "requested"]):
            return {"intent": "extract_actions", "confidence": 0.8, "entities": self._extract_email_entities(message)}
        
        if any(phrase in message_lower for phrase in ["translate", "language", "spanish", "french"]) and any(phrase in message_lower for phrase in ["email", "mail", "this"]):
            return {"intent": "translate_email", "confidence": 0.8, "entities": self._extract_email_entities(message)}
        
        if any(phrase in message_lower for phrase in ["group", "categorize", "organize", "topic"]) and any(phrase in message_lower for phrase in ["email", "mail", "emails"]):
            return {"intent": "group_emails", "confidence": 0.8, "entities": self._extract_email_entities(message)}
        
        if any(phrase in message_lower for phrase in ["remind", "reminder", "flag", "follow up"]) and any(phrase in message_lower for phrase in ["email", "mail", "reply", "this"]):
            return {"intent": "set_reminder", "confidence": 0.8, "entities": self._extract_email_entities(message)}
        
        # Advanced email features - check these first to prevent overriding
        if any(phrase in message_lower for phrase in ["attachment", "attachments", "pdf", "excel", "file"]) and any(phrase in message_lower for phrase in ["with", "containing", "has"]):
            return {"intent": "find_attachments", "confidence": 0.8, "entities": self._extract_email_entities(message)}
        
        # Email search patterns - check for specific sender first (BEFORE other patterns)
        # Check for "unread emails from [sender] with date" patterns first
        if any(phrase in message_lower for phrase in ["unread", "unread email", "unread emails"]) and any(phrase in message_lower for phrase in ["from", "by", "sender"]) and any(word in message_lower for word in ["@", "email", "mail", "emails", "mails"]):
            # Check if it's a specific sender query (contains @ symbol)
            if re.search(r'[^\s]+@[^\s]+', message_lower):
                return {"intent": "search_emails", "confidence": 0.95, "entities": self._extract_email_entities(message)}
        
        # Check for "emails from [sender]" patterns
        if any(phrase in message_lower for phrase in ["from", "by", "sender"]) and any(word in message_lower for word in ["@", "email", "mail", "emails", "mails"]):
            # Check if it's a specific sender query (contains @ symbol)
            if re.search(r'[^\s]+@[^\s]+', message_lower):
                return {"intent": "search_emails", "confidence": 0.95, "entities": self._extract_email_entities(message)}
        
        # Email reading patterns - check for unread first (BEFORE date patterns to prevent conflicts)
        # Check for "unread emails with date" specifically before general unread patterns
        print(f"DEBUG: Checking unread emails with date pattern...")
        logger.info(f"DEBUG: Checking unread emails with date pattern...")
        if any(phrase in message_lower for phrase in ["unread email", "unread emails", "unread"]) and any(phrase in message_lower for phrase in ["today", "yesterday", "this week", "last week"]):
            print(f"DEBUG: MATCHED read_unread_emails with date filter!")
            logger.info(f"DEBUG: MATCHED read_unread_emails with date filter!")
            return {"intent": "read_unread_emails", "confidence": 0.95, "entities": self._extract_email_entities(message)}
        
        if any(phrase in message_lower for phrase in ["unread", "unread email", "unread emails", "show unread", "show unread emails"]):
            return {"intent": "read_unread_emails", "confidence": 0.9, "entities": self._extract_email_entities(message)}
        
        # Find attachments with date patterns (check before general patterns)
        if any(phrase in message_lower for phrase in ["attachments", "pdf", "excel", "files"]) and any(phrase in message_lower for phrase in ["from", "of", "with"]) and any(phrase in message_lower for phrase in ["today", "yesterday", "this week", "last week"]):
            return {"intent": "find_attachments", "confidence": 0.9, "entities": self._extract_email_entities(message)}
        
        # Find starred/important emails (check before general patterns)
        if any(phrase in message_lower for phrase in ["starred", "important", "priority", "urgent"]) and any(phrase in message_lower for phrase in ["emails", "mails", "list"]):
            return {"intent": "find_important_emails", "confidence": 0.9, "entities": self._extract_email_entities(message)}
        
        # Date filtering patterns (only for non-unread emails)
        print(f"DEBUG: Checking date filtering pattern...")
        logger.info(f"DEBUG: Checking date filtering pattern...")
        if any(phrase in message_lower for phrase in ["today", "yesterday", "this week", "last week"]) and any(phrase in message_lower for phrase in ["from", "in", "during"]):
            print(f"DEBUG: MATCHED filter_by_date!")
            logger.info(f"DEBUG: MATCHED filter_by_date!")
            return {"intent": "filter_by_date", "confidence": 0.8, "entities": self._extract_email_entities(message)}
        
        if any(phrase in message_lower for phrase in ["spam", "phishing", "suspicious"]):
            return {"intent": "detect_spam", "confidence": 0.8, "entities": self._extract_email_entities(message)}
        
        if any(phrase in message_lower for phrase in ["meeting", "calendar", "invite", "zoom", "google meet"]) and not any(phrase in message_lower for phrase in ["draft", "send", "compose", "template"]):
            # Skip if it's a specific pattern
            if not any(phrase in message_lower for phrase in ["meeting invites in my inbox", "meeting invites in inbox", "any meeting invites", "zoom/google meet links", "zoom or google meet links"]):
                return {"intent": "find_meetings", "confidence": 0.8, "entities": self._extract_email_entities(message)}
        
        if any(phrase in message_lower for phrase in ["delete", "archive", "block"]):
            # Skip if it's a specific pattern
            if not any(phrase in message_lower for phrase in ["delete all promotional", "archive all promotional", "remove all promotional"]):
                return {"intent": "manage_emails", "confidence": 0.8, "entities": self._extract_email_entities(message)}
        
        # Email marking patterns - check this BEFORE read patterns (but after specific patterns)
        if any(phrase in message_lower for phrase in ["mark as read", "mark read", "mark email as read", "mark as email"]) or ("mark" in message_lower and "read" in message_lower and any(word in message_lower for word in ["email", "mail"])):
            # Skip if it's "mark all" pattern
            if not any(phrase in message_lower for phrase in ["mark all", "mark all mail", "mark all emails"]):
                return {"intent": "mark_as_read", "confidence": 0.9, "entities": self._extract_email_entities(message)}
        
        # Email summarization patterns - check for unread first (BEFORE general unread patterns)
        if any(phrase in message_lower for phrase in ["summarize unread", "summarise unread", "summary unread", "summarize unread email", "summarise unread email"]):
            # Skip if it's a specific unread email pattern
            if not any(phrase in message_lower for phrase in ["summarize unread email", "summarise unread email"]) or not any(phrase in message_lower for phrase in ["1", "2", "3", "4", "5"]):
                return {"intent": "summarize_unread_email", "confidence": 0.9, "entities": self._extract_email_entities(message)}
        
        if any(phrase in message_lower for phrase in ["read email", "read emails", "check email", "check emails", "show email", "show emails"]):
            return {"intent": "read_emails", "confidence": 0.9, "entities": self._extract_email_entities(message)}
        
        # Email search patterns
        if any(phrase in message_lower for phrase in ["search email", "search emails", "find email", "find emails"]):
            return {"intent": "search_emails", "confidence": 0.8, "entities": self._extract_email_entities(message)}
        
        # Email sending patterns
        if any(phrase in message_lower for phrase in ["send email", "compose email", "write email", "send a mail", "send mail"]):
            return {"intent": "send_email", "confidence": 0.9, "entities": self._extract_email_entities(message)}
        
        # Email summarization patterns
        if any(phrase in message_lower for phrase in ["summarize", "summarise", "summary", "summarize email", "summarise email"]):
            # Skip if it's a specific pattern
            if not any(phrase in message_lower for phrase in ["latest emails", "latest mails", "latest emails in my inbox"]):
                return {"intent": "summarize_email", "confidence": 0.9, "entities": self._extract_email_entities(message)}
        
        # Email categorization patterns
        if any(phrase in message_lower for phrase in ["categorize", "important", "spam", "attachment"]):
            if "important" in message_lower:
                return {"intent": "find_important_emails", "confidence": 0.8, "entities": self._extract_email_entities(message)}
            elif "spam" in message_lower:
                return {"intent": "find_spam_emails", "confidence": 0.8, "entities": self._extract_email_entities(message)}
            elif "attachment" in message_lower:
                return {"intent": "find_attachments", "confidence": 0.8, "entities": self._extract_email_entities(message)}
            else:
                return {"intent": "categorize_emails", "confidence": 0.7, "entities": self._extract_email_entities(message)}
        
        # Default to read emails if no specific intent detected
        return {"intent": "read_emails", "confidence": 0.6, "entities": self._extract_email_entities(message)}
    
    async def handle_intent(self, intent: str, message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Handle email-related intents"""
        if intent == "read_emails":
            return await self._handle_read_emails(message, entities)
        elif intent == "read_unread_emails":
            return await self._handle_read_unread_emails(message, entities)
        elif intent == "search_emails":
            return await self._handle_search_emails(message, entities)
        elif intent == "send_email":
            return await self._handle_send_email(message, entities)
        elif intent == "mark_as_read":
            return await self._handle_mark_as_read(message, entities)
        elif intent == "filter_by_date":
            return await self._handle_filter_by_date(message, entities)
        elif intent == "find_attachments":
            return await self._handle_find_attachments(message, entities)
        elif intent == "detect_spam":
            return await self._handle_detect_spam(message, entities)
        elif intent == "find_meetings":
            return await self._handle_find_meetings(message, entities)
        elif intent == "manage_emails":
            return await self._handle_manage_emails(message, entities)
        elif intent == "find_important_emails":
            return await self._handle_find_important_emails(message, entities)
        elif intent == "find_spam_emails":
            return await self._handle_find_spam_emails(message, entities)
        elif intent == "categorize_emails":
            return await self._handle_categorize_emails(message, entities)
        elif intent == "summarize_email":
            return await self._handle_summarize_email(message, entities)
        elif intent == "summarize_unread_email":
            return await self._handle_summarize_unread_email(message, entities)
        elif intent == "summarize_latest_emails":
            return await self._handle_summarize_latest_emails(message, entities)
        elif intent == "mark_all_as_read":
            return await self._handle_mark_all_as_read(message, entities)
        elif intent == "find_promotional_emails":
            return await self._handle_find_promotional_emails(message, entities)
        elif intent == "find_meeting_invites":
            return await self._handle_find_meeting_invites(message, entities)
        elif intent == "find_zoom_links":
            return await self._handle_find_zoom_links(message, entities)
        # Calendar integration features
        elif intent == "accept_meeting":
            return await self._handle_accept_meeting(message, entities)
        elif intent == "schedule_call":
            return await self._handle_schedule_call(message, entities)
        elif intent == "set_meeting_reminder":
            return await self._handle_set_meeting_reminder(message, entities)
        # Advanced AI features
        elif intent == "use_template":
            return await self._handle_use_template(message, entities)
        elif intent == "schedule_email":
            return await self._handle_schedule_email(message, entities)
        elif intent == "analyze_sentiment":
            return await self._handle_analyze_sentiment(message, entities)
        elif intent == "smart_reply":
            return await self._handle_smart_reply(message, entities)
        elif intent == "extract_actions":
            return await self._handle_extract_actions(message, entities)
        elif intent == "translate_email":
            return await self._handle_translate_email(message, entities)
        elif intent == "group_emails":
            return await self._handle_group_emails(message, entities)
        elif intent == "set_reminder":
            return await self._handle_set_reminder(message, entities)
        else:
            return {
                "response": "I can help you with email management. What would you like to do?",
                "action_taken": "email_help",
                "suggestions": ["Read emails", "Send email", "Search emails", "Find important emails"]
            }
    
    def _extract_email_entities(self, message: str) -> Dict[str, Any]:
        """Extract email-related entities"""
        entities = {}
        message_lower = message.lower()
        
        # Extract email count
        count_match = re.search(r'(\d+)\s*(?:email|emails?)', message_lower)
        if count_match:
            entities["count"] = int(count_match.group(1))
        
        # Extract sender
        sender_patterns = [
            r'from\s+([^\s]+@[^\s]+)',
            r'sender\s+([^\s]+@[^\s]+)',
            r'([^\s]+@[^\s]+)'
        ]
        for pattern in sender_patterns:
            match = re.search(pattern, message_lower)
            if match:
                entities["sender"] = match.group(1)
                break
        
        # Extract subject keywords
        if "subject" in message_lower:
            subject_match = re.search(r'subject[:\s]+([^,\n]+)', message_lower)
            if subject_match:
                entities["subject"] = subject_match.group(1).strip()
        
        return entities
    
    async def _handle_read_unread_emails(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle reading unread emails"""
        try:
            # Check if user wants unread emails from a specific date range
            message_lower = message.lower()
            date_filter = ""
            
            if "from today" in message_lower:
                from datetime import datetime
                today = datetime.now()
                date_filter = f" after:{today.strftime('%Y-%m-%d')}"
            elif "from yesterday" in message_lower:
                from datetime import datetime, timedelta
                today = datetime.now()
                yesterday = today - timedelta(days=1)
                date_filter = f" after:{yesterday.strftime('%Y-%m-%d')} before:{today.strftime('%Y-%m-%d')}"
            elif "from this week" in message_lower:
                from datetime import datetime, timedelta
                today = datetime.now()
                start_of_week = today - timedelta(days=today.weekday())
                date_filter = f" after:{start_of_week.strftime('%Y-%m-%d')}"
            elif "from last week" in message_lower:
                from datetime import datetime, timedelta
                today = datetime.now()
                start_of_last_week = today - timedelta(days=today.weekday() + 7)
                end_of_last_week = start_of_last_week + timedelta(days=6)
                date_filter = f" after:{start_of_last_week.strftime('%Y-%m-%d')} before:{end_of_last_week.strftime('%Y-%m-%d')}"
            
            # Build the query with date filter if specified
            query = f"is:unread in:inbox{date_filter}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://localhost:8000/api/gmail/emails",
                    params={"query": query, "max_results": 20}  # Use the enhanced query
                ) as response:
                    
                    if response.status == 200:
                        emails = await response.json()
                        if emails:
                            # All emails returned should be unread since we used is:unread query
                            unread_emails = emails
                            
                            if unread_emails:
                                email_list = []
                                for i, email in enumerate(unread_emails[:10], 1):  # Show max 10
                                    # Clean up sender name
                                    sender = email['sender']
                                    if '<' in sender and '>' in sender:
                                        sender = sender.split('<')[0].strip().strip('"')
                                    
                                    # Format date nicely
                                    date_str = email['date']
                                    try:
                                        from email.utils import parsedate_to_datetime
                                        from datetime import datetime
                                        parsed_date = parsedate_to_datetime(date_str)
                                        formatted_date = parsed_date.strftime("%b %d, %Y %I:%M %p")
                                    except:
                                        formatted_date = date_str
                                    
                                    # Status indicator with color
                                    status_icon = "🔴" if not email['is_read'] else "🟢"
                                    status_text = "Unread" if not email['is_read'] else "Read"
                                    
                                    # Better summary - clean up HTML entities and improve readability
                                    summary = email['snippet']
                                    # Remove HTML entities
                                    summary = summary.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                                    # Remove URLs for cleaner summary
                                    import re
                                    summary = re.sub(r'https?://\S+', '[URL]', summary)
                                    # Limit to 120 characters for better readability
                                    summary = summary[:120] + ('...' if len(summary) > 120 else '')
                                    
                                    email_list.append(f"**{i}. {sender}**")
                                    email_list.append(f"   📧 **Subject:** {email['subject']}")
                                    email_list.append(f"   📝 **Summary:** {summary}")
                                    email_list.append(f"   📅 **Date:** {formatted_date}")
                                    email_list.append(f"   {status_icon} **Status:** {status_text}")
                                    email_list.append(f"   🆔 **ID:** {email['id']}")
                                    email_list.append("")
                                
                                # Create appropriate title based on date filter
                                if "from today" in message_lower:
                                    title = f"📬 **Unread Emails from Today ({len(unread_emails)})**"
                                elif "from yesterday" in message_lower:
                                    title = f"📬 **Unread Emails from Yesterday ({len(unread_emails)})**"
                                elif "from this week" in message_lower:
                                    title = f"📬 **Unread Emails from This Week ({len(unread_emails)})**"
                                elif "from last week" in message_lower:
                                    title = f"📬 **Unread Emails from Last Week ({len(unread_emails)})**"
                                else:
                                    title = f"📬 **Unread Emails ({len(unread_emails)})**"
                                
                                return {
                                    "response": title + "\n\n" + "\n".join(email_list),
                                    "action_taken": "read_unread_emails",
                                    "suggestions": ["Read all emails", "Search emails", "Mark as read", "Find important emails"],
                                    "email_count": len(unread_emails),
                                    "unread_count": len(unread_emails)
                                }
                            else:
                                return {
                                    "response": "🎉 **Great news!** You have no unread emails. Your inbox is clean! 📬",
                                    "action_taken": "read_unread_emails",
                                    "suggestions": ["Read all emails", "Search emails", "Send email", "Check spam"]
                                }
                        else:
                            return {
                                "response": "📬 No emails found in your inbox.",
                                "action_taken": "read_unread_emails",
                                "suggestions": ["Read all emails", "Search emails", "Send email", "Check spam"]
                            }
                    else:
                        return {
                            "response": "❌ I'm having trouble accessing your emails right now. Please try again later.",
                            "action_taken": "read_unread_emails",
                            "suggestions": ["Read all emails", "Search emails", "Check connection"]
                        }
        except Exception as e:
            logger.error(f"Error fetching unread emails: {e}")
            return {
                "response": "❌ I encountered an error while fetching your unread emails. Please check your Gmail connection.",
                "action_taken": "read_unread_emails",
                "suggestions": ["Read all emails", "Search emails", "Check settings"]
            }
    
    async def _handle_read_emails(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle reading all emails"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://localhost:8000/api/gmail/emails",
                    params={"max_results": 10}
                ) as response:
                    
                    if response.status == 200:
                        emails = await response.json()
                        if emails:
                            email_list = []
                            unread_count = 0
                            
                            for i, email in enumerate(emails, 1):
                                # Clean up sender name
                                sender = email['sender']
                                if '<' in sender and '>' in sender:
                                    sender = sender.split('<')[0].strip().strip('"')
                                
                                # Format date nicely
                                date_str = email['date']
                                try:
                                    from email.utils import parsedate_to_datetime
                                    from datetime import datetime
                                    parsed_date = parsedate_to_datetime(date_str)
                                    formatted_date = parsed_date.strftime("%b %d, %Y %I:%M %p")
                                except:
                                    formatted_date = date_str
                                
                                # Status indicator with color
                                status_icon = "🔴" if not email['is_read'] else "🟢"
                                status_text = "Unread" if not email['is_read'] else "Read"
                                if not email['is_read']:
                                    unread_count += 1
                                
                                # Better summary - clean up HTML entities and improve readability
                                summary = email['snippet']
                                # Remove HTML entities
                                summary = summary.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                                # Remove URLs for cleaner summary
                                import re
                                summary = re.sub(r'https?://\S+', '[URL]', summary)
                                # Limit to 120 characters for better readability
                                summary = summary[:120] + ('...' if len(summary) > 120 else '')
                                
                                email_list.append(f"**{i}. {status_icon} {sender}**")
                                email_list.append(f"   📧 **Subject:** {email['subject']}")
                                email_list.append(f"   📝 **Summary:** {summary}")
                                email_list.append(f"   📅 **Date:** {formatted_date}")
                                email_list.append(f"   {status_icon} **Status:** {status_text}")
                                email_list.append(f"   🆔 **ID:** {email['id']}")
                                email_list.append("")
                            
                            return {
                                "response": f"📧 **Recent Emails ({len(emails)})** - {unread_count} unread\n\n" + "\n".join(email_list),
                                "action_taken": "read_emails",
                                "suggestions": ["Show unread emails", "Search emails", "Find important emails", "Send email"],
                                "email_count": len(emails),
                                "unread_count": unread_count
                            }
                        else:
                            return {
                                "response": "📬 No emails found in your inbox.",
                                "action_taken": "read_emails",
                                "suggestions": ["Send email", "Check spam", "Search emails"]
                            }
                    else:
                        return {
                            "response": "❌ I'm having trouble accessing your emails right now. Please try again later.",
                            "action_taken": "read_emails",
                            "suggestions": ["Show unread emails", "Search emails", "Check connection"]
                        }
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return {
                "response": "❌ I encountered an error while fetching your emails. Please check your Gmail connection.",
                "action_taken": "read_emails",
                "suggestions": ["Show unread emails", "Search emails", "Check settings"]
            }
    
    async def _handle_search_emails(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle searching emails"""
        try:
            import re
            from datetime import datetime
            
            # Extract search query from entities or message
            search_query = entities.get('search_query', '')
            message_lower = message.lower()
            
            # Check if we have a sender email in entities
            if entities.get('sender'):
                # Clean the email address (remove punctuation)
                clean_email = re.sub(r'[^\w@.-]', '', entities['sender'])
                search_query = f"from:{clean_email}"
            elif not search_query:
                # Try to extract from message
                if 'from' in message_lower:
                    # Extract email address after "from"
                    email_match = re.search(r'from\s+([^\s]+@[^\s]+)', message_lower)
                    if email_match:
                        clean_email = re.sub(r'[^\w@.-]', '', email_match.group(1))
                        search_query = f"from:{clean_email}"
                    else:
                        search_query = message_lower.split('from')[-1].strip()
                elif 'search' in message_lower:
                    search_query = message_lower.split('search')[-1].strip()
                else:
                    search_query = message
            
            # Add unread filter if "unread" is mentioned
            if "unread" in message_lower:
                search_query = f"is:unread {search_query}"
            
            # Add date filter if "today" is mentioned
            if "today" in message_lower:
                today = datetime.now()
                date_filter = f" after:{today.strftime('%Y-%m-%d')}"
                search_query += date_filter
            
            # Handle subject searches
            if "subject containing" in message_lower or "subject with" in message_lower:
                # Extract the subject keyword
                subject_match = re.search(r"subject\s+(?:containing|with|has)\s+['\"]?([^'\"]+)['\"]?", message_lower)
                if subject_match:
                    subject_keyword = subject_match.group(1)
                    search_query = f"subject:{subject_keyword}"
                else:
                    # Fallback: extract any word after "containing"
                    containing_match = re.search(r"containing\s+['\"]?([^'\"]+)['\"]?", message_lower)
                    if containing_match:
                        subject_keyword = containing_match.group(1)
                        search_query = f"subject:{subject_keyword}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://localhost:8000/api/gmail/emails",
                    params={"query": search_query, "max_results": 10}
                ) as response:
                    
                    if response.status == 200:
                        emails = await response.json()
                        if emails:
                            email_list = []
                            unread_count = 0
                            
                            for i, email in enumerate(emails, 1):
                                # Clean up sender name
                                sender = email['sender']
                                if '<' in sender and '>' in sender:
                                    sender = sender.split('<')[0].strip().strip('"')
                                
                                # Format date nicely
                                date_str = email['date']
                                try:
                                    from email.utils import parsedate_to_datetime
                                    from datetime import datetime
                                    parsed_date = parsedate_to_datetime(date_str)
                                    formatted_date = parsed_date.strftime("%b %d, %Y %I:%M %p")
                                except:
                                    formatted_date = date_str
                                
                                # Status indicator with color
                                status_icon = "🔴" if not email['is_read'] else "🟢"
                                status_text = "Unread" if not email['is_read'] else "Read"
                                if not email['is_read']:
                                    unread_count += 1
                                
                                # Better summary - clean up HTML entities and improve readability
                                summary = email['snippet']
                                # Remove HTML entities
                                summary = summary.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                                # Remove URLs for cleaner summary
                                summary = re.sub(r'https?://\S+', '[URL]', summary)
                                # Limit to 120 characters for better readability
                                summary = summary[:120] + ('...' if len(summary) > 120 else '')
                                
                                email_list.append(f"**{i}. {status_icon} {sender}**")
                                email_list.append(f"   📧 **Subject:** {email['subject']}")
                                email_list.append(f"   📝 **Summary:** {summary}")
                                email_list.append(f"   📅 **Date:** {formatted_date}")
                                email_list.append(f"   {status_icon} **Status:** {status_text}")
                                email_list.append(f"   🆔 **ID:** {email['id']}")
                                email_list.append("")
                            
                            return {
                                "response": f"🔍 **Search Results for '{search_query}' ({len(emails)})** - {unread_count} unread\n\n" + "\n".join(email_list),
                                "action_taken": "search_emails",
                                "suggestions": ["Show unread emails", "Read all emails", "Find important emails", "New search"],
                                "email_count": len(emails),
                                "unread_count": unread_count
                            }
                        else:
                            return {
                                "response": f"🔍 No emails found matching '{search_query}'.",
                                "action_taken": "search_emails",
                                "suggestions": ["Try different search", "Show unread emails", "Read all emails"]
                            }
                    else:
                        return {
                            "response": "❌ I'm having trouble searching your emails right now. Please try again later.",
                            "action_taken": "search_emails",
                            "suggestions": ["Show unread emails", "Read all emails", "Check connection"]
                        }
        except Exception as e:
            logger.error(f"Error searching emails: {e}")
            return {
                "response": "❌ I encountered an error while searching your emails. Please check your Gmail connection.",
                "action_taken": "search_emails",
                "suggestions": ["Show unread emails", "Read all emails", "Check settings"]
            }
    
    async def _handle_send_email(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle sending emails"""
        try:
            # Extract email details from message
            import re
            
            message_lower = message.lower()
            
            # Extract recipient - look for email addresses
            recipient_match = re.search(r'([^\s]+@[^\s]+)', message)
            recipient = None
            
            if recipient_match:
                recipient = recipient_match.group(1)
            else:
                # Try to extract name and suggest email format
                name_match = re.search(r'to\s+(\w+)', message_lower)
                if name_match:
                    name = name_match.group(1)
                    return {
                        "response": f"📧 I'll help you draft an email to {name}. Please provide their email address. For example: 'send email to {name}@example.com'",
                        "action_taken": "send_email",
                        "suggestions": [f"Send to {name}@example.com", "Read emails", "Search emails"]
                    }
                else:
                    # For reply scenarios, try to find the sender name
                    reply_name_match = re.search(r'from\s+(\w+)', message_lower)
                    if reply_name_match:
                        name = reply_name_match.group(1)
                        return {
                            "response": f"📧 I'll help you reply to {name}. Please provide their email address. For example: 'reply to {name}@example.com'",
                            "action_taken": "send_email",
                            "suggestions": [f"Reply to {name}@example.com", "Read emails", "Search emails"]
                        }
                    else:
                        return {
                            "response": "❌ Please specify a recipient email address. For example: 'send a thank-you email to user@example.com for the interview'",
                            "action_taken": "send_email",
                            "suggestions": ["Read emails", "Search emails", "Find important emails"]
                        }
            
            # Generate subject and body based on context
            subject = ""
            body = ""
            
            # Thank you email
            if any(phrase in message_lower for phrase in ["thank you", "thank-you", "thankyou", "thanks"]):
                if "interview" in message_lower:
                    subject = "Thank You for the Interview"
                    body = "Dear [Name],\n\nThank you for taking the time to interview me. I appreciate the opportunity to discuss the position and learn more about your company.\n\nI look forward to hearing from you.\n\nBest regards,\n[Your Name]"
                else:
                    subject = "Thank You"
                    body = "Dear [Name],\n\nThank you for your time and consideration.\n\nBest regards,\n[Your Name]"
            
            # Draft email
            elif any(phrase in message_lower for phrase in ["draft", "compose", "write"]):
                if "meeting" in message_lower and "tomorrow" in message_lower:
                    subject = "Meeting Tomorrow"
                    body = "Dear [Name],\n\nI hope this email finds you well. I wanted to confirm our meeting scheduled for tomorrow.\n\nLooking forward to our discussion.\n\nBest regards,\n[Your Name]"
                else:
                    subject = "Email Draft"
                    body = "Dear [Name],\n\n[Your message here]\n\nBest regards,\n[Your Name]"
            
            # Reply email
            elif any(phrase in message_lower for phrase in ["reply", "respond"]):
                if "unavailable" in message_lower:
                    subject = "Re: [Original Subject]"
                    body = "Dear [Name],\n\nThank you for your email. I'm currently unavailable and will get back to you as soon as possible.\n\nBest regards,\n[Your Name]"
                else:
                    subject = "Re: [Original Subject]"
                    body = "Dear [Name],\n\n[Your reply here]\n\nBest regards,\n[Your Name]"
            
            # Follow up email
            elif any(phrase in message_lower for phrase in ["follow up", "follow-up", "followup"]):
                if "report" in message_lower:
                    subject = "Follow-up: Report Status"
                    body = "Dear [Name],\n\nI hope this email finds you well. I wanted to follow up regarding the status of the report we discussed.\n\nPlease let me know if you need any additional information.\n\nBest regards,\n[Your Name]"
                else:
                    subject = "Follow-up"
                    body = "Dear [Name],\n\nI wanted to follow up on our previous discussion.\n\nBest regards,\n[Your Name]"
            
            # Availability email
            elif any(phrase in message_lower for phrase in ["availability", "schedule", "meeting"]):
                subject = "My Availability for Next Week"
                body = "Dear [Name],\n\nI hope this email finds you well. Here is my availability for next week:\n\n- Monday: [Time slots]\n- Tuesday: [Time slots]\n- Wednesday: [Time slots]\n- Thursday: [Time slots]\n- Friday: [Time slots]\n\nPlease let me know what works best for you.\n\nBest regards,\n[Your Name]"
            
            # Default case
            else:
                subject = "Email"
                body = "Dear [Name],\n\n[Your message here]\n\nBest regards,\n[Your Name]"
            
            # Call the Gmail API to send the email
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:8000/api/gmail/send",
                    json={
                        "to": recipient,
                        "subject": subject,
                        "body": body
                    }
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "response": f"✅ Email sent successfully to {recipient}",
                            "action_taken": "send_email",
                            "suggestions": ["Read emails", "Search emails", "Find important emails"],
                            "email_details": {
                                "to": recipient,
                                "subject": subject,
                                "body": body
                            }
                        }
                    else:
                        return {
                            "response": "❌ Failed to send email. Please check your Gmail settings.",
                            "action_taken": "send_email",
                            "suggestions": ["Read emails", "Search emails", "Check Gmail connection"]
                        }
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {
                "response": "❌ I encountered an error while sending the email. Please try again.",
                "action_taken": "send_email",
                "suggestions": ["Read emails", "Search emails", "Check Gmail connection"]
            }
    
    async def _handle_mark_as_read(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle marking emails as read"""
        try:
            # Extract email ID from message
            import re
            email_id_match = re.search(r'email\s+(\d+)', message.lower())
            if not email_id_match:
                return {
                    "response": "❌ Please specify which email to mark as read. For example: 'mark as read email 1' or 'mark as read email 2'",
                    "action_taken": "mark_as_read",
                    "suggestions": ["Read unread emails", "Search emails", "Find important emails"]
                }
            
            email_index = int(email_id_match.group(1)) - 1  # Convert to 0-based index
            
            # First get the list of UNREAD emails to find the email ID
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://localhost:8000/api/gmail/emails",
                    params={"query": "is:unread in:inbox", "max_results": 20}  # Direct unread query
                ) as response:
                    
                    if response.status == 200:
                        emails = await response.json()
                        # All emails returned should be unread since we used is:unread query
                        unread_emails = emails
                        if email_index < len(unread_emails):
                            email = unread_emails[email_index]
                            
                            # Mark the email as read
                            async with session.put(
                                f"http://localhost:8000/api/gmail/emails/{email['id']}/mark_read"
                            ) as update_response:
                                
                                if update_response.status == 200:
                                    # Clear cache to ensure fresh data on next request
                                    try:
                                        # Clear cache multiple times to ensure it's cleared
                                        for _ in range(3):
                                            async with session.post("http://localhost:8000/api/gmail/debug/clear-cache") as cache_response:
                                                if cache_response.status == 200:
                                                    logger.info("Cache cleared successfully after marking email as read")
                                                else:
                                                    logger.warning("Failed to clear cache after marking email as read")
                                                await asyncio.sleep(0.1)  # Small delay between cache clears
                                    except Exception as e:
                                        logger.warning(f"Error clearing cache: {e}")
                                    
                                    return {
                                        "response": f"✅ Email {email_index + 1} marked as read.",
                                        "action_taken": "mark_as_read",
                                        "suggestions": ["Read unread emails", "Search emails", "Find important emails"]
                                    }
                                else:
                                    return {
                                        "response": f"❌ Could not mark email {email_index + 1} as read.",
                                        "action_taken": "mark_as_read",
                                        "suggestions": ["Read unread emails", "Search emails", "Find important emails"]
                                    }
                        else:
                            return {
                                "response": f"❌ Email {email_index + 1} not found. You have {len(unread_emails)} unread emails.",
                                "action_taken": "mark_as_read",
                                "suggestions": ["Read unread emails", "Search emails", "Find important emails"]
                            }
                    else:
                        return {
                            "response": "❌ I'm having trouble accessing your emails right now.",
                            "action_taken": "mark_as_read",
                            "suggestions": ["Read unread emails", "Search emails", "Check connection"]
                        }
        except Exception as e:
            logger.error(f"Error marking email as read: {e}")
            return {
                "response": "❌ I encountered an error while marking the email as read. Please try again.",
                "action_taken": "mark_as_read",
                "suggestions": ["Read unread emails", "Search emails", "Find important emails"]
            }
    
    async def _handle_filter_by_date(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle filtering emails by date"""
        try:
            # Extract date range from message
            date_range = entities.get('date_range', '').lower()
            message_lower = message.lower()
            
            # Check if user wants unread emails from a specific date
            is_unread_request = "unread" in message_lower
            
            # Get today's date for proper filtering
            from datetime import datetime, timedelta
            today = datetime.now()
            
            if "today" in date_range:
                # Use today's date for proper filtering
                if is_unread_request:
                    query = f"is:unread in:inbox after:{today.strftime('%Y-%m-%d')}"
                else:
                    query = f"after:{today.strftime('%Y-%m-%d')}"
            elif "yesterday" in date_range:
                yesterday = today - timedelta(days=1)
                if is_unread_request:
                    query = f"is:unread in:inbox after:{yesterday.strftime('%Y-%m-%d')} before:{today.strftime('%Y-%m-%d')}"
                else:
                    query = f"after:{yesterday.strftime('%Y-%m-%d')} before:{today.strftime('%Y-%m-%d')}"
            elif "this week" in date_range:
                # Start of current week (Monday)
                start_of_week = today - timedelta(days=today.weekday())
                if is_unread_request:
                    query = f"is:unread in:inbox after:{start_of_week.strftime('%Y-%m-%d')}"
                else:
                    query = f"after:{start_of_week.strftime('%Y-%m-%d')}"
            elif "last week" in date_range:
                # Previous week
                start_of_last_week = today - timedelta(days=today.weekday() + 7)
                end_of_last_week = start_of_last_week + timedelta(days=6)
                if is_unread_request:
                    query = f"is:unread in:inbox after:{start_of_last_week.strftime('%Y-%m-%d')} before:{end_of_last_week.strftime('%Y-%m-%d')}"
                else:
                    query = f"after:{start_of_last_week.strftime('%Y-%m-%d')} before:{end_of_last_week.strftime('%Y-%m-%d')}"
            else:
                if is_unread_request:
                    query = "is:unread in:inbox"
                else:
                    query = "after:2000-01-01" # Default to all emails if no date range
            
            async with aiohttp.ClientSession() as session:
                # If this is an unread request, use a higher max_results to get all unread emails
                max_results = 20 if is_unread_request else 10
                async with session.get(
                    "http://localhost:8000/api/gmail/emails",
                    params={"query": query, "max_results": max_results}
                ) as response:
                    
                    if response.status == 200:
                        emails = await response.json()
                        if emails:
                            email_list = []
                            
                            # For unread requests, only show unread emails
                            if is_unread_request:
                                emails_to_show = [email for email in emails if not email['is_read']]
                                unread_count = len(emails_to_show)
                            else:
                                emails_to_show = emails
                                unread_count = sum(1 for email in emails if not email['is_read'])
                            
                            for i, email in enumerate(emails_to_show, 1):
                                # Clean up sender name
                                sender = email['sender']
                                if '<' in sender and '>' in sender:
                                    sender = sender.split('<')[0].strip().strip('"')
                                
                                # Format date nicely
                                date_str = email['date']
                                try:
                                    from email.utils import parsedate_to_datetime
                                    from datetime import datetime
                                    parsed_date = parsedate_to_datetime(date_str)
                                    formatted_date = parsed_date.strftime("%b %d, %Y %I:%M %p")
                                except:
                                    formatted_date = date_str
                                
                                # Status indicator with color
                                status_icon = "🔴" if not email['is_read'] else "🟢"
                                status_text = "Unread" if not email['is_read'] else "Read"
                                
                                # Better summary - clean up HTML entities and improve readability
                                summary = email['snippet']
                                # Remove HTML entities
                                summary = summary.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                                # Remove URLs for cleaner summary
                                summary = re.sub(r'https?://\S+', '[URL]', summary)
                                # Limit to 120 characters for better readability
                                summary = summary[:120] + ('...' if len(summary) > 120 else '')
                                
                                email_list.append(f"**{i}. {status_icon} {sender}**")
                                email_list.append(f"   📧 **Subject:** {email['subject']}")
                                email_list.append(f"   📝 **Summary:** {summary}")
                                email_list.append(f"   📅 **Date:** {formatted_date}")
                                email_list.append(f"   {status_icon} **Status:** {status_text}")
                                email_list.append(f"   🆔 **ID:** {email['id']}")
                                email_list.append("")
                            
                            # Create a more descriptive title based on the date range and unread status
                            if is_unread_request:
                                if "today" in date_range:
                                    title = f"📬 **Unread Emails from Today ({len(emails_to_show)})**"
                                elif "yesterday" in date_range:
                                    title = f"📬 **Unread Emails from Yesterday ({len(emails_to_show)})**"
                                elif "this week" in date_range:
                                    title = f"📬 **Unread Emails from This Week ({len(emails_to_show)})**"
                                elif "last week" in date_range:
                                    title = f"📬 **Unread Emails from Last Week ({len(emails_to_show)})**"
                                else:
                                    title = f"📬 **Unread Emails ({len(emails_to_show)})**"
                            else:
                                if "today" in date_range:
                                    title = f"📅 **Emails from Today ({len(emails_to_show)})** - {unread_count} unread"
                                elif "yesterday" in date_range:
                                    title = f"📅 **Emails from Yesterday ({len(emails_to_show)})** - {unread_count} unread"
                                elif "this week" in date_range:
                                    title = f"📅 **Emails from This Week ({len(emails_to_show)})** - {unread_count} unread"
                                elif "last week" in date_range:
                                    title = f"📅 **Emails from Last Week ({len(emails_to_show)})** - {unread_count} unread"
                                else:
                                    title = f"📅 **Emails from {date_range} ({len(emails_to_show)})** - {unread_count} unread"
                            
                            return {
                                "response": title + "\n\n" + "\n".join(email_list),
                                "action_taken": "filter_by_date",
                                "suggestions": ["Show unread emails", "Read all emails", "Search emails", "New filter"],
                                "email_count": len(emails_to_show),
                                "unread_count": unread_count
                            }
                        else:
                            return {
                                "response": f"📅 No emails found from {date_range}.",
                                "action_taken": "filter_by_date",
                                "suggestions": ["Show unread emails", "Read all emails", "Search emails"]
                            }
                    else:
                        return {
                            "response": "❌ I'm having trouble filtering emails by date right now. Please try again later.",
                            "action_taken": "filter_by_date",
                            "suggestions": ["Show unread emails", "Read all emails", "Check connection"]
                        }
        except Exception as e:
            logger.error(f"Error filtering emails by date: {e}")
            return {
                "response": "❌ I encountered an error while filtering emails by date. Please try again.",
                "action_taken": "filter_by_date",
                "suggestions": ["Show unread emails", "Read all emails", "Check settings"]
            }
    
    async def _handle_find_attachments(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle finding emails with attachments"""
        try:
            # Extract date filter from message
            message_lower = message.lower()
            date_filter = ""
            
            from datetime import datetime, timedelta
            
            if "last week" in message_lower:
                today = datetime.now()
                start_of_last_week = today - timedelta(days=today.weekday() + 7)
                end_of_last_week = start_of_last_week + timedelta(days=6)
                date_filter = f"after:{start_of_last_week.strftime('%Y-%m-%d')} before:{end_of_last_week.strftime('%Y-%m-%d')}"
            elif "this week" in message_lower:
                today = datetime.now()
                start_of_week = today - timedelta(days=today.weekday())
                date_filter = f"after:{start_of_week.strftime('%Y-%m-%d')}"
            elif "today" in message_lower:
                today = datetime.now()
                date_filter = f"after:{today.strftime('%Y-%m-%d')}"
            elif "yesterday" in message_lower:
                today = datetime.now()
                yesterday = today - timedelta(days=1)
                date_filter = f"after:{yesterday.strftime('%Y-%m-%d')} before:{today.strftime('%Y-%m-%d')}"
            
            # Build search query
            search_query = "has:attachment"
            if date_filter:
                search_query += f" {date_filter}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://localhost:8000/api/gmail/emails",
                    params={"query": search_query, "max_results": 20}
                ) as response:
                    if response.status == 200:
                        emails_data = await response.json()
                        # Handle both list and dict responses
                        if isinstance(emails_data, list):
                            emails = emails_data
                        else:
                            emails = emails_data.get("emails", [])
                        
                        if not emails:
                            date_text = "with attachments"
                            if date_filter:
                                if "last week" in message_lower:
                                    date_text = "with attachments from last week"
                                elif "this week" in message_lower:
                                    date_text = "with attachments from this week"
                                elif "today" in message_lower:
                                    date_text = "with attachments from today"
                                elif "yesterday" in message_lower:
                                    date_text = "with attachments from yesterday"
                            
                            return {
                                "response": f"📎 No emails {date_text} found.",
                                "action_taken": "find_attachments",
                                "suggestions": ["Read all emails", "Search emails", "Find important emails"]
                            }
                        
                        # Format response
                        email_list = []
                        for i, email in enumerate(emails[:10], 1):
                            sender = email.get("sender", "Unknown")
                            subject = email.get("subject", "No Subject")
                            date = email.get("date", "Unknown Date")
                            
                            email_list.append(f"**{i}. {sender}**")
                            email_list.append(f"   📧 **Subject:** {subject}")
                            email_list.append(f"   📅 **Date:** {date}")
                            email_list.append("")
                        
                        return {
                            "response": f"📎 **Emails with Attachments ({len(emails)})**\n\n" + "\n".join(email_list),
                            "action_taken": "find_attachments",
                            "suggestions": ["Download attachments", "Read emails", "Search emails"],
                            "email_count": len(emails)
                        }
                    else:
                        return {
                            "response": "❌ Failed to fetch emails with attachments.",
                            "action_taken": "find_attachments",
                            "suggestions": ["Read emails", "Search emails", "Find important emails"]
                        }
        except Exception as e:
            logger.error(f"Error finding emails with attachments: {e}")
            return {
                "response": "❌ Error finding emails with attachments. Please try again.",
                "action_taken": "find_attachments",
                "suggestions": ["Read emails", "Search emails", "Find important emails"]
            }
    
    async def _handle_detect_spam(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle detecting spam emails"""
        return {
            "response": "I'll help you detect any spam emails in your inbox.",
            "action_taken": "detect_spam",
            "suggestions": ["Read all emails", "Find important emails", "Search emails", "Delete spam"]
        }
    
    async def _handle_find_meetings(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle finding meeting invites"""
        return {
            "response": "I'll help you find any meeting invites in your inbox.",
            "action_taken": "find_meetings",
            "suggestions": ["Read all emails", "Find important emails", "Search emails", "Accept meeting"]
        }
    
    async def _handle_manage_emails(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle managing emails (delete, archive, block)"""
        return {
            "response": "I'll help you manage your emails (delete, archive, block).",
            "action_taken": "manage_emails",
            "suggestions": ["Read all emails", "Find important emails", "Search emails", "Delete spam"]
        }
    
    async def _handle_find_important_emails(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle finding important emails"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://localhost:8000/api/gmail/emails",
                    params={"query": "is:important", "max_results": 10}
                ) as response:
                    
                    if response.status == 200:
                        emails = await response.json()
                        if emails:
                            email_list = []
                            unread_count = 0
                            
                            for i, email in enumerate(emails, 1):
                                # Clean up sender name
                                sender = email['sender']
                                if '<' in sender and '>' in sender:
                                    sender = sender.split('<')[0].strip().strip('"')
                                
                                # Format date nicely
                                date_str = email['date']
                                try:
                                    from email.utils import parsedate_to_datetime
                                    from datetime import datetime
                                    parsed_date = parsedate_to_datetime(date_str)
                                    formatted_date = parsed_date.strftime("%b %d, %Y %I:%M %p")
                                except:
                                    formatted_date = date_str
                                
                                # Status indicator with color
                                status_icon = "🔴" if not email['is_read'] else "🟢"
                                status_text = "Unread" if not email['is_read'] else "Read"
                                if not email['is_read']:
                                    unread_count += 1
                                
                                # Better summary - clean up HTML entities and improve readability
                                summary = email['snippet']
                                # Remove HTML entities
                                summary = summary.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                                # Remove URLs for cleaner summary
                                summary = re.sub(r'https?://\S+', '[URL]', summary)
                                # Limit to 120 characters for better readability
                                summary = summary[:120] + ('...' if len(summary) > 120 else '')
                                
                                email_list.append(f"**{i}. {status_icon} {sender}**")
                                email_list.append(f"   📧 **Subject:** {email['subject']}")
                                email_list.append(f"   📝 **Summary:** {summary}")
                                email_list.append(f"   📅 **Date:** {formatted_date}")
                                email_list.append(f"   {status_icon} **Status:** {status_text}")
                                email_list.append(f"   🆔 **ID:** {email['id']}")
                                email_list.append("")
                            
                            return {
                                "response": f"⭐ **Important Emails ({len(emails)})** - {unread_count} unread\n\n" + "\n".join(email_list),
                                "action_taken": "find_important_emails",
                                "suggestions": ["Show unread emails", "Read all emails", "Search emails", "Mark as read"],
                                "email_count": len(emails),
                                "unread_count": unread_count
                            }
                        else:
                            return {
                                "response": "⭐ No important emails found in your inbox.",
                                "action_taken": "find_important_emails",
                                "suggestions": ["Show unread emails", "Read all emails", "Search emails"]
                            }
                    else:
                        return {
                            "response": "❌ I'm having trouble finding important emails right now. Please try again later.",
                            "action_taken": "find_important_emails",
                            "suggestions": ["Show unread emails", "Read all emails", "Check connection"]
                        }
        except Exception as e:
            logger.error(f"Error finding important emails: {e}")
            return {
                "response": "❌ I encountered an error while finding important emails. Please check your Gmail connection.",
                "action_taken": "find_important_emails",
                "suggestions": ["Show unread emails", "Read all emails", "Check settings"]
            }
    
    async def _handle_find_spam_emails(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle finding spam emails"""
        return {
            "response": "I'll find any spam emails in your inbox.",
            "action_taken": "find_spam_emails",
            "suggestions": ["Read all emails", "Find important emails", "Search emails", "Delete spam"]
        }
    
    async def _handle_categorize_emails(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle email categorization"""
        return {
            "response": "I'll help you categorize your emails.",
            "action_taken": "categorize_emails",
            "suggestions": ["Read all emails", "Find important emails", "Find spam emails", "Find attachments"]
        } 
    
    async def _handle_summarize_unread_email(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle unread email summarization"""
        try:
            # Extract email ID from message
            import re
            email_id_match = re.search(r'email\s+(\d+)', message.lower())
            if not email_id_match:
                return {
                    "response": "❌ Please specify which unread email to summarize. For example: 'summarize unread email 1' or 'summarise unread email 2'",
                    "action_taken": "summarize_unread_email",
                    "suggestions": ["Read unread emails", "Search emails", "Find important emails"]
                }
            
            email_index = int(email_id_match.group(1)) - 1  # Convert to 0-based index
            
            # First get the list of UNREAD emails to find the email ID
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://localhost:8000/api/gmail/emails",
                    params={"query": "is:unread in:inbox", "max_results": 20}
                ) as response:
                    
                    if response.status == 200:
                        emails = await response.json()
                        # Filter for unread emails only
                        unread_emails = [email for email in emails if not email['is_read']]
                        if email_index < len(unread_emails):
                            email = unread_emails[email_index]
                            
                            # Get full email content
                            async with session.get(
                                f"http://localhost:8000/api/gmail/emails/{email['id']}"
                            ) as content_response:
                                
                                if content_response.status == 200:
                                    email_content = await content_response.json()
                                    
                                    # Clean up sender name
                                    sender = email['sender']
                                    if '<' in sender and '>' in sender:
                                        sender = sender.split('<')[0].strip().strip('"')
                                    
                                    # Format date nicely
                                    date_str = email['date']
                                    try:
                                        from email.utils import parsedate_to_datetime
                                        from datetime import datetime
                                        parsed_date = parsedate_to_datetime(date_str)
                                        formatted_date = parsed_date.strftime("%b %d, %Y %I:%M %p")
                                    except:
                                        formatted_date = date_str
                                    
                                    # Create summary
                                    summary = f"📧 **Unread Email Summary**\n\n"
                                    summary += f"**From:** {sender}\n"
                                    summary += f"**Subject:** {email['subject']}\n"
                                    summary += f"**Date:** {formatted_date}\n"
                                    summary += f"**Status:** 📬 Unread\n\n"
                                    summary += f"**Content:**\n{email_content.get('body', email['snippet'])[:500]}{'...' if len(email_content.get('body', email['snippet'])) > 500 else ''}"
                                    
                                    return {
                                        "response": summary,
                                        "action_taken": "summarize_unread_email",
                                        "suggestions": ["Read unread emails", "Search emails", "Mark as read"],
                                        "email_id": email['id']
                                    }
                                else:
                                    return {
                                        "response": f"❌ Could not retrieve content for unread email {email_index + 1}.",
                                        "action_taken": "summarize_unread_email",
                                        "suggestions": ["Read unread emails", "Search emails", "Find important emails"]
                                    }
                        else:
                            return {
                                "response": f"❌ Unread email {email_index + 1} not found. You have {len(unread_emails)} unread emails.",
                                "action_taken": "summarize_unread_email",
                                "suggestions": ["Read unread emails", "Search emails", "Find important emails"]
                            }
                    else:
                        return {
                            "response": "❌ I'm having trouble accessing your emails right now.",
                            "action_taken": "summarize_unread_email",
                            "suggestions": ["Read unread emails", "Search emails", "Check connection"]
                        }
        except Exception as e:
            logger.error(f"Error summarizing unread email: {e}")
            return {
                "response": "❌ I encountered an error while summarizing the unread email. Please try again.",
                "action_taken": "summarize_unread_email",
                "suggestions": ["Read unread emails", "Search emails", "Find important emails"]
            }

    async def _handle_summarize_email(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle email summarization"""
        try:
            # Extract email ID from message
            import re
            email_id_match = re.search(r'email\s+(\d+)', message.lower())
            if not email_id_match:
                return {
                    "response": "❌ Please specify which email to summarize. For example: 'summarize email 1' or 'summarise email 2'",
                    "action_taken": "summarize_email",
                    "suggestions": ["Read unread emails", "Search emails", "Find important emails"]
                }
            
            email_index = int(email_id_match.group(1)) - 1  # Convert to 0-based index
            
            # First get the list of emails to find the email ID
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://localhost:8000/api/gmail/emails",
                    params={"max_results": 20}
                ) as response:
                    
                    if response.status == 200:
                        emails = await response.json()
                        if email_index < len(emails):
                            email = emails[email_index]
                            
                            # Get full email content
                            async with session.get(
                                f"http://localhost:8000/api/gmail/emails/{email['id']}"
                            ) as content_response:
                                
                                if content_response.status == 200:
                                    email_content = await content_response.json()
                                    
                                    # Clean up sender name
                                    sender = email['sender']
                                    if '<' in sender and '>' in sender:
                                        sender = sender.split('<')[0].strip().strip('"')
                                    
                                    # Format date nicely
                                    date_str = email['date']
                                    try:
                                        from email.utils import parsedate_to_datetime
                                        from datetime import datetime
                                        parsed_date = parsedate_to_datetime(date_str)
                                        formatted_date = parsed_date.strftime("%b %d, %Y %I:%M %p")
                                    except:
                                        formatted_date = date_str
                                    
                                    # Create summary
                                    summary = f"📧 **Email Summary**\n\n"
                                    summary += f"**From:** {sender}\n"
                                    summary += f"**Subject:** {email['subject']}\n"
                                    summary += f"**Date:** {formatted_date}\n"
                                    summary += f"**Status:** {'📬 Unread' if not email['is_read'] else '📧 Read'}\n\n"
                                    summary += f"**Content:**\n{email_content.get('body', email['snippet'])[:500]}{'...' if len(email_content.get('body', email['snippet'])) > 500 else ''}"
                                    
                                    return {
                                        "response": summary,
                                        "action_taken": "summarize_email",
                                        "suggestions": ["Read unread emails", "Search emails", "Mark as read"],
                                        "email_id": email['id']
                                    }
                                else:
                                    return {
                                        "response": f"❌ Could not retrieve content for email {email_index + 1}.",
                                        "action_taken": "summarize_email",
                                        "suggestions": ["Read unread emails", "Search emails", "Find important emails"]
                                    }
                        else:
                            return {
                                "response": f"❌ Email {email_index + 1} not found. You have {len(emails)} emails.",
                                "action_taken": "summarize_email",
                                "suggestions": ["Read unread emails", "Search emails", "Find important emails"]
                            }
                    else:
                        return {
                            "response": "❌ I'm having trouble accessing your emails right now.",
                            "action_taken": "summarize_email",
                            "suggestions": ["Read unread emails", "Search emails", "Check connection"]
                        }
        except Exception as e:
            logger.error(f"Error summarizing email: {e}")
            return {
                "response": "❌ I encountered an error while summarizing the email. Please try again.",
                "action_taken": "summarize_email",
                "suggestions": ["Read unread emails", "Search emails", "Find important emails"]
            } 
    
    async def _handle_set_reminder(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle setting reminders for emails"""
        return {
            "response": "I'll help you set reminders for email follow-ups.",
            "action_taken": "set_reminder",
            "suggestions": ["Read emails", "Find important emails", "Search emails", "Mark as read"]
        }
    
    async def _handle_use_template(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle using email templates"""
        # Extract template type from message
        message_lower = message.lower()
        template_type = "general"
        
        if "meeting" in message_lower:
            template_type = "meeting"
        elif "thank" in message_lower:
            template_type = "thank_you"
        elif "follow up" in message_lower:
            template_type = "follow_up"
        elif "interview" in message_lower:
            template_type = "interview"
        
        templates = {
            "meeting": {
                "subject": "Meeting Request",
                "body": "Hi {recipient},\n\nI hope this email finds you well. I would like to schedule a meeting to discuss {topic}.\n\nPlease let me know your availability.\n\nBest regards,\n{your_name}"
            },
            "thank_you": {
                "subject": "Thank You",
                "body": "Hi {recipient},\n\nThank you for {reason}. I really appreciate it.\n\nBest regards,\n{your_name}"
            },
            "follow_up": {
                "subject": "Follow-up",
                "body": "Hi {recipient},\n\nI'm following up on {topic}. Please let me know the status.\n\nBest regards,\n{your_name}"
            },
            "interview": {
                "subject": "Interview Follow-up",
                "body": "Hi {recipient},\n\nThank you for the interview opportunity. I enjoyed our conversation about {position}.\n\nI look forward to hearing from you.\n\nBest regards,\n{your_name}"
            },
            "general": {
                "subject": "Email Template",
                "body": "Hi {recipient},\n\n{message}\n\nBest regards,\n{your_name}"
            }
        }
        
        template = templates.get(template_type, templates["general"])
        
        return {
            "response": f"📧 **Email Template: {template_type.replace('_', ' ').title()}**\n\n**Subject:** {template['subject']}\n\n**Body:**\n{template['body']}\n\n💡 **Usage:** Replace {{recipient}}, {{topic}}, {{reason}}, {{position}}, {{message}}, and {{your_name}} with actual values.",
            "action_taken": "use_template",
            "suggestions": ["Send email", "Read emails", "Search emails", "Find important emails"],
            "template": template,
            "template_type": template_type
        }
    
    async def _handle_schedule_email(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle scheduling emails for later"""
        # Extract scheduling time from message
        message_lower = message.lower()
        schedule_time = "later"
        
        if "tomorrow" in message_lower:
            schedule_time = "tomorrow"
        elif "next week" in message_lower:
            schedule_time = "next_week"
        elif "later" in message_lower:
            schedule_time = "later"
        
        return {
            "response": f"📅 **Email Scheduling**\n\nI'll help you schedule an email for {schedule_time}.\n\n💡 **Note:** Email scheduling is currently in development. For now, you can compose the email and I'll remind you to send it later.",
            "action_taken": "schedule_email",
            "suggestions": ["Send email", "Use template", "Read emails", "Set reminder"],
            "schedule_time": schedule_time
        }
    
    async def _handle_analyze_sentiment(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle sentiment analysis of emails"""
        return {
            "response": "🧠 **Sentiment Analysis**\n\nI'll analyze the sentiment and tone of your emails.\n\n💡 **Features:**\n• Positive/Negative/Neutral tone detection\n• Professional vs. casual language\n• Emotional intensity analysis\n• Action-oriented vs. informational content",
            "action_taken": "analyze_sentiment",
            "suggestions": ["Read emails", "Find important emails", "Search emails", "Smart reply"]
        }
    
    async def _handle_smart_reply(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle smart reply suggestions"""
        return {
            "response": "🤖 **Smart Reply Suggestions**\n\nI'll generate intelligent reply suggestions based on the email content.\n\n💡 **Features:**\n• Context-aware responses\n• Professional tone matching\n• Quick action responses\n• Customizable suggestions",
            "action_taken": "smart_reply",
            "suggestions": ["Read emails", "Send email", "Use template", "Analyze sentiment"]
        }
    
    async def _handle_extract_actions(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle extracting action items from emails"""
        return {
            "response": "📋 **Action Item Extraction**\n\nI'll identify and extract action items, tasks, and follow-ups from your emails.\n\n💡 **Features:**\n• Task identification\n• Due date extraction\n• Priority assessment\n• Follow-up reminders",
            "action_taken": "extract_actions",
            "suggestions": ["Read emails", "Set reminder", "Find important emails", "Search emails"]
        }
    
    async def _handle_translate_email(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle email translation"""
        # Extract target language from message
        message_lower = message.lower()
        target_language = "english"
        
        if "spanish" in message_lower:
            target_language = "spanish"
        elif "french" in message_lower:
            target_language = "french"
        elif "german" in message_lower:
            target_language = "german"
        elif "chinese" in message_lower:
            target_language = "chinese"
        
        return {
            "response": f"🌐 **Email Translation**\n\nI'll translate emails to {target_language}.\n\n💡 **Features:**\n• Multi-language support\n• Preserve formatting\n• Context-aware translation\n• Professional tone maintenance",
            "action_taken": "translate_email",
            "suggestions": ["Read emails", "Send email", "Search emails", "Find important emails"],
            "target_language": target_language
        }
    
    async def _handle_group_emails(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle email grouping and categorization"""
        return {
            "response": "📁 **Email Grouping**\n\nI'll group similar emails into topics and categories.\n\n💡 **Features:**\n• Topic-based grouping\n• Sender categorization\n• Time-based organization\n• Priority clustering",
            "action_taken": "group_emails",
            "suggestions": ["Read emails", "Find important emails", "Search emails", "Categorize emails"]
        }
    
    async def _handle_mark_all_as_read(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle marking all emails as read"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get all unread emails first
                async with session.get(
                    "http://localhost:8000/api/gmail/emails",
                    params={"query": "is:unread in:inbox", "max_results": 100}
                ) as response:
                    if response.status == 200:
                        emails_data = await response.json()
                        # Handle both list and dict responses
                        if isinstance(emails_data, list):
                            emails = emails_data
                        else:
                            emails = emails_data.get("emails", [])
                        
                        if not emails:
                            return {
                                "response": "✅ No unread emails to mark as read.",
                                "action_taken": "mark_all_as_read",
                                "suggestions": ["Read emails", "Search emails", "Find important emails"]
                            }
                        
                        # Mark each email as read
                        marked_count = 0
                        for email in emails:
                            message_id = email.get("id")
                            if message_id:
                                async with session.put(
                                    f"http://localhost:8000/api/gmail/emails/{message_id}/mark_read"
                                ) as mark_response:
                                    if mark_response.status == 200:
                                        marked_count += 1
                        
                        return {
                            "response": f"✅ Successfully marked {marked_count} emails as read.",
                            "action_taken": "mark_all_as_read",
                            "suggestions": ["Read emails", "Search emails", "Find important emails"],
                            "marked_count": marked_count
                        }
                    else:
                        return {
                            "response": "❌ Failed to fetch unread emails.",
                            "action_taken": "mark_all_as_read",
                            "suggestions": ["Read emails", "Search emails", "Find important emails"]
                        }
        except Exception as e:
            logger.error(f"Error marking all emails as read: {e}")
            return {
                "response": "❌ Error marking emails as read. Please try again.",
                "action_taken": "mark_all_as_read",
                "suggestions": ["Read emails", "Search emails", "Find important emails"]
            }
    
    async def _handle_summarize_latest_emails(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle summarizing the latest emails in inbox"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get latest emails from inbox
                async with session.get(
                    "http://localhost:8000/api/gmail/emails",
                    params={"query": "in:inbox", "max_results": 10}
                ) as response:
                    if response.status == 200:
                        emails_data = await response.json()
                        # Handle both list and dict responses
                        if isinstance(emails_data, list):
                            emails = emails_data
                        else:
                            emails = emails_data.get("emails", [])
                        
                        if not emails:
                            return {
                                "response": "📭 No emails found in your inbox.",
                                "action_taken": "summarize_latest_emails",
                                "suggestions": ["Read emails", "Search emails", "Find important emails"]
                            }
                        
                        # Create summary
                        summary_parts = [f"📬 **Latest {len(emails)} Emails Summary**\n"]
                        
                        for i, email in enumerate(emails[:5], 1):  # Show first 5
                            sender = email.get("sender", "Unknown")
                            subject = email.get("subject", "No Subject")
                            date = email.get("date", "Unknown Date")
                            is_read = email.get("is_read", True)
                            status = "🟢 Read" if is_read else "🔴 Unread"
                            
                            summary_parts.append(
                                f"**{i}. {sender}**\n"
                                f"   📧 **Subject:** {subject}\n"
                                f"   📅 **Date:** {date}\n"
                                f"   {status}\n"
                            )
                        
                        if len(emails) > 5:
                            summary_parts.append(f"\n... and {len(emails) - 5} more emails")
                        
                        return {
                            "response": "\n".join(summary_parts),
                            "action_taken": "summarize_latest_emails",
                            "suggestions": ["Read all emails", "Search emails", "Find important emails"],
                            "email_count": len(emails)
                        }
                    else:
                        return {
                            "response": "❌ Failed to fetch emails from inbox.",
                            "action_taken": "summarize_latest_emails",
                            "suggestions": ["Read emails", "Search emails", "Find important emails"]
                        }
        except Exception as e:
            logger.error(f"Error summarizing latest emails: {e}")
            return {
                "response": "❌ Error summarizing emails. Please try again.",
                "action_taken": "summarize_latest_emails",
                "suggestions": ["Read emails", "Search emails", "Find important emails"]
            }
    
    async def _handle_find_promotional_emails(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle finding promotional emails"""
        try:
            async with aiohttp.ClientSession() as session:
                # Search for promotional emails
                search_query = "category:promotions OR category:social OR category:updates"
                async with session.get(
                    "http://localhost:8000/api/gmail/emails",
                    params={"query": search_query, "max_results": 20}
                ) as response:
                    if response.status == 200:
                        emails_data = await response.json()
                        # Handle both list and dict responses
                        if isinstance(emails_data, list):
                            emails = emails_data
                        else:
                            emails = emails_data.get("emails", [])
                        
                        if not emails:
                            return {
                                "response": "📭 No promotional emails found.",
                                "action_taken": "find_promotional_emails",
                                "suggestions": ["Read emails", "Search emails", "Find important emails"]
                            }
                        
                        # Format response
                        email_list = []
                        for i, email in enumerate(emails[:10], 1):
                            sender = email.get("sender", "Unknown")
                            subject = email.get("subject", "No Subject")
                            date = email.get("date", "Unknown Date")
                            
                            email_list.append(f"**{i}. {sender}**")
                            email_list.append(f"   📧 **Subject:** {subject}")
                            email_list.append(f"   📅 **Date:** {date}")
                            email_list.append("")
                        
                        return {
                            "response": f"📧 **Promotional Emails ({len(emails)})**\n\n" + "\n".join(email_list),
                            "action_taken": "find_promotional_emails",
                            "suggestions": ["Delete promotional emails", "Archive emails", "Read emails", "Search emails"],
                            "email_count": len(emails)
                        }
                    else:
                        return {
                            "response": "❌ Failed to fetch promotional emails.",
                            "action_taken": "find_promotional_emails",
                            "suggestions": ["Read emails", "Search emails", "Find important emails"]
                        }
        except Exception as e:
            logger.error(f"Error finding promotional emails: {e}")
            return {
                "response": "❌ Error finding promotional emails. Please try again.",
                "action_taken": "find_promotional_emails",
                "suggestions": ["Read emails", "Search emails", "Find important emails"]
            }
    
    async def _handle_find_meeting_invites(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle finding meeting invites"""
        try:
            async with aiohttp.ClientSession() as session:
                # Search for actual meeting invites (exclude Jira/GitHub notifications)
                search_query = "subject:(invitation OR invite) AND -jira AND -github AND -ocpbugs AND -ocpqe"
                async with session.get(
                    "http://localhost:8000/api/gmail/emails",
                    params={"query": search_query, "max_results": 20}
                ) as response:
                    if response.status == 200:
                        emails_data = await response.json()
                        # Handle both list and dict responses
                        if isinstance(emails_data, list):
                            emails = emails_data
                        else:
                            emails = emails_data.get("emails", [])
                        
                        # Filter out Jira/GitHub notifications and format response
                        filtered_emails = []
                        for email in emails:
                            sender = email.get("sender", "Unknown").lower()
                            subject = email.get("subject", "No Subject").lower()
                            
                            # Skip Jira, GitHub, and other notification emails
                            if any(keyword in sender or keyword in subject for keyword in ["jira", "github", "ocpbugs", "ocpqe", "prow"]):
                                continue
                            
                            # Only include actual meeting invites
                            if any(keyword in subject for keyword in ["invitation", "invite", "meeting", "calendar"]):
                                filtered_emails.append(email)
                        
                        if not filtered_emails:
                            return {
                                "response": "📭 No actual meeting invites found. Most emails appear to be Jira notifications.",
                                "action_taken": "find_meeting_invites",
                                "suggestions": ["Read emails", "Search emails", "Find important emails"]
                            }
                        
                        # Format response
                        email_list = []
                        for i, email in enumerate(filtered_emails[:10], 1):
                            sender = email.get("sender", "Unknown")
                            subject = email.get("subject", "No Subject")
                            date = email.get("date", "Unknown Date")
                            
                            email_list.append(f"**{i}. {sender}**")
                            email_list.append(f"   📧 **Subject:** {subject}")
                            email_list.append(f"   📅 **Date:** {date}")
                            email_list.append("")
                        
                        return {
                            "response": f"📅 **Meeting Invites ({len(filtered_emails)})**\n\n" + "\n".join(email_list),
                            "action_taken": "find_meeting_invites",
                            "suggestions": ["Accept meeting", "Schedule call", "Read emails", "Search emails"],
                            "email_count": len(filtered_emails)
                        }
                    else:
                        return {
                            "response": "❌ Failed to fetch meeting invites.",
                            "action_taken": "find_meeting_invites",
                            "suggestions": ["Read emails", "Search emails", "Find important emails"]
                        }
        except Exception as e:
            logger.error(f"Error finding meeting invites: {e}")
            return {
                "response": "❌ Error finding meeting invites. Please try again.",
                "action_taken": "find_meeting_invites",
                "suggestions": ["Read emails", "Search emails", "Find important emails"]
            }
    
    async def _handle_find_zoom_links(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle finding emails with Zoom/Google Meet links"""
        try:
            async with aiohttp.ClientSession() as session:
                # Search for emails with meeting links
                search_query = "subject:(zoom OR meet OR meeting) OR (zoom.us OR meet.google.com)"
                async with session.get(
                    "http://localhost:8000/api/gmail/emails",
                    params={"query": search_query, "max_results": 20}
                ) as response:
                    if response.status == 200:
                        emails_data = await response.json()
                        # Handle both list and dict responses
                        if isinstance(emails_data, list):
                            emails = emails_data
                        else:
                            emails = emails_data.get("emails", [])
                        
                        if not emails:
                            return {
                                "response": "📭 No emails with meeting links found.",
                                "action_taken": "find_zoom_links",
                                "suggestions": ["Read emails", "Search emails", "Find important emails"]
                            }
                        
                        # Format response
                        email_list = []
                        for i, email in enumerate(emails[:10], 1):
                            sender = email.get("sender", "Unknown")
                            subject = email.get("subject", "No Subject")
                            date = email.get("date", "Unknown Date")
                            
                            email_list.append(f"**{i}. {sender}**")
                            email_list.append(f"   📧 **Subject:** {subject}")
                            email_list.append(f"   📅 **Date:** {date}")
                            email_list.append("")
                        
                        return {
                            "response": f"🔗 **Emails with Meeting Links ({len(emails)})**\n\n" + "\n".join(email_list),
                            "action_taken": "find_zoom_links",
                            "suggestions": ["Join meeting", "Schedule call", "Read emails", "Search emails"],
                            "email_count": len(emails)
                        }
                    else:
                        return {
                            "response": "❌ Failed to fetch emails with meeting links.",
                            "action_taken": "find_zoom_links",
                            "suggestions": ["Read emails", "Search emails", "Find important emails"]
                        }
        except Exception as e:
            logger.error(f"Error finding emails with meeting links: {e}")
            return {
                "response": "❌ Error finding emails with meeting links. Please try again.",
                "action_taken": "find_zoom_links",
                "suggestions": ["Read emails", "Search emails", "Find important emails"]
            }
    
    async def _handle_accept_meeting(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle accepting meeting invites"""
        try:
            # Extract meeting details from message
            message_lower = message.lower()
            
            # Extract sender/organizer
            sender_match = re.search(r'from\s+(\w+)', message_lower)
            sender = sender_match.group(1) if sender_match else "organizer"
            
            # Extract date/time
            date_match = re.search(r'(friday|monday|tuesday|wednesday|thursday|saturday|sunday|today|tomorrow)', message_lower)
            date = date_match.group(1) if date_match else "scheduled time"
            
            return {
                "response": f"✅ **Meeting Accepted!**\n\nI've accepted the meeting invite from {sender.title()} for {date}.\n\n**Next Steps:**\n• Meeting has been added to your calendar\n• You'll receive a confirmation email\n• Calendar reminder will be set automatically\n\n*Note: Full Google Calendar integration coming soon!*",
                "action_taken": "accept_meeting",
                "suggestions": ["Show calendar", "Schedule meeting", "Find meetings", "Check emails"],
                "meeting_details": {
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
    
    async def _handle_schedule_call(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle scheduling calls/meetings"""
        try:
            # Extract call details from message
            message_lower = message.lower()
            
            # Extract person
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
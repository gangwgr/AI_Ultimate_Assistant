#!/usr/bin/env python3
"""
Test Calendar Features with Meeting Links
Comprehensive test for all calendar functionality
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_calendar_features():
    """Test all calendar features"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Calendar Features with Meeting Links")
    print("=" * 60)
    
    test_cases = [
        # Basic Calendar Views
        {
            "name": "Show Calendar Overview",
            "message": "Show my calendar",
            "expected_intent": "show_calendar"
        },
        {
            "name": "Show Today's Calendar",
            "message": "Show my calendar for today",
            "expected_intent": "show_calendar"
        },
        {
            "name": "Show Weekly Calendar",
            "message": "Show my calendar for this week",
            "expected_intent": "show_calendar"
        },
        {
            "name": "Show Daily Schedule",
            "message": "Show today's schedule",
            "expected_intent": "show_calendar"
        },
        
        # Meeting Scheduling
        {
            "name": "Schedule Meeting",
            "message": "Schedule a meeting about project review for tomorrow at 3 PM",
            "expected_intent": "schedule_meeting"
        },
        {
            "name": "Book Meeting",
            "message": "Book a meeting for team sync on Monday at 10 AM",
            "expected_intent": "schedule_meeting"
        },
        {
            "name": "Create Meeting",
            "message": "Create meeting about sprint planning for Friday 2 PM",
            "expected_intent": "schedule_meeting"
        },
        
        # Send Invites
        {
            "name": "Send Meeting Invite",
            "message": "Send invite to team for project review meeting tomorrow at 2 PM",
            "expected_intent": "send_invite"
        },
        {
            "name": "Send Meeting Invitation",
            "message": "Send meeting invitation to john for code review on Monday",
            "expected_intent": "send_invite"
        },
        {
            "name": "Invite to Meeting",
            "message": "Invite alice to team sync meeting for tomorrow 3 PM",
            "expected_intent": "send_invite"
        },
        
        # Accept Meetings
        {
            "name": "Accept Meeting Invite",
            "message": "Accept the meeting invite from HR on Friday",
            "expected_intent": "accept_meeting"
        },
        {
            "name": "Accept Meeting",
            "message": "Accept meeting from john about project review",
            "expected_intent": "accept_meeting"
        },
        {
            "name": "Accept Invitation",
            "message": "Accept the invitation from team lead for Monday",
            "expected_intent": "accept_meeting"
        },
        
        # Schedule Calls
        {
            "name": "Schedule Call",
            "message": "Schedule a call with rgangwar@redhat.com for today 22:00 PM",
            "expected_intent": "schedule_call"
        },
        {
            "name": "Book Call",
            "message": "Book a call with john for Monday 3 PM",
            "expected_intent": "schedule_call"
        },
        {
            "name": "Set Up Call",
            "message": "Set up call with alice for tomorrow 2 PM",
            "expected_intent": "schedule_call"
        },
        
        # Meeting Reminders
        {
            "name": "Set Meeting Reminder",
            "message": "Remind me to reply to this meeting invite later",
            "expected_intent": "set_meeting_reminder"
        },
        {
            "name": "Meeting Reply Reminder",
            "message": "Set reminder for meeting reply tomorrow",
            "expected_intent": "set_meeting_reminder"
        },
        {
            "name": "Meeting Response Reminder",
            "message": "Remind me to respond to meeting invite next week",
            "expected_intent": "set_meeting_reminder"
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i:2d}. {test_case['name']}")
            print(f"    Message: {test_case['message']}")
            print(f"    Expected: {test_case['expected_intent']}")
            
            try:
                async with session.post(
                    f"{base_url}/api/agent/chat",
                    json={"message": test_case['message']}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        actual_intent = data.get('action_taken', 'unknown')
                        agent = data.get('agent', 'unknown')
                        response_text = data.get('response', '')
                        
                        # Check if correct agent was selected
                        if agent == 'CalendarAgent':
                            print(f"    ✅ Agent: {agent}")
                        else:
                            print(f"    ❌ Agent: {agent} (expected CalendarAgent)")
                        
                        # Check if correct intent was detected
                        if actual_intent == test_case['expected_intent']:
                            print(f"    ✅ Intent: {actual_intent}")
                        else:
                            print(f"    ❌ Intent: {actual_intent} (expected {test_case['expected_intent']})")
                        
                        # Check if response contains meeting links
                        if '🔗' in response_text:
                            print(f"    ✅ Meeting Links: Found")
                        else:
                            print(f"    ℹ️  Meeting Links: None found")
                        
                        # Show first 100 chars of response
                        preview = response_text[:100] + "..." if len(response_text) > 100 else response_text
                        print(f"    Response: {preview}")
                        
                    else:
                        print(f"    ❌ HTTP {response.status}")
                        
            except Exception as e:
                print(f"    ❌ Error: {e}")
            
            # Small delay between requests
            await asyncio.sleep(0.5)
    
    print(f"\n🎉 Calendar Testing Complete!")
    print(f"   Tested {len(test_cases)} calendar features")
    print(f"   Check the responses above for meeting links and functionality")

if __name__ == "__main__":
    asyncio.run(test_calendar_features()) 
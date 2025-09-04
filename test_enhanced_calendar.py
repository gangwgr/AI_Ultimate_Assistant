#!/usr/bin/env python3
"""
Test Enhanced Calendar Functionality
"""

import asyncio
import aiohttp
import json

async def test_enhanced_calendar():
    """Test the enhanced calendar functionality"""
    
    test_cases = [
        # Daily and Weekly Views
        ("Show my calendar", "show_calendar"),
        ("Show my calendar for today", "show_daily_calendar"),
        ("Show my calendar for this week", "show_weekly_calendar"),
        ("Show today's schedule", "show_daily_calendar"),
        ("Show this week's calendar", "show_weekly_calendar"),
        
        # Meeting Scheduling
        ("Schedule a meeting about project review for tomorrow at 3 PM", "schedule_meeting"),
        ("Book a meeting for team sync on Monday at 10 AM", "schedule_meeting"),
        ("Create meeting about sprint planning for Friday 2 PM", "schedule_meeting"),
        
        # Send Invites
        ("Send invite to team for project review meeting tomorrow at 2 PM", "send_invite"),
        ("Send meeting invitation to john for code review on Monday", "send_invite"),
        ("Invite alice to team sync meeting for tomorrow 3 PM", "send_invite"),
        
        # Accept Meetings
        ("Accept the meeting invite from HR on Friday", "accept_meeting"),
        ("Accept meeting from john about project review", "accept_meeting"),
        ("Accept the invitation from team lead for Monday", "accept_meeting"),
        
        # Schedule Calls
        ("Schedule a call with rgangwar@redhat.com for today 22:00 PM", "schedule_call"),
        ("Book a call with john for Monday 3 PM", "schedule_call"),
        ("Set up call with alice for tomorrow 2 PM", "schedule_call"),
        
        # Meeting Reminders
        ("Remind me to reply to this meeting invite later", "set_meeting_reminder"),
        ("Set reminder for meeting reply tomorrow", "set_meeting_reminder"),
        ("Remind me to respond to meeting invite next week", "set_meeting_reminder"),
    ]
    
    print("📅 Testing Enhanced Calendar Functionality")
    print("=" * 70)
    
    async with aiohttp.ClientSession() as session:
        for i, (test_case, expected_intent) in enumerate(test_cases, 1):
            print(f"\n{i}. Testing: '{test_case}'")
            print(f"   Expected intent: {expected_intent}")
            
            try:
                async with session.post(
                    "http://localhost:8000/api/agent/chat",
                    json={"message": test_case}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        actual_intent = result.get("action_taken", "unknown")
                        response_text = result.get("response", "No response")
                        agent = result.get("agent", "unknown")
                        
                        print(f"   ✅ Agent: {agent}")
                        print(f"   ✅ Actual intent: {actual_intent}")
                        
                        if actual_intent == expected_intent:
                            print(f"   ✅ CORRECT! Intent matched")
                        else:
                            print(f"   ❌ WRONG! Expected {expected_intent}, got {actual_intent}")
                        
                        # Check if response is meaningful
                        if "❌" in response_text and "Error" in response_text:
                            print(f"   ⚠️  Handler error: {response_text[:50]}...")
                        elif "❌" in response_text or "Please specify" in response_text:
                            print(f"   ⚠️  Response needs improvement: {response_text[:50]}...")
                        else:
                            print(f"   ✅ Good response: {response_text[:50]}...")
                    else:
                        print(f"   ❌ HTTP {response.status}")
                        
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # Small delay between requests
            await asyncio.sleep(1)
    
    print("\n" + "=" * 70)
    print("🎉 Enhanced Calendar Testing completed!")

if __name__ == "__main__":
    asyncio.run(test_enhanced_calendar()) 
#!/usr/bin/env python3
"""
Test Calendar Integration Features
"""

import asyncio
import aiohttp
import json

async def test_calendar_integration():
    """Test the calendar integration features"""
    
    test_cases = [
        ("Show my calendar", "show_calendar"),
        ("Accept the meeting invite from HR on Friday", "accept_meeting"),
        ("Schedule a call with John for Monday 3 PM", "schedule_call"),
        ("Remind me to reply to this meeting invite later", "set_meeting_reminder"),
        ("Do I have any meeting invites in my inbox", "find_meeting_invites"),
        ("Find emails with Zoom/Google Meet links", "find_zoom_links"),
    ]
    
    print("📅 Testing Calendar Integration Features")
    print("=" * 60)
    
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
    
    print("\n" + "=" * 60)
    print("🎉 Calendar Integration Testing completed!")

if __name__ == "__main__":
    asyncio.run(test_calendar_integration()) 
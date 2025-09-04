#!/usr/bin/env python3
"""
Test Meeting Invite Fix
Test the improved meeting invite functionality
"""

import asyncio
import aiohttp
import json

async def test_meeting_invite_fix():
    """Test the improved meeting invite functionality"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Improved Meeting Invite Functionality")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "Email Address with Title and Time",
            "message": "send a meeting invite to rgangwar@redhat.com title test at 10:00 today",
            "expected_recipient": "rgangwar@redhat.com",
            "expected_title": "test",
            "expected_time": "10:00"
        },
        {
            "name": "Name with Title and Time",
            "message": "send invite to john title project review at 2:30 PM tomorrow",
            "expected_recipient": "john",
            "expected_title": "project review",
            "expected_time": "2:30 PM"
        },
        {
            "name": "Team with Topic and Time",
            "message": "send meeting invitation to team for sprint planning at 3:00 PM today",
            "expected_recipient": "team",
            "expected_title": "sprint planning",
            "expected_time": "3:00 PM"
        },
        {
            "name": "Email with About and Time",
            "message": "send invite to alice@company.com about code review at 11:00 AM tomorrow",
            "expected_recipient": "alice@company.com",
            "expected_title": "code review",
            "expected_time": "11:00 AM"
        },
        {
            "name": "Simple Format",
            "message": "send meeting invite to bob title team sync at 9:00 AM today",
            "expected_recipient": "bob",
            "expected_title": "team sync",
            "expected_time": "9:00 AM"
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. {test_case['name']}")
            print(f"   Message: {test_case['message']}")
            print(f"   Expected: {test_case['expected_recipient']} | {test_case['expected_title']} | {test_case['expected_time']}")
            
            try:
                async with session.post(
                    f"{base_url}/api/agent/chat",
                    json={"message": test_case['message']}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        response_text = data.get('response', '')
                        invite_details = data.get('invite_details', {})
                        
                        # Check if correct agent was selected
                        agent = data.get('agent', 'unknown')
                        if agent == 'CalendarAgent':
                            print(f"   ✅ Agent: {agent}")
                        else:
                            print(f"   ❌ Agent: {agent} (expected CalendarAgent)")
                        
                        # Check if correct intent was detected
                        intent = data.get('action_taken', 'unknown')
                        if intent == 'send_invite':
                            print(f"   ✅ Intent: {intent}")
                        else:
                            print(f"   ❌ Intent: {intent} (expected send_invite)")
                        
                        # Check extracted details
                        actual_recipient = invite_details.get('recipients', '')
                        actual_topic = invite_details.get('topic', '')
                        actual_time = invite_details.get('time', '')
                        
                        print(f"   📧 Recipient: {actual_recipient}")
                        print(f"   📝 Topic: {actual_topic}")
                        print(f"   ⏰ Time: {actual_time}")
                        
                        # Check if details match expectations
                        recipient_match = test_case['expected_recipient'].lower() in actual_recipient.lower()
                        title_match = test_case['expected_title'].lower() in actual_topic.lower()
                        time_match = test_case['expected_time'].lower() in actual_time.lower()
                        
                        if recipient_match:
                            print(f"   ✅ Recipient: Correct")
                        else:
                            print(f"   ❌ Recipient: Expected '{test_case['expected_recipient']}', got '{actual_recipient}'")
                        
                        if title_match:
                            print(f"   ✅ Title: Correct")
                        else:
                            print(f"   ❌ Title: Expected '{test_case['expected_title']}', got '{actual_topic}'")
                        
                        if time_match:
                            print(f"   ✅ Time: Correct")
                        else:
                            print(f"   ❌ Time: Expected '{test_case['expected_time']}', got '{actual_time}'")
                        
                        # Show first 150 chars of response
                        preview = response_text[:150] + "..." if len(response_text) > 150 else response_text
                        print(f"   Response: {preview}")
                        
                    else:
                        print(f"   ❌ HTTP {response.status}")
                        
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # Small delay between requests
            await asyncio.sleep(0.5)
    
    print(f"\n🎉 Meeting Invite Testing Complete!")
    print(f"   Tested {len(test_cases)} meeting invite scenarios")
    print(f"   Check the extracted details above for accuracy")

if __name__ == "__main__":
    asyncio.run(test_meeting_invite_fix()) 
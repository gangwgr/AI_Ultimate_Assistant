#!/usr/bin/env python3
"""
Focused test for specific intent detection fixes
"""

import asyncio
import aiohttp
import json

async def test_specific_fixes():
    """Test the specific intent detection fixes"""
    
    test_cases = [
        # These should now work correctly
        ("mark all mail as read", "mark_all_as_read"),
        ("summarise unread email 1", "summarize_unread_email"),
        ("Summarize the latest emails in my inbox", "summarize_latest_emails"),
        ("Find emails with the subject containing 'invoice'", "search_emails"),
        ("Do I have any meeting invites in my inbox?", "find_meeting_invites"),
        ("Find emails with Zoom/Google Meet links", "find_zoom_links"),
        ("Delete all promotional emails", "find_promotional_emails"),
    ]
    
    print("🧪 Testing Specific Intent Detection Fixes")
    print("=" * 50)
    
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
                        
                        print(f"   ✅ Actual intent: {actual_intent}")
                        
                        if actual_intent == expected_intent:
                            print(f"   ✅ CORRECT! Intent matched")
                        else:
                            print(f"   ❌ WRONG! Expected {expected_intent}, got {actual_intent}")
                        
                        # Check if response is meaningful
                        if "❌" in response_text or "Please specify" in response_text:
                            print(f"   ⚠️  Response needs improvement: {response_text[:50]}...")
                        else:
                            print(f"   ✅ Good response: {response_text[:50]}...")
                    else:
                        print(f"   ❌ HTTP {response.status}")
                        
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # Small delay between requests
            await asyncio.sleep(0.5)
    
    print("\n" + "=" * 50)
    print("🎉 Testing completed!")

if __name__ == "__main__":
    asyncio.run(test_specific_fixes()) 
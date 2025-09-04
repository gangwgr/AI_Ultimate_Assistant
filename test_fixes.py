#!/usr/bin/env python3
"""
Test fixes for attachments and email composition
"""

import asyncio
import aiohttp
import json

async def test_fixes():
    """Test the fixes for attachments and email composition"""
    
    test_cases = [
        ("Show emails with attachments from last week", "find_attachments"),
        ("Show emails with attachments of today", "find_attachments"),
        ("send a thank-you email to rgangwar@redhat.com for the interview", "send_email"),
        ("draft an email to john about the meeting tomorrow", "send_email"),
        ("reply to the latest email from bob and say i'm unavailable", "send_email"),
        ("follow up with team regarding the status of the report", "send_email"),
        ("send my availability for next week to client@example.com", "send_email"),
    ]
    
    print("🧪 Testing Fixes for Attachments and Email Composition")
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
    print("🎉 Testing completed!")

if __name__ == "__main__":
    asyncio.run(test_fixes()) 
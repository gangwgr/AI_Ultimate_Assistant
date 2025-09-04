#!/usr/bin/env python3
"""
Test script to verify email functionality fixes
"""

import asyncio
import aiohttp
import json

async def test_email_functionality():
    """Test various email functionality"""
    
    test_cases = [
        # Working cases
        "show my unread mails of today",
        "mark email 1 as read",
        "send a mail to rgangwar@redhat.com subject test body test",
        "summarise email 1",
        
        # Previously not working cases
        "Do I have any today emails from skundu@redhat.com?",
        "Do I have any emails from skundu@redhat.com?",
        "mark all mail as read",
        "summarise unread email 1",
        "Summarize the latest emails in my inbox",
        "Show emails with attachments from last week",
        "Show emails with attachments of today",
        
        # Advanced features
        "List my starred or important emails",
        "Find emails with the subject containing 'invoice'",
        "Do I have any meeting invites in my inbox?",
        "Find emails with Zoom/Google Meet links",
        "Delete all promotional emails",
    ]
    
    print("🧪 Testing Email Functionality Fixes")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. Testing: '{test_case}'")
            
            try:
                async with session.post(
                    "http://localhost:8000/api/agent/chat",
                    json={"message": test_case}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        intent = result.get("action_taken", "unknown")
                        response_text = result.get("response", "No response")
                        
                        print(f"   ✅ Intent: {intent}")
                        print(f"   📝 Response: {response_text[:100]}...")
                        
                        # Check if it's a proper response
                        if "❌" in response_text or "Please specify" in response_text:
                            print(f"   ⚠️  May need improvement")
                        else:
                            print(f"   ✅ Working properly")
                    else:
                        print(f"   ❌ HTTP {response.status}")
                        
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            # Small delay between requests
            await asyncio.sleep(0.5)
    
    print("\n" + "=" * 50)
    print("🎉 Testing completed!")

if __name__ == "__main__":
    asyncio.run(test_email_functionality()) 
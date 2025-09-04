#!/usr/bin/env python3
"""
Debug test for single case
"""

import asyncio
import aiohttp
import json

async def test_debug_single():
    """Test single case with debug output"""
    
    test_case = "mark all mail as read"
    expected_intent = "mark_all_as_read"
    
    print(f"🧪 Testing: '{test_case}'")
    print(f"Expected intent: {expected_intent}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                "http://localhost:8000/api/agent/chat",
                json={"message": test_case}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    actual_intent = result.get("action_taken", "unknown")
                    response_text = result.get("response", "No response")
                    
                    print(f"✅ Actual intent: {actual_intent}")
                    
                    if actual_intent == expected_intent:
                        print(f"✅ CORRECT! Intent matched")
                    else:
                        print(f"❌ WRONG! Expected {expected_intent}, got {actual_intent}")
                    
                    print(f"Response: {response_text[:100]}...")
                else:
                    print(f"❌ HTTP {response.status}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_debug_single()) 
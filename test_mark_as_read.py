#!/usr/bin/env python3
"""
Test script to verify mark as read functionality
"""
import asyncio
import aiohttp
import json

async def test_mark_as_read():
    """Test mark as read functionality"""
    print("🧪 Testing Mark as Read Functionality")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Clear cache
        print("\n🧹 Step 1: Clearing cache")
        print("-" * 30)
        try:
            response = await session.post("http://localhost:8000/api/gmail/debug/clear-cache")
            if response.status == 200:
                result = await response.json()
                print(f"✅ {result.get('message', 'Cache cleared')}")
            else:
                print(f"⚠️  Cache clear failed: {response.status}")
        except Exception as e:
            print(f"⚠️  Cache clear error: {e}")
        
        # Step 2: Check initial unread count
        print("\n📧 Step 2: Check initial unread count")
        print("-" * 30)
        response = await session.post(
            "http://localhost:8000/api/agent/chat",
            json={"message": "Show unread emails"}
        )
        if response.status == 200:
            result = await response.json()
            initial_count = result.get('unread_count', 0)
            print(f"📊 Initial unread count: {initial_count}")
            print(f"🤖 Response: {result.get('response', 'N/A')[:100]}...")
        else:
            print(f"❌ Error: {response.status}")
            return
        
        if initial_count == 0:
            print("✅ No unread emails to test with")
            return
        
        # Step 3: Mark email 1 as read
        print(f"\n📧 Step 3: Mark email 1 as read")
        print("-" * 30)
        response = await session.post(
            "http://localhost:8000/api/agent/chat",
            json={"message": "mark email 1 as read"}
        )
        if response.status == 200:
            result = await response.json()
            print(f"🤖 Response: {result.get('response', 'N/A')}")
            print(f"📋 Action: {result.get('action_taken', 'N/A')}")
        else:
            print(f"❌ Error: {response.status}")
            return
        
        # Step 4: Check unread count after marking as read
        print("\n📧 Step 4: Check unread count after marking as read")
        print("-" * 30)
        response = await session.post(
            "http://localhost:8000/api/agent/chat",
            json={"message": "Show unread emails"}
        )
        if response.status == 200:
            result = await response.json()
            final_count = result.get('unread_count', 0)
            print(f"📊 Final unread count: {final_count}")
            print(f"🤖 Response: {result.get('response', 'N/A')[:100]}...")
            
            # Check if count decreased
            if final_count < initial_count:
                print(f"✅ SUCCESS: Unread count decreased from {initial_count} to {final_count}")
            else:
                print(f"❌ FAILED: Unread count did not decrease (was {initial_count}, now {final_count})")
        else:
            print(f"❌ Error: {response.status}")
    
    print("\n✅ Mark as Read Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_mark_as_read()) 
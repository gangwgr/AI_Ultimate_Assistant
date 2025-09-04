#!/usr/bin/env python3
"""
Test script to check actual unread email status
"""
import asyncio
import aiohttp
import json

async def test_unread_status():
    """Test actual unread email status"""
    print("🔍 Testing Actual Unread Email Status")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Clear cache
        print("\n🧹 Step 1: Clearing cache")
        print("-" * 30)
        response = await session.post("http://localhost:8000/api/gmail/debug/clear-cache")
        if response.status == 200:
            result = await response.json()
            print(f"✅ {result.get('message', 'Cache cleared')}")
        else:
            print(f"❌ Error clearing cache: {response.status}")
        
        # Step 2: Check actual unread status
        print("\n📧 Step 2: Checking actual unread status")
        print("-" * 30)
        response = await session.get("http://localhost:8000/api/gmail/debug/unread-status")
        if response.status == 200:
            result = await response.json()
            actual_count = result.get('actual_unread_count', 0)
            unread_emails = result.get('unread_emails', [])
            
            print(f"📊 Actual unread count from Gmail API: {actual_count}")
            print(f"📋 Cache cleared: {result.get('cache_cleared', False)}")
            
            if unread_emails:
                print("\n📬 Actual unread emails:")
                for i, email in enumerate(unread_emails, 1):
                    print(f"  {i}. {email.get('sender', 'Unknown')}")
                    print(f"     Subject: {email.get('subject', 'No Subject')}")
                    print(f"     Date: {email.get('date', 'Unknown')}")
                    print(f"     Labels: {email.get('labels', [])}")
                    print()
            else:
                print("✅ No unread emails found")
        else:
            print(f"❌ Error checking unread status: {response.status}")
        
        # Step 3: Test the regular unread emails endpoint
        print("\n📧 Step 3: Testing regular unread emails endpoint")
        print("-" * 30)
        response = await session.post(
            "http://localhost:8000/api/agent/chat",
            json={"message": "Show unread emails"}
        )
        if response.status == 200:
            result = await response.json()
            print(f"🤖 Agent response: {result.get('response', 'N/A')[:200]}...")
            print(f"📊 Unread count reported: {result.get('unread_count', 'N/A')}")
        else:
            print(f"❌ Error: {response.status}")
    
    print("\n✅ Unread Status Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_unread_status()) 
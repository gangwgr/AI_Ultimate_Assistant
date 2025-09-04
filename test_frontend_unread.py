#!/usr/bin/env python3
"""
Test script to verify frontend unread email functionality
"""
import asyncio
import aiohttp
import json

async def test_frontend_unread():
    """Test frontend unread email functionality"""
    print("🧪 Testing Frontend Unread Email Functionality")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Test the main Gmail API endpoint
        print("\n📧 Step 1: Test main Gmail API endpoint")
        print("-" * 30)
        response = await session.get("http://localhost:8000/api/gmail/emails?query=is:unread in:inbox&max_results=20")
        if response.status == 200:
            emails = await response.json()
            print(f"📊 Main API - Unread count: {len(emails)}")
            for i, email in enumerate(emails, 1):
                print(f"  {i}. {email.get('sender', 'Unknown')} - {email.get('subject', 'No Subject')}")
        else:
            print(f"❌ Main API error: {response.status}")
        
        # Step 2: Test the notifications endpoint (old)
        print("\n📧 Step 2: Test notifications endpoint (old)")
        print("-" * 30)
        response = await session.get("http://localhost:8000/api/notifications/unread-emails")
        if response.status == 200:
            data = await response.json()
            print(f"📊 Notifications API - Unread count: {data.get('count', 0)}")
            emails = data.get('unread_emails', [])
            for i, email in enumerate(emails, 1):
                print(f"  {i}. {email.get('sender', 'Unknown')} - {email.get('subject', 'No Subject')}")
        else:
            print(f"❌ Notifications API error: {response.status}")
        
        # Step 3: Test the agent endpoint
        print("\n📧 Step 3: Test agent endpoint")
        print("-" * 30)
        response = await session.post(
            "http://localhost:8000/api/agent/chat",
            json={"message": "Show unread emails"}
        )
        if response.status == 200:
            result = await response.json()
            print(f"📊 Agent - Unread count: {result.get('unread_count', 'N/A')}")
            print(f"🤖 Response: {result.get('response', 'N/A')[:100]}...")
        else:
            print(f"❌ Agent error: {response.status}")
    
    print("\n✅ Frontend Unread Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_frontend_unread()) 
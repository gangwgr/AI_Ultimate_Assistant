#!/usr/bin/env python3
"""
Test script to debug cache issue
"""
import asyncio
import aiohttp
import json

async def test_cache_issue():
    """Test cache issue"""
    print("🧪 Testing Cache Issue")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Clear cache manually
        print("\n🧹 Step 1: Clear cache manually")
        print("-" * 30)
        try:
            from app.api.gmail import clear_email_cache, clear_gmail_service_cache
            clear_email_cache()
            clear_gmail_service_cache()
            print("✅ Cache cleared manually")
        except Exception as e:
            print(f"❌ Error clearing cache: {e}")
        
        # Step 2: Check unread emails
        print("\n📧 Step 2: Check unread emails")
        print("-" * 30)
        response = await session.get("http://localhost:8000/api/gmail/emails?query=is:unread in:inbox&max_results=20")
        if response.status == 200:
            emails = await response.json()
            print(f"📊 Unread count: {len(emails)}")
            for i, email in enumerate(emails, 1):
                print(f"  {i}. {email.get('sender', 'Unknown')} - {email.get('subject', 'No Subject')}")
        else:
            print(f"❌ Error: {response.status}")
        
        # Step 3: Mark email as read
        print("\n📧 Step 3: Mark email as read")
        print("-" * 30)
        if len(emails) > 0:
            email_id = emails[0]['id']
            response = await session.put(f"http://localhost:8000/api/gmail/emails/{email_id}/mark_read")
            if response.status == 200:
                result = await response.json()
                print(f"✅ {result.get('message', 'Email marked as read')}")
            else:
                print(f"❌ Error marking as read: {response.status}")
        
        # Step 4: Check unread emails again
        print("\n📧 Step 4: Check unread emails again")
        print("-" * 30)
        response = await session.get("http://localhost:8000/api/gmail/emails?query=is:unread in:inbox&max_results=20")
        if response.status == 200:
            emails = await response.json()
            print(f"📊 Unread count: {len(emails)}")
            for i, email in enumerate(emails, 1):
                print(f"  {i}. {email.get('sender', 'Unknown')} - {email.get('subject', 'No Subject')}")
        else:
            print(f"❌ Error: {response.status}")
    
    print("\n✅ Cache Issue Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_cache_issue()) 
#!/usr/bin/env python3
"""
Test script to simulate the real user scenario
"""

import asyncio
import aiohttp
import json

async def test_real_scenario():
    """Test the real user scenario"""
    print("🧪 Testing Real User Scenario")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Show unread emails
        print("\n📧 Step 1: Show unread emails")
        print("-" * 30)
        
        response = await session.post(
            "http://localhost:8000/api/agent/chat",
            json={"message": "Show unread emails"}
        )
        
        if response.status == 200:
            result = await response.json()
            print(f"Unread Count: {result.get('unread_count', 'N/A')}")
            print(f"Response Preview: {result.get('response', 'N/A')[:100]}...")
        else:
            print(f"❌ Error: {response.status}")
        
        # Step 2: Mark email 1 as read
        print("\n📧 Step 2: Mark email 1 as read")
        print("-" * 30)
        
        response = await session.post(
            "http://localhost:8000/api/agent/chat",
            json={"message": "mark email 1 as read"}
        )
        
        if response.status == 200:
            result = await response.json()
            print(f"Intent: {result.get('action_taken', 'N/A')}")
            print(f"Response: {result.get('response', 'N/A')}")
        else:
            print(f"❌ Error: {response.status}")
        
        # Step 3: Show unread emails again
        print("\n📧 Step 3: Show unread emails again")
        print("-" * 30)
        
        response = await session.post(
            "http://localhost:8000/api/agent/chat",
            json={"message": "Show unread emails"}
        )
        
        if response.status == 200:
            result = await response.json()
            print(f"Unread Count: {result.get('unread_count', 'N/A')}")
            print(f"Response Preview: {result.get('response', 'N/A')[:100]}...")
        else:
            print(f"❌ Error: {response.status}")
        
        # Step 4: Mark email 2 as read
        print("\n📧 Step 4: Mark email 2 as read")
        print("-" * 30)
        
        response = await session.post(
            "http://localhost:8000/api/agent/chat",
            json={"message": "mark email 2 as read"}
        )
        
        if response.status == 200:
            result = await response.json()
            print(f"Intent: {result.get('action_taken', 'N/A')}")
            print(f"Response: {result.get('response', 'N/A')}")
        else:
            print(f"❌ Error: {response.status}")
        
        # Step 5: Show unread emails one more time
        print("\n📧 Step 5: Show unread emails one more time")
        print("-" * 30)
        
        response = await session.post(
            "http://localhost:8000/api/agent/chat",
            json={"message": "Show unread emails"}
        )
        
        if response.status == 200:
            result = await response.json()
            print(f"Unread Count: {result.get('unread_count', 'N/A')}")
            print(f"Response Preview: {result.get('response', 'N/A')[:100]}...")
        else:
            print(f"❌ Error: {response.status}")
    
    print("\n✅ Real User Scenario Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_real_scenario()) 
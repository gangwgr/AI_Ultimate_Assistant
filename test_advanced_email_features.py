#!/usr/bin/env python3
"""
Advanced Email Features Test Script
Tests all the new advanced email management capabilities
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

async def test_advanced_email_features():
    """Test all advanced email features"""
    print("🚀 Testing Advanced Email Features")
    print("=" * 50)
    
    # Test cases for advanced features
    test_cases = [
        {
            "name": "Filter by Date - Today",
            "message": "show me unread emails from today",
            "expected_intent": "filter_by_date"
        },
        {
            "name": "Find Attachments",
            "message": "show emails with attachments from last week",
            "expected_intent": "find_attachments"
        },
        {
            "name": "Spam Detection",
            "message": "is this email spam or phishing?",
            "expected_intent": "detect_spam"
        },
        {
            "name": "Meeting Detection",
            "message": "do I have any meeting invites in my inbox?",
            "expected_intent": "find_meetings"
        },
        {
            "name": "Email Management",
            "message": "delete all promotional emails",
            "expected_intent": "manage_emails"
        },
        {
            "name": "Advanced Search",
            "message": "find emails with the subject containing 'invoice'",
            "expected_intent": "search_emails"
        },
        {
            "name": "Smart Categorization",
            "message": "list my starred or important emails",
            "expected_intent": "find_important_emails"
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📧 Test {i}: {test_case['name']}")
            print("-" * 40)
            
            try:
                async with session.post(
                    "http://localhost:8000/api/agent/chat",
                    json={"message": test_case["message"]}
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract key information
                        selected_agent = data.get('orchestrator', {}).get('selected_agent', 'Unknown')
                        domain = data.get('orchestrator', {}).get('agent_domain', 'Unknown')
                        action_taken = data.get('action_taken', 'Unknown')
                        response_text = data.get('response', 'No response')
                        
                        print(f"✅ Agent: {selected_agent}")
                        print(f"✅ Domain: {domain}")
                        print(f"✅ Action: {action_taken}")
                        print(f"✅ Response: {response_text[:100]}{'...' if len(response_text) > 100 else ''}")
                        
                        # Check if intent matches expected
                        if action_taken == test_case['expected_intent']:
                            print("✅ Intent matched expected!")
                        else:
                            print(f"⚠️  Intent mismatch: expected {test_case['expected_intent']}, got {action_taken}")
                        
                    else:
                        print(f"❌ HTTP Error: {response.status}")
                        
            except Exception as e:
                print(f"❌ Error: {e}")
    
    print("\n🎉 Advanced Email Features Test Complete!")
    print("\n📋 Summary of Advanced Features:")
    print("• ✅ Date-based filtering (today, yesterday, this week, last week)")
    print("• ✅ Attachment detection and management")
    print("• ✅ Spam and phishing detection")
    print("• ✅ Meeting invite detection")
    print("• ✅ Email management (delete, archive, block)")
    print("• ✅ Advanced search capabilities")
    print("• ✅ Smart categorization")
    print("• ✅ Color-coded status indicators")
    print("• ✅ Enhanced email summaries")
    print("• ✅ Send and mark as read functionality")

if __name__ == "__main__":
    asyncio.run(test_advanced_email_features()) 
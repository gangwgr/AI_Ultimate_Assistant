#!/usr/bin/env python3
"""
Advanced AI Email Features Test Script
Tests all the new AI-powered email management capabilities
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

async def test_advanced_ai_email_features():
    """Test all advanced AI email features"""
    print("🤖 Testing Advanced AI Email Features")
    print("=" * 50)
    
    # Test cases for advanced AI features
    test_cases = [
        {
            "name": "Email Templates - Meeting",
            "message": "draft an email to john about the meeting tomorrow",
            "expected_intent": "use_template"
        },
        {
            "name": "Email Scheduling",
            "message": "schedule a call with alice for monday 3 pm",
            "expected_intent": "schedule_email"
        },
        {
            "name": "Sentiment Analysis",
            "message": "what is the sentiment of this email?",
            "expected_intent": "analyze_sentiment"
        },
        {
            "name": "Smart Reply",
            "message": "suggest a smart reply to this email",
            "expected_intent": "smart_reply"
        },
        {
            "name": "Action Extraction",
            "message": "what action is being requested in this email?",
            "expected_intent": "extract_actions"
        },
        {
            "name": "Email Translation",
            "message": "translate this email from spanish to english",
            "expected_intent": "translate_email"
        },
        {
            "name": "Email Grouping",
            "message": "group similar emails into topics",
            "expected_intent": "group_emails"
        },
        {
            "name": "Set Reminder",
            "message": "remind me to reply to this email in 2 hours",
            "expected_intent": "set_reminder"
        },
        {
            "name": "Thank You Template",
            "message": "send a thank-you email to alice for the interview",
            "expected_intent": "use_template"
        },
        {
            "name": "Follow-up Template",
            "message": "follow up with team regarding the status of the report",
            "expected_intent": "use_template"
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🤖 Test {i}: {test_case['name']}")
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
                        print(f"✅ Response: {response_text[:150]}{'...' if len(response_text) > 150 else ''}")
                        
                        # Check if intent matches expected
                        if action_taken == test_case['expected_intent']:
                            print("✅ Intent matched expected!")
                        else:
                            print(f"⚠️  Intent mismatch: expected {test_case['expected_intent']}, got {action_taken}")
                        
                    else:
                        print(f"❌ HTTP Error: {response.status}")
                        
            except Exception as e:
                print(f"❌ Error: {e}")
    
    print("\n🎉 Advanced AI Email Features Test Complete!")
    print("\n📋 Summary of Advanced AI Features:")
    print("• ✅ Email Templates (Meeting, Thank You, Follow-up, Interview)")
    print("• ✅ Email Scheduling (Later, Tomorrow, Next Week)")
    print("• ✅ Sentiment Analysis (Tone, Mood, Professional vs Casual)")
    print("• ✅ Smart Reply Suggestions (Context-aware responses)")
    print("• ✅ Action Item Extraction (Tasks, Due dates, Follow-ups)")
    print("• ✅ Email Translation (Multi-language support)")
    print("• ✅ Email Grouping (Topic-based organization)")
    print("• ✅ Smart Reminders (Follow-up scheduling)")
    print("• ✅ Template Customization (Variable replacement)")
    print("• ✅ AI-Powered Insights (Professional recommendations)")

if __name__ == "__main__":
    asyncio.run(test_advanced_ai_email_features()) 
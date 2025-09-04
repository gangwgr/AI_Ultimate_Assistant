#!/usr/bin/env python3
"""
Test script for Jira summarize functionality
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'AI_Ultimate_Assistant'))
from app.services.jira_agent import JiraAgent

async def test_jira_summarize():
    """Test Jira summarize functionality"""
    agent = JiraAgent()
    
    # Test messages
    test_messages = [
        "Summarize the Jira issue OCPQE-30241",
        "What is Jira issue OCPQE-30241 about?",
        "Explain OCPQE-30241",
        "Tell me about OCPQE-30241"
    ]
    
    print("🔍 Testing Jira Summarize Functionality")
    print("=" * 60)
    
    for message in test_messages:
        print(f"\n📝 Testing message: '{message}'")
        
        # Analyze intent
        intent_result = await agent.analyze_intent(message)
        print(f"✅ Intent: {intent_result['intent']}")
        print(f"✅ Confidence: {intent_result['confidence']}")
        print(f"✅ Entities: {intent_result['entities']}")
        
        # Handle intent
        if intent_result['intent'] == 'summarize_jira_issue':
            response = await agent.handle_intent(
                intent_result['intent'], 
                message, 
                intent_result['entities']
            )
            print(f"✅ Response: {response['response'][:200]}...")
        else:
            print(f"❌ Wrong intent detected: {intent_result['intent']}")
    
    print("\n" + "=" * 60)
    print("🎯 Testing with actual Jira data")
    print("=" * 60)
    
    # Test with a specific issue
    message = "Summarize the Jira issue OCPQE-30241"
    intent_result = await agent.analyze_intent(message)
    
    if intent_result['intent'] == 'summarize_jira_issue':
        response = await agent.handle_intent(
            intent_result['intent'], 
            message, 
            intent_result['entities']
        )
        print(f"✅ Full Response:\n{response['response']}")
    else:
        print(f"❌ Intent detection failed: {intent_result['intent']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_jira_summarize())

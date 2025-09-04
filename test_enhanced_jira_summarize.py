#!/usr/bin/env python3
"""
Test script for enhanced Jira summarize and content analysis functionality
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'AI_Ultimate_Assistant'))
from app.services.jira_agent import JiraAgent

async def test_enhanced_jira_functionality():
    """Test enhanced Jira summarize and content analysis functionality"""
    agent = JiraAgent()
    
    # Test messages for different types of analysis
    test_messages = [
        "Summarize the Jira issue OCPQE-30241",
        "Summarise content of OCPQE-30241",
        "Content summary for OCPQE-30241",
        "Analyze content of OCPQE-30241",
        "What is Jira issue OCPQE-30241 about?"
    ]
    
    print("🔍 Testing Enhanced Jira Summarize and Content Analysis")
    print("=" * 70)
    
    for message in test_messages:
        print(f"\n📝 Testing message: '{message}'")
        
        # Analyze intent
        intent_result = await agent.analyze_intent(message)
        print(f"✅ Intent: {intent_result['intent']}")
        print(f"✅ Confidence: {intent_result['confidence']}")
        print(f"✅ Entities: {intent_result['entities']}")
        
        # Handle intent
        if intent_result['intent'] in ['summarize_jira_issue', 'analyze_jira_content']:
            response = await agent.handle_intent(
                intent_result['intent'], 
                message, 
                intent_result['entities']
            )
            print(f"✅ Response Type: {response['action_taken']}")
            print(f"✅ Response Preview: {response['response'][:300]}...")
        else:
            print(f"❌ Wrong intent detected: {intent_result['intent']}")
    
    print("\n" + "=" * 70)
    print("🎯 Testing Detailed Content Analysis")
    print("=" * 70)
    
    # Test with content analysis
    message = "Summarise content of OCPQE-30241"
    intent_result = await agent.analyze_intent(message)
    
    if intent_result['intent'] == 'analyze_jira_content':
        response = await agent.handle_intent(
            intent_result['intent'], 
            message, 
            intent_result['entities']
        )
        print(f"✅ Full Content Analysis Response:\n{response['response']}")
    else:
        print(f"❌ Content analysis intent detection failed: {intent_result['intent']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_enhanced_jira_functionality())

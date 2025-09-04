#!/usr/bin/env python3
"""
Test script for Must-Gather Agent functionality
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'AI_Ultimate_Assistant'))
from app.services.must_gather_agent import MustGatherAgent
from app.services.multi_agent_orchestrator import MultiAgentOrchestrator

async def test_must_gather_agent():
    """Test Must-Gather Agent functionality"""
    agent = MustGatherAgent()
    orchestrator = MultiAgentOrchestrator()
    
    # Test messages for different must-gather analysis types
    test_messages = [
        "Analyze must-gather path /path/to/must-gather",
        "Extract cluster info from must-gather",
        "Analyze pod logs in must-gather",
        "Analyze events from must-gather",
        "Analyze resources in must-gather",
        "Analyze network issues in must-gather",
        "Analyze storage problems in must-gather",
        "Analyze security issues in must-gather",
        "Analyze performance problems in must-gather",
        "Generate report from must-gather",
        "Compare must-gather captures",
        "What can you analyze in must-gather?"
    ]
    
    print("🔍 Testing Must-Gather Agent Functionality")
    print("=" * 70)
    
    for message in test_messages:
        print(f"\n📝 Testing message: '{message}'")
        
        # Test agent routing
        selected_agent, domain, confidence = orchestrator._select_agent(message)
        print(f"✅ Selected Agent: {selected_agent}")
        print(f"✅ Domain: {domain}")
        print(f"✅ Confidence: {confidence}")
        
        # Test intent analysis
        intent_result = await agent.analyze_intent(message)
        print(f"✅ Intent: {intent_result['intent']}")
        print(f"✅ Confidence: {intent_result['confidence']}")
        print(f"✅ Entities: {intent_result['entities']}")
        
        # Test intent handling
        if intent_result['intent'] != 'analyze_must_gather':
            response = await agent.handle_intent(
                intent_result['intent'], 
                message, 
                intent_result['entities']
            )
            print(f"✅ Response Type: {response['action_taken']}")
            print(f"✅ Response Preview: {response['response'][:200]}...")
        else:
            print(f"✅ General must-gather analysis intent detected")
    
    print("\n" + "=" * 70)
    print("🎯 Testing Multi-Agent Orchestrator Routing")
    print("=" * 70)
    
    # Test orchestrator routing
    routing_tests = [
        "Analyze must-gather path /tmp/must-gather-123",
        "Extract cluster info from must-gather logs",
        "Compare two must-gather captures",
        "Generate comprehensive report from must-gather"
    ]
    
    for message in routing_tests:
        print(f"\n📝 Testing routing: '{message}'")
        selected_agent, domain, confidence = orchestrator._select_agent(message)
        print(f"✅ Selected Agent: {selected_agent}")
        print(f"✅ Domain: {domain}")
        print(f"✅ Confidence: {confidence}")
        
        # Test with orchestrator
        response = await orchestrator.process_message(message)
        print(f"✅ Response Agent: {response.get('agent', 'Unknown')}")
        print(f"✅ Action Taken: {response.get('action_taken', 'Unknown')}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_must_gather_agent())

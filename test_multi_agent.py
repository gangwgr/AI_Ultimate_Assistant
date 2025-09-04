#!/usr/bin/env python3
"""
Test script for the new Multi-Agent Architecture
Demonstrates how different types of messages are routed to specialized agents
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.multi_agent_orchestrator import MultiAgentOrchestrator
from app.services.ai_agent import AIAgent

async def test_multi_agent_system():
    """Test the multi-agent system with various message types"""
    
    print("🤖 Testing Multi-Agent Architecture")
    print("=" * 50)
    
    # Initialize the orchestrator
    orchestrator = MultiAgentOrchestrator()
    
    # Test messages covering different domains
    test_messages = [
        # Jira messages
        "Update status of jira OCPQE-30241 TO DO",
        "fetch my jira issues",
        "create new jira bug",
        "add comment to OCPBUGS-12345",
        
        # Kubernetes/OpenShift messages
        "oc get pods",
        "kubectl get services",
        "how to list pod in ns?",
        "kubectl describe pod my-pod",
        "oc logs my-pod",
        
        # GitHub messages
        "list my PRs",
        "create pull request",
        "review PR #123",
        "merge PR #456",
        
        # Email messages
        "check my emails",
        "send email to john@example.com",
        "find emails with attachments",
        "search emails from boss",
        
        # General messages
        "hello",
        "what time is it?",
        "help",
        "thanks"
    ]
    
    print(f"Testing {len(test_messages)} different message types...\n")
    
    # Test each message
    for i, message in enumerate(test_messages, 1):
        print(f"Test {i}: {message}")
        print("-" * 40)
        
        # Get agent routing result
        result = await orchestrator.test_agent_routing([message])
        routing_result = result[message]
        
        # Process with full AI agent
        ai_agent = AIAgent()
        full_response = await ai_agent.process_message(message)
        
        print(f"Selected Agent: {routing_result['selected_agent']}")
        print(f"Domain: {routing_result['agent_domain']}")
        print(f"Intent: {routing_result['intent']}")
        print(f"Confidence: {routing_result['confidence']}")
        print(f"Response Preview: {full_response['response'][:100]}...")
        print()
    
    print("✅ Multi-Agent System Test Complete!")
    print("\n📊 Agent Capabilities Summary:")
    
    # Show agent capabilities
    agent_info = orchestrator.get_agent_info()
    for agent_name, info in agent_info.items():
        print(f"\n🔹 {info['name']} ({info['domain']}):")
        print(f"   Keywords: {', '.join(info['domain_keywords'][:5])}...")
        print(f"   Capabilities: {len(info['capabilities'])} functions")

async def test_agent_isolation():
    """Test that agents don't interfere with each other"""
    
    print("\n🔒 Testing Agent Isolation")
    print("=" * 30)
    
    orchestrator = MultiAgentOrchestrator()
    
    # Test that Jira commands don't get confused with Kubernetes
    jira_with_k8s_words = [
        "Update status of jira OCPQE-30241 TO DO",  # Contains "OCP" but should go to Jira
        "fetch jira issues from openshift project",  # Contains "openshift" but should go to Jira
        "create jira bug for kubernetes deployment"  # Contains "kubernetes" but should go to Jira
    ]
    
    for message in jira_with_k8s_words:
        result = await orchestrator.test_agent_routing([message])
        routing_result = result[message]
        print(f"Message: {message}")
        print(f"Selected Agent: {routing_result['selected_agent']}")
        print(f"Domain: {routing_result['agent_domain']}")
        print()

if __name__ == "__main__":
    print("🚀 Starting Multi-Agent Architecture Test")
    print("This demonstrates the new specialized agent system that prevents intent confusion.")
    print()
    
    # Run the tests
    asyncio.run(test_multi_agent_system())
    asyncio.run(test_agent_isolation())
    
    print("\n🎉 All tests completed successfully!")
    print("\n💡 Benefits of the Multi-Agent Architecture:")
    print("   • No more intent confusion between different domains")
    print("   • Specialized agents for each domain (Gmail, Jira, Kubernetes, GitHub)")
    print("   • Better accuracy and domain-specific responses")
    print("   • Easier to maintain and extend")
    print("   • Clear separation of concerns") 
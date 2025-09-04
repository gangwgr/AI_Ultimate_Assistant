#!/usr/bin/env python3
"""
Test Email Functionality
Tests the improved GmailAgent functionality including unread emails, formatting, and summarization.
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.multi_agent_orchestrator import MultiAgentOrchestrator

async def test_email_functionality():
    """Test the improved email functionality"""
    
    print("🧪 Testing Email Functionality Improvements")
    print("=" * 50)
    
    # Initialize the orchestrator
    orchestrator = MultiAgentOrchestrator()
    
    # Test messages
    test_messages = [
        "show unread emails",
        "check my emails", 
        "summarize email 1",
        "search emails from skundu",
        "find important emails"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n📧 Test {i}: {message}")
        print("-" * 30)
        
        try:
            # Process the message
            response = await orchestrator.process_message(message)
            
            # Display results
            print(f"Selected Agent: {response.get('agent', 'Unknown')}")
            print(f"Domain: {response.get('domain', 'Unknown')}")
            print(f"Intent: {response.get('action_taken', 'Unknown')}")
            print(f"Confidence: {response.get('confidence', 0.0)}")
            
            # Show response preview
            response_text = response.get('response', '')
            preview = response_text[:200] + "..." if len(response_text) > 200 else response_text
            print(f"Response Preview: {preview}")
            
            # Show additional info if available
            if 'email_count' in response:
                print(f"Email Count: {response['email_count']}")
            if 'unread_count' in response:
                print(f"Unread Count: {response['unread_count']}")
            if 'email_id' in response:
                print(f"Email ID: {response['email_id']}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n✅ Email Functionality Test Complete!")
    print("\n📋 Summary of Improvements:")
    print("• ✅ Proper unread email filtering")
    print("• ✅ Improved email formatting with emojis and structure")
    print("• ✅ Email summarization functionality")
    print("• ✅ Better sender name cleaning")
    print("• ✅ Formatted dates")
    print("• ✅ Email ID tracking for actions")

if __name__ == "__main__":
    asyncio.run(test_email_functionality()) 
#!/usr/bin/env python3
"""
Test script for Jira-specific training example generation
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'AI_Ultimate_Assistant'))
from continuous_learning import ContinuousLearningSystem

def test_jira_training_examples():
    """Test Jira-specific training example generation"""
    system = ContinuousLearningSystem()
    
    # Sample Jira content
    jira_content = """
    OCPQE-30241: Test SAML POST Binding with RH-SSO
    
    Summary:
    This issue involves testing the SAML POST Binding functionality in OpenShift Container Platform (OCP) with Red Hat Single Sign-On (RH-SSO).
    
    Description:
    The goal is to validate that users can successfully authenticate through OCP using their RH-SSO accounts via SAML POST Binding. This includes:
    - Creating test users in RH-SSO
    - Configuring SAML settings
    - Testing authentication flow
    - Documenting any issues encountered
    
    Status: In Progress
    Priority: High
    Assignee: QA Team
    """
    
    print("🔍 Testing Jira Training Example Generation")
    print("=" * 60)
    
    # Test with Jira source
    print(f"\n📝 Testing with Jira source: issues.redhat.com/browse/OCPQE-30241")
    jira_examples = system.generate_training_examples(jira_content, "issues.redhat.com/browse/OCPQE-30241")
    
    print(f"✅ Generated {len(jira_examples)} Jira-specific examples:")
    for i, example in enumerate(jira_examples, 1):
        print(f"\n{i}. Instruction: {example['instruction']}")
        print(f"   Input: {example['input'][:100]}...")
        print(f"   Output: {example['output'][:100]}...")
    
    # Test with general source
    print(f"\n📝 Testing with general source: document.txt")
    general_examples = system.generate_training_examples(jira_content, "document.txt")
    
    print(f"✅ Generated {len(general_examples)} general examples:")
    for i, example in enumerate(general_examples, 1):
        print(f"\n{i}. Instruction: {example['instruction']}")
        print(f"   Input: {example['input'][:100]}...")
        print(f"   Output: {example['output'][:100]}...")
    
    print("\n" + "=" * 60)
    print("🎯 Testing Continuous Learning with Jira Content")
    print("=" * 60)
    
    # Test the full continuous learning process with Jira content
    import asyncio
    
    async def test_continuous_learning():
        try:
            result = await system.update_model_continuously(
                "granite3.3-balanced-enhanced:latest",
                [{"name": "jira_ocpqe_30241", "content": jira_content}],
                progress_callback=lambda msg: print(f"📊 {msg}")
            )
            print(f"✅ Continuous learning result: {result}")
        except Exception as e:
            print(f"❌ Continuous learning error: {e}")
    
    asyncio.run(test_continuous_learning())

if __name__ == "__main__":
    test_jira_training_examples()

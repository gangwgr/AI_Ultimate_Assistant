#!/usr/bin/env python3
"""
Quick Test for Advanced Filtering
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.report_portal_agent import ReportPortalAgent

async def quick_filter_test():
    """Quick test of the filtering functionality without AI analysis."""
    
    print("🧪 **Quick Filter Test**")
    print("=" * 40)
    
    # Configuration
    rp_url = "https://reportportal-openshift.apps.dno.ocp-hub.prod.psi.redhat.com"
    rp_token = "rgangwar_jEwGN5nJSCu0ff5r1RJl0cgdL4mYfUiXKRsE7Si6wn9xHfOeE-eIAKRxyDSyGH7v"
    project = "PROW"
    ssl_verify = False
    
    try:
        # Initialize the agent
        print("🔧 **Initializing Report Portal Agent**")
        agent = ReportPortalAgent(rp_url, rp_token, project, ssl_verify)
        print("✅ Agent initialized successfully")
        print()
        
        # Test 1: Get available versions
        print("🔍 **Test 1: Discovering Available Versions**")
        versions = await agent.get_available_versions(hours_back=24)
        print(f"✅ Found {len(versions)} available versions:")
        for version in versions[:5]:  # Show first 5
            print(f"   - {version}")
        print()
        
        # Test 2: Get available components
        print("🔍 **Test 2: Discovering Available Components**")
        components = await agent.get_available_components(hours_back=24)
        print(f"✅ Found {len(components)} available components:")
        for component in components[:5]:  # Show first 5
            print(f"   - {component}")
        print()
        
        # Test 3: Get failed tests with filtering (without AI analysis)
        print("🎯 **Test 3: Filtering Tests (No AI Analysis)**")
        test_versions = ["4.19"]
        test_components = ["API_Server"]
        print(f"Testing filter for version: {test_versions}, component: {test_components}")
        
        # Get filtered tests without AI analysis
        filtered_tests = await agent._get_failed_tests(
            hours_back=24, 
            components=test_components, 
            versions=test_versions
        )
        print(f"✅ Found {len(filtered_tests)} filtered tests")
        
        if filtered_tests:
            print("📋 Sample filtered tests:")
            for i, test in enumerate(filtered_tests[:3]):  # Show first 3
                print(f"   {i+1}. {test.get('name', 'Unknown')}")
                print(f"      ID: {test.get('id')}")
                print(f"      Status: {test.get('status')}")
                print()
        
        print("🎉 **Quick Filter Test Completed!**")
        print("✅ Version discovery working")
        print("✅ Component discovery working")
        print("✅ Filtering working")
        
        return True
        
    except Exception as e:
        print(f"❌ **Test Failed: {e}**")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(quick_filter_test())

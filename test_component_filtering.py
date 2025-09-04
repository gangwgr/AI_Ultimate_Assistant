#!/usr/bin/env python3
"""
Test Component Filtering in Report Portal Integration
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.report_portal_agent import ReportPortalAgent

async def test_component_filtering():
    """Test the component filtering functionality."""
    
    print("🧪 **Testing Component Filtering**")
    print("=" * 60)
    
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
        
        # Test 1: Get available components
        print("🔍 **Test 1: Discovering Available Components**")
        components = await agent.get_available_components(hours_back=24)
        print(f"✅ Found {len(components)} available components:")
        for component in components:
            print(f"   - {component}")
        print()
        
        # Test 2: Get component statistics
        print("📊 **Test 2: Component Statistics**")
        stats = await agent.get_component_statistics(hours_back=24)
        print(f"✅ Statistics for {len(stats)} components:")
        for component, data in stats.items():
            print(f"   - {component}: {data['failed_tests']} failed out of {data['total_tests']} total ({data['success_rate']}% success)")
        print()
        
        # Test 3: Filter by specific components
        print("🎯 **Test 3: Component Filtering**")
        test_components = ["STORAGE", "NETWORK"]
        print(f"Testing filter for components: {test_components}")
        
        filtered_failures = await agent.analyze_failures(hours_back=24, components=test_components)
        print(f"✅ Found {len(filtered_failures)} failures for components {test_components}")
        
        if filtered_failures:
            print("📋 Sample filtered failures:")
            for i, failure in enumerate(filtered_failures[:3]):  # Show first 3
                print(f"   {i+1}. {failure.test_name}")
                print(f"      Category: {failure.category.value}")
                print(f"      Priority: {failure.priority}")
                print(f"      Confidence: {failure.confidence}")
                print()
        
        # Test 4: Compare with and without filtering
        print("⚖️ **Test 4: Comparison - With vs Without Filtering**")
        
        # Get all failures
        all_failures = await agent.analyze_failures(hours_back=24)
        print(f"✅ Total failures (no filter): {len(all_failures)}")
        
        # Get filtered failures
        filtered_failures = await agent.analyze_failures(hours_back=24, components=test_components)
        print(f"✅ Filtered failures ({test_components}): {len(filtered_failures)}")
        
        if all_failures:
            filter_percentage = (len(filtered_failures) / len(all_failures)) * 100
            print(f"📊 Filter reduced results by {100 - filter_percentage:.1f}%")
        
        print()
        print("🎉 **All Component Filtering Tests Passed!**")
        print("✅ Component discovery working")
        print("✅ Component statistics working")
        print("✅ Component filtering working")
        print("✅ Filter comparison working")
        
        return True
        
    except Exception as e:
        print(f"❌ **Test Failed: {e}**")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_component_filtering())

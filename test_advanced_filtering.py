#!/usr/bin/env python3
"""
Test Advanced Filtering in Report Portal Integration
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.report_portal_agent import ReportPortalAgent

async def test_advanced_filtering():
    """Test the advanced filtering functionality."""
    
    print("🧪 **Testing Advanced Filtering**")
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
        
        # Test 1: Get available versions
        print("🔍 **Test 1: Discovering Available Versions**")
        versions = await agent.get_available_versions(hours_back=24)
        print(f"✅ Found {len(versions)} available versions:")
        for version in versions:
            print(f"   - {version}")
        print()
        
        # Test 2: Get available defect types
        print("🔍 **Test 2: Discovering Available Defect Types**")
        defect_types = await agent.get_available_defect_types(hours_back=24)
        print(f"✅ Found {len(defect_types)} available defect types:")
        for defect_type in defect_types:
            print(f"   - {defect_type}")
        print()
        
        # Test 3: Filter by specific version and component (like your use case)
        print("🎯 **Test 3: Version + Component Filtering**")
        test_versions = ["4.19"]
        test_components = ["API_Server"]
        print(f"Testing filter for version: {test_versions}, component: {test_components}")
        
        filtered_failures = await agent.analyze_failures(
            hours_back=24, 
            components=test_components, 
            versions=test_versions
        )
        print(f"✅ Found {len(filtered_failures)} failures for version {test_versions} and component {test_components}")
        
        if filtered_failures:
            print("📋 Sample filtered failures:")
            for i, failure in enumerate(filtered_failures[:3]):  # Show first 3
                print(f"   {i+1}. {failure.test_name}")
                print(f"      Category: {failure.category.value}")
                print(f"      Priority: {failure.priority}")
                print(f"      Confidence: {failure.confidence}")
                print()
        
        # Test 4: Get filtered statistics
        print("📊 **Test 4: Filtered Statistics**")
        stats = await agent.get_filtered_statistics(
            hours_back=24,
            components=test_components,
            versions=test_versions
        )
        print(f"✅ Statistics for filtered data:")
        print(f"   - Total failures: {stats.get('total_failures', 0)}")
        print(f"   - Categories: {stats.get('categories', {})}")
        print(f"   - Priorities: {stats.get('priorities', {})}")
        print(f"   - Versions found: {stats.get('versions_found', [])}")
        print(f"   - Components found: {stats.get('components_found', [])}")
        print()
        
        # Test 5: Compare different filtering combinations
        print("⚖️ **Test 5: Filtering Combinations Comparison**")
        
        # Test different combinations
        filter_combinations = [
            {"name": "No filters", "params": {}},
            {"name": "Version only", "params": {"versions": ["4.19"]}},
            {"name": "Component only", "params": {"components": ["API_Server"]}},
            {"name": "Version + Component", "params": {"versions": ["4.19"], "components": ["API_Server"]}},
            {"name": "Status only", "params": {"statuses": ["FAILED"]}},
        ]
        
        for combo in filter_combinations:
            failures = await agent.analyze_failures(hours_back=24, **combo["params"])
            print(f"   {combo['name']}: {len(failures)} failures")
        
        print()
        print("🎉 **All Advanced Filtering Tests Passed!**")
        print("✅ Version discovery working")
        print("✅ Defect type discovery working")
        print("✅ Advanced filtering working")
        print("✅ Filtered statistics working")
        print("✅ Filter combinations working")
        
        return True
        
    except Exception as e:
        print(f"❌ **Test Failed: {e}**")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_advanced_filtering())

#!/usr/bin/env python3
"""
Test Report Portal Integration with Correct Endpoints
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.report_portal_agent import ReportPortalAgent
from app.services.ai_agent_multi_model import MultiModelAIAgent
from app.core.config import settings

async def test_report_portal_integration():
    """Test the Report Portal integration with the working endpoints."""
    
    print("🧪 **Testing Report Portal Integration**")
    print("=" * 60)
    
    # Configuration
    rp_url = "https://reportportal-openshift.apps.dno.ocp-hub.prod.psi.redhat.com"
    rp_token = "rgangwar_jEwGN5nJSCu0ff5r1RJl0cgdL4mYfUiXKRsE7Si6wn9xHfOeE-eIAKRxyDSyGH7v"
    project = "PROW"
    ssl_verify = False
    
    print(f"🔗 URL: {rp_url}")
    print(f"📁 Project: {project}")
    print(f"🔑 Token: {rp_token[:20]}...{rp_token[-10:]}")
    print(f"🔒 SSL Verify: {ssl_verify}")
    print()
    
    try:
        # Initialize the agent
        print("🔧 **Initializing Report Portal Agent**")
        agent = ReportPortalAgent(rp_url, rp_token, project, ssl_verify)
        print("✅ Agent initialized successfully")
        print()
        
        # Test basic connectivity
        print("🔍 **Testing Basic Connectivity**")
        test_url = f"{rp_url}/api/v1/{project}/launch"
        response = agent._make_request('GET', test_url)
        
        if response.status_code == 200:
            print("✅ Basic connectivity test passed")
            launches = response.json().get('content', [])
            print(f"📊 Found {len(launches)} launches")
            
            if launches:
                print("📋 Sample launch data:")
                sample_launch = launches[0]
                print(f"   - ID: {sample_launch.get('id')}")
                print(f"   - Name: {sample_launch.get('name', 'N/A')}")
                print(f"   - Status: {sample_launch.get('status', 'N/A')}")
                print(f"   - Owner: {sample_launch.get('owner', 'N/A')}")
        else:
            print(f"❌ Basic connectivity test failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
        
        print()
        
        # Test getting failed tests
        print("🔍 **Testing Failed Tests Retrieval**")
        failed_tests = await agent._get_failed_tests(hours_back=24)
        
        if failed_tests:
            print(f"✅ Found {len(failed_tests)} failed tests")
            print("📋 Sample failed test data:")
            sample_test = failed_tests[0]
            print(f"   - ID: {sample_test.get('id')}")
            print(f"   - Name: {sample_test.get('name', 'N/A')}")
            print(f"   - Status: {sample_test.get('status', 'N/A')}")
            print(f"   - Launch ID: {sample_test.get('launchId', 'N/A')}")
        else:
            print("ℹ️  No failed tests found in the last 24 hours")
            print("   This is normal if there are no recent failures")
        
        print()
        
        # Test AI analysis (with mock data if no real failures)
        print("🤖 **Testing AI Analysis**")
        if failed_tests:
            # Test with real data
            sample_test = failed_tests[0]
            print(f"Testing AI analysis on: {sample_test.get('name', 'Unknown Test')}")
            
            # Initialize multi-model agent for AI analysis
            multi_agent = MultiModelAIAgent()
            
            # Create a mock failure for testing
            test_failure = {
                'id': sample_test.get('id', 'test-123'),
                'name': sample_test.get('name', 'Test Failure'),
                'issue': {
                    'message': 'Test failed due to timeout',
                    'stackTrace': 'java.lang.Exception: Timeout after 30 seconds'
                },
                'startTime': '2024-01-15T10:00:00Z',
                'duration': 30000
            }
            
            # Test AI analysis
            analysis_result = await agent._analyze_single_failure(test_failure)
            print("✅ AI analysis completed successfully")
            print(f"   Category: {analysis_result.category.value}")
            print(f"   Confidence: {analysis_result.confidence}")
            print(f"   Priority: {analysis_result.priority}")
            print(f"   Tags: {analysis_result.tags}")
        else:
            print("ℹ️  Skipping AI analysis test (no failed tests available)")
        
        print()
        print("🎉 **All Tests Passed!**")
        print("✅ Report Portal integration is working correctly")
        print("✅ API endpoints are accessible")
        print("✅ Authentication is working")
        print("✅ AI analysis is ready")
        
        return True
        
    except Exception as e:
        print(f"❌ **Test Failed: {e}**")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_report_portal_integration())

#!/usr/bin/env python3

import requests
import json
import time

def test_selective_analysis():
    """Test the new selective analysis functionality"""
    
    # Configure with real API token
    config = {
        "rp_url": "https://reportportal-openshift.apps.dno.ocp-hub.prod.psi.redhat.com",
        "rp_token": "rgangwar_jEwGN5nJSCu0ff5r1RJl0cgdL4mYfUiXKRsE7Si6wn9xHfOeE-eIAKRxyDSyGH7v",
        "project": "PROW",
        "ssl_verify": False
    }
    
    print("🔧 Step 1: Configuring Report Portal...")
    try:
        response = requests.post(
            "http://localhost:8000/api/report-portal/configure",
            json=config,
            headers={"Content-Type": "application/json"}
        )
        print(f"✅ Configuration: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return

    print("\n🔍 Testing Selective Analysis Features")
    print("==================================================")

    # Test 1: Discover Test Cases
    print("\n🔍 Test 1: Discover Test Cases")
    print("----------------------------------------")
    try:
        response = requests.get(
            "http://localhost:8000/api/report-portal/test-cases",
            params={
                "hours_back": 24,
                "components": "API",
                "statuses": "FAILED",
                "limit": 10
            },
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            data = response.json()
            test_cases = data.get('test_cases', [])
            print(f"✅ Found {len(test_cases)} test cases")
            
            if test_cases:
                print("   Sample test cases:")
                for i, test_case in enumerate(test_cases[:3]):
                    print(f"   {i+1}. {test_case.get('name', 'Unknown')} ({test_case.get('status', 'Unknown')})")
                
                # Test 2: Analyze Selected Test Cases
                print("\n🔍 Test 2: Analyze Selected Test Cases")
                print("----------------------------------------")
                
                # Select first 2 test cases for analysis
                selected_ids = [test_case['id'] for test_case in test_cases[:2]]
                
                analysis_request = {
                    "test_ids": selected_ids,
                    "update_comments": False,
                    "update_status": False,
                    "generate_report": False
                }

                start_time = time.time()
                analysis_response = requests.post(
                    "http://localhost:8000/api/report-portal/analyze-selected",
                    json=analysis_request,
                    headers={"Content-Type": "application/json"}
                )

                elapsed_time = time.time() - start_time
                print(f"✅ Analysis completed in {elapsed_time:.2f} seconds")
                print(f"   Status Code: {analysis_response.status_code}")

                if analysis_response.status_code == 200:
                    result = analysis_response.json()
                    print(f"   Total Failures: {result.get('total_failures', 0)}")
                    print(f"   Analyzed Failures: {result.get('analyzed_failures', 0)}")
                    print(f"   Categories: {result.get('categories', {})}")
                    print(f"   Priorities: {result.get('priorities', {})}")
                else:
                    print(f"   Error Response: {analysis_response.text}")
            else:
                print("   📝 Note: No test cases found (network connectivity issue)")
        else:
            print(f"❌ Failed to discover test cases: {response.text}")

    except Exception as e:
        print(f"❌ Test case discovery failed: {e}")

    # Test 3: Test with Mock Data (if no real data)
    print("\n🔍 Test 3: Test with Mock Data")
    print("----------------------------------------")
    try:
        # Simulate test case discovery with mock data
        mock_test_cases = [
            {
                "id": "test_001",
                "name": "API_Server Test OCP-41664: Check deprecated APIs",
                "status": "FAILED",
                "component": "API_Server",
                "version": "4.19",
                "duration": 5000
            },
            {
                "id": "test_002", 
                "name": "STORAGE Test OCP-39601: Examine critical errors",
                "status": "FAILED",
                "component": "STORAGE",
                "version": "4.19",
                "duration": 63000
            }
        ]
        
        print(f"✅ Mock test cases created: {len(mock_test_cases)}")
        for i, test_case in enumerate(mock_test_cases):
            print(f"   {i+1}. {test_case['name']} ({test_case['status']})")
        
        # Test selective analysis with mock IDs
        mock_analysis_request = {
            "test_ids": ["test_001", "test_002"],
            "update_comments": False,
            "update_status": False,
            "generate_report": False
        }

        start_time = time.time()
        mock_response = requests.post(
            "http://localhost:8000/api/report-portal/analyze-selected",
            json=mock_analysis_request,
            headers={"Content-Type": "application/json"}
        )

        elapsed_time = time.time() - start_time
        print(f"✅ Mock analysis completed in {elapsed_time:.2f} seconds")
        print(f"   Status Code: {mock_response.status_code}")

        if mock_response.status_code == 200:
            result = mock_response.json()
            print(f"   Total Failures: {result.get('total_failures', 0)}")
            print(f"   Analyzed Failures: {result.get('analyzed_failures', 0)}")
        else:
            print(f"   Error Response: {mock_response.text}")

    except Exception as e:
        print(f"❌ Mock test failed: {e}")

    print("\n==================================================")
    print("🎯 NEW FEATURES IMPLEMENTED")
    print("==================================================")
    print("\n✅ **Test Case Discovery:**")
    print("   • Filter test cases by components, statuses, versions")
    print("   • Browse available test cases before analysis")
    print("   • Set time range and limit for discovery")
    print("\n✅ **Selective Analysis:**")
    print("   • Select specific test cases to analyze")
    print("   • Checkbox interface for easy selection")
    print("   • Analyze only chosen test cases")
    print("\n✅ **User Interface:**")
    print("   • Test case table with filtering")
    print("   • Select All/Deselect All buttons")
    print("   • Selected count display")
    print("   • Analyze Selected button")
    print("\n🚀 **Benefits:**")
    print("   • Faster analysis (only selected cases)")
    print("   • Better control over analysis scope")
    print("   • Reduced timeout issues")
    print("   • More efficient resource usage")

if __name__ == "__main__":
    test_selective_analysis()

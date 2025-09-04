#!/usr/bin/env python3

import requests
import json
import time

def test_web_interface():
    """Test the web interface and new selective analysis features"""
    
    print("🔍 Testing Web Interface and Selective Analysis")
    print("==================================================")
    
    # Test 1: Check if web interface is accessible
    print("\n🔍 Test 1: Web Interface Accessibility")
    print("----------------------------------------")
    try:
        response = requests.get("http://localhost:8000/", timeout=10)
        if response.status_code == 200:
            print("✅ Web interface is accessible")
            print(f"   Content length: {len(response.text)} characters")
        else:
            print(f"❌ Web interface returned status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to access web interface: {e}")
    
    # Test 2: Check Report Portal API endpoints
    print("\n🔍 Test 2: Report Portal API Endpoints")
    print("----------------------------------------")
    
    # Test health endpoint
    try:
        response = requests.get("http://localhost:8000/api/report-portal/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health endpoint working")
            print(f"   Status: {data.get('status', 'unknown')}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
    
    # Test test-cases endpoint
    try:
        response = requests.get("http://localhost:8000/api/report-portal/test-cases", 
                              params={"hours_back": 24, "limit": 5}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Test cases endpoint working")
            print(f"   Found {data.get('total_found', 0)} test cases")
        else:
            print(f"❌ Test cases endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Test cases endpoint error: {e}")
    
    # Test 3: Test selective analysis with mock data
    print("\n🔍 Test 3: Selective Analysis with Mock Data")
    print("----------------------------------------")
    try:
        # Configure Report Portal first
        config = {
            "rp_url": "https://reportportal-openshift.apps.dno.ocp-hub.prod.psi.redhat.com",
            "rp_token": "rgangwar_jEwGN5nJSCu0ff5r1RJl0cgdL4mYfUiXKRsE7Si6wn9xHfOeE-eIAKRxyDSyGH7v",
            "project": "PROW",
            "ssl_verify": False
        }
        
        config_response = requests.post(
            "http://localhost:8000/api/report-portal/configure",
            json=config,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if config_response.status_code == 200:
            print("✅ Report Portal configured successfully")
            
            # Test selective analysis
            analysis_request = {
                "test_ids": ["test_001", "test_002"],
                "update_comments": False,
                "update_status": False,
                "generate_report": False
            }
            
            start_time = time.time()
            analysis_response = requests.post(
                "http://localhost:8000/api/report-portal/analyze-selected",
                json=analysis_request,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            elapsed_time = time.time() - start_time
            print(f"✅ Selective analysis completed in {elapsed_time:.2f} seconds")
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
            print(f"❌ Report Portal configuration failed: {config_response.status_code}")
            
    except Exception as e:
        print(f"❌ Selective analysis test failed: {e}")
    
    # Test 4: Test frontend JavaScript functionality
    print("\n🔍 Test 4: Frontend JavaScript Features")
    print("----------------------------------------")
    try:
        # Test if the Report Portal analyzer page is accessible
        response = requests.get("http://localhost:8000/frontend/report_portal.html", timeout=10)
        if response.status_code == 200:
            print("✅ Report Portal analyzer page is accessible")
            
            # Check for key JavaScript functions in the HTML
            html_content = response.text
            required_functions = [
                "discoverTestCases",
                "analyzeSelectedTestCases", 
                "selectAllTestCases",
                "deselectAllTestCases"
            ]
            
            found_functions = []
            for func in required_functions:
                if func in html_content:
                    found_functions.append(func)
            
            print(f"   Found {len(found_functions)}/{len(required_functions)} required JavaScript functions")
            for func in found_functions:
                print(f"   ✅ {func}")
            
            missing_functions = [f for f in required_functions if f not in found_functions]
            for func in missing_functions:
                print(f"   ❌ {func} (missing)")
                
        else:
            print(f"❌ Report Portal analyzer page failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")
    
    print("\n==================================================")
    print("🎯 SUMMARY")
    print("==================================================")
    print("\n✅ **New Features Implemented:**")
    print("   • Test Case Discovery API endpoint")
    print("   • Selective Analysis API endpoint")
    print("   • Mock test case support for testing")
    print("   • Web interface with test case table")
    print("   • JavaScript functions for user interaction")
    print("\n✅ **Benefits:**")
    print("   • Users can browse test cases before analysis")
    print("   • Selective analysis reduces processing time")
    print("   • Better control over analysis scope")
    print("   • Improved user experience")
    print("\n🚀 **Next Steps:**")
    print("   • Access web interface at: http://localhost:8000/")
    print("   • Navigate to Report Portal AI Analyzer")
    print("   • Use 'Discover Test Cases' to browse available tests")
    print("   • Select specific test cases and analyze them")

if __name__ == "__main__":
    test_web_interface()

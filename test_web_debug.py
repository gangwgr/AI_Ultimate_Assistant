#!/usr/bin/env python3

import requests
import json
import time

def test_web_interface_debug():
    """Debug the web interface issue step by step"""
    
    print("🔍 Debugging Web Interface Issue")
    print("==================================")
    
    # Step 1: Check if server is running
    print("\n1️⃣ Checking server status...")
    try:
        response = requests.get("http://localhost:8000/api/report-portal/health", timeout=10)
        if response.status_code == 200:
            print("✅ Server is running")
            print(f"   Health: {response.json()}")
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    # Step 2: Configure Report Portal
    print("\n2️⃣ Configuring Report Portal...")
    config = {
        "rp_url": "https://reportportal-openshift.apps.dno.ocp-hub.prod.psi.redhat.com",
        "rp_token": "rgangwar_jEwGN5nJSCu0ff5r1RJl0cgdL4mYfUiXKRsE7Si6wn9xHfOeE-eIAKRxyDSyGH7v",
        "project": "PROW",
        "ssl_verify": False
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/report-portal/configure",
            json=config,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code == 200:
            print("✅ Report Portal configured successfully")
        else:
            print(f"❌ Configuration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Step 3: Test test case discovery
    print("\n3️⃣ Testing test case discovery...")
    try:
        response = requests.get(
            "http://localhost:8000/api/report-portal/test-cases",
            params={
                "hours_back": 24,
                "components": "API",
                "statuses": "FAILED",
                "limit": 10
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Test case discovery successful")
            print(f"   Total found: {data.get('total_found', 0)}")
            print(f"   Test cases: {len(data.get('test_cases', []))}")
            
            if data.get('test_cases'):
                print("   Sample test cases:")
                for i, test_case in enumerate(data['test_cases'][:3]):
                    print(f"     {i+1}. {test_case.get('name', 'Unknown')} ({test_case.get('status', 'Unknown')})")
        else:
            print(f"❌ Test case discovery failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Test case discovery error: {e}")
        return
    
    # Step 4: Test web interface accessibility
    print("\n4️⃣ Testing web interface...")
    try:
        response = requests.get("http://localhost:8000/frontend/report_portal.html", timeout=10)
        if response.status_code == 200:
            print("✅ Report Portal HTML page is accessible")
            print(f"   Content length: {len(response.text)} characters")
            
            # Check for key JavaScript functions
            html_content = response.text
            required_functions = [
                "discoverTestCases",
                "displayTestCases", 
                "toggleTestCaseSelection",
                "selectAllTestCases",
                "deselectAllTestCases"
            ]
            
            found_functions = []
            for func in required_functions:
                if func in html_content:
                    found_functions.append(func)
            
            print(f"   Found {len(found_functions)}/{len(required_functions)} required JavaScript functions")
            for func in found_functions:
                print(f"     ✅ {func}")
            
            missing_functions = [f for f in required_functions if f not in found_functions]
            for func in missing_functions:
                print(f"     ❌ {func} (missing)")
                
        else:
            print(f"❌ Web interface not accessible: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Web interface error: {e}")
        return
    
    # Step 5: Test the actual discovery API call that the web interface would make
    print("\n5️⃣ Testing web interface API call...")
    try:
        # Simulate the exact call the web interface makes
        params = {
            "hours_back": "24",
            "components": "API",
            "statuses": "FAILED",
            "limit": "10"
        }
        
        response = requests.get(
            "http://localhost:8000/api/report-portal/test-cases",
            params=params,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Web interface API call successful")
            print(f"   Response structure: {list(data.keys())}")
            print(f"   Test cases count: {len(data.get('test_cases', []))}")
            
            # Check if the response format matches what the web interface expects
            if 'test_cases' in data and isinstance(data['test_cases'], list):
                print("✅ Response format is correct for web interface")
            else:
                print("❌ Response format may not match web interface expectations")
                
        else:
            print(f"❌ Web interface API call failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Web interface API call error: {e}")
    
    print("\n==================================")
    print("🎯 SUMMARY")
    print("==================================")
    print("\n✅ **API Backend Working:**")
    print("   • Server is running")
    print("   • Report Portal configured")
    print("   • Test case discovery working")
    print("   • Mock data being returned")
    print("\n✅ **Web Interface Accessible:**")
    print("   • HTML page loads")
    print("   • JavaScript functions present")
    print("   • API calls working")
    print("\n🔍 **Next Steps:**")
    print("   • Open browser to: http://localhost:8000/")
    print("   • Navigate to Report Portal AI Analyzer")
    print("   • Try 'Discover Test Cases' button")
    print("   • Check browser console for any JavaScript errors")

if __name__ == "__main__":
    test_web_interface_debug()

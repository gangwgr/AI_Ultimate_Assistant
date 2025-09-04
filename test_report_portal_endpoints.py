#!/usr/bin/env python3
"""
Comprehensive Report Portal API Endpoint Tester
Tests various API endpoints to find the correct ones for this Report Portal instance.
"""

import requests
import urllib3
import json
from typing import Dict, Any

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_endpoint(url: str, headers: Dict[str, str], description: str) -> Dict[str, Any]:
    """Test a specific endpoint and return results."""
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        return {
            "description": description,
            "url": url,
            "status_code": response.status_code,
            "success": 200 <= response.status_code < 300,
            "response": response.text[:500] if response.text else "No response body",
            "headers": dict(response.headers)
        }
    except Exception as e:
        return {
            "description": description,
            "url": url,
            "status_code": None,
            "success": False,
            "response": f"Error: {str(e)}",
            "headers": {}
        }

def main():
    print("🔍 **Report Portal API Endpoint Discovery**")
    print("=" * 60)
    
    # Configuration
    base_url = "https://reportportal-openshift.apps.dno.ocp-hub.prod.psi.redhat.com"
    project = "PROW"
    token = "rgangwar_jEwGN5nJSCu0ff5r1RJl0cgdL4mYfUiXKRsE7Si6wn9xHfOeE-eIAKRxyDSyGH7v"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"🔗 Base URL: {base_url}")
    print(f"📁 Project: {project}")
    print(f"🔑 Token: {token[:20]}...{token[-10:]}")
    print()
    
    # Test different API endpoint patterns
    endpoints_to_test = [
        # Standard Report Portal v1 API endpoints
        f"{base_url}/api/v1/{project}/user",
        f"{base_url}/api/v1/{project}/launch",
        f"{base_url}/api/v1/{project}/testitem",
        f"{base_url}/api/v1/{project}/dashboard",
        
        # Alternative API versions
        f"{base_url}/api/v2/{project}/user",
        f"{base_url}/api/v2/{project}/launch",
        
        # Different project name variations
        f"{base_url}/api/v1/prow/user",
        f"{base_url}/api/v1/PROW/user",
        f"{base_url}/api/v1/prow/user",
        
        # Root API endpoints
        f"{base_url}/api/v1/user",
        f"{base_url}/api/v1/launch",
        f"{base_url}/api/v1/testitem",
        
        # Health check endpoints
        f"{base_url}/api/v1/health",
        f"{base_url}/health",
        f"{base_url}/api/health",
        
        # Info endpoints
        f"{base_url}/api/v1/info",
        f"{base_url}/api/info",
        f"{base_url}/info",
    ]
    
    print("🧪 **Testing API Endpoints**")
    print("=" * 60)
    
    successful_endpoints = []
    
    for endpoint in endpoints_to_test:
        result = test_endpoint(endpoint, headers, f"Testing {endpoint}")
        
        status_icon = "✅" if result["success"] else "❌"
        print(f"{status_icon} {result['description']}")
        print(f"   Status: {result['status_code']}")
        print(f"   Response: {result['response'][:100]}...")
        print()
        
        if result["success"]:
            successful_endpoints.append(result)
    
    print("📊 **Summary**")
    print("=" * 60)
    
    if successful_endpoints:
        print(f"✅ Found {len(successful_endpoints)} working endpoints:")
        for endpoint in successful_endpoints:
            print(f"   - {endpoint['url']}")
            print(f"     Status: {endpoint['status_code']}")
            print(f"     Response: {endpoint['response'][:200]}...")
            print()
    else:
        print("❌ No working endpoints found.")
        print()
        print("🔧 **Troubleshooting Suggestions:**")
        print("1. Check if the API token is valid and not expired")
        print("2. Verify the project name is correct")
        print("3. Check if this Report Portal instance uses a different API structure")
        print("4. Contact the Report Portal administrator for API documentation")
        print("5. Try accessing the Report Portal UI to verify your access")
    
    # Test without authentication to see if it's an auth issue
    print("\n🔍 **Testing without authentication**")
    print("=" * 60)
    
    no_auth_headers = {"Content-Type": "application/json"}
    no_auth_result = test_endpoint(f"{base_url}/api/v1/{project}/user", no_auth_headers, "Testing without auth")
    
    print(f"{'✅' if no_auth_result['success'] else '❌'} No Auth Test")
    print(f"   Status: {no_auth_result['status_code']}")
    print(f"   Response: {no_auth_result['response'][:200]}...")
    
    if no_auth_result['status_code'] == 401:
        print("   ✅ Authentication is required (expected)")
    elif no_auth_result['success']:
        print("   ⚠️  Endpoint works without auth (unexpected)")
    else:
        print("   ❌ Endpoint not found or other error")

if __name__ == "__main__":
    main()

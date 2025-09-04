#!/usr/bin/env python3
"""
Test script to debug Report Portal connection issues
"""

import requests
import json
from datetime import datetime

def test_report_portal_connection():
    """Test connection to Report Portal with different authentication methods"""
    
    # Your Report Portal details
    rp_url = "https://reportportal-openshift.apps.dno.ocp-hub.prod.psi.redhat.com"
    username = "your_username"  # You'll need to provide this
    password = "Akus@@24061992"
    project = "PROW"
    
    print("🔍 **Report Portal Connection Test**")
    print("=" * 50)
    print(f"URL: {rp_url}")
    print(f"Project: {project}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    print()
    
    # Test 1: Basic connection test
    print("📡 **Test 1: Basic Connection**")
    try:
        response = requests.get(f"{rp_url}/api/v1", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        print("✅ Basic connection successful")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    # Test 2: Authentication test
    print("\n🔐 **Test 2: Authentication**")
    try:
        # Try basic auth
        auth_response = requests.get(
            f"{rp_url}/api/v1/{project}/user",
            auth=(username, password),
            timeout=10
        )
        print(f"Status Code: {auth_response.status_code}")
        print(f"Response: {auth_response.text[:200]}...")
        
        if auth_response.status_code == 200:
            print("✅ Authentication successful")
        elif auth_response.status_code == 401:
            print("❌ Authentication failed - check username/password")
        elif auth_response.status_code == 403:
            print("❌ Access forbidden - check permissions")
        else:
            print(f"⚠️ Unexpected status: {auth_response.status_code}")
            
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
    
    # Test 3: Project access test
    print("\n📁 **Test 3: Project Access**")
    try:
        project_response = requests.get(
            f"{rp_url}/api/v1/{project}/launch",
            auth=(username, password),
            timeout=10
        )
        print(f"Status Code: {project_response.status_code}")
        print(f"Response: {project_response.text[:200]}...")
        
        if project_response.status_code == 200:
            print("✅ Project access successful")
        elif project_response.status_code == 404:
            print("❌ Project not found - check project name")
        elif project_response.status_code == 403:
            print("❌ No access to project - check permissions")
        else:
            print(f"⚠️ Unexpected status: {project_response.status_code}")
            
    except Exception as e:
        print(f"❌ Project access test failed: {e}")
    
    # Test 4: API token test (if available)
    print("\n🎫 **Test 4: API Token Test**")
    print("Note: You may need to generate an API token from Report Portal UI")
    print("Look for 'API Tokens' or 'Personal Access Tokens' in your RP settings")
    
    # Test 5: Common issues and solutions
    print("\n🔧 **Common Issues & Solutions**")
    print("=" * 40)
    
    print("1. **Authentication Issues:**")
    print("   • Check if username is correct (not email)")
    print("   • Verify password is correct")
    print("   • Try generating an API token instead of password")
    print("   • Check if account is active and not locked")
    
    print("\n2. **Network Issues:**")
    print("   • Verify you can access the URL in browser")
    print("   • Check if VPN is required for internal Red Hat network")
    print("   • Try from different network if possible")
    
    print("\n3. **Project Issues:**")
    print("   • Verify project name 'PROW' is correct")
    print("   • Check if you have access to this project")
    print("   • Ask admin to add you to the project")
    
    print("\n4. **Red Hat Specific:**")
    print("   • This appears to be a Red Hat internal instance")
    print("   • May require Red Hat SSO authentication")
    print("   • Check if you need to use Red Hat SSO instead of direct auth")
    
    print("\n5. **API Token Generation:**")
    print("   • Log into Report Portal UI")
    print("   • Go to User Settings/Profile")
    print("   • Look for 'API Tokens' or 'Personal Access Tokens'")
    print("   • Generate a new token with appropriate permissions")
    
    return True

def test_with_api_token():
    """Test with API token if available"""
    print("\n🎫 **API Token Test**")
    print("If you have an API token, test it here:")
    
    rp_url = "https://reportportal-openshift.apps.dno.ocp-hub.prod.psi.redhat.com"
    project = "PROW"
    
    # You would replace this with your actual API token
    api_token = input("Enter your API token (or press Enter to skip): ").strip()
    
    if not api_token:
        print("Skipping API token test")
        return
    
    try:
        headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f"{rp_url}/api/v1/{project}/user",
            headers=headers,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("✅ API token authentication successful")
        else:
            print(f"❌ API token authentication failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ API token test failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting Report Portal Connection Tests")
    print("=" * 50)
    
    # Get username
    username = input("Enter your Report Portal username: ").strip()
    
    if not username:
        print("❌ Username is required")
        exit(1)
    
    # Update the test function with username
    import sys
    import types
    
    # Create a new function with the username
    def test_with_username():
        rp_url = "https://reportportal-openshift.apps.dno.ocp-hub.prod.psi.redhat.com"
        username_input = username
        password = "Akus@@24061992"
        project = "PROW"
        
        print("🔍 **Report Portal Connection Test**")
        print("=" * 50)
        print(f"URL: {rp_url}")
        print(f"Project: {project}")
        print(f"Username: {username_input}")
        print(f"Password: {'*' * len(password)}")
        print()
        
        # Test basic connection
        print("📡 **Test 1: Basic Connection**")
        try:
            response = requests.get(f"{rp_url}/api/v1", timeout=10)
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                print("✅ Basic connection successful")
            else:
                print(f"⚠️ Unexpected status: {response.status_code}")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
        
        # Test authentication
        print("\n🔐 **Test 2: Authentication**")
        try:
            auth_response = requests.get(
                f"{rp_url}/api/v1/{project}/user",
                auth=(username_input, password),
                timeout=10
            )
            print(f"Status Code: {auth_response.status_code}")
            print(f"Response: {auth_response.text[:200]}...")
            
            if auth_response.status_code == 200:
                print("✅ Authentication successful")
            elif auth_response.status_code == 401:
                print("❌ Authentication failed - check username/password")
            elif auth_response.status_code == 403:
                print("❌ Access forbidden - check permissions")
            else:
                print(f"⚠️ Unexpected status: {auth_response.status_code}")
                
        except Exception as e:
            print(f"❌ Authentication test failed: {e}")
        
        # Test project access
        print("\n📁 **Test 3: Project Access**")
        try:
            project_response = requests.get(
                f"{rp_url}/api/v1/{project}/launch",
                auth=(username_input, password),
                timeout=10
            )
            print(f"Status Code: {project_response.status_code}")
            print(f"Response: {project_response.text[:200]}...")
            
            if project_response.status_code == 200:
                print("✅ Project access successful")
            elif project_response.status_code == 404:
                print("❌ Project not found - check project name")
            elif project_response.status_code == 403:
                print("❌ No access to project - check permissions")
            else:
                print(f"⚠️ Unexpected status: {project_response.status_code}")
                
        except Exception as e:
            print(f"❌ Project access test failed: {e}")
        
        return True
    
    # Run the test
    test_with_username()
    
    # Offer API token test
    test_with_api_token()
    
    print("\n" + "=" * 50)
    print("🎯 **Next Steps:**")
    print("1. If authentication failed, check your username/password")
    print("2. If project access failed, verify project name and permissions")
    print("3. Try generating an API token from Report Portal UI")
    print("4. Check if Red Hat SSO authentication is required")
    print("5. Contact your Report Portal administrator for help")

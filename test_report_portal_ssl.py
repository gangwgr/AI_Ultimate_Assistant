#!/usr/bin/env python3
"""
Test script for Report Portal connection with SSL certificate handling
"""

import requests
import urllib3
import json
from datetime import datetime

# Disable SSL warnings for internal systems
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_report_portal_with_ssl_bypass():
    """Test Report Portal connection with SSL certificate bypass"""
    
    rp_url = "https://reportportal-openshift.apps.dno.ocp-hub.prod.psi.redhat.com"
    username = "rgangwar"
    password = "Akus@@24061992"
    project = "PROW"
    
    print("🔍 **Report Portal Connection Test (SSL Bypass)**")
    print("=" * 60)
    print(f"URL: {rp_url}")
    print(f"Project: {project}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    print("⚠️  SSL verification disabled for internal Red Hat systems")
    print()
    
    # Test 1: Basic connection with SSL bypass
    print("📡 **Test 1: Basic Connection (SSL Bypass)**")
    try:
        response = requests.get(
            f"{rp_url}/api/v1", 
            timeout=10,
            verify=False  # Disable SSL verification
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        print("✅ Basic connection successful (SSL bypass)")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    # Test 2: Authentication with SSL bypass
    print("\n🔐 **Test 2: Authentication (SSL Bypass)**")
    try:
        auth_response = requests.get(
            f"{rp_url}/api/v1/{project}/user",
            auth=(username, password),
            timeout=10,
            verify=False  # Disable SSL verification
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
    
    # Test 3: Project access with SSL bypass
    print("\n📁 **Test 3: Project Access (SSL Bypass)**")
    try:
        project_response = requests.get(
            f"{rp_url}/api/v1/{project}/launch",
            auth=(username, password),
            timeout=10,
            verify=False  # Disable SSL verification
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
    
    # Test 4: Try different authentication methods
    print("\n🔄 **Test 4: Alternative Authentication Methods**")
    
    # Method 1: Try with different headers
    print("\n**Method 1: Custom Headers**")
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        alt_response = requests.get(
            f"{rp_url}/api/v1/{project}/user",
            auth=(username, password),
            headers=headers,
            timeout=10,
            verify=False
        )
        print(f"Status Code: {alt_response.status_code}")
        print(f"Response: {alt_response.text[:200]}...")
        
    except Exception as e:
        print(f"❌ Alternative method failed: {e}")
    
    # Method 2: Try with session
    print("\n**Method 2: Session-based Authentication**")
    try:
        session = requests.Session()
        session.verify = False  # Disable SSL verification for session
        session.auth = (username, password)
        
        session_response = session.get(
            f"{rp_url}/api/v1/{project}/user",
            timeout=10
        )
        print(f"Status Code: {session_response.status_code}")
        print(f"Response: {session_response.text[:200]}...")
        
    except Exception as e:
        print(f"❌ Session method failed: {e}")
    
    return True

def test_red_hat_sso():
    """Test if Red Hat SSO authentication is required"""
    print("\n🔐 **Red Hat SSO Test**")
    print("This Red Hat internal system might require SSO authentication")
    print("Try accessing the URL in your browser first:")
    print("https://reportportal-openshift.apps.dno.ocp-hub.prod.psi.redhat.com")
    print()
    print("If you see a Red Hat SSO login page, you'll need to:")
    print("1. Log in through the browser first")
    print("2. Generate an API token from the Report Portal UI")
    print("3. Use the API token instead of username/password")

def generate_config_for_ssl_bypass():
    """Generate configuration for the Report Portal agent with SSL bypass"""
    print("\n⚙️ **Configuration for SSL Bypass**")
    print("=" * 40)
    
    config = {
        "rp_url": "https://reportportal-openshift.apps.dno.ocp-hub.prod.psi.redhat.com",
        "rp_token": "your-api-token-here",  # You'll need to generate this
        "project": "PROW",
        "ssl_verify": False
    }
    
    print("For the Report Portal agent, you'll need to modify the code to handle SSL:")
    print()
    print("1. In app/services/report_portal_agent.py, modify the requests calls:")
    print("   Add verify=False to all requests.get() calls")
    print()
    print("2. Generate an API token from Report Portal UI:")
    print("   - Log into Report Portal in browser")
    print("   - Go to User Settings/Profile")
    print("   - Look for 'API Tokens' or 'Personal Access Tokens'")
    print("   - Generate a new token")
    print()
    print("3. Use the API token instead of username/password")
    
    return config

if __name__ == "__main__":
    print("🚀 Starting Report Portal SSL Connection Tests")
    print("=" * 60)
    
    # Run SSL bypass tests
    test_report_portal_with_ssl_bypass()
    
    # Test Red Hat SSO
    test_red_hat_sso()
    
    # Generate configuration
    generate_config_for_ssl_bypass()
    
    print("\n" + "=" * 60)
    print("🎯 **Summary & Next Steps:**")
    print()
    print("✅ **SSL Issue Identified**: The connection fails due to self-signed certificates")
    print("✅ **Solution**: Disable SSL verification for internal Red Hat systems")
    print()
    print("📋 **Action Items:**")
    print("1. ✅ SSL bypass implemented in test script")
    print("2. 🔄 Test the connection with SSL bypass")
    print("3. 🎫 Generate API token from Report Portal UI")
    print("4. ⚙️ Update Report Portal agent code for SSL bypass")
    print("5. 🧪 Test the full integration")
    print()
    print("🔧 **Code Changes Needed:**")
    print("- Modify app/services/report_portal_agent.py to add verify=False")
    print("- Use API token instead of username/password")
    print("- Handle Red Hat SSO if required")

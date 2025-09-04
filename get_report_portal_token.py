#!/usr/bin/env python3
"""
Script to help you get API token from Report Portal
"""

import requests
import urllib3

# Disable SSL warnings for internal systems
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_connection_with_token():
    """Test connection with API token"""
    
    rp_url = "https://reportportal-openshift.apps.dno.ocp-hub.prod.psi.redhat.com"
    project = "PROW"
    
    print("🔍 **Report Portal API Token Test**")
    print("=" * 50)
    print(f"URL: {rp_url}")
    print(f"Project: {project}")
    print()
    
    # Get API token from user
    api_token = input("Enter your Report Portal API token: ").strip()
    
    if not api_token:
        print("❌ API token is required")
        return False
    
    print(f"Token: {'*' * (len(api_token) - 4)}{api_token[-4:]}")
    print()
    
    # Test connection with API token
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Test user endpoint
        print("📡 **Test 1: User Authentication**")
        response = requests.get(
            f"{rp_url}/api/v1/{project}/user",
            headers=headers,
            verify=False,  # Disable SSL verification for Red Hat internal
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("✅ API token authentication successful")
        else:
            print(f"❌ API token authentication failed: {response.status_code}")
            return False
        
        # Test project access
        print("\n📁 **Test 2: Project Access**")
        project_response = requests.get(
            f"{rp_url}/api/v1/{project}/launch",
            headers=headers,
            verify=False,
            timeout=10
        )
        print(f"Status Code: {project_response.status_code}")
        print(f"Response: {project_response.text[:200]}...")
        
        if project_response.status_code == 200:
            print("✅ Project access successful")
        else:
            print(f"❌ Project access failed: {project_response.status_code}")
            return False
        
        print("\n✅ **Connection successful!**")
        print("You can now use this API token in the Report Portal integration.")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def get_setup_instructions():
    """Print setup instructions"""
    
    print("📋 **How to Get API Token from Report Portal**")
    print("=" * 50)
    print()
    print("1. **Open Report Portal in Browser**")
    print("   URL: https://reportportal-openshift.apps.dno.ocp-hub.prod.psi.redhat.com")
    print("   Log in with your Red Hat credentials")
    print()
    print("2. **Navigate to User Settings**")
    print("   - Click on your username/profile in the top right")
    print("   - Look for 'Settings', 'Profile', or 'API Tokens'")
    print()
    print("3. **Generate API Token**")
    print("   - Find 'API Tokens' or 'Personal Access Tokens' section")
    print("   - Click 'Generate New Token' or 'Create Token'")
    print("   - Give it a name like 'AI Analyzer'")
    print("   - Select appropriate permissions (read/write)")
    print()
    print("4. **Copy the Token**")
    print("   - Copy the generated token immediately")
    print("   - Store it securely (you won't see it again)")
    print()
    print("5. **Test the Token**")
    print("   - Run this script again with your token")
    print()
    print("⚠️  **Important Notes:**")
    print("   - API tokens are sensitive - keep them secure")
    print("   - Tokens may expire - check Report Portal settings")
    print("   - Use API tokens instead of username/password")
    print("   - Set ssl_verify=False for Red Hat internal systems")

def main():
    """Main function"""
    
    print("🚀 **Report Portal API Token Setup**")
    print("=" * 50)
    print()
    
    # Show setup instructions
    get_setup_instructions()
    
    print("\n" + "=" * 50)
    print("🎯 **Ready to Test?**")
    print()
    
    # Ask if user wants to test
    test_now = input("Do you have an API token to test? (y/n): ").strip().lower()
    
    if test_now == 'y':
        success = test_connection_with_token()
        
        if success:
            print("\n✅ **Setup Complete!**")
            print("You can now configure the Report Portal integration with:")
            print("- URL: https://reportportal-openshift.apps.dno.ocp-hub.prod.psi.redhat.com")
            print("- Project: PROW")
            print("- API Token: [your token]")
            print("- SSL Verify: False")
        else:
            print("\n❌ **Setup Failed**")
            print("Please check your API token and try again.")
    else:
        print("\n📝 **Next Steps:**")
        print("1. Follow the instructions above to get your API token")
        print("2. Run this script again to test the token")
        print("3. Configure the Report Portal integration")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Simple Jira authentication test for Red Hat Issues
"""
import json
import requests
import base64
from requests.auth import HTTPBasicAuth
import getpass

def test_basic_auth():
    """Test different authentication methods"""
    
    print("🔧 Red Hat Jira Authentication Test")
    print("=" * 50)
    
    # Load existing config
    try:
        with open('jira_config.json', 'r') as f:
            config = json.load(f)
        
        server = config['server']
        username = config['username'] 
        token = config['token']
        
        print(f"Server: {server}")
        print(f"Username: {username}")
        print(f"Token (first 10 chars): {token[:10]}...")
        print()
        
    except FileNotFoundError:
        print("❌ jira_config.json not found")
        return
    
    # Test 1: Current config
    print("🔧 Test 1: Current configuration")
    print("-" * 30)
    
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    auth = HTTPBasicAuth(username, token)
    
    try:
        response = requests.get(f"{server}/rest/api/2/myself", auth=auth, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Success! Logged in as: {user_data.get('displayName', 'Unknown')}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print()
    
    # Test 2: Check if we need to authenticate differently
    print("🔧 Test 2: Check authentication requirements")
    print("-" * 30)
    
    try:
        # Test without authentication to see what's required
        response = requests.get(f"{server}/rest/api/2/myself", timeout=10)
        print(f"No-auth status: {response.status_code}")
        
        if response.status_code == 401:
            auth_header = response.headers.get('www-authenticate', '')
            print(f"Auth methods suggested: {auth_header}")
            
            if 'oauth' in auth_header.lower():
                print("⚠️  OAuth may be required instead of basic auth")
            
    except Exception as e:
        print(f"Exception in auth check: {e}")
    
    print()
    
    # Test 3: Manual input for verification
    print("🔧 Test 3: Manual verification")
    print("-" * 30)
    print("Let's try with fresh credentials...")
    
    try:
        new_username = input(f"Username (current: {username}): ").strip() or username
        new_token = getpass.getpass("API Token (leave blank to use existing): ").strip() or token
        
        auth = HTTPBasicAuth(new_username, new_token)
        response = requests.get(f"{server}/rest/api/2/myself", auth=auth, headers=headers, timeout=10)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Success! Logged in as: {user_data.get('displayName', 'Unknown')}")
            
            # Update config if different
            if new_username != username or new_token != token:
                config['username'] = new_username
                config['token'] = new_token
                
                with open('jira_config.json', 'w') as f:
                    json.dump(config, f, indent=2)
                print("✅ Updated jira_config.json with working credentials")
                
            return True
        else:
            print(f"❌ Still failed: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except KeyboardInterrupt:
        print("\nCancelled by user")
    except Exception as e:
        print(f"Exception: {e}")
    
    print()
    print("💡 Suggestions:")
    print("1. Check if your API token is still valid")
    print("2. For Red Hat Jira, you might need to generate a new Personal Access Token")
    print("3. Visit: https://issues.redhat.com/secure/ViewProfile.jspa")
    print("4. Go to 'Personal Access Tokens' and create a new one")
    print("5. Make sure you have the right permissions")
    
    return False

if __name__ == "__main__":
    test_basic_auth() 
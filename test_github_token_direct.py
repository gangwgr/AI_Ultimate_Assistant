#!/usr/bin/env python3
"""
Direct GitHub token test to check actual permissions
"""

import asyncio
import aiohttp
import json
import os
from app.services.secure_config import secure_config

async def test_github_token_direct():
    """Test GitHub token directly with GitHub API"""
    
    print("🔍 Direct GitHub Token Test")
    print("=" * 60)
    
    # Get token from secure config
    token = secure_config.get_github_token()
    if not token:
        print("❌ No GitHub token found in secure config")
        return
    
    print(f"Token: {token[:10]}...{token[-4:]}")
    print()
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AI-Ultimate-Assistant/1.0"
    }
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Get user info directly
        print("🔐 Test 1: Direct User Info")
        print("-" * 40)
        try:
            async with session.get("https://api.github.com/user", headers=headers) as response:
                print(f"Status: {response.status}")
                print(f"Headers: {dict(response.headers)}")
                
                if response.status == 200:
                    user_data = await response.json()
                    print(f"✅ User: {user_data.get('login', 'Unknown')}")
                    print(f"   Name: {user_data.get('name', 'Unknown')}")
                    
                    # Check scopes from headers
                    scopes = response.headers.get('X-OAuth-Scopes', '')
                    print(f"   Scopes: {scopes}")
                    
                    if scopes:
                        scope_list = [s.strip() for s in scopes.split(',')]
                        print(f"   Scope list: {scope_list}")
                        
                        required_scopes = ['repo', 'public_repo', 'pull_request', 'issues']
                        missing = [s for s in required_scopes if s not in scope_list]
                        
                        if missing:
                            print(f"   ⚠️  Missing scopes: {missing}")
                        else:
                            print(f"   ✅ All required scopes present")
                    else:
                        print(f"   ⚠️  No scopes detected in headers")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ Error: {error_text}")
                    
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        # Test 2: Test repository access
        print("\n📚 Test 2: Repository Access")
        print("-" * 40)
        try:
            async with session.get("https://api.github.com/user/repos", headers=headers) as response:
                print(f"Status: {response.status}")
                
                if response.status == 200:
                    repos = await response.json()
                    print(f"✅ Repository access successful")
                    print(f"   Found {len(repos)} repositories")
                    if repos:
                        print(f"   Sample: {repos[0].get('full_name', 'N/A')}")
                else:
                    error_text = await response.text()
                    print(f"❌ Repository access failed: {error_text}")
                    
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        # Test 3: Test specific repository access (replace with your repo)
        print("\n🔍 Test 3: Specific Repository Access")
        print("-" * 40)
        
        # You can replace these with your actual repository details
        test_owner = "gangwgr"  # Your username
        test_repo = "test-repo"  # Replace with actual repo name
        
        try:
            async with session.get(f"https://api.github.com/repos/{test_owner}/{test_repo}", headers=headers) as response:
                print(f"Testing: {test_owner}/{test_repo}")
                print(f"Status: {response.status}")
                
                if response.status == 200:
                    repo_data = await response.json()
                    print(f"✅ Repository access successful")
                    print(f"   Name: {repo_data.get('full_name', 'N/A')}")
                    print(f"   Private: {repo_data.get('private', 'N/A')}")
                    print(f"   Permissions: {repo_data.get('permissions', {})}")
                elif response.status == 404:
                    print(f"⚠️  Repository not found (404) - this is normal if repo doesn't exist")
                else:
                    error_text = await response.text()
                    print(f"❌ Repository access failed: {error_text}")
                    
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        # Test 4: Test issue/PR commenting permissions
        print("\n💬 Test 4: Issue/PR Commenting Permissions")
        print("-" * 40)
        
        # Test with a public repository that likely exists
        test_owner = "octocat"
        test_repo = "Hello-World"
        
        try:
            # First check if we can access the repo
            async with session.get(f"https://api.github.com/repos/{test_owner}/{test_repo}", headers=headers) as response:
                if response.status == 200:
                    print(f"✅ Can access {test_owner}/{test_repo}")
                    
                    # Try to get issues to test permissions
                    async with session.get(f"https://api.github.com/repos/{test_owner}/{test_repo}/issues", headers=headers) as response:
                        print(f"Issues access status: {response.status}")
                        
                        if response.status == 200:
                            print(f"✅ Can access issues")
                        elif response.status == 403:
                            print(f"❌ No permission to access issues")
                        else:
                            error_text = await response.text()
                            print(f"⚠️  Issues access: {error_text}")
                else:
                    print(f"⚠️  Cannot access {test_owner}/{test_repo}")
                    
        except Exception as e:
            print(f"❌ Test failed: {e}")

def check_token_in_secure_config():
    """Check token in secure config"""
    print("\n🔧 Secure Config Check")
    print("=" * 60)
    
    try:
        token = secure_config.get_github_token()
        if token:
            print(f"✅ Token found in secure config")
            print(f"   Length: {len(token)}")
            print(f"   Preview: {token[:10]}...{token[-4:]}")
            
            # Check token format
            if token.startswith('ghp_'):
                print(f"   Format: GitHub Personal Access Token (classic)")
            elif token.startswith('github_pat_'):
                print(f"   Format: GitHub Personal Access Token (fine-grained)")
            elif len(token) == 40:
                print(f"   Format: Legacy token (40 characters)")
            else:
                print(f"   Format: Unknown")
        else:
            print(f"❌ No token found in secure config")
            
    except Exception as e:
        print(f"❌ Error checking secure config: {e}")

if __name__ == "__main__":
    print("🚀 Direct GitHub Token Test")
    print("=" * 60)
    
    check_token_in_secure_config()
    
    asyncio.run(test_github_token_direct())
    
    print("\n" + "=" * 60)
    print("💡 Analysis:")
    print("• If scopes are missing, your token needs more permissions")
    print("• If scopes are present but PR commenting fails, it's a different issue")
    print("• Try the PR reviewer UI: http://127.0.0.1:8000/frontend/pr_reviewer.html")

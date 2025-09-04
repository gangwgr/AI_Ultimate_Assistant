#!/usr/bin/env python3
"""
Detailed GitHub PR reviewer issue diagnostic
"""

import asyncio
import aiohttp
import json
import os

async def debug_github_issues():
    """Debug GitHub PR reviewer issues"""
    
    print("🔍 Detailed GitHub PR Reviewer Debug")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8000"
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Check GitHub user info in detail
        print("\n🔐 Test 1: GitHub User Authentication")
        print("-" * 40)
        try:
            async with session.get(f"{base_url}/api/github/user") as response:
                print(f"Status: {response.status}")
                print(f"Headers: {dict(response.headers)}")
                
                if response.status == 200:
                    user_info = await response.json()
                    print(f"✅ User info received:")
                    print(f"   Raw response: {json.dumps(user_info, indent=2)}")
                    
                    # Check if user has proper permissions
                    if user_info.get('login'):
                        print(f"   ✅ User login: {user_info['login']}")
                    else:
                        print(f"   ❌ No user login found - token may have insufficient permissions")
                    
                    # Check token scopes
                    scopes = response.headers.get('X-OAuth-Scopes', '')
                    print(f"   Token scopes: {scopes}")
                    
                    required_scopes = ['repo', 'public_repo', 'pull_request']
                    missing_scopes = [scope for scope in required_scopes if scope not in scopes]
                    if missing_scopes:
                        print(f"   ⚠️  Missing scopes: {missing_scopes}")
                    else:
                        print(f"   ✅ All required scopes present")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ Authentication failed: {error_text}")
                    
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        # Test 2: Check if we can list repositories
        print("\n📚 Test 2: Repository Access")
        print("-" * 40)
        try:
            async with session.get(f"{base_url}/api/github/repos") as response:
                print(f"Status: {response.status}")
                
                if response.status == 200:
                    repos = await response.json()
                    print(f"✅ Repository access successful")
                    print(f"   Found {len(repos)} repositories")
                    if repos:
                        print(f"   Sample repo: {repos[0].get('full_name', 'N/A')}")
                else:
                    error_text = await response.text()
                    print(f"❌ Repository access failed: {error_text}")
                    
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        # Test 3: Test comment posting with detailed error handling
        print("\n💬 Test 3: Comment Posting (with detailed error)")
        print("-" * 40)
        
        # You can replace these with actual values for testing
        test_owner = "test-owner"  # Replace with actual owner
        test_repo = "test-repo"    # Replace with actual repo
        test_pr = 1               # Replace with actual PR number
        
        if test_owner == "test-owner":
            print("⏭️  Skipping - please update with real PR details")
        else:
            try:
                # Test simple comment first
                payload = {
                    "owner": test_owner,
                    "repo": test_repo,
                    "pr_number": test_pr,
                    "comment_body": "🤖 Test comment from AI Ultimate Assistant - " + str(asyncio.get_event_loop().time())
                }
                
                print(f"Testing comment on: {test_owner}/{test_repo}#{test_pr}")
                
                async with session.post(
                    f"{base_url}/api/github/repos/{test_owner}/{test_repo}/pulls/{test_pr}/comment",
                    json=payload
                ) as response:
                    print(f"Status: {response.status}")
                    print(f"Headers: {dict(response.headers)}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print("✅ Comment posted successfully!")
                        print(f"   Response: {json.dumps(result, indent=2)}")
                    else:
                        error_text = await response.text()
                        print(f"❌ Comment posting failed: {error_text}")
                        
                        # Parse error details
                        try:
                            error_json = json.loads(error_text)
                            if 'message' in error_json:
                                print(f"   GitHub error: {error_json['message']}")
                            if 'documentation_url' in error_json:
                                print(f"   Documentation: {error_json['documentation_url']}")
                        except:
                            pass
                            
            except Exception as e:
                print(f"❌ Test failed: {e}")
        
        # Test 4: Check GitHub API rate limits
        print("\n⏱️  Test 4: Rate Limit Check")
        print("-" * 40)
        try:
            async with session.get(f"{base_url}/api/github/user") as response:
                rate_limit = response.headers.get('X-RateLimit-Remaining', 'Unknown')
                rate_limit_reset = response.headers.get('X-RateLimit-Reset', 'Unknown')
                print(f"   Rate limit remaining: {rate_limit}")
                print(f"   Rate limit reset: {rate_limit_reset}")
                
                if rate_limit != 'Unknown':
                    if int(rate_limit) < 10:
                        print(f"   ⚠️  Low rate limit remaining - may affect functionality")
                    else:
                        print(f"   ✅ Rate limit OK")
                        
        except Exception as e:
            print(f"❌ Rate limit check failed: {e}")

def check_token_permissions():
    """Check GitHub token permissions"""
    print("\n🔑 Token Permission Analysis")
    print("=" * 60)
    
    print("Required permissions for PR commenting:")
    print("✅ repo - Full control of private repositories")
    print("✅ public_repo - Access public repositories")
    print("✅ pull_request - Access pull requests")
    print("✅ issues - Access issues (for PR comments)")
    
    print("\n💡 Common issues:")
    print("1. Token expired - Generate new token")
    print("2. Insufficient scopes - Add required permissions")
    print("3. Repository access - Ensure token has access to target repo")
    print("4. Rate limiting - Check API rate limits")
    print("5. Repository permissions - Ensure user has write access")

if __name__ == "__main__":
    print("🚀 GitHub PR Reviewer Detailed Diagnostic")
    print("=" * 60)
    
    check_token_permissions()
    
    asyncio.run(debug_github_issues())
    
    print("\n" + "=" * 60)
    print("💡 Next Steps:")
    print("1. Check the diagnostic output above")
    print("2. Verify GitHub token permissions")
    print("3. Test with a real PR using the UI at:")
    print("   http://127.0.0.1:8000/frontend/pr_reviewer.html")
    print("4. Check server logs for detailed error messages")

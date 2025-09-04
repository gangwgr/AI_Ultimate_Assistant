#!/usr/bin/env python3
"""
Test script to diagnose GitHub PR reviewer issues
"""

import asyncio
import aiohttp
import json
import os

async def test_github_pr_reviewer():
    """Test GitHub PR reviewer functionality"""
    
    print("🔍 Testing GitHub PR Reviewer")
    print("=" * 60)
    
    # Test configuration
    base_url = "http://127.0.0.1:8000"
    
    # Test cases - replace with your actual PR details
    test_cases = [
        {
            "name": "Test PR Review Comment",
            "owner": "your-username",  # Replace with actual owner
            "repo": "your-repo",       # Replace with actual repo
            "pr_number": 1,            # Replace with actual PR number
            "endpoint": "/api/github/repos/{owner}/{repo}/pulls/{pr_number}/review-comment"
        },
        {
            "name": "Test PR Comment",
            "owner": "your-username",  # Replace with actual owner
            "repo": "your-repo",       # Replace with actual repo
            "pr_number": 1,            # Replace with actual PR number
            "endpoint": "/api/github/repos/{owner}/{repo}/pulls/{pr_number}/comment"
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        
        # First, test GitHub authentication
        print("\n🔐 Testing GitHub Authentication...")
        try:
            async with session.get(f"{base_url}/api/github/user") as response:
                if response.status == 200:
                    user_info = await response.json()
                    print(f"✅ GitHub authentication successful")
                    print(f"   User: {user_info.get('login', 'Unknown')}")
                    print(f"   Name: {user_info.get('name', 'Unknown')}")
                else:
                    error_text = await response.text()
                    print(f"❌ GitHub authentication failed: {response.status}")
                    print(f"   Error: {error_text}")
                    print("\n💡 Troubleshooting:")
                    print("   1. Check if GITHUB_TOKEN is set in environment")
                    print("   2. Verify token has appropriate permissions")
                    print("   3. Ensure token is not expired")
                    return
        except Exception as e:
            print(f"❌ Authentication test failed: {e}")
            return
        
        # Test each endpoint
        for test_case in test_cases:
            print(f"\n🧪 {test_case['name']}")
            print("-" * 40)
            
            owner = test_case['owner']
            repo = test_case['repo']
            pr_number = test_case['pr_number']
            endpoint = test_case['endpoint'].format(owner=owner, repo=repo, pr_number=pr_number)
            
            # Skip if using placeholder values
            if owner == "your-username" or repo == "your-repo":
                print(f"⏭️  Skipping {test_case['name']} - please update with real PR details")
                continue
            
            try:
                if "review-comment" in endpoint:
                    # Test review comment generation
                    payload = {
                        "owner": owner,
                        "repo": repo,
                        "pr_number": pr_number,
                        "model_preference": "gemini",
                        "auto_comment": True
                    }
                    
                    async with session.post(f"{base_url}{endpoint}", json=payload) as response:
                        print(f"Response status: {response.status}")
                        
                        if response.status == 200:
                            result = await response.json()
                            print("✅ Review comment generated successfully!")
                            print(f"   Auto-posted: {result.get('auto_posted', False)}")
                            if result.get('comment_result', {}).get('post_error'):
                                print(f"   Post error: {result['comment_result']['post_error']}")
                        else:
                            error_text = await response.text()
                            print(f"❌ Failed to generate review comment: {response.status}")
                            print(f"   Error: {error_text}")
                
                elif "comment" in endpoint:
                    # Test simple comment posting
                    payload = {
                        "owner": owner,
                        "repo": repo,
                        "pr_number": pr_number,
                        "comment_body": "🤖 Test comment from AI Ultimate Assistant"
                    }
                    
                    async with session.post(f"{base_url}{endpoint}", json=payload) as response:
                        print(f"Response status: {response.status}")
                        
                        if response.status == 200:
                            result = await response.json()
                            print("✅ Comment posted successfully!")
                            print(f"   Comment URL: {result.get('comment', {}).get('html_url', 'N/A')}")
                        else:
                            error_text = await response.text()
                            print(f"❌ Failed to post comment: {response.status}")
                            print(f"   Error: {error_text}")
                            
            except Exception as e:
                print(f"❌ Test failed: {e}")
        
        # Test PR access
        print(f"\n🔍 Testing PR Access...")
        try:
            # Replace with actual PR details
            test_owner = "your-username"  # Replace
            test_repo = "your-repo"       # Replace
            test_pr = 1                   # Replace
            
            if test_owner != "your-username":
                async with session.get(f"{base_url}/api/github/repos/{test_owner}/{test_repo}/pulls/{test_pr}") as response:
                    if response.status == 200:
                        pr_info = await response.json()
                        print("✅ PR access successful!")
                        print(f"   PR Title: {pr_info.get('title', 'N/A')}")
                        print(f"   State: {pr_info.get('state', 'N/A')}")
                        print(f"   Author: {pr_info.get('user', {}).get('login', 'N/A')}")
                    else:
                        error_text = await response.text()
                        print(f"❌ PR access failed: {response.status}")
                        print(f"   Error: {error_text}")
            else:
                print("⏭️  Skipping PR access test - please update with real PR details")
                
        except Exception as e:
            print(f"❌ PR access test failed: {e}")

def check_environment():
    """Check environment configuration"""
    print("🔧 Environment Check")
    print("=" * 60)
    
    # Check GitHub token
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        print(f"✅ GITHUB_TOKEN is set (length: {len(github_token)})")
        print(f"   Token preview: {github_token[:10]}...{github_token[-4:]}")
    else:
        print("❌ GITHUB_TOKEN is not set")
        print("   Please set GITHUB_TOKEN environment variable")
    
    # Check secure config
    try:
        from app.services.secure_config import secure_config
        secure_token = secure_config.get_github_token()
        if secure_token:
            print(f"✅ Secure config has GitHub token (length: {len(secure_token)})")
        else:
            print("⚠️  Secure config has no GitHub token")
    except Exception as e:
        print(f"⚠️  Secure config not available: {e}")
    
    print()

if __name__ == "__main__":
    print("🚀 GitHub PR Reviewer Diagnostic Tool")
    print("=" * 60)
    
    check_environment()
    
    print("💡 Instructions:")
    print("1. Update the test cases with your actual PR details")
    print("2. Ensure GITHUB_TOKEN has appropriate permissions:")
    print("   - repo (for private repos)")
    print("   - public_repo (for public repos)")
    print("   - pull_request (for commenting)")
    print("3. Run the test to diagnose issues")
    print("=" * 60)
    
    asyncio.run(test_github_pr_reviewer())

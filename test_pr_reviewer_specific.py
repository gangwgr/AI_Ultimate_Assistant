#!/usr/bin/env python3
"""
Test PR reviewer with specific repository
"""

import asyncio
import aiohttp
import json

async def test_pr_reviewer():
    """Test PR reviewer with openshift/openshift-tests-private PR #26676"""
    
    print("🔍 Testing PR Reviewer with Specific Repository")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8000"
    
    # Test repository details
    owner = "openshift"
    repo = "openshift-tests-private"
    pr_number = 26676
    
    print(f"Testing PR: {owner}/{repo}#{pr_number}")
    print(f"URL: https://github.com/{owner}/{repo}/pull/{pr_number}")
    print()
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Get PR information
        print("🔍 Test 1: Get PR Information")
        print("-" * 40)
        try:
            async with session.get(f"{base_url}/api/github/repos/{owner}/{repo}/pulls/{pr_number}") as response:
                print(f"Status: {response.status}")
                
                if response.status == 200:
                    pr_info = await response.json()
                    print("✅ PR access successful!")
                    print(f"   Title: {pr_info.get('title', 'N/A')}")
                    print(f"   State: {pr_info.get('state', 'N/A')}")
                    print(f"   Author: {pr_info.get('user', {}).get('login', 'N/A')}")
                    print(f"   Created: {pr_info.get('created_at', 'N/A')}")
                    print(f"   Updated: {pr_info.get('updated_at', 'N/A')}")
                    print(f"   Commits: {pr_info.get('commits', 'N/A')}")
                    print(f"   Changed Files: {pr_info.get('changed_files', 'N/A')}")
                else:
                    error_text = await response.text()
                    print(f"❌ PR access failed: {error_text}")
                    return
                    
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return
        
        # Test 2: Get PR files
        print("\n📁 Test 2: Get PR Files")
        print("-" * 40)
        try:
            async with session.get(f"{base_url}/api/github/repos/{owner}/{repo}/pulls/{pr_number}/files") as response:
                print(f"Status: {response.status}")
                
                if response.status == 200:
                    files = await response.json()
                    print(f"✅ Files access successful!")
                    print(f"   Found {len(files)} changed files")
                    
                    # Show first few files
                    for i, file in enumerate(files[:5]):
                        print(f"   {i+1}. {file.get('filename', 'N/A')}")
                        print(f"      Status: {file.get('status', 'N/A')}")
                        print(f"      Changes: +{file.get('additions', 0)} -{file.get('deletions', 0)}")
                    
                    if len(files) > 5:
                        print(f"   ... and {len(files) - 5} more files")
                else:
                    error_text = await response.text()
                    print(f"❌ Files access failed: {error_text}")
                    
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        # Test 3: Generate AI Review Comment
        print("\n🤖 Test 3: Generate AI Review Comment")
        print("-" * 40)
        try:
            payload = {
                "owner": owner,
                "repo": repo,
                "pr_number": pr_number,
                "model_preference": "gemini",
                "auto_comment": False  # Don't auto-post, just generate
            }
            
            async with session.post(f"{base_url}/api/github/repos/{owner}/{repo}/pulls/{pr_number}/review-comment", json=payload) as response:
                print(f"Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print("✅ AI review comment generated successfully!")
                    print(f"   Auto-posted: {result.get('auto_posted', False)}")
                    
                    comment_result = result.get('comment_result', {})
                    if comment_result.get('comment_generated'):
                        print(f"   Comment generated: ✅")
                        comment_body = comment_result.get('comment_body', '')
                        print(f"   Comment length: {len(comment_body)} characters")
                        
                        # Show first 500 characters of the comment
                        preview = comment_body[:500]
                        if len(comment_body) > 500:
                            preview += "..."
                        print(f"   Comment preview:\n{preview}")
                    else:
                        print(f"   Comment generation failed")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ AI review failed: {error_text}")
                    
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        # Test 4: Post a simple comment
        print("\n💬 Test 4: Post Simple Comment")
        print("-" * 40)
        try:
            payload = {
                "owner": owner,
                "repo": repo,
                "pr_number": pr_number,
                "comment_body": "🤖 Test comment from AI Ultimate Assistant - Testing PR reviewer functionality"
            }
            
            async with session.post(f"{base_url}/api/github/repos/{owner}/{repo}/pulls/{pr_number}/comment", json=payload) as response:
                print(f"Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print("✅ Comment posted successfully!")
                    comment = result.get('comment', {})
                    print(f"   Comment URL: {comment.get('html_url', 'N/A')}")
                    print(f"   Comment ID: {comment.get('id', 'N/A')}")
                else:
                    error_text = await response.text()
                    print(f"❌ Comment posting failed: {error_text}")
                    
        except Exception as e:
            print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("🚀 PR Reviewer Test for openshift/openshift-tests-private#26676")
    print("=" * 60)
    
    asyncio.run(test_pr_reviewer())
    
    print("\n" + "=" * 60)
    print("💡 Next Steps:")
    print("1. Check the results above")
    print("2. If successful, try the UI: http://127.0.0.1:8000/frontend/pr_reviewer.html")
    print("3. Enter the PR details manually in the UI")

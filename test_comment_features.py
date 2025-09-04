#!/usr/bin/env python3
"""
Test script for comment features (post, edit, delete)
"""

import asyncio
import aiohttp
import json

async def test_comment_features():
    """Test comment posting, editing, and deletion"""
    
    print("🔍 Testing Comment Features")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8000"
    
    # Test repository details
    owner = "openshift"
    repo = "openshift-tests-private"
    pr_number = 26676
    
    print(f"Testing PR: {owner}/{repo}#{pr_number}")
    print()
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Get existing comments
        print("📋 Test 1: Get Existing Comments")
        print("-" * 40)
        try:
            async with session.get(f"{base_url}/api/github/repos/{owner}/{repo}/pulls/{pr_number}/comments") as response:
                print(f"Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    comments = result.get('comments', [])
                    print(f"✅ Found {len(comments)} existing comments")
                    
                    for i, comment in enumerate(comments[:3]):  # Show first 3
                        print(f"   {i+1}. {comment.get('user', {}).get('login', 'Unknown')}: {comment.get('body', '')[:100]}...")
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to get comments: {error_text}")
                    
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        # Test 2: Post a new comment
        print("\n💬 Test 2: Post New Comment")
        print("-" * 40)
        test_comment = "🤖 Test comment from AI Ultimate Assistant - Testing comment features"
        
        try:
            payload = {
                "owner": owner,
                "repo": repo,
                "pr_number": pr_number,
                "comment_body": test_comment
            }
            
            async with session.post(f"{base_url}/api/github/repos/{owner}/{repo}/pulls/{pr_number}/comment", json=payload) as response:
                print(f"Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    comment = result.get('comment', {})
                    comment_id = comment.get('id')
                    print(f"✅ Comment posted successfully!")
                    print(f"   Comment ID: {comment_id}")
                    print(f"   Comment URL: {comment.get('html_url', 'N/A')}")
                    
                    # Test 3: Edit the comment
                    print("\n✏️  Test 3: Edit Comment")
                    print("-" * 40)
                    updated_comment = "🤖 Updated test comment from AI Ultimate Assistant - Comment editing works!"
                    
                    edit_payload = {
                        "owner": owner,
                        "repo": repo,
                        "pr_number": pr_number,
                        "comment_id": comment_id,
                        "comment_body": updated_comment
                    }
                    
                    async with session.patch(f"{base_url}/api/github/repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id}", json=edit_payload) as edit_response:
                        print(f"Edit Status: {edit_response.status}")
                        
                        if edit_response.status == 200:
                            edit_result = await edit_response.json()
                            print(f"✅ Comment updated successfully!")
                            print(f"   Updated body: {edit_result.get('comment', {}).get('body', '')[:100]}...")
                            
                            # Test 4: Delete the comment
                            print("\n🗑️  Test 4: Delete Comment")
                            print("-" * 40)
                            
                            delete_payload = {
                                "owner": owner,
                                "repo": repo,
                                "pr_number": pr_number,
                                "comment_id": comment_id
                            }
                            
                            async with session.delete(f"{base_url}/api/github/repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id}", json=delete_payload) as delete_response:
                                print(f"Delete Status: {delete_response.status}")
                                
                                if delete_response.status == 200:
                                    delete_result = await delete_response.json()
                                    print(f"✅ Comment deleted successfully!")
                                    print(f"   Message: {delete_result.get('message', 'N/A')}")
                                else:
                                    error_text = await delete_response.text()
                                    print(f"❌ Failed to delete comment: {error_text}")
                        else:
                            error_text = await edit_response.text()
                            print(f"❌ Failed to edit comment: {error_text}")
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to post comment: {error_text}")
                    
        except Exception as e:
            print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("🚀 Comment Features Test")
    print("Features being tested:")
    print("✅ Get existing comments")
    print("✅ Post new comment")
    print("✅ Edit comment")
    print("✅ Delete comment")
    print("=" * 60)
    
    asyncio.run(test_comment_features())
    
    print("\n" + "=" * 60)
    print("💡 Next Steps:")
    print("1. Check the results above")
    print("2. Try the enhanced UI: http://127.0.0.1:8000/frontend/pr_reviewer.html")
    print("3. Test comment features in the UI")

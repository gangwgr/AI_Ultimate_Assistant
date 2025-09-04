#!/usr/bin/env python3
"""
Test script for enhanced AI review functionality with preview mode
"""

import asyncio
import aiohttp
import json

async def test_enhanced_ai_review():
    """Test the enhanced AI review with preview and selective posting"""
    
    print("🔍 Testing Enhanced AI Review Features")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8000"
    
    # Test repository details
    owner = "openshift"
    repo = "openshift-tests-private"
    pr_number = 26676
    
    print(f"Testing PR: {owner}/{repo}#{pr_number}")
    print()
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Generate AI review comments in preview mode
        print("🤖 Test 1: Generate AI Review Comments (Preview Mode)")
        print("-" * 50)
        try:
            payload = {
                "owner": owner,
                "repo": repo,
                "pr_number": pr_number,
                "model_preference": "ollama",
                "preview_only": True
            }
            
            async with session.post(f"{base_url}/api/github/repos/{owner}/{repo}/pulls/{pr_number}/review-comment", json=payload) as response:
                print(f"Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    comments = result.get('comments', [])
                    print(f"✅ Generated {len(comments)} AI review comments in preview mode")
                    
                    # Display sample comments
                    for i, comment in enumerate(comments[:3]):  # Show first 3
                        print(f"\n   📝 Comment {i+1}:")
                        print(f"      File: {comment.get('file', 'N/A')}")
                        print(f"      Line: {comment.get('line', 'N/A')}")
                        print(f"      Body: {comment.get('body', 'N/A')[:200]}...")
                    
                    # Test 2: Post individual comments
                    if comments:
                        print(f"\n💬 Test 2: Post Individual Comments")
                        print("-" * 50)
                        
                        # Post first comment individually
                        first_comment = comments[0]
                        comment_payload = {
                            "owner": owner,
                            "repo": repo,
                            "pr_number": pr_number,
                            "comment_body": f"🤖 AI Review Comment (Test): {first_comment.get('body', '')[:100]}..."
                        }
                        
                        async with session.post(f"{base_url}/api/github/repos/{owner}/{repo}/pulls/{pr_number}/comment", json=comment_payload) as comment_response:
                            print(f"Individual Comment Status: {comment_response.status}")
                            
                            if comment_response.status == 200:
                                comment_result = await comment_response.json()
                                print(f"✅ Individual comment posted successfully!")
                                print(f"   Comment URL: {comment_result.get('comment', {}).get('html_url', 'N/A')}")
                            else:
                                error_text = await comment_response.text()
                                print(f"❌ Failed to post individual comment: {error_text}")
                    
                    # Test 3: Get existing comments
                    print(f"\n📋 Test 3: Get Existing Comments")
                    print("-" * 50)
                    
                    async with session.get(f"{base_url}/api/github/repos/{owner}/{repo}/pulls/{pr_number}/comments") as comments_response:
                        print(f"Get Comments Status: {comments_response.status}")
                        
                        if comments_response.status == 200:
                            comments_result = await comments_response.json()
                            existing_comments = comments_result.get('comments', [])
                            print(f"✅ Found {len(existing_comments)} existing comments")
                            
                            for i, comment in enumerate(existing_comments[:2]):  # Show first 2
                                print(f"   {i+1}. {comment.get('user', {}).get('login', 'Unknown')}: {comment.get('body', '')[:100]}...")
                        else:
                            error_text = await comments_response.text()
                            print(f"❌ Failed to get comments: {error_text}")
                    
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to generate AI review: {error_text}")
                    
        except Exception as e:
            print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("🚀 Enhanced AI Review Test")
    print("Features being tested:")
    print("✅ AI review comments in preview mode")
    print("✅ Individual comment posting")
    print("✅ Comment retrieval and display")
    print("✅ Selective comment management")
    print("=" * 60)
    
    asyncio.run(test_enhanced_ai_review())
    
    print("\n" + "=" * 60)
    print("💡 Next Steps:")
    print("1. Check the results above")
    print("2. Try the enhanced UI: http://127.0.0.1:8000/frontend/pr_reviewer.html")
    print("3. Test AI review with preview and selective posting")
    print("4. Edit comments before posting")

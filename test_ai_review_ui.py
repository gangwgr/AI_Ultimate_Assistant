#!/usr/bin/env python3
"""
Test script for AI review UI functionality
"""

import asyncio
import aiohttp
import json

async def test_ai_review_ui():
    """Test the AI review UI functionality"""
    
    print("🔍 Testing AI Review UI Functionality")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8000"
    
    # Test repository details
    owner = "openshift"
    repo = "openshift-tests-private"
    pr_number = 26676
    
    print(f"Testing PR: {owner}/{repo}#{pr_number}")
    print()
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Generate AI review in preview mode
        print("🤖 Test 1: Generate AI Review (Preview Mode)")
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
                    print(f"✅ AI review generated successfully!")
                    
                    # Check response format
                    if 'comments' in result:
                        comments = result['comments']
                        print(f"   Found {len(comments)} comments in array format")
                        for i, comment in enumerate(comments[:2]):
                            print(f"   Comment {i+1}: {comment.get('file', 'N/A')} Line {comment.get('line', 'N/A')}")
                    elif 'comment_result' in result:
                        comment_body = result['comment_result'].get('comment_body', '')
                        print(f"   Found single comment result ({len(comment_body)} characters)")
                        print(f"   Preview: {comment_body[:200]}...")
                    else:
                        print(f"   Unexpected response format: {list(result.keys())}")
                    
                    print(f"\n📋 Response keys: {list(result.keys())}")
                    
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to generate AI review: {error_text}")
                    
        except Exception as e:
            print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("🚀 AI Review UI Test")
    print("Features being tested:")
    print("✅ AI review generation in preview mode")
    print("✅ Response format handling")
    print("✅ Comment parsing and display")
    print("=" * 60)
    
    asyncio.run(test_ai_review_ui())
    
    print("\n" + "=" * 60)
    print("💡 Next Steps:")
    print("1. Check the results above")
    print("2. Try the enhanced UI: http://127.0.0.1:8000/frontend/pr_reviewer.html")
    print("3. Test AI review with preview and selective posting")
    print("4. Check browser console for debug logs")

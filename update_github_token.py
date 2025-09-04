#!/usr/bin/env python3
"""
Script to update GitHub token with proper permissions
"""

import os
import sys
from app.services.secure_config import secure_config

def update_github_token():
    """Update GitHub token with proper permissions"""
    
    print("🔑 GitHub Token Update Tool")
    print("=" * 60)
    
    print("❌ Current Issue: GitHub token missing required scopes")
    print("   Missing: repo, public_repo, pull_request, issues")
    print()
    
    print("📋 Required Steps:")
    print("1. Go to: https://github.com/settings/tokens")
    print("2. Click 'Generate new token (classic)'")
    print("3. Name: 'AI Ultimate Assistant PR Reviewer'")
    print("4. Select these scopes:")
    print("   ✅ repo - Full control of private repositories")
    print("   ✅ public_repo - Access public repositories")
    print("   ✅ pull_request - Access pull requests")
    print("   ✅ issues - Access issues (for PR comments)")
    print("5. Click 'Generate token'")
    print("6. Copy the new token")
    print()
    
    # Get current token info
    current_token = secure_config.get_github_token()
    if current_token:
        print(f"Current token: {current_token[:10]}...{current_token[-4:]}")
    else:
        print("No current token found")
    
    print()
    
    # Get new token from user
    new_token = input("Enter your new GitHub token (or press Enter to skip): ").strip()
    
    if not new_token:
        print("⏭️  Token update skipped")
        return
    
    # Validate token format
    if not (new_token.startswith('ghp_') or new_token.startswith('github_pat_') or len(new_token) == 40):
        print("⚠️  Warning: Token format doesn't match expected patterns")
        print("   Expected: ghp_... or github_pat_... or 40-character token")
        proceed = input("Continue anyway? (y/N): ").strip().lower()
        if proceed != 'y':
            print("❌ Token update cancelled")
            return
    
    # Update token
    try:
        success = secure_config.set_github_token(new_token)
        if success:
            print("✅ GitHub token updated successfully!")
            print("   You can now test PR commenting functionality")
        else:
            print("❌ Failed to update GitHub token")
    except Exception as e:
        print(f"❌ Error updating token: {e}")

def test_token():
    """Test the current token"""
    print("\n🧪 Testing Current Token")
    print("-" * 40)
    
    token = secure_config.get_github_token()
    if not token:
        print("❌ No token found")
        return
    
    print(f"Token: {token[:10]}...{token[-4:]}")
    
    # Test with curl (if available)
    import subprocess
    try:
        result = subprocess.run([
            'curl', '-H', f'Authorization: token {token}',
            '-H', 'Accept: application/vnd.github.v3+json',
            'https://api.github.com/user'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Token test successful")
            import json
            try:
                user_data = json.loads(result.stdout)
                print(f"   User: {user_data.get('login', 'Unknown')}")
                print(f"   Name: {user_data.get('name', 'Unknown')}")
            except:
                print("   Response received but couldn't parse JSON")
        else:
            print(f"❌ Token test failed: {result.stderr}")
    except Exception as e:
        print(f"⚠️  Couldn't test token: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_token()
    else:
        update_github_token()
        
        print("\n" + "=" * 60)
        print("💡 Next Steps:")
        print("1. Test the new token: python update_github_token.py test")
        print("2. Try PR commenting at: http://127.0.0.1:8000/frontend/pr_reviewer.html")
        print("3. Run diagnostics: python debug_github_issues.py")

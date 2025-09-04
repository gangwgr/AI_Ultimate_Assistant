#!/usr/bin/env python3
"""
Google Calendar Setup Script
Helps configure Google Calendar integration
"""

import os
import json
import sys
from pathlib import Path

def setup_google_calendar():
    """Setup Google Calendar integration"""
    
    print("🔧 Google Calendar Setup")
    print("=" * 50)
    
    # Check if credentials directory exists
    credentials_dir = Path("credentials")
    if not credentials_dir.exists():
        credentials_dir.mkdir()
        print("✅ Created credentials directory")
    
    # Check for Google credentials file
    google_creds_file = credentials_dir / "google_credentials.json"
    
    if not google_creds_file.exists():
        print("\n❌ Google credentials file not found!")
        print("\n📋 To set up Google Calendar integration:")
        print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable Google Calendar API")
        print("4. Create OAuth 2.0 credentials")
        print("5. Download the credentials JSON file")
        print("6. Save it as 'credentials/google_credentials.json'")
        print("\n📁 Expected file structure:")
        print("credentials/")
        print("├── google_credentials.json  ← Your OAuth credentials")
        print("└── calendar_token.json      ← Auto-generated after first login")
        
        print("\n🔗 Quick Links:")
        print("• Google Cloud Console: https://console.cloud.google.com/")
        print("• Google Calendar API: https://developers.google.com/calendar/api")
        print("• OAuth 2.0 Setup: https://developers.google.com/identity/protocols/oauth2")
        
        return False
    
    print("✅ Google credentials file found")
    
    # Check if token file exists
    token_file = credentials_dir / "calendar_token.json"
    if token_file.exists():
        print("✅ Calendar token file found (already authenticated)")
        return True
    else:
        print("⚠️  Calendar token file not found")
        print("   You'll need to authenticate on first calendar access")
        return True

def test_google_calendar_connection():
    """Test Google Calendar connection"""
    try:
        from app.services.google_calendar_service import GoogleCalendarService
        
        print("\n🧪 Testing Google Calendar Connection...")
        
        calendar_service = GoogleCalendarService()
        is_connected = calendar_service._get_service() is not None
        
        if is_connected:
            print("✅ Google Calendar connection successful!")
            return True
        else:
            print("❌ Google Calendar connection failed")
            print("   Check your credentials and try again")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Google Calendar connection: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 AI Ultimate Assistant - Google Calendar Setup")
    print("=" * 60)
    
    # Setup Google Calendar
    setup_success = setup_google_calendar()
    
    if setup_success:
        print("\n🔍 Testing connection...")
        test_success = test_google_calendar_connection()
        
        if test_success:
            print("\n🎉 Google Calendar setup complete!")
            print("   You can now use calendar commands like:")
            print("   • 'Show my calendar'")
            print("   • 'Show my calendar for today'")
            print("   • 'Show my calendar for this week'")
            print("   • 'Schedule a meeting'")
            print("   • 'Send invite to team'")
        else:
            print("\n⚠️  Setup incomplete - authentication required")
            print("   Run the assistant and try a calendar command to authenticate")
    else:
        print("\n❌ Setup incomplete - credentials required")
        print("   Please follow the setup instructions above")

if __name__ == "__main__":
    main() 
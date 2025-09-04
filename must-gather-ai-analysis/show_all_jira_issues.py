#!/usr/bin/env python3
"""
Script to fetch and display all Jira issues with clickable links
"""
import json
from jira_integration import JiraIntegration

def debug_all_fields(jira_integration, username):
    """Debug function to see all available fields"""
    print("\n🔍 DEBUG: Fetching sample issue with ALL fields...")
    
    # Get one issue with ALL fields
    params = {
        'jql': f'assignee = "{username}"',
        'maxResults': 1,
        'fields': '*all'  # Request ALL fields
    }
    
    response = jira_integration._make_request(
        'GET',
        f"{jira_integration.server_url}/rest/api/2/search",
        params=params,
        timeout=30
    )
    
    if response.status_code == 200:
        issues = response.json().get('issues', [])
        if issues:
            issue = issues[0]
            fields = issue.get('fields', {})
            print(f"\n📊 ALL fields in issue {issue.get('key')}:")
            
            qa_related_fields = []
            user_related_fields = []
            
            for field_key, field_value in sorted(fields.items()):
                if field_value is not None:
                    field_str = str(field_value)
                    
                    # Look for QA-related content or user objects
                    is_qa_related = 'qa' in field_key.lower() or 'qa' in field_str.lower()
                    is_user_field = (isinstance(field_value, dict) and 'displayName' in field_value) or \
                                   (isinstance(field_value, list) and field_value and 
                                    isinstance(field_value[0], dict) and 'displayName' in field_value[0])
                    
                    if is_qa_related:
                        qa_related_fields.append((field_key, field_value))
                        print(f"  🎯 QA FIELD - {field_key}: {field_str[:100]}...")
                    elif is_user_field:
                        user_related_fields.append((field_key, field_value))
                        if isinstance(field_value, dict):
                            display_name = field_value.get('displayName', 'Unknown')
                            print(f"  👤 USER FIELD - {field_key}: {display_name}")
                        elif isinstance(field_value, list) and field_value:
                            display_names = [item.get('displayName', 'Unknown') for item in field_value]
                            print(f"  👥 USER LIST - {field_key}: {display_names}")
                    elif field_key.startswith('customfield_'):
                        # Show custom fields that might be relevant
                        short_val = field_str[:50] if len(field_str) < 100 else field_str[:50] + "..."
                        print(f"  📋 {field_key}: {short_val}")
            
            print(f"\n📈 Found {len(qa_related_fields)} QA fields, {len(user_related_fields)} user fields")
            
            # Check if any user fields contain our username
            print(f"\n🔍 Checking user fields for '{username}':")
            for field_key, field_value in user_related_fields:
                field_str = str(field_value)
                if username in field_str:
                    print(f"  ✅ Found username in {field_key}: {field_str[:100]}...")
            
            return qa_related_fields + user_related_fields
    
    return []

def main():
    # Load Jira configuration
    try:
        with open('jira_config.json', 'r') as f:
            config = json.load(f)
        
        # Initialize Jira integration with proper auth method detection
        token = config['token']
        # Auto-detect auth method like the AI builder does
        auth_method = "pat_bearer" if len(token) > 20 else "basic"
        
        jira = JiraIntegration(
            server_url=config['server'],
            username=config['username'],
            api_token=token,
            auth_method=auth_method
        )
        
        print(f"🔧 Using authentication method: {auth_method}")
        
        # DEBUG: First check what fields are available
        qa_fields = debug_all_fields(jira, config['username'])
        
        print("\n" + "="*60)
        print("🧪 TESTING QA CONTACT ISSUES")
        print("="*60)
        
        qa_issues = jira.get_user_issues(
            username=config['username'], 
            issue_type="qa_contact", 
            max_results=50, 
            exclude_closed=False
        )
        
        print(f"\n📋 **QA Contact Issues** ({len(qa_issues)} issues):\n")
        
        if qa_issues:
            for i, issue in enumerate(qa_issues[:5], 1):  # Show first 5
                issue_key = issue.get('key', 'Unknown')
                summary = issue.get('fields', {}).get('summary', 'No summary')
                status = issue.get('fields', {}).get('status', {}).get('name', 'Unknown')
                
                print(f"{i:2d}. {issue_key}: {summary[:60]}...")
                print(f"    📈 Status: {status}")
        else:
            print("❌ No QA contact issues found with current JQL:")
            print(f'    ("QA Contact" = "{config["username"]}" OR "QA Assignee" = "{config["username"]}" OR cf[12316243] = "{config["username"]}")')
            
            # Try alternative field names based on what we found
            print("\n🔄 Trying alternative QA field searches...")
            for field_name, field_value in qa_fields:
                if 'qa' in field_name.lower():
                    print(f"  Testing field: {field_name}")
                    alt_jql = f'{field_name} = "{config["username"]}"'
                    alt_params = {
                        'jql': alt_jql,
                        'maxResults': 5,
                        'fields': 'summary,status'
                    }
                    try:
                        alt_response = jira._make_request(
                            'GET',
                            f"{jira.server_url}/rest/api/2/search",
                            params=alt_params,
                            timeout=10
                        )
                        if alt_response.status_code == 200:
                            alt_issues = alt_response.json().get('issues', [])
                            print(f"    ✅ Found {len(alt_issues)} issues with {field_name}")
                        else:
                            print(f"    ❌ Failed to search {field_name}: {alt_response.status_code}")
                    except Exception as e:
                        print(f"    ❌ Error searching {field_name}: {e}")
        
        print(f"\n📊 Summary:")
        print(f"   • QA Contact issues found: {len(qa_issues)}")
        print(f"   • Total QA/custom fields discovered: {len(qa_fields)}")
        
    except FileNotFoundError:
        print("❌ jira_config.json not found. Please configure Jira integration first.")
    except Exception as e:
        print(f"❌ Error fetching Jira issues: {str(e)}")

if __name__ == "__main__":
    main() 
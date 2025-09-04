#!/usr/bin/env python3
"""
Debug script to test Jira connection and queries
"""
import json
from jira_integration import JiraIntegration

def main():
    # Load Jira configuration
    try:
        with open('jira_config.json', 'r') as f:
            config = json.load(f)
        
        print("🔧 Debug: Jira Configuration")
        print(f"Server: {config['server']}")
        print(f"Username: {config['username']}")
        print(f"Token: {config['token'][:10]}..." if config['token'] else "No token")
        print()
        
        # Initialize Jira integration
        jira = JiraIntegration(
            server_url=config['server'],
            username=config['username'],
            api_token=config['token']
        )
        
        print("🔧 Debug: Testing basic authentication...")
        
        # Test basic connection with a simple API call
        response = jira._make_request('GET', f"{config['server']}/rest/api/2/myself")
        print(f"Authentication test status: {response.status_code}")
        if response.status_code == 200:
            user_info = response.json()
            print(f"✅ Successfully authenticated as: {user_info.get('displayName', 'Unknown')}")
            print(f"Account ID: {user_info.get('accountId', 'Unknown')}")
            print(f"Email: {user_info.get('emailAddress', 'Unknown')}")
        else:
            print(f"❌ Authentication failed: {response.text}")
            return
        
        print("\n🔧 Debug: Testing JQL queries...")
        
        # Test different JQL queries
        test_queries = [
            f'assignee = "{config["username"]}"',
            f'assignee = currentUser()',
            f'assignee was "{config["username"]}"',
            f'assignee in (currentUser())'
        ]
        
        for i, jql in enumerate(test_queries, 1):
            print(f"\n{i}. Testing JQL: {jql}")
            
            params = {
                'jql': jql,
                'maxResults': 5,
                'fields': 'summary,status,assignee'
            }
            
            response = jira._make_request(
                'GET',
                f"{config['server']}/rest/api/2/search",
                params=params
            )
            
            if response.status_code == 200:
                result = response.json()
                issue_count = result.get('total', 0)
                issues = result.get('issues', [])
                print(f"   ✅ Query successful: Found {issue_count} issues")
                
                for issue in issues[:3]:  # Show first 3
                    key = issue.get('key', 'Unknown')
                    summary = issue.get('fields', {}).get('summary', 'No summary')
                    print(f"      - {key}: {summary[:50]}...")
                    
            else:
                print(f"   ❌ Query failed: {response.status_code} - {response.text}")
        
        print("\n🔧 Debug: Testing with original script method...")
        
        # Test the exact method used in the original script
        open_issues = jira.get_user_issues(
            username=config['username'], 
            issue_type="assigned", 
            max_results=50, 
            exclude_closed=True
        )
        
        print(f"Original method returned: {len(open_issues)} issues")
        
        # Test without exclude_closed
        all_issues = jira.get_user_issues(
            username=config['username'], 
            issue_type="assigned", 
            max_results=50, 
            exclude_closed=False
        )
        
        print(f"Without exclude_closed filter: {len(all_issues)} issues")
        
    except FileNotFoundError:
        print("❌ jira_config.json not found. Please configure Jira integration first.")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
import requests
import json
from datetime import datetime
import pandas as pd
import os
import streamlit as st
from requests.auth import HTTPBasicAuth
from typing import List, Dict, Any, Optional

class JiraIntegration:
    def __init__(self, server_url: str, username: str, api_token: str, auth_method: str = "basic"):
        """Initialize Jira integration with authentication"""
        self.server_url = server_url.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.auth_method = auth_method
        
        # Set up authentication based on method
        if auth_method == "basic":
            self.auth = HTTPBasicAuth(username, api_token)
            self.headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        elif auth_method == "pat_basic":
            # Basic auth with username + PAT
            self.auth = HTTPBasicAuth(username, api_token)
            self.headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        elif auth_method == "pat_bearer":
            # Bearer token with PAT
            self.auth = None
            self.headers = {
                'Authorization': f'Bearer {api_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        elif auth_method == "pat_custom":
            # Custom header with PAT
            self.auth = None
            self.headers = {
                'X-Atlassian-Token': api_token,
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        else:
            # Default to basic auth
            self.auth = HTTPBasicAuth(username, api_token)
            self.headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
    
    def _make_request(self, method: str, url: str, **kwargs):
        """Make request with appropriate authentication"""
        if self.auth:
            kwargs['auth'] = self.auth
        kwargs['headers'] = self.headers
        
        return requests.request(method, url, **kwargs)
        
    def test_connection(self) -> bool:
        """Test Jira connection with SSO-specific error handling"""
        try:
            # Debug: Print request details
            url = f"{self.server_url}/rest/api/2/myself"
            print(f"DEBUG: Making request to: {url}")
            print(f"DEBUG: Username: {self.username}")
            print(f"DEBUG: Headers: {self.headers}")
            print(f"DEBUG: Auth type: HTTPBasicAuth")
            
            response = self._make_request('GET', url, timeout=10)
            
            # Debug: Print response details  
            print(f"DEBUG: Response status: {response.status_code}")
            print(f"DEBUG: Response headers: {dict(response.headers)}")
            print(f"DEBUG: Response text (first 500 chars): {response.text[:500]}")
            
            if response.status_code == 200:
                user_data = response.json()
                st.success(f"✅ Connected successfully as {user_data.get('displayName', 'Unknown User')}")
                return True
            elif response.status_code == 401:
                # Detect server type for appropriate error message
                is_redhat_error = 'redhat.com' in self.server_url
                is_atlassian_error = 'atlassian.net' in self.server_url
                
                if is_redhat_error:
                    st.error("❌ **Red Hat Authentication Failed (401)**\n\n" +
                            "**For Red Hat Jira:**\n" +
                            "• Double-check your **Red Hat username** (e.g., rhn-support-rgangwar)\n" +
                            "• **Verify your password** - try logging into https://issues.redhat.com manually\n" +
                            "• **Check VPN connection** - Red Hat systems may require VPN\n" +
                            "• **Verify account status** - ensure your Red Hat account is active\n" +
                            "• **Contact IT support** if you continue having issues")
                elif is_atlassian_error:
                    st.error("❌ **Atlassian Authentication Failed (401)**\n\n" +
                            "**For Atlassian Cloud:**\n" +
                            "• Double-check your **email address** (not display name)\n" +
                            "• **Regenerate API token** from Atlassian Account Settings\n" +
                            "• Visit: https://id.atlassian.com/manage-profile/security/api-tokens")
                else:
                    st.error("❌ **Authentication Failed (401)**\n\n" +
                            "• **Check your credentials** - username and password/token\n" +
                            "• **Verify server URL** - ensure it's correct\n" +
                            "• **Contact administrator** if issues persist")
                return False
            elif response.status_code == 403:
                # Get the actual Jira error message
                try:
                    jira_error = response.json()
                    error_messages = jira_error.get('errorMessages', [])
                    error_details = jira_error.get('errors', {})
                    
                    detailed_error = "**Jira Error Details:**\n"
                    if error_messages:
                        detailed_error += f"• Messages: {', '.join(error_messages)}\n"
                    if error_details:
                        detailed_error += f"• Details: {error_details}\n"
                    detailed_error += f"• Raw Response: {response.text}\n"
                    
                except:
                    # If JSON parsing fails, show raw response
                    detailed_error = f"**Raw Jira Response:**\n{response.text}\n"
                
                st.error("❌ **Access Forbidden (403)**\n\n" +
                        "Your credentials are valid but you don't have API access.\n\n" +
                        detailed_error + 
                        "\nContact your Jira administrator to enable API access.")
                return False
            elif response.status_code == 404:
                st.error("❌ **Server Not Found (404)**\n\n" +
                        "Check your server URL format:\n" +
                        "• Should be: `https://yourcompany.atlassian.net`\n" +
                        "• No trailing slash\n" +
                        "• Make sure it's your correct Jira instance")
                return False
            else:
                st.error(f"❌ **Connection Failed ({response.status_code})**\n\n{response.text}")
                return False
                
        except requests.exceptions.Timeout:
            st.error("❌ **Connection Timeout**\n\nServer is taking too long to respond. Check your network connection.")
            return False
        except requests.exceptions.ConnectionError:
            st.error("❌ **Connection Error**\n\nCannot reach the server. Check your server URL and network connection.")
            return False
        except Exception as e:
            st.error(f"❌ **Unexpected Error**\n\n{str(e)}")
            return False
    
    def test_raw_connection(self) -> dict:
        """Test connection and return raw response details for debugging"""
        try:
            import base64
            
            # Manual basic auth header creation (same as requests does)
            credentials = f"{self.username}:{self.api_token}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            manual_headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            url = f"{self.server_url}/rest/api/2/myself"
            
            # Test with manual headers
            print(f"DEBUG: Testing manual auth header...")
            print(f"DEBUG: Manual Authorization header: Basic {encoded_credentials[:20]}...")
            
            response = requests.get(url, headers=manual_headers, timeout=10)
            
            result = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'text': response.text,
                'url': url,
                'request_headers': manual_headers
            }
            
            # Add decoded credentials for debugging (first few chars only)
            result['decoded_username'] = credentials.split(':')[0]
            result['credential_length'] = len(credentials)
            
            return result
        except Exception as e:
            return {'error': str(e)}
    
    def test_pat_authentication(self, personal_access_token: str) -> dict:
        """Test Personal Access Token authentication with multiple methods"""
        url = f"{self.server_url}/rest/api/2/myself"
        results = {}
        
        # Method 1: Basic Auth with username + PAT as password
        try:
            import base64
            credentials = f"{self.username}:{personal_access_token}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            basic_pat_headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            response1 = requests.get(url, headers=basic_pat_headers, timeout=10)
            results['basic_auth_pat'] = {
                'method': 'Basic Auth (username + PAT)',
                'status_code': response1.status_code,
                'headers': dict(response1.headers),
                'text': response1.text,
                'success': response1.status_code == 200
            }
        except Exception as e:
            results['basic_auth_pat'] = {'error': str(e)}
        
        # Method 2: Bearer token authentication
        try:
            bearer_headers = {
                'Authorization': f'Bearer {personal_access_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            response2 = requests.get(url, headers=bearer_headers, timeout=10)
            results['bearer_token'] = {
                'method': 'Bearer Token',
                'status_code': response2.status_code,
                'headers': dict(response2.headers),
                'text': response2.text,
                'success': response2.status_code == 200
            }
        except Exception as e:
            results['bearer_token'] = {'error': str(e)}
        
        # Method 3: Custom PAT header (some Jira instances use this)
        try:
            custom_headers = {
                'X-Atlassian-Token': personal_access_token,
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            response3 = requests.get(url, headers=custom_headers, timeout=10)
            results['custom_header'] = {
                'method': 'Custom Header (X-Atlassian-Token)',
                'status_code': response3.status_code,
                'headers': dict(response3.headers),
                'text': response3.text,
                'success': response3.status_code == 200
            }
        except Exception as e:
            results['custom_header'] = {'error': str(e)}
        
        return results
    
    def get_user_issues(self, username: str, issue_type: str = "assigned", max_results: int = 100, exclude_closed: bool = False) -> List[Dict]:
        """Fetch issues based on different criteria"""
        try:
            # Different JQL queries based on issue type
            if issue_type == "assigned":
                jql = f'assignee = "{username}"'
            elif issue_type == "qa_contact":
                # Common QA Contact field names in different Jira instances
                jql = f'("QA Contact" = "{username}" OR "QA Assignee" = "{username}" OR cf[12316243] = "{username}")'
            elif issue_type == "reported":
                jql = f'reporter = "{username}"'
            elif issue_type == "all_mine":
                jql = f'(assignee = "{username}" OR reporter = "{username}" OR "QA Contact" = "{username}")'
            else:
                jql = f'assignee = "{username}"'
            
            # Add filter for open issues if requested
            if exclude_closed:
                jql += ' AND statusCategory != Done'
            
            # Add ordering
            jql += ' ORDER BY updated DESC'
            
            params = {
                'jql': jql,
                'maxResults': max_results,
                'fields': 'summary,description,status,priority,assignee,reporter,created,updated,transitions,customfield_12316243,customfield_12316244'
            }
            
            response = self._make_request(
                'GET',
                f"{self.server_url}/rest/api/2/search",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('issues', [])
            else:
                st.error(f"Failed to fetch issues: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            st.error(f"Error fetching issues: {str(e)}")
            return []
    
    def get_issue_transitions(self, issue_key: str) -> List[Dict]:
        """Get available transitions for an issue"""
        try:
            response = self._make_request(
                'GET',
                f"{self.server_url}/rest/api/2/issue/{issue_key}/transitions",
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json().get('transitions', [])
            else:
                st.error(f"Failed to get transitions for {issue_key}: {response.status_code}")
                return []
                
        except Exception as e:
            st.error(f"Error getting transitions for {issue_key}: {str(e)}")
            return []
    
    def add_comment_to_issue(self, issue_key: str, comment_text: str) -> bool:
        """Add a comment to a Jira issue"""
        try:
            comment_data = {
                "body": comment_text
            }
            
            response = self._make_request(
                'POST',
                f"{self.server_url}/rest/api/2/issue/{issue_key}/comment",
                json=comment_data,
                timeout=15
            )
            
            if response.status_code == 201:
                return True
            else:
                st.error(f"Failed to add comment to {issue_key}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            st.error(f"Error adding comment to {issue_key}: {str(e)}")
            return False
    
    def transition_issue(self, issue_key: str, transition_id: str, comment: str = "") -> bool:
        """Transition an issue to a new status"""
        try:
            transition_data: Dict[str, Any] = {
                "transition": {
                    "id": transition_id
                }
            }
            
            # Add comment if provided
            if comment:
                transition_data["update"] = {
                    "comment": [
                        {
                            "add": {
                                "body": comment
                            }
                        }
                    ]
                }
            
            response = self._make_request(
                'POST',
                f"{self.server_url}/rest/api/2/issue/{issue_key}/transitions",
                json=transition_data,
                timeout=15
            )
            
            if response.status_code == 204:
                return True
            else:
                st.error(f"Failed to transition {issue_key}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            st.error(f"Error transitioning {issue_key}: {str(e)}")
            return False
    
    def format_issue_data(self, issue: Dict) -> Dict:
        """Format issue data for better readability"""
        fields = issue.get('fields', {})
        
        # Extract key information
        formatted_issue = {
            'key': issue.get('key', ''),
            'summary': fields.get('summary', ''),
            'description': fields.get('description', ''),
            'status': fields.get('status', {}).get('name', ''),
            'priority': fields.get('priority', {}).get('name', ''),
            'assignee': fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned',
            'reporter': fields.get('reporter', {}).get('displayName', ''),
            'created': fields.get('created', ''),
            'updated': fields.get('updated', ''),
            'url': f"{self.server_url}/browse/{issue.get('key', '')}"
        }
        
        # Extract QA Contact if available
        qa_contact_fields = ['customfield_12316243', 'customfield_12316244']
        for field in qa_contact_fields:
            if field in fields and fields[field]:
                if isinstance(fields[field], dict):
                    formatted_issue['qa_contact'] = fields[field].get('displayName', '')
                else:
                    formatted_issue['qa_contact'] = str(fields[field])
                break
        
        return formatted_issue
    
    def search_issues_by_text(self, search_text: str, username: str) -> List[Dict]:
        """Search issues by text in summary or description"""
        try:
            jql = f'(assignee = "{username}" OR reporter = "{username}") AND (summary ~ "{search_text}" OR description ~ "{search_text}") ORDER BY updated DESC'
            
            params = {
                'jql': jql,
                'maxResults': 50,
                'fields': 'summary,description,status,priority,assignee,reporter,created,updated'
            }
            
            response = self._make_request(
                'GET',
                f"{self.server_url}/rest/api/2/search",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('issues', [])
            else:
                return []
                
        except Exception as e:
            st.error(f"Error searching issues: {str(e)}")
            return []
    
    def generate_training_data(self, issues: List[Dict], include_actions: bool = True) -> List[Dict]:
        """Generate training data from Jira issues including action capabilities"""
        training_data = []
        
        for issue in issues:
            formatted_issue = self.format_issue_data(issue)
            issue_key = formatted_issue['key']
            
            # Basic issue information training
            training_data.extend([
                {
                    'instruction': f"What is the summary of Jira issue {issue_key}?",
                    'input': f"Issue: {issue_key}",
                    'output': f"The summary of {issue_key} is: {formatted_issue['summary']}"
                },
                {
                    'instruction': f"What is the current status of {issue_key}?",
                    'input': f"Issue: {issue_key}",
                    'output': f"The current status of {issue_key} is: {formatted_issue['status']}"
                },
                {
                    'instruction': f"Who is assigned to {issue_key}?",
                    'input': f"Issue: {issue_key}",
                    'output': f"{issue_key} is assigned to: {formatted_issue['assignee']}"
                }
            ])
            
            # Add action-oriented training if requested
            if include_actions:
                training_data.extend([
                    {
                        'instruction': f"Add a comment to {issue_key} saying the work is completed",
                        'input': f"Issue: {issue_key}, Action: add comment",
                        'output': f"I'll add a comment to {issue_key}. The comment 'Work completed' has been added to the issue."
                    },
                    {
                        'instruction': f"Update {issue_key} status to Done",
                        'input': f"Issue: {issue_key}, Action: change status",
                        'output': f"I'll update the status of {issue_key} to Done. The issue has been transitioned successfully."
                    },
                    {
                        'instruction': f"Mark {issue_key} as completed",
                        'input': f"Issue: {issue_key}, Action: complete",
                        'output': f"I'll mark {issue_key} as completed by transitioning it to Done status and adding a completion comment."
                    }
                ])
        
        # Add general Jira interaction training
        training_data.extend([
            {
                'instruction': "How do I update a Jira issue?",
                'input': "Jira actions",
                'output': "I can help you update Jira issues in several ways: 1) Add comments to issues, 2) Change issue status (e.g., mark as Done), 3) Search for specific issues. Just tell me the issue key and what you want to do."
            },
            {
                'instruction': "Add a comment to my latest issue",
                'input': "Jira comment",
                'output': "I'll add a comment to your most recently updated issue. What would you like the comment to say?"
            },
            {
                'instruction': "Show me my assigned issues",
                'input': "Jira query",
                'output': "I'll fetch all issues currently assigned to you that are not completed."
            }
        ])
        
        return training_data
    
    def save_training_data(self, training_data: List[Dict], filename: str = "") -> str:
        """Save training data to JSONL file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"jira_training_data_{timestamp}.jsonl"
        
        with open(filename, 'w', encoding='utf-8') as f:
            for item in training_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        return filename
    
    def get_work_summary(self, issues: List[Dict], issue_type: str = "assigned") -> str:
        """Generate a summary of current work"""
        if not issues:
            return "No issues found."
        
        # Simple analysis
        status_counts = {}
        priority_counts = {}
        
        for issue in issues:
            formatted = self.format_issue_data(issue)
            status = formatted['status']
            priority = formatted['priority']
            
            status_counts[status] = status_counts.get(status, 0) + 1
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        type_labels = {
            "assigned": "Assigned to You",
            "qa_contact": "QA Contact",
            "reported": "Reported by You",
            "all_mine": "All Your Issues"
        }
        
        summary = f"""## {type_labels.get(issue_type, "Your Issues")} Summary

**Total Issues**: {len(issues)}

**Status Breakdown**:
"""
        
        for status, count in status_counts.items():
            summary += f"- {status}: {count} issues\n"
        
        summary += "\n**Priority Breakdown**:\n"
        for priority, count in priority_counts.items():
            summary += f"- {priority}: {count} issues\n"
        
        return summary

# Enhanced chatbot functions for Jira integration
def process_jira_command(user_message: str, jira_integration: Optional[JiraIntegration] = None) -> str:
    """Process Jira-related commands in natural language"""
    
    if not jira_integration:
        return "Jira integration is not configured. Please set up your Jira connection first."
    
    message_lower = user_message.lower()
    
    # Extract issue key if present (e.g., PROJ-123)
    import re
    issue_key_pattern = r'([A-Z]+-\d+)'
    issue_keys = re.findall(issue_key_pattern, user_message.upper())
    
    try:
        # Capability questions for updates (e.g., "can you update jira status or comments")
        if any(phrase in message_lower for phrase in ["can you update", "can you modify", "can you change", "update jira", "modify jira", "change jira"]):
            return """✅ **Yes! I can update Jira status and comments!**

**📝 Comment Commands:**
• `"Add comment to OCPBUGS-12345 saying work completed"`
• `"Comment on API-1718: Testing finished successfully"`
• `"Add comment to CNTRLPLANE-910 saying Ready for review"`

**🔄 Status Update Commands:**
• `"Mark OCPBUGS-12345 as completed"`
• `"Set API-1718 to done"`
• `"Mark CNTRLPLANE-910 as finished"`

**✨ Features:**
• ✅ **Auto-timestamps** - Adds completion dates
• ✅ **Smart transitions** - Finds available status changes
• ✅ **Error handling** - Shows available options if needed
• ✅ **Real updates** - Actually modifies your Red Hat Jira issues

**🎯 Try it now with any of your 25 open issues!**

Example: `"Add comment to CNTRLPLANE-910 saying Testing in progress"`"""
        
        # Capability questions for creation (e.g., "can you create jira")
        elif any(phrase in message_lower for phrase in ["can you create", "create jira", "make jira", "new jira", "create issue", "create ticket"]):
            return """❌ **Currently, I cannot create new Jira issues.**

**🔧 What I CAN do:**
• ✅ **View issues** - `"my open jira issues"`, `"my on_qa issues"`
• ✅ **Update status** - `"Mark PROJ-123 as completed"`
• ✅ **Add comments** - `"Comment on PROJ-123: Work done"`
• ✅ **Search issues** - `"find issues with QA"`

**💡 What I CANNOT do (yet):**
• ❌ **Create new issues**
• ❌ **Assign issues** to other users
• ❌ **Upload attachments**
• ❌ **Edit issue descriptions**

**🚀 For creating issues, you'll need to:**
• Use Red Hat Jira web interface: https://issues.redhat.com
• Use Jira CLI tools
• Use direct Jira REST API

**🎯 But I can help manage your existing 25 open issues!**
Try: `"my open jira issues"` to see what you can work with."""
        
        # Status-based searches (e.g., "my issues with status QA")
        elif any(phrase in message_lower for phrase in ["with status", "status:", "status qa", "status on_qa", "status review"]):
            # Extract status name from the message
            status_terms = ["qa", "on_qa", "on qa", "review", "testing", "verify"]
            found_status = None
            for term in status_terms:
                if term in message_lower:
                    found_status = term.upper().replace(" ", "_")
                    break
            
            if found_status:
                # Search for issues with specific status
                custom_jql = f'assignee = "{jira_integration.username}" AND status ~ "{found_status}"'
                params = {
                    'jql': custom_jql,
                    'maxResults': 50,
                    'fields': 'summary,status,priority,assignee'
                }
                response = jira_integration._make_request(
                    'GET',
                    f"{jira_integration.server_url}/rest/api/2/search",
                    params=params,
                    timeout=30
                )
                issues = response.json().get('issues', []) if response.status_code == 200 else []
                
                if issues:
                    result = f"📋 **Issues with Status containing '{found_status}'** ({len(issues)} issues):\n\n"
                    for i, issue in enumerate(issues, 1):
                        formatted = jira_integration.format_issue_data(issue)
                        issue_key = formatted['key']
                        summary = formatted['summary']
                        status = formatted['status']
                        issue_link = f"{jira_integration.server_url}/browse/{issue_key}"
                        styled_link = f'<a href="{issue_link}" style="color: #000000; font-weight: bold; text-decoration: none;" target="_blank">{issue_key}</a>'
                        
                        result += f"{i:2d}. {styled_link}\n\n"
                        result += f"&nbsp;&nbsp;&nbsp;&nbsp;📝 **{summary}**\n\n"
                        result += f"&nbsp;&nbsp;&nbsp;&nbsp;📈 Status: **{status}**\n\n"
                        result += f"&nbsp;&nbsp;&nbsp;&nbsp;🔗 Direct Link: <a href='{issue_link}' style='color: #333333; text-decoration: underline;' target='_blank'>{issue_link}</a>\n\n"
                        result += "---\n\n"
                    return result
                else:
                    return f"✅ No issues found with status containing '{found_status}'"
        
        # ON_QA specific searches (e.g., "my on_qa jira issues", "find issues with ON_QA")
        elif any(phrase in message_lower for phrase in ["on_qa", "on qa", "find issues with on_qa", "my on_qa", "search on_qa", "list on_qa"]):
            # Use the real Red Hat Jira ON_QA filter
            custom_jql = f'project = OCPBUGS AND status in (Post, ON_QA) AND (component in (kube-apiserver, openshift-apiserver, service-ca, kube-storage-version-migrator, "Documentation / API server") OR "QA Contact" in (wk2019, rhn-support-rgangwar, rhn-support-dpunia)) AND "QA Contact" = "{jira_integration.username}" AND resolution = Unresolved ORDER BY cf[12315948] ASC, status DESC, updated DESC, priority DESC'
            
            params = {
                'jql': custom_jql,
                'maxResults': 50,
                'fields': 'summary,status,priority,assignee,components,customfield_12315948'
            }
            response = jira_integration._make_request(
                'GET',
                f"{jira_integration.server_url}/rest/api/2/search",
                params=params,
                timeout=30
            )
            issues = response.json().get('issues', []) if response.status_code == 200 else []
            
            if issues:
                result = f"📋 **ON_QA Issues (QA Contact: You)** ({len(issues)} issues):\n\n"
                for i, issue in enumerate(issues, 1):
                    formatted = jira_integration.format_issue_data(issue)
                    issue_key = formatted['key']
                    summary = formatted['summary']
                    status = formatted['status']
                    priority = formatted['priority']
                    
                    # Get component information
                    components = issue.get('fields', {}).get('components', [])
                    component_names = [comp.get('name', '') for comp in components] if components else ['None']
                    component_str = ', '.join(component_names[:2])  # Show first 2 components
                    if len(component_names) > 2:
                        component_str += f" (+{len(component_names)-2} more)"
                    
                    issue_link = f"{jira_integration.server_url}/browse/{issue_key}"
                    styled_link = f'<a href="{issue_link}" style="color: #000000; font-weight: bold; text-decoration: none;" target="_blank">{issue_key}</a>'
                    
                    result += f"{i:2d}. {styled_link}\n\n"
                    result += f"&nbsp;&nbsp;&nbsp;&nbsp;📝 **{summary}**\n\n"
                    result += f"&nbsp;&nbsp;&nbsp;&nbsp;📈 Status: **{status}** | 🎯 Priority: **{priority}**\n\n"
                    result += f"&nbsp;&nbsp;&nbsp;&nbsp;🔧 Components: **{component_str}**\n\n"
                    result += f"&nbsp;&nbsp;&nbsp;&nbsp;🔗 Direct Link: <a href='{issue_link}' style='color: #333333; text-decoration: underline;' target='_blank'>{issue_link}</a>\n\n"
                    result += "---\n\n"
                return result
            else:
                return """📋 **ON_QA Issues**: ✅ No issues found where you are the QA Contact in ON_QA status.

**🎯 Search Criteria Used:**
• Project: **OCPBUGS** 
• Status: **Post** or **ON_QA**
• QA Contact: **rhn-support-rgangwar** (you)
• Components: **kube-apiserver, openshift-apiserver, service-ca, etc.**
• Resolution: **Unresolved**

**💡 This means**: All your OCPBUGS ON_QA work is currently clear! 🎉"""
        
        # General text searches for other terms
        elif any(phrase in message_lower for phrase in ["find issues with", "search issues", "issues with"]):
            # Extract search terms for general searches
            search_terms = []
            if "qa review" in message_lower:
                search_terms.append("QA Review")
            if "testing" in message_lower:
                search_terms.append("testing")
            
            if search_terms:
                search_text = " OR ".join(search_terms)
                # Search in summary, description
                custom_jql = f'assignee = "{jira_integration.username}" AND (summary ~ "{search_text}" OR description ~ "{search_text}")'
                params = {
                    'jql': custom_jql,
                    'maxResults': 50,
                    'fields': 'summary,status,priority,assignee'
                }
                response = jira_integration._make_request(
                    'GET',
                    f"{jira_integration.server_url}/rest/api/2/search",
                    params=params,
                    timeout=30
                )
                issues = response.json().get('issues', []) if response.status_code == 200 else []
                
                if issues:
                    result = f"📋 **Issues containing '{search_text}'** ({len(issues)} issues):\n\n"
                    for i, issue in enumerate(issues, 1):
                        formatted = jira_integration.format_issue_data(issue)
                        issue_key = formatted['key']
                        summary = formatted['summary']
                        status = formatted['status']
                        issue_link = f"{jira_integration.server_url}/browse/{issue_key}"
                        styled_link = f'<a href="{issue_link}" style="color: #000000; font-weight: bold; text-decoration: none;" target="_blank">{issue_key}</a>'
                        
                        result += f"{i:2d}. {styled_link}\n\n"
                        result += f"&nbsp;&nbsp;&nbsp;&nbsp;📝 **{summary}**\n\n"
                        result += f"&nbsp;&nbsp;&nbsp;&nbsp;📈 Status: **{status}**\n\n"
                        result += f"&nbsp;&nbsp;&nbsp;&nbsp;🔗 Direct Link: <a href='{issue_link}' style='color: #333333; text-decoration: underline;' target='_blank'>{issue_link}</a>\n\n"
                        result += "---\n\n"
                    return result
                else:
                    return f"✅ No issues found containing '{search_text}'"
        
        # Count/List issues commands
        elif any(phrase in message_lower for phrase in ["how many", "count", "number of", "show my", "list my", "show issues", "list issues", "my issues", "my jira issues", "my jira", "jira issues", "get my issues", "fetch my issues", "list all jiras", "all jiras"]):
            # Determine issue type based on keywords (more specific for QA Contact)
            if any(word in message_lower for word in ["qa contact", "qa contact issues"]) and not any(word in message_lower for word in ["status", "with", "find", "search"]):
                issue_type = "qa_contact"
                type_name = "QA Contact"
            elif any(word in message_lower for word in ["reported", "created", "reported by me"]):
                issue_type = "reported" 
                type_name = "Reported by Me"
            elif any(word in message_lower for word in ["all", "all my"]):
                issue_type = "all_mine"
                type_name = "All My Issues"
            else:
                issue_type = "assigned"
                type_name = "Assigned to Me"
            
            # Check if user wants only open issues
            exclude_closed = any(word in message_lower for word in ["open", "active", "pending", "not closed", "not done"])
            if exclude_closed:
                type_name = f"Open {type_name}"
            
            # Fetch issues
            issues = jira_integration.get_user_issues(jira_integration.username, issue_type, 100, exclude_closed)
            
            if issues:
                count = len(issues)
                
                # Determine if user wants just count or full list
                if any(word in message_lower for word in ["how many", "count", "number"]):
                    # Just return count
                    return f"📊 You have **{count}** issues in '{type_name}' category."
                else:
                    # Return list with details and styled clickable links
                    result = f"📋 **{type_name}** ({count} issues):\n\n"
                    
                    for i, issue in enumerate(issues, 1):  # Show all issues
                        formatted = jira_integration.format_issue_data(issue)
                        issue_key = formatted['key']
                        summary = formatted['summary']
                        status = formatted['status']
                        priority = formatted['priority']
                        
                        # Create styled HTML link with black color
                        issue_link = f"{jira_integration.server_url}/browse/{issue_key}"
                        styled_link = f'<a href="{issue_link}" style="color: #000000; font-weight: bold; text-decoration: none;" target="_blank">{issue_key}</a>'
                        
                        result += f"{i:2d}. {styled_link}\n\n"
                        result += f"&nbsp;&nbsp;&nbsp;&nbsp;📝 **{summary}**\n\n"
                        result += f"&nbsp;&nbsp;&nbsp;&nbsp;📈 Status: **{status}** | 🎯 Priority: **{priority}**\n\n"
                        result += f"&nbsp;&nbsp;&nbsp;&nbsp;🔗 Direct Link: <a href='{issue_link}' style='color: #333333; text-decoration: underline;' target='_blank'>{issue_link}</a>\n\n"
                        result += "---\n\n"
                    
                    return result
            else:
                # Special message for QA Contact queries
                if issue_type == "qa_contact":
                    return """📋 **QA Contact Issues**: ✅ No issues found where you are the QA Contact.

**ℹ️ Note**: Red Hat Jira typically manages QA workflow through **statuses** and **labels** rather than a QA Contact field.

**🔍 Try these alternatives:**
• `"my issues with status QA"` - Find issues in QA status
• `"find issues with ON_QA"` - Search for ON_QA labels  
• `"search issues QA Review"` - Look for QA Review status
• `"my issues status:QA"` - JQL-style status search

**📊 Your current workload**: You have **25 open assigned issues** to work on."""
                else:
                    return f"✅ No issues found in '{type_name}' category."
        
        # Add comment commands
        elif any(phrase in message_lower for phrase in ["add comment", "comment on", "add note"]):
            if issue_keys:
                issue_key = issue_keys[0]
                # Extract comment text
                comment_text = "Work completed via AI assistant"
                if "saying" in message_lower:
                    comment_start = message_lower.find("saying") + 6
                    comment_text = user_message[comment_start:].strip().strip('"\'')
                elif "comment:" in message_lower:
                    comment_start = message_lower.find("comment:") + 8
                    comment_text = user_message[comment_start:].strip().strip('"\'')
                
                success = jira_integration.add_comment_to_issue(issue_key, comment_text)
                if success:
                    return f"✅ Comment added to {issue_key}: '{comment_text}'"
                else:
                    return f"❌ Failed to add comment to {issue_key}"
            else:
                return "Please specify the issue key (e.g., PROJ-123) to add a comment to."
        
        # Status update commands
        elif any(phrase in message_lower for phrase in ["mark as done", "mark completed", "set to done", "complete", "finish"]):
            if issue_keys:
                issue_key = issue_keys[0]
                # Get available transitions
                transitions = jira_integration.get_issue_transitions(issue_key)
                
                # Find "Done" or similar transition
                done_transition = None
                for transition in transitions:
                    transition_name = transition['name'].lower()
                    if any(done_word in transition_name for done_word in ['done', 'complete', 'close', 'resolve']):
                        done_transition = transition
                        break
                
                if done_transition:
                    comment = f"Issue completed via AI assistant on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    success = jira_integration.transition_issue(issue_key, done_transition['id'], comment)
                    if success:
                        return f"✅ {issue_key} marked as {done_transition['name']} with completion comment"
                    else:
                        return f"❌ Failed to update status of {issue_key}"
                else:
                    available_transitions = [t['name'] for t in transitions]
                    return f"❌ No 'Done' transition found for {issue_key}. Available transitions: {', '.join(available_transitions)}"
            else:
                return "Please specify the issue key (e.g., PROJ-123) to mark as completed."
        
        # Search commands
        elif any(phrase in message_lower for phrase in ["find issues", "search issues", "my issues with"]):
            search_terms = user_message.split()
            search_text = " ".join([term for term in search_terms if not term.lower() in ["find", "search", "issues", "my", "with"]])
            
            if search_text:
                issues = jira_integration.search_issues_by_text(search_text, jira_integration.username)
                if issues:
                    result = f"Found {len(issues)} issues matching '{search_text}':\n"
                    for issue in issues[:5]:  # Show top 5
                        formatted = jira_integration.format_issue_data(issue)
                        result += f"- {formatted['key']}: {formatted['summary']} ({formatted['status']})\n"
                    return result
                else:
                    return f"No issues found matching '{search_text}'"
            else:
                return "Please specify what to search for in your issues."
        
        # General issue info commands
        elif issue_keys:
            issue_key = issue_keys[0]
            # This would need to fetch specific issue details
            return f"I found issue {issue_key} in your message. What would you like to do with it? I can add comments, update status, or provide details."
        
        else:
            return """I can help you with Jira tasks! Here are some examples:
            
• "Add comment to PROJ-123 saying work is done"
• "Mark PROJ-123 as completed"  
• "Find issues with authentication"
• "Comment on PROJ-123: Ready for testing"
• "Set PROJ-123 to done"

Just mention the issue key and what you want to do!"""
        
        # Default fallback if no command matches
        return "I can help you with Jira tasks! Please try commands like 'my jira issues', 'find issues with QA', or 'add comment to PROJ-123 saying work done'."
    
    except Exception as e:
        return f"Error processing Jira command: {str(e)}"

def create_jira_tab():
    """Create Streamlit tab for Jira integration"""
    st.header("🎫 Jira Integration")
    
    # Configuration section
    st.subheader("Configuration")
    
    # Load saved configuration first
    config_file = "jira_config.json"
    saved_config = {}
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                saved_config = json.load(f)
        except:
            pass
    
    # Detect server type and show appropriate guidance
    server_url = saved_config.get('server', '')
    is_redhat = 'redhat.com' in server_url or 'issues.redhat.com' in server_url
    is_atlassian_cloud = 'atlassian.net' in server_url
    
    if is_redhat:
        st.info("""
        🔴 **Red Hat Jira Instance Detected:**
        
        ✅ **Authentication Method**: **Personal Access Token (Bearer)** 
        • **Server URL**: `https://issues.redhat.com`
        • **Username**: Your **Red Hat username** (e.g., `rhn-support-rgangwar`)
        • **Token**: Your **Personal Access Token** (get from Profile → Personal Access Tokens)
        
        🎉 **Good News**: Red Hat Jira supports Bearer token authentication with PATs!
        Get your token from: https://issues.redhat.com/secure/ViewProfile.jspa → Personal Access Tokens
        """)
    elif is_atlassian_cloud:
        st.info("""
        🔐 **Atlassian Cloud SSO Setup:**
        
        • **Server URL**: `https://yourcompany.atlassian.net` (replace 'yourcompany')
        • **Username**: Your **email address** (e.g., `you@company.com`)  
        • **API Token**: Get from [Atlassian Account](https://id.atlassian.com/manage-profile/security/api-tokens)
        
        ⚠️ **Important**: Use your email address as username, NOT your display name!
        """)
    else:
        st.info("""
        🔧 **Jira Configuration:**
        
        • **For Red Hat Jira**: Use username + password
        • **For Atlassian Cloud**: Use email + API token
        • **For Self-hosted**: Username + password (usually)
        
        Enter your server URL first to get specific guidance.
        """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Default server URL based on common patterns
        default_server = 'https://issues.redhat.com' if is_redhat else 'https://your-company.atlassian.net'
        
        jira_server = st.text_input(
            "Jira Server URL",
            value=saved_config.get('server', default_server),
            help="Red Hat users: https://issues.redhat.com | Atlassian Cloud: https://yourcompany.atlassian.net"
        )
        
        # Update server type detection when user changes URL
        is_redhat = jira_server and ('redhat.com' in jira_server or 'issues.redhat.com' in jira_server)
        is_atlassian_cloud = jira_server and 'atlassian.net' in jira_server
        
        if is_redhat:
            jira_username = st.text_input(
                "Red Hat Username",
                value=saved_config.get('username', ''),
                help="Your Red Hat username (e.g., rsmith, not email)",
                placeholder="rsmith"
            )
        elif is_atlassian_cloud:
            jira_username = st.text_input(
                "Email Address",
                value=saved_config.get('username', ''),
                help="For Atlassian Cloud: Use your EMAIL ADDRESS (e.g., you@company.com)",
                placeholder="you@company.com"
            )
        else:
            jira_username = st.text_input(
                "Username/Email",
                value=saved_config.get('username', ''),
                help="Username for self-hosted Jira or email for cloud",
                placeholder="username or email"
            )
        
    with col2:
        # Update server type detection for password field
        is_redhat_pwd = jira_server and ('redhat.com' in jira_server or 'issues.redhat.com' in jira_server)
        is_atlassian_cloud_pwd = jira_server and 'atlassian.net' in jira_server
        
        if is_redhat_pwd:
            jira_token = st.text_input(
                "Personal Access Token",
                type="password",
                value=saved_config.get('token', '') if saved_config.get('token') else '',
                help="Your Red Hat Personal Access Token (get from Profile → Personal Access Tokens)",
                placeholder="Your Personal Access Token (NOT password)"
            )
        elif is_atlassian_cloud_pwd:
            jira_token = st.text_input(
                "API Token",
                type="password",
                value=saved_config.get('token', '') if saved_config.get('token') else '',
                help="Get from https://id.atlassian.com/manage-profile/security/api-tokens",
                placeholder="Your API token (required for Atlassian Cloud)"
            )
        else:
            jira_token = st.text_input(
                "Password/API Token",
                type="password",
                value=saved_config.get('token', '') if saved_config.get('token') else '',
                help="Password for self-hosted Jira or API token for cloud",
                placeholder="Password or API token"
            )
        
        max_issues = st.number_input(
            "Max Issues to Fetch",
            min_value=10,
            max_value=500,
            value=100,
            help="Maximum number of issues to fetch"
        )
    
    # Save configuration
    if st.button("💾 Save Configuration"):
        config = {
            'server': jira_server,
            'username': jira_username,
            'token': jira_token
        }
        with open(config_file, 'w') as f:
            json.dump(config, f)
        st.success("Configuration saved!")
    
    # Test connection
    col_test1, col_test2 = st.columns(2)
    
    with col_test1:
        if st.button("🔍 Test Connection"):
            if jira_server and jira_username and jira_token:
                # Check if this looks like a PAT (longer than typical password)
                auth_method = "pat_bearer" if len(jira_token) > 20 else "basic"
                jira = JiraIntegration(jira_server, jira_username, jira_token, auth_method)
                if jira.test_connection():
                    st.success(f"✅ Connection successful using {auth_method}!")
                else:
                    st.error("❌ Connection failed!")
            else:
                st.error("Please fill in all configuration fields")
    
    with col_test2:
        if st.button("🔧 Debug Connection"):
            if jira_server and jira_username and jira_token:
                # Auto-detect auth method
                auth_method = "pat_bearer" if len(jira_token) > 20 else "basic"
                jira = JiraIntegration(jira_server, jira_username, jira_token, auth_method)
                
                st.write(f"**🔍 Raw Connection Test Results (using {auth_method}):**")
                debug_result = jira.test_raw_connection()
                
                if 'error' in debug_result:
                    st.error(f"Error: {debug_result['error']}")
                else:
                    st.write(f"**Status Code:** {debug_result['status_code']}")
                    st.write(f"**URL:** {debug_result['url']}")
                    st.write(f"**Auth Method:** {auth_method}")
                    
                    # Show decoded username for verification
                    if 'decoded_username' in debug_result:
                        st.write(f"**Decoded Username:** {debug_result['decoded_username']}")
                    
                    # Show request headers (but hide full auth)
                    req_headers = debug_result['request_headers'].copy()
                    if 'Authorization' in req_headers:
                        auth_header = req_headers['Authorization']
                        req_headers['Authorization'] = f"{auth_header[:15]}...{auth_header[-10:]}"
                    st.write(f"**Request Headers:** {req_headers}")
                    
                    st.write(f"**Response Headers:** {debug_result['headers']}")
                    
                    if debug_result['status_code'] == 200:
                        st.success("🎉 **Connection Working!** You can now fetch your issues.")
                    else:
                        # Check for OAuth requirement
                        auth_header = debug_result['headers'].get('WWW-Authenticate', '')
                        if 'oauth' in auth_header.lower():
                            st.warning("🚨 **OAuth Required**: This Jira instance requires OAuth authentication, not basic auth!")
                            st.info("💡 **Try Personal Access Token**: Red Hat Jira may support Personal Access Tokens instead of passwords.")
                    
                    st.text_area("**Response Body:**", debug_result['text'], height=200)
            else:
                st.error("Please fill in all configuration fields")
    
    # New section for Personal Access Token testing
    st.subheader("🔑 Alternative: Personal Access Token")
    st.info("""
    **If basic authentication fails**, Red Hat Jira might require Personal Access Tokens:
    
    1. **Get PAT from**: https://issues.redhat.com/secure/ViewProfile.jspa → Personal Access Tokens
    2. **Create new token** with appropriate permissions
    3. **Test token below** using Bearer authentication
    """)
    
    col_pat1, col_pat2 = st.columns(2)
    
    with col_pat1:
        personal_access_token = st.text_input(
            "Personal Access Token",
            type="password",
            help="Get from your Red Hat Jira profile → Personal Access Tokens"
        )
    
    with col_pat2:
        if st.button("🔑 Test PAT"):
            if jira_server and jira_username and personal_access_token:
                # Create jira object with username for PAT testing
                jira = JiraIntegration(jira_server, jira_username, personal_access_token)
                
                st.write("**🔍 Personal Access Token Test (Multiple Methods):**")
                pat_results = jira.test_pat_authentication(personal_access_token)
                
                success_found = False
                successful_method = None
                
                for method_name, result in pat_results.items():
                    if 'error' in result:
                        st.error(f"**{method_name.replace('_', ' ').title()}**: Error - {result['error']}")
                    else:
                        status_code = result['status_code']
                        method_display = result['method']
                        
                        if result.get('success', False):
                            st.success(f"✅ **{method_display}**: SUCCESS (Status: {status_code})")
                            success_found = True
                            successful_method = method_display
                            
                            try:
                                user_data = json.loads(result['text'])
                                st.write(f"   👤 **Logged in as:** {user_data.get('displayName', 'Unknown')}")
                                st.write(f"   📧 **Email:** {user_data.get('emailAddress', 'Unknown')}")
                            except:
                                pass
                        else:
                            st.error(f"❌ **{method_display}**: Failed (Status: {status_code})")
                            
                            # Show response for debugging
                            with st.expander(f"View {method_display} Response"):
                                st.text_area(f"{method_display} Response:", result['text'], height=100, key=f"response_{method_name}")
                
                if success_found:
                    st.info(f"💡 **Recommendation**: Use **{successful_method}** for your Jira integration!")
                    
                    # Update session state with working method
                    st.session_state.jira_auth_method = successful_method
                    st.session_state.jira_pat = personal_access_token
                else:
                    st.warning("⚠️ None of the PAT authentication methods worked. Check your token and permissions.")
            else:
                st.error("Please enter server URL, username, and Personal Access Token")
    
    st.divider()
    
    # Fetch and analyze issues with different options
    st.subheader("📋 Fetch Your Issues")
    
    # Issue type selection
    col1, col2 = st.columns(2)
    with col1:
        issue_type = st.selectbox(
            "Select Issue Type",
            options=[
                ("assigned", "🎯 Assigned to Me"),
                ("qa_contact", "🔍 QA Contact"),
                ("reported", "📝 Reported by Me"),
                ("all_mine", "📊 All My Issues")
            ],
            format_func=lambda x: x[1]
        )
    
    with col2:
        if st.button("🔄 Fetch Issues"):
            if not all([jira_server, jira_username, jira_token]):
                st.error("Please configure Jira connection first")
            else:
                # Ensure all values are strings
                server_str = str(jira_server) if jira_server else ""
                username_str = str(jira_username) if jira_username else ""
                token_str = str(jira_token) if jira_token else ""
                
                # Auto-detect auth method based on token length
                auth_method = "pat_bearer" if len(token_str) > 20 else "basic"
                
                with st.spinner(f"Fetching {issue_type[1].lower()} using {auth_method}..."):
                    jira = JiraIntegration(server_str, username_str, token_str, auth_method)
                    
                    # Fetch issues based on type
                    issues = jira.get_user_issues(username_str, issue_type[0], max_issues)
                    
                    if issues:
                        st.success(f"✅ Fetched {len(issues)} issues")
                        
                        # Store in session state
                        st.session_state.jira_issues = issues
                        st.session_state.jira_integration = jira
                        st.session_state.jira_issue_type = issue_type[0]
                        
                        # Display summary
                        summary = jira.get_work_summary(issues, issue_type[0])
                        st.markdown(summary)
                        
                        # Show recent issues
                        st.subheader("🔍 Recent Issues")
                        for issue in issues[:5]:
                            formatted = jira.format_issue_data(issue)
                            with st.expander(f"{formatted['key']}: {formatted['summary']}"):
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.write(f"**Status**: {formatted['status']}")
                                    st.write(f"**Priority**: {formatted['priority']}")
                                    st.write(f"**Assignee**: {formatted['assignee']}")
                                with col_b:
                                    st.write(f"**Reporter**: {formatted['reporter']}")
                                    st.write(f"**Updated**: {formatted['updated']}")
                                    st.write(f"**URL**: {formatted['url']}")
                                
                                if formatted['description']:
                                    st.write(f"**Description**: {formatted['description'][:200]}...")
                                
                                # Quick action buttons
                                col_btn1, col_btn2 = st.columns(2)
                                with col_btn1:
                                    if st.button(f"💬 Add Comment", key=f"comment_{formatted['key']}"):
                                        comment_text = st.text_input(f"Comment for {formatted['key']}:", key=f"comment_input_{formatted['key']}")
                                        if comment_text:
                                            success = jira.add_comment_to_issue(formatted['key'], comment_text)
                                            if success:
                                                st.success(f"Comment added to {formatted['key']}")
                                            else:
                                                st.error("Failed to add comment")
                                
                                with col_btn2:
                                    if st.button(f"✅ Mark Done", key=f"done_{formatted['key']}"):
                                        transitions = jira.get_issue_transitions(formatted['key'])
                                        done_transition = None
                                        for transition in transitions:
                                            if any(word in transition['name'].lower() for word in ['done', 'complete', 'close']):
                                                done_transition = transition
                                                break
                                        
                                        if done_transition:
                                            comment = f"Completed via AI Assistant on {datetime.now().strftime('%Y-%m-%d')}"
                                            success = jira.transition_issue(formatted['key'], done_transition['id'], comment)
                                            if success:
                                                st.success(f"{formatted['key']} marked as {done_transition['name']}")
                                                st.rerun()
                                            else:
                                                st.error("Failed to update status")
                                        else:
                                            st.warning(f"No 'Done' transition available for {formatted['key']}")
                    else:
                        st.warning("No issues found")
    
    st.divider()
    
    # Generate training data
    st.subheader("🤖 Generate Training Data")
    
    if st.session_state.get('jira_issues'):
        col1, col2 = st.columns(2)
        
        with col1:
            include_actions = st.checkbox("Include Action Training", value=True, 
                                        help="Include training for commenting and status updates")
        
        with col2:
            if st.button("📚 Generate Training Data from Issues"):
                with st.spinner("Generating training data..."):
                    jira = st.session_state.jira_integration
                    training_data = jira.generate_training_data(st.session_state.jira_issues, include_actions)
                    
                    # Save training data
                    filename = jira.save_training_data(training_data)
                    
                    st.success(f"✅ Generated {len(training_data)} training examples")
                    st.info(f"📁 Saved to: {filename}")
                    
                    # Add to session training data
                    if 'training_data' not in st.session_state:
                        st.session_state.training_data = []
                    st.session_state.training_data.extend(training_data)
                    
                    # Show preview
                    st.subheader("📋 Training Data Preview")
                    for i, item in enumerate(training_data[:3]):
                        with st.expander(f"Example {i+1}"):
                            st.write(f"**Question**: {item['instruction']}")
                            st.write(f"**Answer**: {item['output'][:200]}...")
    
    else:
        st.info("👆 Fetch your issues first to generate training data")
    
    st.divider()
    
    # Quick Actions
    st.subheader("⚡ Quick Actions")
    
    if st.session_state.get('jira_integration'):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Add Comment to Issue:**")
            issue_key_comment = st.text_input("Issue Key:", placeholder="PROJ-123")
            comment_text = st.text_area("Comment:")
            
            if st.button("💬 Add Comment"):
                if issue_key_comment and comment_text:
                    jira = st.session_state.jira_integration
                    success = jira.add_comment_to_issue(issue_key_comment, comment_text)
                    if success:
                        st.success(f"✅ Comment added to {issue_key_comment}")
                    else:
                        st.error("❌ Failed to add comment")
                else:
                    st.warning("Please enter both issue key and comment")
        
        with col2:
            st.write("**Search Issues:**")
            search_query = st.text_input("Search Term:", placeholder="authentication, bug, etc.")
            
            if st.button("🔍 Search"):
                if search_query:
                    jira = st.session_state.jira_integration
                    results = jira.search_issues_by_text(search_query, jira.username)
                    if results:
                        st.write(f"Found {len(results)} issues:")
                        for issue in results[:5]:
                            formatted = jira.format_issue_data(issue)
                            st.write(f"• {formatted['key']}: {formatted['summary']}")
                    else:
                        st.write("No issues found")
                else:
                    st.warning("Please enter a search term")
    
    # Help section
    st.divider()
    st.subheader("ℹ️ Help")
    
    st.markdown("""
    **Chatbot Jira Commands:**
    
    Once you've fetched your issues, you can use these natural language commands in the chatbot:
    
    • `"Add comment to PROJ-123 saying work is completed"`
    • `"Mark PROJ-123 as completed"`
    • `"Find issues with authentication"`
    • `"Comment on PROJ-123: Ready for testing"`
    • `"Set PROJ-123 to completed"`
    
    **Issue Types:**
    - **Assigned to Me**: Issues currently assigned to you
    - **QA Contact**: Issues where you're the QA contact
    - **Reported by Me**: Issues you created/reported
    - **All My Issues**: All issues where you're involved
    
    **Setup Instructions:**
    
    **For Red Hat Jira (https://issues.redhat.com):**
    1. **Server URL**: `https://issues.redhat.com`
    2. **Username**: Your **Red Hat username** (e.g., `rsmith`)
    3. **Password**: Your **Red Hat password** (password authentication works!)
    4. Test connection and fetch your issues
    5. Generate training data to teach the AI about your work
    6. Use natural language commands in the chatbot to manage issues
    
    **For Atlassian Cloud SSO:**
    1. **Server URL**: Your Jira instance URL (e.g., `https://company.atlassian.net`)
    2. **Username**: Use your **email address** (not username)
    3. **API Token**: Get from [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
       - Go to Account Settings → Security → API tokens
       - Create API token → Copy the token
       - Paste token in the API Token field above
    4. Test connection and fetch your issues
    5. Generate training data to teach the AI about your work
    6. Use natural language commands in the chatbot to manage issues
    
    **For Self-hosted Jira:**
    1. **Server URL**: Your Jira server URL
    2. **Username**: Your Jira username
    3. **Password**: Your password (usually works for self-hosted)
    
    **Troubleshooting SSO Issues:**
    - ✅ **Use email address** as username, not display name
    - ✅ **Generate new API token** from Atlassian Account Settings
    - ✅ **Check server URL** format: `https://yourcompany.atlassian.net` (no trailing slash)
    - ✅ **Verify permissions** - ensure you can access Jira normally
    - ✅ **Try different custom fields** for QA Contact (varies by organization)
    
    **Common SSO Authentication Errors:**
    - `401 Unauthorized`: Wrong email/token combination
    - `403 Forbidden`: Insufficient permissions
    - `404 Not Found`: Wrong server URL
    
    **API Token Security:**
    - 🔒 Tokens are stored locally in `jira_config.json`
    - 🔄 Regenerate tokens periodically for security
    - 🚫 Never share your API tokens
    """)
    
    # Additional SSO-specific help
    st.subheader("🔐 SSO-Specific Notes")
    st.info("""
    **For SSO-enabled Jira (Atlassian Cloud):**
    
    • **Always use your email address** as the username
    • **API tokens are required** - passwords won't work
    • **Token permissions** inherit from your Jira account permissions
    • **Organization policies** may restrict API access - contact your admin if needed
    
    **Getting your API token:**
    1. Visit: https://id.atlassian.com/manage-profile/security/api-tokens
    2. Click "Create API token"
    3. Give it a descriptive name (e.g., "AI Assistant")
    4. Copy the token immediately (you can't see it again)
    5. Paste it in the API Token field above
    """)
    
    st.subheader("🔑 Authentication Options")
    st.markdown("""
    **Authentication by Jira Type:**
    
    1. **✅ Red Hat Jira (https://issues.redhat.com)**
       - **Username + Password** authentication supported
       - Use your Red Hat username (not email)
       - Use your regular Red Hat password
       - **No API token needed!** 🎉
    
    2. **✅ Atlassian Cloud (company.atlassian.net)**
       - **Email + API Token** required for SSO
       - Passwords disabled for security reasons
       - Get API token from: https://id.atlassian.com/manage-profile/security/api-tokens
    
    3. **✅ Self-hosted Jira**
       - **Username + Password** usually works
       - Some instances may require API tokens
       - Check with your administrator
    
    4. **✅ Personal Access Tokens (Some instances)**
       - Available in newer Jira Data Center versions
       - More granular permissions than passwords
       - Check with your admin if available
    
    **Why Different Authentication Methods?**
    - 🔒 **Security policies** vary by organization
    - 🌐 **Cloud vs self-hosted** have different requirements
    - 🛡️ **Red Hat allows passwords** for internal tools
    - 🏢 **Enterprise instances** may have custom auth
    """)
    
    st.subheader("🔍 Testing Your SSO Connection")
    st.markdown("""
    **If connection fails:**
    1. Double-check your **email address** (not display name)
    2. **Regenerate API token** from Atlassian Account Settings
    3. **Verify server URL** format: `https://yourcompany.atlassian.net`
    4. **Check browser access** - can you log into Jira normally?
    5. **Contact IT admin** if API access is restricted
    """)
    
    # Session-based alternative information
    st.subheader("🔧 Alternative: Manual Workflow")
    st.info("""
    **If you can't use API tokens**, you can still benefit from AI assistance:
    
    1. **Manual Issue Export**: Export your issues from Jira as CSV/Excel
    2. **Upload to AI Assistant**: Use the document upload feature
    3. **Generate Training Data**: Create training data from your exported issues
    4. **AI-Powered Analysis**: Get insights about your work patterns
    5. **Manual Updates**: Copy AI-generated comments back to Jira manually
    
    While not as automated, this approach still provides valuable AI assistance!
    """) 
import logging
import requests
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from requests.auth import HTTPBasicAuth
import os

from app.core.config import settings

logger = logging.getLogger(__name__)

class JiraService:
    def __init__(self):
        """Initialize Jira service with configuration from settings"""
        self.load_credentials()
        self.initialize_connection()
    
    def load_credentials(self) -> None:
        """Load Jira credentials from file or environment"""
        creds_file = os.path.join(settings.credentials_dir, "jira_credentials.json")
        
        # Try to load from credentials file first
        if os.path.exists(creds_file):
            try:
                with open(creds_file, 'r') as f:
                    creds = json.load(f)
                self.server_url = creds.get('server_url', settings.jira_server_url)
                self.username = creds.get('username', settings.jira_username)
                self.api_token = creds.get('api_token', settings.jira_api_token)
                self.auth_method = creds.get('auth_method', settings.jira_auth_method)
                logger.info("Loaded Jira credentials from file")
                return
            except Exception as e:
                logger.error(f"Error loading Jira credentials from file: {e}")
        
        # Fall back to settings
        self.server_url = settings.jira_server_url.rstrip('/')
        self.username = settings.jira_username
        self.api_token = settings.jira_api_token
        self.auth_method = settings.jira_auth_method
        logger.info("Using Jira credentials from settings")
    
    def save_credentials(self, server_url: str, username: str, api_token: str, auth_method: str = "basic") -> bool:
        """Save Jira credentials to file"""
        try:
            creds_file = os.path.join(settings.credentials_dir, "jira_credentials.json")
            creds = {
                'server_url': server_url.rstrip('/'),
                'username': username,
                'api_token': api_token,
                'auth_method': auth_method
            }
            
            # Create credentials directory if it doesn't exist
            os.makedirs(settings.credentials_dir, exist_ok=True)
            
            # Save credentials
            with open(creds_file, 'w') as f:
                json.dump(creds, f, indent=2)
            
            # Update current instance
            self.server_url = server_url.rstrip('/')
            self.username = username
            self.api_token = api_token
            self.auth_method = auth_method
            
            # Reinitialize connection with new credentials
            self.initialize_connection()
            
            logger.info("Saved Jira credentials to file")
            return True
            
        except Exception as e:
            logger.error(f"Error saving Jira credentials: {e}")
            return False
    
    def initialize_connection(self) -> None:
        """Initialize Jira connection with current credentials"""
        # Set up authentication based on method
        if self.auth_method == "basic":
            self.auth = HTTPBasicAuth(self.username, self.api_token)
            self.headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        elif self.auth_method in ["pat_bearer", "bearer"]:
            # Bearer token with PAT
            self.auth = None
            self.headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        else:
            # Default to basic auth
            self.auth = HTTPBasicAuth(self.username, self.api_token)
            self.headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
    
    def test_connection_details(self) -> Dict[str, Any]:
        """Test Jira connection and return detailed results"""
        try:
            url = f"{self.server_url}/rest/api/2/myself"
            
            # Test the connection
            response = self._make_request('GET', url, timeout=10)
            
            result = {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'server_url': self.server_url,
                'username': self.username,
                'auth_method': self.auth_method,
                'headers': {k: v for k, v in self.headers.items() if k != 'Authorization'},
                'error': None
            }
            
            if response.status_code == 200:
                user_data = response.json()
                result.update({
                    'display_name': user_data.get('displayName'),
                    'email': user_data.get('emailAddress'),
                    'active': user_data.get('active', False),
                    'timezone': user_data.get('timeZone')
                })
            elif response.status_code == 401:
                result['error'] = "Authentication failed. Check your credentials."
            elif response.status_code == 403:
                result['error'] = "Permission denied. Check your access rights."
            elif response.status_code == 404:
                result['error'] = "Server not found. Check your server URL."
            else:
                result['error'] = f"Unexpected error: {response.text}"
            
            return result
            
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': "Connection failed. Check server URL and network connection.",
                'server_url': self.server_url,
                'username': self.username,
                'auth_method': self.auth_method
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'server_url': self.server_url,
                'username': self.username,
                'auth_method': self.auth_method
            }
    
    def test_connection(self) -> bool:
        """Simple test of Jira connection"""
        try:
            url = f"{self.server_url}/rest/api/2/myself"
            response = self._make_request('GET', url, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"Connected to Jira as {user_data.get('displayName', 'Unknown User')}")
                return True
            else:
                logger.error(f"Jira connection failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error testing Jira connection: {e}")
            return False
    
    def _make_request(self, method: str, url: str, **kwargs):
        """Make request with appropriate authentication"""
        if self.auth:
            kwargs['auth'] = self.auth
        kwargs['headers'] = self.headers
        
        return requests.request(method, url, **kwargs)
    
    def get_issue(self, issue_key: str) -> Optional[Dict]:
        """Get a single Jira issue by key with comments"""
        try:
            response = self._make_request(
                'GET',
                f"{self.server_url}/rest/api/2/issue/{issue_key}?expand=comments",
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get issue {issue_key}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting issue {issue_key}: {e}")
            return None
    
    def add_comment(self, issue_key: str, comment_text: str) -> bool:
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
                logger.info(f"Added comment to {issue_key}")
                return True
            else:
                logger.error(f"Failed to add comment to {issue_key}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding comment to {issue_key}: {e}")
            return False

    def get_comments(self, issue_key: str) -> List[Dict]:
        """Get comments for a Jira issue"""
        try:
            response = self._make_request(
                'GET',
                f"{self.server_url}/rest/api/2/issue/{issue_key}/comment",
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json().get('comments', [])
            else:
                logger.error(f"Failed to get comments for {issue_key}: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting comments for {issue_key}: {e}")
            return []

    def create_issue(self, project: str, summary: str, description: str, issue_type: str = "Task") -> Dict:
        """Create a new Jira issue"""
        try:
            issue_data = {
                "fields": {
                    "project": {
                        "key": project
                    },
                    "summary": summary,
                    "description": description,
                    "issuetype": {
                        "name": issue_type
                    }
                }
            }
            
            response = self._make_request(
                'POST',
                f"{self.server_url}/rest/api/2/issue",
                json=issue_data,
                timeout=15
            )
            
            if response.status_code == 201:
                created_issue = response.json()
                logger.info(f"Created issue {created_issue.get('key')}")
                return created_issue
            else:
                logger.error(f"Failed to create issue: {response.status_code} - {response.text}")
                raise Exception(f"Failed to create issue: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error creating issue: {e}")
            raise e

    def update_issue(self, issue_key: str, **fields) -> Dict:
        """Update a Jira issue with new field values"""
        try:
            update_data = {
                "fields": {}
            }
            
            # Handle status updates
            if "status" in fields:
                # Get available transitions
                transitions = self.get_transitions(issue_key)
                target_status = fields["status"]
                
                # Find the transition ID for the target status
                transition_id = None
                for transition in transitions:
                    if transition.get("to", {}).get("name") == target_status:
                        transition_id = transition.get("id")
                        break
                
                if transition_id:
                    # Use transition API to change status
                    self.transition_issue(issue_key, transition_id)
                else:
                    logger.warning(f"No transition found for status '{target_status}'")
            
            # Handle other field updates
            for field, value in fields.items():
                if field != "status":  # Status is handled separately
                    update_data["fields"][field] = value
            
            # Only make update request if there are other fields to update
            if len(update_data["fields"]) > 0:
                response = self._make_request(
                    'PUT',
                    f"{self.server_url}/rest/api/2/issue/{issue_key}",
                    json=update_data,
                    timeout=15
                )
                
                if response.status_code != 204:
                    logger.error(f"Failed to update issue {issue_key}: {response.status_code}")
                    raise Exception(f"Failed to update issue: {response.status_code}")
            
            # Return the updated issue
            return self.get_issue(issue_key)
                
        except Exception as e:
            logger.error(f"Error updating issue {issue_key}: {e}")
            raise e
    
    def get_transitions(self, issue_key: str) -> List[Dict]:
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
                logger.error(f"Failed to get transitions for {issue_key}: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting transitions for {issue_key}: {e}")
            return []
    
    def get_projects(self) -> List[Dict]:
        """Get all projects from Jira"""
        try:
            response = self._make_request(
                'GET',
                f"{self.server_url}/rest/api/2/project",
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get projects: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting projects: {e}")
            return []
    
    def get_project_statuses(self, project_key: str) -> List[Dict]:
        """Get all statuses for a specific project"""
        try:
            response = self._make_request(
                'GET',
                f"{self.server_url}/rest/api/2/project/{project_key}/statuses",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                statuses = []
                for issue_type in data:
                    for status in issue_type.get('statuses', []):
                        statuses.append({
                            'id': status.get('id'),
                            'name': status.get('name'),
                            'description': status.get('description'),
                            'category': status.get('statusCategory', {}).get('name', '')
                        })
                return statuses
            else:
                logger.error(f"Failed to get statuses for project {project_key}: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting statuses for project {project_key}: {e}")
            return []
    
    def get_all_statuses(self) -> List[Dict]:
        """Get all statuses across all projects"""
        try:
            response = self._make_request(
                'GET',
                f"{self.server_url}/rest/api/2/status",
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get all statuses: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting all statuses: {e}")
            return []
    
    def get_issue_types(self) -> List[Dict]:
        """Get all issue types from Jira"""
        try:
            response = self._make_request(
                'GET',
                f"{self.server_url}/rest/api/2/issuetype",
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get issue types: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting issue types: {e}")
            return []
    
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
                logger.info(f"Transitioned {issue_key} with ID {transition_id}")
                return True
            else:
                logger.error(f"Failed to transition {issue_key}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error transitioning {issue_key}: {e}")
            return False

    def assign_issue(self, issue_key: str, assignee: str) -> bool:
        """
        Assign an issue to a user
        
        Args:
            issue_key: The issue key (e.g., "PROJ-123")
            assignee: The username or email of the assignee
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            url = f"{self.server_url}/rest/api/2/issue/{issue_key}/assignee"
            
            # Prepare assignment data
            assignment_data = {
                "name": assignee
            }
            
            # Make the assignment request
            response = self._make_request("PUT", url, json=assignment_data, timeout=15)
            if response and response.status_code == 204:
                logger.info(f"Successfully assigned {issue_key} to {assignee}")
                return True
            else:
                logger.error(f"Failed to assign {issue_key} to {assignee}: {response.status_code if response else 'No response'}")
                return False
                
        except Exception as e:
            logger.error(f"Error assigning issue {issue_key} to {assignee}: {e}")
            return False
    
    def search_issues(self, jql: str, max_results: int = 50) -> List[Dict]:
        """Search issues using JQL"""
        try:
            params = {
                'jql': jql,
                'maxResults': max_results,
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
                logger.error(f"Failed to search issues: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching issues with JQL '{jql}': {e}")
            return []
    
    def get_my_issues(self, issue_type: str = "assigned", max_results: int = 100, status_filter: str = None, additional_filters: Dict = None) -> List[Dict]:
        """Get issues based on different criteria with support for combined queries"""
        try:
            # Different JQL queries based on issue type - using only standard Jira fields
            if issue_type == "assigned":
                jql = f'assignee = "{self.username}"'
            elif issue_type == "qa_contact":
                # Use custom JQL for QA Contact
                jql = f'"QA Contact" = "{self.username}" AND resolution = Unresolved ORDER BY cf[12315948] ASC, status DESC, updated DESC, priority DESC'
            elif issue_type == "reported":
                jql = f'reporter = "{self.username}"'
            elif issue_type == "all_mine":
                jql = f'(assignee = "{self.username}" OR reporter = "{self.username}")'
            else:
                jql = f'assignee = "{self.username}"'
            
            # Add status filter if provided
            if status_filter and status_filter.strip():
                if 'ORDER BY' in jql.upper():
                    # If JQL already has ORDER BY, insert status filter before it
                    jql = jql.replace(' ORDER BY', f' AND status = "{status_filter}" ORDER BY')
                else:
                    jql += f' AND status = "{status_filter}"'
            
            # Add additional filters if provided
            if additional_filters:
                for filter_type, filter_value in additional_filters.items():
                    if filter_type == 'priority':
                        if 'ORDER BY' in jql.upper():
                            jql = jql.replace(' ORDER BY', f' AND priority = "{filter_value}" ORDER BY')
                        else:
                            jql += f' AND priority = "{filter_value}"'
                    elif filter_type == 'project':
                        if 'ORDER BY' in jql.upper():
                            jql = jql.replace(' ORDER BY', f' AND project = "{filter_value}" ORDER BY')
                        else:
                            jql += f' AND project = "{filter_value}"'
                    elif filter_type == 'issue_type':
                        if 'ORDER BY' in jql.upper():
                            jql = jql.replace(' ORDER BY', f' AND issuetype = "{filter_value}" ORDER BY')
                        else:
                            jql += f' AND issuetype = "{filter_value}"'
            
            # Add ordering only if not already present
            if 'ORDER BY' not in jql.upper():
                jql += ' ORDER BY updated DESC'
            
            logger.info(f"Executing JQL: {jql}")
            return self.search_issues(jql, max_results)
            
        except Exception as e:
            logger.error(f"Error getting issues for type {issue_type}: {e}")
            return []
    
    def format_issue(self, issue: Dict) -> Dict:
        """Format issue data for better readability"""
        fields = issue.get('fields', {})
        
        # Handle None values for assignee and reporter
        assignee = fields.get('assignee')
        assignee_name = assignee.get('displayName', 'Unassigned') if assignee else 'Unassigned'
        
        reporter = fields.get('reporter')
        reporter_name = reporter.get('displayName', 'Unknown') if reporter else 'Unknown'
        
        formatted_issue = {
            'key': issue.get('key', ''),
            'summary': fields.get('summary', ''),
            'description': fields.get('description', ''),
            'status': fields.get('status', {}).get('name', ''),
            'priority': fields.get('priority', {}).get('name', ''),
            'assignee': assignee_name,
            'reporter': reporter_name,
            'created': fields.get('created', ''),
            'updated': fields.get('updated', ''),
            'url': f"{self.server_url}/browse/{issue.get('key', '')}"
        }
        
        return formatted_issue

# Global Jira service instance
jira_service = JiraService() 
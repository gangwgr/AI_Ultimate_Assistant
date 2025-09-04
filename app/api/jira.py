from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from pydantic import BaseModel
import logging

from app.services.jira_service import jira_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jira", tags=["jira"])

class JiraIssue(BaseModel):
    key: str
    summary: str
    description: Optional[str]
    status: str
    priority: str
    assignee: str
    reporter: str
    created: str
    updated: str
    url: str

class JiraComment(BaseModel):
    issue_key: str
    comment: str

class JiraTransition(BaseModel):
    issue_key: str
    transition_id: str
    comment: Optional[str] = None

class JiraAssignment(BaseModel):
    issue_key: str
    assignee: str

class JiraCredentials(BaseModel):
    server_url: str
    username: str
    api_token: str
    auth_method: str = "basic"

@router.post("/credentials")
async def save_credentials(credentials: JiraCredentials):
    """Save Jira credentials"""
    if jira_service.save_credentials(
        credentials.server_url,
        credentials.username,
        credentials.api_token,
        credentials.auth_method
    ):
        return {"status": "success", "message": "Credentials saved successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save credentials")

@router.get("/test-connection")
async def test_jira_connection():
    """Test Jira connection and credentials"""
    try:
        # Test the connection using the service method
        if jira_service.test_connection():
            connection_details = jira_service.test_connection_details()
            return {
                "success": True,
                "message": "Jira connection test successful",
                "connection_details": connection_details
            }
        else:
            raise HTTPException(status_code=401, detail="Failed to connect to Jira")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Jira connection test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connection-details")
async def get_connection_details():
    """Get detailed Jira connection status"""
    details = jira_service.test_connection_details()
    if details['success']:
        return details
    else:
        raise HTTPException(status_code=500, detail=details['error'])

@router.get("/issues/my/{issue_type}")
async def get_my_issues(issue_type: str = "assigned", status: Optional[str] = None, max_results: int = 100) -> List[JiraIssue]:
    """Get my Jira issues based on type and optional status filter"""
    issues = jira_service.get_my_issues(issue_type, max_results, status)
    return [JiraIssue(**jira_service.format_issue(issue)) for issue in issues]

@router.get("/issues/{issue_key}")
async def get_issue(issue_key: str) -> JiraIssue:
    """Get a single Jira issue"""
    issue = jira_service.get_issue(issue_key)
    if issue:
        return JiraIssue(**jira_service.format_issue(issue))
    else:
        raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found")

@router.post("/issues/{issue_key}/comment")
async def add_comment(comment: JiraComment):
    """Add a comment to a Jira issue"""
    if jira_service.add_comment(comment.issue_key, comment.comment):
        return {"status": "success", "message": f"Comment added to {comment.issue_key}"}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to add comment to {comment.issue_key}")

@router.get("/issues/{issue_key}/comments")
async def get_comments(issue_key: str) -> List[Dict]:
    """Get comments for a Jira issue"""
    comments = jira_service.get_comments(issue_key)
    return comments

@router.get("/issues/{issue_key}/transitions")
async def get_transitions(issue_key: str) -> List[Dict]:
    """Get available transitions for an issue"""
    transitions = jira_service.get_transitions(issue_key)
    if transitions:
        return transitions
    else:
        raise HTTPException(status_code=404, detail=f"No transitions found for {issue_key}")

@router.post("/issues/{issue_key}/transition")
async def transition_issue(transition: JiraTransition):
    """Transition a Jira issue to a new status"""
    # Convert optional comment to empty string if None
    comment = transition.comment if transition.comment is not None else ""
    if jira_service.transition_issue(transition.issue_key, transition.transition_id, comment):
        return {"status": "success", "message": f"Transitioned {transition.issue_key}"}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to transition {transition.issue_key}")

@router.post("/issues/{issue_key}/assign")
async def assign_issue(assignment: JiraAssignment):
    """Assign a Jira issue to a user"""
    if jira_service.assign_issue(assignment.issue_key, assignment.assignee):
        return {"status": "success", "message": f"Issue {assignment.issue_key} assigned to {assignment.assignee}"}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to assign issue {assignment.issue_key} to {assignment.assignee}")

@router.get("/search")
async def search_issues(jql: str, max_results: int = 50) -> List[JiraIssue]:
    """Search Jira issues using JQL"""
    issues = jira_service.search_issues(jql, max_results)
    return [JiraIssue(**jira_service.format_issue(issue)) for issue in issues] 
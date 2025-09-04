import re
import logging
from typing import Dict, List, Any
from .base_agent import BaseAgent
from .jira_service import jira_service

logger = logging.getLogger(__name__)

class JiraAgent(BaseAgent):
    """Specialized agent for Jira issue management"""
    
    def __init__(self):
        super().__init__("JiraAgent", "jira")
        
    def get_capabilities(self) -> List[str]:
        return [
            "fetch_jira_issues", "create_jira_issue", "update_jira_status", 
            "add_jira_comment", "assign_jira_issue", "search_jira_issues",
            "jira_status_lookup", "jira_metadata_query", "jira_advanced_filter",
            "jira_sprint_query"
        ]
    
    def get_domain_keywords(self) -> List[str]:
        return [
            "jira", "issue", "bug", "story", "task", "epic", "sprint", "project",
            "status", "assign", "comment", "create", "update", "fetch", "search",
            "ocpqe", "ocpbugs", "api", "openshift"
        ]
    
    async def analyze_intent(self, message: str) -> Dict[str, Any]:
        """Analyze Jira-related intent"""
        message_lower = message.lower()
        
        # Jira detailed content analysis patterns (MUST be before general patterns)
        if any(phrase in message_lower for phrase in ["summarise content", "content summary", "analyze content", "content analysis"]) and any(word in message_lower for word in ["jira", "issue", "bug", "story", "task", "ocpqe", "ocpbugs"]):
            return {"intent": "analyze_jira_content", "confidence": 0.95, "entities": self._extract_jira_entities(message)}
        
        # Jira summarize/explain patterns (MUST be before general patterns)
        if any(phrase in message_lower for phrase in ["summarize", "explain", "what is", "tell me about"]) and any(word in message_lower for word in ["jira", "issue", "bug", "story", "task", "ocpqe", "ocpbugs"]):
            return {"intent": "summarize_jira_issue", "confidence": 0.95, "entities": self._extract_jira_entities(message)}
        
        # Jira comment patterns (MUST be before general "add" patterns)
        if any(phrase in message_lower for phrase in ["add comment", "comment", "reply"]) and any(word in message_lower for word in ["jira", "issue", "bug", "story", "task", "to", "on"]):
            return {"intent": "add_jira_comment", "confidence": 0.95, "entities": self._extract_jira_entities(message)}
        
        # More specific comment patterns
        if ("add comment" in message_lower or "comment" in message_lower or "reply" in message_lower) and any(word in message_lower for word in ["ocpqe", "ocpbugs", "api", "jira"]):
            return {"intent": "add_jira_comment", "confidence": 0.95, "entities": self._extract_jira_entities(message)}
        
        # Jira status update patterns (MUST be before general patterns)
        if any(phrase in message_lower for phrase in ["update status", "change status", "set status", "update", "to"]) and any(word in message_lower for word in ["jira", "issue", "bug", "story", "task", "ocpqe", "ocpbugs"]):
            return {"intent": "update_jira_status", "confidence": 0.95, "entities": self._extract_jira_entities(message)}
        
        # Specific status update patterns for common formats
        if ("update" in message_lower and "status" in message_lower) or ("update" in message_lower and "to" in message_lower):
            return {"intent": "update_jira_status", "confidence": 0.9, "entities": self._extract_jira_entities(message)}
        
        # More specific pattern for "update jira [issue] status to [status]"
        if "update" in message_lower and "status" in message_lower and "to" in message_lower:
            return {"intent": "update_jira_status", "confidence": 0.95, "entities": self._extract_jira_entities(message)}
        
        # Jira assignment patterns (MUST be before general patterns)
        if any(phrase in message_lower for phrase in ["assign", "assign to", "reassign"]) and any(word in message_lower for word in ["jira", "issue", "bug", "story", "task"]):
            return {"intent": "assign_jira_issue", "confidence": 0.95, "entities": self._extract_jira_entities(message)}
        
        # Jira project listing patterns (MUST be before general fetch patterns)
        if "projects" in message_lower and any(phrase in message_lower for phrase in ["show", "list", "all", "get"]) and any(word in message_lower for word in ["jira", "project"]):
            return {"intent": "list_jira_projects", "confidence": 0.95, "entities": self._extract_jira_entities(message)}
        
        # Jira issue creation patterns
        if any(phrase in message_lower for phrase in ["create", "new"]) and any(word in message_lower for word in ["jira", "issue", "bug", "story", "task"]):
            return {"intent": "create_jira_issue", "confidence": 0.9, "entities": self._extract_jira_entities(message)}
        
        # Jira issue fetching patterns
        if any(phrase in message_lower for phrase in ["fetch", "get", "show", "list"]) and any(word in message_lower for word in ["jira", "issue", "bug", "story", "task"]):
            return {"intent": "fetch_jira_issues", "confidence": 0.9, "entities": self._extract_jira_entities(message)}
        
        # POST NEW action pattern (must be before general fetch patterns)
        if "post new" in message_lower or "post_new" in message_lower:
            return {"intent": "post_new_action", "confidence": 0.95, "entities": self._extract_jira_entities(message)}
        
        # Jira advanced filtering patterns
        if any(phrase in message_lower for phrase in ["filter", "advanced", "query"]) and any(word in message_lower for word in ["jira", "issue", "bug", "story", "task"]):
            return {"intent": "jira_advanced_filter", "confidence": 0.8, "entities": self._extract_jira_entities(message)}
        
        # Default to fetch issues if no specific intent detected
        return {"intent": "fetch_jira_issues", "confidence": 0.6, "entities": self._extract_jira_entities(message)}
    
    async def handle_intent(self, intent: str, message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Jira-related intents"""
        if intent == "analyze_jira_content":
            return await self._handle_analyze_jira_content(message, entities)
        elif intent == "summarize_jira_issue":
            return await self._handle_summarize_jira_issue(message, entities)
        elif intent == "fetch_jira_issues":
            return await self._handle_fetch_jira_issues(message, entities)
        elif intent == "create_jira_issue":
            return await self._handle_create_jira_issue(message, entities)
        elif intent == "update_jira_status":
            return await self._handle_update_jira_status(message, entities)
        elif intent == "add_jira_comment":
            return await self._handle_add_jira_comment(message, entities)
        elif intent == "assign_jira_issue":
            return await self._handle_assign_jira_issue(message, entities)
        elif intent == "jira_advanced_filter":
            return await self._handle_jira_advanced_filter(message, entities)
        elif intent == "list_jira_projects":
            return await self._handle_list_jira_projects(message, entities)
        elif intent == "post_new_action":
            return await self._handle_post_new_action(message, entities)
        else:
            return {
                "response": "I can help you with Jira issue management. What would you like to do?",
                "action_taken": "jira_help",
                "suggestions": ["Fetch my issues", "Create new issue", "Update issue status", "Add comment"]
            }
    
    async def _handle_list_jira_projects(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle listing Jira projects"""
        try:
            # Get all projects from Jira
            projects = jira_service.get_projects()
            
            if projects:
                # Format the response
                project_list = []
                for i, project in enumerate(projects, 1):
                    project_list.append(f"**{i}. {project.get('key', 'N/A')}**")
                    project_list.append(f"   📋 **Name:** {project.get('name', 'N/A')}")
                    project_list.append(f"   📊 **Type:** {project.get('projectTypeKey', 'N/A')}")
                    project_list.append(f"   👤 **Lead:** {project.get('lead', {}).get('displayName', 'N/A')}")
                    project_list.append(f"   🔗 **URL:** {project.get('self', 'N/A')}")
                    project_list.append("")
                
                return {
                    "response": f"📋 **Available Jira Projects ({len(projects)})**\n\n" + "\n".join(project_list),
                    "action_taken": "list_jira_projects",
                    "suggestions": ["Fetch my issues", "Create new issue", "Update issue status", "Add comment"],
                    "project_count": len(projects)
                }
            else:
                return {
                    "response": "📋 No Jira projects found.",
                    "action_taken": "list_jira_projects",
                    "suggestions": ["Fetch my issues", "Create new issue", "Check connection"]
                }
                
        except Exception as e:
            logger.error(f"Error listing Jira projects: {e}")
            return {
                "response": "❌ I encountered an error while fetching Jira projects. Please check your Jira connection.",
                "action_taken": "list_jira_projects",
                "suggestions": ["Check connection", "Fetch my issues", "Create new issue"]
            }
    
    def _extract_jira_entities(self, message: str) -> Dict[str, Any]:
        """Extract Jira-related entities"""
        entities = {}
        message_lower = message.lower()
        
        # Extract Jira issue key (e.g., OCPQE-30241, OCPBUGS-12345) - MUST be first
        issue_patterns = [
            r'([A-Z]+-\d+)',  # Standard Jira key format
        ]
        
        for pattern in issue_patterns:
            # Search in original message (case-sensitive) for issue keys
            match = re.search(pattern, message)
            if match:
                entities["issue_key"] = match.group(1).upper()
                break
        
        # Extract status dynamically from Jira
        try:
            # Get all available statuses from Jira
            all_statuses = jira_service.get_all_statuses()
            
            # Look for status mentions in the message
            for status in all_statuses:
                status_name = status.get('name', '').lower()
                # Use word boundaries to avoid partial matches
                if re.search(r'\b' + re.escape(status_name) + r'\b', message_lower):
                    entities["status"] = status.get('name', '')
                    break
        except Exception as e:
            logger.error(f"Error getting statuses from Jira: {e}")
            # Fallback to basic status extraction
            status_patterns = [
                r'status[:\s]+([^\s,]+(?:\s+[^\s,]+)*)',  # "status: To Do" or "status To Do"
                r'to\s+([^\s,]+(?:\s+[^\s,]+)*)',  # "update to To Do" or "update to TODO"
                r'([a-z]+(?:\s+[a-z]+)*)\s+status',  # "To Do status"
                r'update\s+to\s+([^\s,]+(?:\s+[^\s,]+)*)',  # "update to In Progress"
                r'change\s+to\s+([^\s,]+(?:\s+[^\s,]+)*)',  # "change to QA"
                r'set\s+to\s+([^\s,]+(?:\s+[^\s,]+)*)',  # "set to Ready"
                r'move\s+to\s+([^\s,]+(?:\s+[^\s,]+)*)',  # "move to Review"
            ]
            
            for pattern in status_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    extracted_status = match.group(1).strip()
                    # Handle common variations and abbreviations
                    status_variations = {
                        "todo": "To Do",
                        "inprogress": "In Progress", 
                        "in progress": "In Progress",
                        "codereview": "Code Review",
                        "code review": "Code Review",
                        "peerreview": "Peer Review",
                        "peer review": "Peer Review",
                        "qa": "QA",
                        "onqa": "ON_QA",
                        "on qa": "ON_QA",
                        "verified": "Verified",
                        "closed": "Closed",
                        "resolved": "Resolved",
                        "new": "New",
                        "open": "Open",
                        "blocked": "Blocked",
                        "onhold": "On Hold",
                        "on hold": "On Hold",
                        "pending": "Pending",
                        "ready": "Ready",
                        "done": "Done",
                        "completed": "Completed",
                        "cancelled": "Cancelled",
                        "rejected": "Rejected",
                        "invalid": "Invalid",
                        "duplicate": "Duplicate",
                        "wontfix": "WON'T FIX",
                        "wont do": "Won't Do",
                        "qa in progress": "QA In Progress",
                        "ready for qa": "Ready for QA",
                        "failed qa": "Failed QA",
                        "qa verified": "QA VERIFIED",
                        "qa blocked": "QA Blocked",
                        "verified qa": "Verified QA",
                        "active testing": "Active Testing",
                        "in testing": "In Testing",
                        "testing": "Testing",
                        "ready for test": "Ready for Test",
                        "awaiting review": "Awaiting Review",
                        "in review": "In Review",
                        "review": "Review",
                        "reviewed": "Reviewed",
                        "ready for review": "Ready for Review",
                        "under review": "Under Review",
                        "waiting for review": "Waiting for Review",
                        "dev complete": "Dev Complete",
                        "dev in progress": "Dev In Progress",
                        "development complete": "Development Complete",
                        "feature complete": "Feature Complete",
                        "work in progress": "Work In Progress",
                        "build in progress": "Build In Progress",
                        "signing in progress": "Signing In Progress",
                        "backlog": "Backlog",
                        "analysis": "Analysis",
                        "planning": "Planning",
                        "in planning": "In Planning",
                        "planned": "Planned",
                        "documentation": "Documentation",
                        "documenting": "Documenting",
                        "draft": "Draft",
                        "refinement": "Refinement",
                        "to document": "To Document"
                    }
                    
                    # Check if extracted status matches any variation
                    if extracted_status in status_variations:
                        entities["status"] = status_variations[extracted_status]
                    else:
                        # Default to title case
                        entities["status"] = extracted_status.title()
                    break
        
        # Handle special cases for "POST NEW" - this might be an action, not a status
        if "post new" in message_lower or "post_new" in message_lower:
            # Don't extract this as a status, it's likely an action
            if "status" in entities:
                del entities["status"]
        
        # Fix common status mapping issues
        if "status" in entities:
            status = entities["status"]
            # Enhanced status mapping for all major categories
            status_mapping = {
                # Basic Workflow
                "ToDo": "To Do",
                "InProgress": "In Progress", 
                "CodeReview": "Code Review",
                "PeerReview": "Peer Review",
                "QA": "QA",
                "ON_QA": "ON_QA",
                "Verified": "Verified",
                "Closed": "Closed",
                "Resolved": "Resolved",
                
                # QA Related
                "QAInProgress": "QA In Progress",
                "ReadyForQA": "Ready for QA", 
                "FailedQA": "Failed QA",
                "QAVERIFIED": "QA VERIFIED",
                "QABlocked": "QA Blocked",
                "VerifiedQA": "Verified QA",
                "ActiveTesting": "Active Testing",
                "InTesting": "In Testing",
                "Testing": "Testing",
                "ReadyForTest": "Ready for Test",
                
                # Review Related
                "AwaitingReview": "Awaiting Review",
                "InReview": "In Review",
                "Review": "Review",
                "Reviewed": "Reviewed",
                "ReadyForReview": "Ready for Review",
                "UnderReview": "Under Review",
                "WaitingForReview": "Waiting for Review",
                
                # Progress Related
                "DevComplete": "Dev Complete",
                "DevInProgress": "Dev In Progress",
                "DevelopmentComplete": "Development Complete",
                "FeatureComplete": "Feature Complete",
                "WorkInProgress": "Work In Progress",
                "BuildInProgress": "Build In Progress",
                "SigningInProgress": "Signing In Progress",
                
                # Planning
                "Backlog": "Backlog",
                "Analysis": "Analysis",
                "Planning": "Planning",
                "InPlanning": "In Planning",
                "Planned": "Planned",
                
                # Documentation
                "Documentation": "Documentation",
                "Documenting": "Documenting",
                "Draft": "Draft",
                "Refinement": "Refinement",
                "ToDocument": "To Document",
                
                # Other Common
                "New": "New",
                "Open": "Open",
                "Blocked": "Blocked",
                "OnHold": "On Hold",
                "Pending": "Pending",
                "Ready": "Ready",
                "Done": "Done",
                "Completed": "Completed",
                "Cancelled": "Cancelled",
                "Rejected": "Rejected",
                "Invalid": "Invalid",
                "Duplicate": "Duplicate",
                "WontFix": "WON'T FIX",
                "WontDo": "Won't Do"
            }
            
            # Apply mapping if status exists in mapping
            if status in status_mapping:
                entities["status"] = status_mapping[status]
            # Handle common variations
            elif status == "todo":
                entities["status"] = "To Do"
            elif status == "inprogress":
                entities["status"] = "In Progress"
            elif status == "codereview":
                entities["status"] = "Code Review"
            elif status == "peerreview":
                entities["status"] = "Peer Review"
            elif status == "qa":
                entities["status"] = "QA"
            elif status == "verified":
                entities["status"] = "Verified"
            elif status == "closed":
                entities["status"] = "Closed"
            elif status == "resolved":
                entities["status"] = "Resolved"
            elif status == "new":
                entities["status"] = "New"
            elif status == "open":
                entities["status"] = "Open"
            elif status == "blocked":
                entities["status"] = "Blocked"
            elif status == "onhold":
                entities["status"] = "On Hold"
            elif status == "pending":
                entities["status"] = "Pending"
            elif status == "ready":
                entities["status"] = "Ready"
            elif status == "done":
                entities["status"] = "Done"
            elif status == "completed":
                entities["status"] = "Completed"
            elif status == "cancelled":
                entities["status"] = "Cancelled"
            elif status == "rejected":
                entities["status"] = "Rejected"
            elif status == "invalid":
                entities["status"] = "Invalid"
            elif status == "duplicate":
                entities["status"] = "Duplicate"
            elif status == "wontfix":
                entities["status"] = "WON'T FIX"
            elif status == "wontdo":
                entities["status"] = "Won't Do"
        
        # Extract assignee
        assignee_patterns = [
            r'assign\s+to\s+([^\s,]+)',
            r'assigned\s+to\s+([^\s,]+)',
            r'assignee[:\s]+([^\s,]+)'
        ]
        
        for pattern in assignee_patterns:
            match = re.search(pattern, message_lower)
            if match:
                entities["assignee"] = match.group(1)
                break
        
        # Extract comment text
        comment_patterns = [
            r'add\s+comment\s+to\s+jira\s+[a-z]+-\d+\s+(.+)',  # "add comment to jira OCPQE-30241 working on it"
            r'add\s+comment\s+to\s+[a-z]+-\d+\s+(.+)',  # "add comment to OCPQE-30241 working on it"
            r'comment\s+on\s+[a-z]+-\d+\s+(.+)',  # "comment on OCPQE-30241 working on it"
            r'reply\s+to\s+[a-z]+-\d+\s+(.+)',  # "reply to OCPQE-30241 working on it"
            r'add\s+comment\s+[a-z]+-\d+\s+(.+)',  # "add comment OCPQE-30241 working on it"
            r'comment\s+[a-z]+-\d+\s+(.+)',  # "comment OCPQE-30241 working on it"
        ]
        
        for pattern in comment_patterns:
            match = re.search(pattern, message_lower)
            if match:
                comment_text = match.group(1).strip()
                if comment_text:
                    entities["comment"] = comment_text
                break
        
        # Extract project dynamically from Jira (only if issue key is not already extracted)
        if not entities.get("issue_key"):
            try:
                # Get all projects from Jira
                projects = jira_service.get_projects()
                
                # Look for project mentions in the message (but avoid extracting from status names)
                for project in projects:
                    project_key = project.get('key', '').lower()
                    # Only extract if it's a standalone project mention, not part of a status
                    if project_key in message_lower and len(project_key) > 1:  # Avoid single letter matches
                        # Check if this is not part of a status name
                        status_names = []
                        if 'all_statuses' in locals():
                            status_names = [status.get('name', '').lower() for status in all_statuses]
                        
                        # Also check if it's not part of common words
                        common_words = ['new', 'verified', 'progress', 'review', 'complete', 'pending', 'waiting']
                        is_part_of_status = any(project_key in status_name for status_name in status_names)
                        is_part_of_common_word = any(project_key in word for word in common_words)
                        
                        if not is_part_of_status and not is_part_of_common_word:
                            entities["project"] = project.get('key', '')
                            break
            except Exception as e:
                logger.error(f"Error getting projects from Jira: {e}")
                # Fallback to basic project extraction
                if "ocpqe" in message_lower:
                    entities["project"] = "OCPQE"
                elif "ocpbugs" in message_lower:
                    entities["project"] = "OCPBUGS"
                elif "api" in message_lower:
                    entities["project"] = "API"
        
        return entities
    
    async def _handle_fetch_jira_issues(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle fetching Jira issues"""
        try:
            # Determine issue type based on message
            message_lower = message.lower()
            issue_type = "assigned"  # Default
            
            if "reported" in message_lower or "created" in message_lower:
                issue_type = "reported"
            elif "all" in message_lower or "mine" in message_lower:
                issue_type = "all_mine"
            elif "qa" in message_lower or "contact" in message_lower:
                issue_type = "qa_contact"
            
            # Get status filter from entities
            status_filter = entities.get("status")
            
            # Get issues from Jira with status filter
            issues = jira_service.get_my_issues(issue_type=issue_type, max_results=20, status_filter=status_filter)
            
            if issues:
                # Format the response
                issue_list = []
                for i, issue in enumerate(issues, 1):
                    formatted_issue = jira_service.format_issue(issue)
                    
                    # Status indicator
                    status = formatted_issue['status']
                    priority = formatted_issue['priority']
                    
                    # Priority emoji
                    priority_emoji = "🔴" if priority == "Critical" else "🟡" if priority == "High" else "🟢" if priority == "Medium" else "⚪"
                    
                    issue_list.append(f"**{i}. {priority_emoji} {formatted_issue['key']}**")
                    issue_list.append(f"   📋 **Summary:** {formatted_issue['summary']}")
                    issue_list.append(f"   📊 **Status:** {status}")
                    issue_list.append(f"   🎯 **Priority:** {priority}")
                    issue_list.append(f"   👤 **Assignee:** {formatted_issue['assignee']}")
                    issue_list.append(f"   📅 **Updated:** {formatted_issue['updated'][:10]}")
                    issue_list.append(f"   🔗 **URL:** {formatted_issue['url']}")
                    issue_list.append("")
                
                return {
                    "response": f"📋 **Your Jira Issues ({len(issues)})**\n\n" + "\n".join(issue_list),
                    "action_taken": "fetch_jira_issues",
                    "suggestions": ["Create new issue", "Update issue status", "Add comment", "Search issues"],
                    "issue_count": len(issues)
                }
            else:
                return {
                    "response": "📋 No Jira issues found for you.",
                    "action_taken": "fetch_jira_issues",
                    "suggestions": ["Create new issue", "Search issues", "Check other projects"]
                }
                
        except Exception as e:
            logger.error(f"Error fetching Jira issues: {e}")
            return {
                "response": "❌ I encountered an error while fetching your Jira issues. Please check your Jira connection.",
                "action_taken": "fetch_jira_issues",
                "suggestions": ["Check connection", "Create new issue", "Search issues"]
            }
    
    async def _handle_create_jira_issue(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle creating Jira issues"""
        project = entities.get("project", "OCPQE")
        return {
            "response": f"I'll help you create a new Jira issue in the {project} project. What type of issue would you like to create?",
            "action_taken": "create_jira_issue",
            "suggestions": ["Bug", "Story", "Task", "Epic"]
        }
    
    async def _handle_update_jira_status(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle updating Jira issue status"""
        issue_key = entities.get("issue_key")
        status = entities.get("status")
        
        if issue_key and status:
            try:
                # Get available transitions for the issue
                transitions = jira_service.get_transitions(issue_key)
                
                if transitions:
                    # Find the matching transition
                    target_transition = None
                    for transition in transitions:
                        # Try exact match first
                        if transition['name'].upper() == status.upper():
                            target_transition = transition
                            break
                        # Try with spaces replaced by underscores
                        elif transition['name'].upper().replace(' ', '_') == status.upper():
                            target_transition = transition
                            break
                        # Try with underscores replaced by spaces
                        elif transition['name'].upper().replace('_', ' ') == status.upper():
                            target_transition = transition
                            break
                        # Try case-insensitive partial match
                        elif status.upper() in transition['name'].upper() or transition['name'].upper() in status.upper():
                            target_transition = transition
                            break
                    
                    if target_transition:
                        # Perform the transition
                        success = jira_service.transition_issue(issue_key, target_transition['id'], f"Status updated to {status}")
                        
                        if success:
                            return {
                                "response": f"✅ Successfully updated {issue_key} status to **{status}**.",
                                "action_taken": "update_jira_status",
                                "suggestions": ["Add comment", "Assign issue", "Fetch my issues", "Create new issue"],
                                "issue_key": issue_key,
                                "new_status": status
                            }
                        else:
                            return {
                                "response": f"❌ Failed to update {issue_key} status to {status}. Please try again.",
                                "action_taken": "update_jira_status_failed",
                                "suggestions": ["Check permissions", "Fetch my issues", "Create new issue"]
                            }
                    else:
                        # List available transitions
                        available_statuses = [t['name'] for t in transitions]
                        return {
                            "response": f"❌ Status '{status}' not available for {issue_key}. Available statuses: {', '.join(available_statuses)}",
                            "action_taken": "update_jira_status_invalid",
                            "suggestions": available_statuses[:5] + ["Fetch my issues", "Create new issue"]
                        }
                else:
                    return {
                        "response": f"❌ Could not retrieve available transitions for {issue_key}.",
                        "action_taken": "update_jira_status_error",
                        "suggestions": ["Check permissions", "Fetch my issues", "Create new issue"]
                    }
                    
            except Exception as e:
                logger.error(f"Error updating Jira status: {e}")
                return {
                    "response": f"❌ Error updating {issue_key} status: {str(e)}",
                    "action_taken": "update_jira_status_error",
                    "suggestions": ["Check connection", "Fetch my issues", "Create new issue"]
                }
        else:
            return {
                "response": "I need the issue key and status to update. Which issue would you like to update?",
                "action_taken": "update_jira_status_info_needed",
                "suggestions": ["Provide issue key", "Specify status", "Fetch my issues", "Create new issue"]
            }
    
    async def _handle_add_jira_comment(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle adding Jira comments"""
        issue_key = entities.get("issue_key")
        comment_text = entities.get("comment")
        
        # Debug logging
        logger.debug(f"Jira comment handler - message: '{message}', entities: {entities}")
        logger.debug(f"Extracted issue_key: {issue_key}, comment_text: {comment_text}")
        
        if issue_key:
            if comment_text:
                try:
                    # Add the comment to Jira
                    success = jira_service.add_comment(issue_key, comment_text)
                    if success:
                        return {
                            "response": f"✅ Successfully added comment to {issue_key}: **{comment_text}**",
                            "action_taken": "add_jira_comment",
                            "suggestions": ["Update status", "Assign issue", "Fetch my issues", "Create new issue"],
                            "issue_key": issue_key,
                            "comment": comment_text
                        }
                    else:
                        return {
                            "response": f"❌ Failed to add comment to {issue_key}. Please try again.",
                            "action_taken": "add_jira_comment_failed",
                            "suggestions": ["Check permissions", "Fetch my issues", "Create new issue"]
                        }
                except Exception as e:
                    logger.error(f"Error adding Jira comment: {e}")
                    return {
                        "response": f"❌ Error adding comment to {issue_key}: {str(e)}",
                        "action_taken": "add_jira_comment_error",
                        "suggestions": ["Check connection", "Fetch my issues", "Create new issue"]
                    }
            else:
                return {
                    "response": f"I'll help you add a comment to {issue_key}. What would you like to say?",
                    "action_taken": "add_jira_comment",
                    "suggestions": ["Update status", "Assign issue", "Fetch my issues", "Create new issue"]
                }
        else:
            return {
                "response": "I need the issue key to add a comment. Which issue would you like to comment on?",
                "action_taken": "add_jira_comment_info_needed",
                "suggestions": ["Provide issue key", "Fetch my issues", "Create new issue", "Update status"]
            }
    
    async def _handle_assign_jira_issue(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle assigning Jira issues"""
        issue_key = entities.get("issue_key")
        assignee = entities.get("assignee")
        
        if issue_key and assignee:
            return {
                "response": f"I'll assign {issue_key} to {assignee}.",
                "action_taken": "assign_jira_issue",
                "suggestions": ["Add comment", "Update status", "Fetch my issues", "Create new issue"]
            }
        else:
            return {
                "response": "I need the issue key and assignee. Which issue would you like to assign?",
                "action_taken": "assign_jira_issue_info_needed",
                "suggestions": ["Provide issue key", "Specify assignee", "Fetch my issues", "Create new issue"]
            }
    
    async def _handle_jira_advanced_filter(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle advanced Jira filtering"""
        return {
            "response": "I'll help you with advanced Jira filtering. What specific criteria would you like to filter by?",
            "action_taken": "jira_advanced_filter",
            "suggestions": ["Filter by status", "Filter by priority", "Filter by assignee", "Filter by date"]
        }
    
    async def _handle_post_new_action(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle POST NEW action - this might be a custom workflow action"""
        try:
            # This could be a custom workflow action or status transition
            # For now, let's treat it as a request to move issues to a "New" status
            return {
                "response": "🔄 **POST NEW Action**\n\nI understand you want to perform a 'POST NEW' action. This could be:\n\n• Moving issues to 'New' status\n• Creating new issues\n• Posting new content\n\nCould you clarify what specific action you'd like to perform?",
                "action_taken": "post_new_action",
                "suggestions": ["Move issues to New status", "Create new issue", "Post new content", "Show available actions"]
            }
        except Exception as e:
            logger.error(f"Error handling POST NEW action: {e}")
            return {
                "response": "❌ I encountered an error while processing the POST NEW action.",
                "action_taken": "post_new_action",
                "suggestions": ["Try again", "Create new issue", "Show available actions"]
            }
    
    async def _handle_summarize_jira_issue(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle summarizing a specific Jira issue"""
        issue_key = entities.get("issue_key")
        
        if issue_key:
            try:
                # Get the specific issue details from Jira
                issue_data = jira_service.get_issue(issue_key)
                
                if issue_data:
                    # Format the issue data using the service's format_issue method
                    issue_details = jira_service.format_issue(issue_data)
                    
                    # Get comments for the issue
                    comments = jira_service.get_comments(issue_key)
                    
                    # Format the summary
                    summary = f"📋 **Jira Issue Summary: {issue_key}**\n\n"
                    summary += f"**Summary:** {issue_details.get('summary', 'N/A')}\n"
                    summary += f"**Status:** {issue_details.get('status', 'N/A')}\n"
                    summary += f"**Priority:** {issue_details.get('priority', 'N/A')}\n"
                    summary += f"**Assignee:** {issue_details.get('assignee', 'N/A')}\n"
                    summary += f"**Reporter:** {issue_details.get('reporter', 'N/A')}\n"
                    summary += f"**Created:** {issue_details.get('created', 'N/A')}\n"
                    summary += f"**Updated:** {issue_details.get('updated', 'N/A')}\n"
                    
                    # Add description if available
                    description = issue_details.get('description', '')
                    if description:
                        # Truncate description if too long
                        if len(description) > 500:
                            description = description[:500] + "..."
                        summary += f"\n**Description:** {description}\n"
                    
                    # Add comments summary
                    if comments:
                        summary += f"\n💬 **Comments ({len(comments)}):**\n"
                        for i, comment in enumerate(comments[:5], 1):  # Show first 5 comments
                            author = comment.get('author', {}).get('displayName', 'Unknown')
                            body = comment.get('body', '')
                            created = comment.get('created', '')
                            
                            # Truncate comment body if too long
                            if len(body) > 200:
                                body = body[:200] + "..."
                            
                            summary += f"  **{i}.** {author} ({created}): {body}\n"
                        
                        if len(comments) > 5:
                            summary += f"  ... and {len(comments) - 5} more comments\n"
                    else:
                        summary += f"\n💬 **Comments:** No comments yet\n"
                    
                    # Add activity summary
                    summary += f"\n📊 **Activity Summary:**\n"
                    summary += f"  • Issue created on {issue_details.get('created', 'N/A')}\n"
                    summary += f"  • Last updated on {issue_details.get('updated', 'N/A')}\n"
                    summary += f"  • Current status: {issue_details.get('status', 'N/A')}\n"
                    summary += f"  • Assigned to: {issue_details.get('assignee', 'N/A')}\n"
                    
                    # Add key insights
                    summary += f"\n🔍 **Key Insights:**\n"
                    if issue_details.get('status') == 'In Progress':
                        summary += f"  • This issue is currently being worked on\n"
                    elif issue_details.get('status') == 'To Do':
                        summary += f"  • This issue is pending and needs to be started\n"
                    elif issue_details.get('status') == 'Done':
                        summary += f"  • This issue has been completed\n"
                    
                    if comments:
                        summary += f"  • Has {len(comments)} comment(s) indicating active discussion\n"
                    else:
                        summary += f"  • No comments yet - may need attention\n"
                    
                    summary += f"\n🔗 **URL:** {issue_details.get('url', f'https://issues.redhat.com/browse/{issue_key}')}"
                    
                    return {
                        "response": summary,
                        "action_taken": "summarize_jira_issue",
                        "suggestions": ["Update status", "Add comment", "Assign issue", "Fetch all issues"],
                        "issue_key": issue_key,
                        "issue_details": issue_details,
                        "comment_count": len(comments) if comments else 0
                    }
                else:
                    return {
                        "response": f"❌ Could not find Jira issue {issue_key}. Please check the issue key and try again.",
                        "action_taken": "summarize_jira_issue_not_found",
                        "suggestions": ["Check issue key", "Fetch my issues", "Create new issue"]
                    }
                    
            except Exception as e:
                logger.error(f"Error summarizing Jira issue {issue_key}: {e}")
                return {
                    "response": f"❌ Error summarizing Jira issue {issue_key}: {str(e)}",
                    "action_taken": "summarize_jira_issue_error",
                    "suggestions": ["Check connection", "Fetch my issues", "Create new issue"]
                }
        else:
            return {
                "response": "I need the issue key to summarize a Jira issue. Which issue would you like me to summarize?",
                "action_taken": "summarize_jira_issue_info_needed",
                "suggestions": ["Provide issue key", "Fetch my issues", "Create new issue"]
            } 
    
    async def _handle_analyze_jira_content(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle detailed content analysis of a Jira issue"""
        issue_key = entities.get("issue_key")
        
        if issue_key:
            try:
                # Get the specific issue details from Jira
                issue_data = jira_service.get_issue(issue_key)
                
                if issue_data:
                    # Format the issue data using the service's format_issue method
                    issue_details = jira_service.format_issue(issue_data)
                    
                    # Get comments for the issue
                    comments = jira_service.get_comments(issue_key)
                    
                    # Create detailed content analysis
                    analysis = f"🔍 **Detailed Content Analysis: {issue_key}**\n\n"
                    
                    # Basic issue info
                    analysis += f"📋 **Issue Overview:**\n"
                    analysis += f"  • **Key:** {issue_key}\n"
                    analysis += f"  • **Summary:** {issue_details.get('summary', 'N/A')}\n"
                    analysis += f"  • **Status:** {issue_details.get('status', 'N/A')}\n"
                    analysis += f"  • **Priority:** {issue_details.get('priority', 'N/A')}\n"
                    analysis += f"  • **Assignee:** {issue_details.get('assignee', 'N/A')}\n"
                    analysis += f"  • **Reporter:** {issue_details.get('reporter', 'N/A')}\n\n"
                    
                    # Content analysis
                    analysis += f"📄 **Content Analysis:**\n"
                    
                    # Description analysis
                    description = issue_details.get('description', '')
                    if description:
                        word_count = len(description.split())
                        analysis += f"  • **Description:** {word_count} words\n"
                        analysis += f"  • **Content Type:** Detailed description provided\n"
                        if len(description) > 1000:
                            analysis += f"  • **Complexity:** High (detailed description)\n"
                        elif len(description) > 500:
                            analysis += f"  • **Complexity:** Medium\n"
                        else:
                            analysis += f"  • **Complexity:** Low (brief description)\n"
                    else:
                        analysis += f"  • **Description:** No description provided\n"
                        analysis += f"  • **Content Type:** Minimal information\n"
                        analysis += f"  • **Complexity:** Low\n"
                    
                    # Comments analysis
                    if comments:
                        analysis += f"\n💬 **Comments Analysis:**\n"
                        analysis += f"  • **Total Comments:** {len(comments)}\n"
                        
                        # Analyze comment activity
                        recent_comments = [c for c in comments if c.get('created', '') > '2025-07-20']  # Recent activity
                        analysis += f"  • **Recent Activity:** {len(recent_comments)} recent comments\n"
                        
                        # Comment authors
                        authors = set()
                        for comment in comments:
                            author = comment.get('author', {}).get('displayName', 'Unknown')
                            authors.add(author)
                        analysis += f"  • **Participants:** {len(authors)} different people\n"
                        analysis += f"  • **Authors:** {', '.join(list(authors)[:3])}{'...' if len(authors) > 3 else ''}\n"
                        
                        # Comment content analysis
                        total_comment_words = sum(len(c.get('body', '').split()) for c in comments)
                        avg_comment_length = total_comment_words / len(comments) if comments else 0
                        analysis += f"  • **Average Comment Length:** {avg_comment_length:.1f} words\n"
                        
                        if avg_comment_length > 50:
                            analysis += f"  • **Discussion Level:** High (detailed comments)\n"
                        elif avg_comment_length > 20:
                            analysis += f"  • **Discussion Level:** Medium\n"
                        else:
                            analysis += f"  • **Discussion Level:** Low (brief comments)\n"
                    else:
                        analysis += f"\n💬 **Comments Analysis:**\n"
                        analysis += f"  • **Total Comments:** 0\n"
                        analysis += f"  • **Discussion Level:** None\n"
                        analysis += f"  • **Recommendation:** Consider adding comments for better tracking\n"
                    
                    # Activity timeline
                    analysis += f"\n📊 **Activity Timeline:**\n"
                    analysis += f"  • **Created:** {issue_details.get('created', 'N/A')}\n"
                    analysis += f"  • **Last Updated:** {issue_details.get('updated', 'N/A')}\n"
                    
                    # Status analysis
                    status = issue_details.get('status', '')
                    analysis += f"\n🎯 **Status Analysis:**\n"
                    if status == 'In Progress':
                        analysis += f"  • **Current State:** Actively being worked on\n"
                        analysis += f"  • **Recommendation:** Monitor progress and provide updates\n"
                    elif status == 'To Do':
                        analysis += f"  • **Current State:** Pending work\n"
                        analysis += f"  • **Recommendation:** Consider starting work or reassigning\n"
                    elif status == 'Done':
                        analysis += f"  • **Current State:** Completed\n"
                        analysis += f"  • **Recommendation:** Review and close if appropriate\n"
                    else:
                        analysis += f"  • **Current State:** {status}\n"
                        analysis += f"  • **Recommendation:** Review status appropriateness\n"
                    
                    # Content insights
                    analysis += f"\n🔍 **Content Insights:**\n"
                    if description and len(description) > 500:
                        analysis += f"  • **Rich Content:** Detailed description provides good context\n"
                    elif description:
                        analysis += f"  • **Basic Content:** Description could be more detailed\n"
                    else:
                        analysis += f"  • **Minimal Content:** Consider adding description\n"
                    
                    if comments and len(comments) > 5:
                        analysis += f"  • **Active Discussion:** Multiple comments indicate ongoing work\n"
                    elif comments:
                        analysis += f"  • **Some Discussion:** Limited comments present\n"
                    else:
                        analysis += f"  • **No Discussion:** No comments yet\n"
                    
                    analysis += f"\n🔗 **URL:** {issue_details.get('url', f'https://issues.redhat.com/browse/{issue_key}')}"
                    
                    return {
                        "response": analysis,
                        "action_taken": "analyze_jira_content",
                        "suggestions": ["Update status", "Add comment", "Assign issue", "Fetch all issues"],
                        "issue_key": issue_key,
                        "issue_details": issue_details,
                        "comment_count": len(comments) if comments else 0,
                        "analysis_type": "detailed_content"
                    }
                else:
                    return {
                        "response": f"❌ Could not find Jira issue {issue_key}. Please check the issue key and try again.",
                        "action_taken": "analyze_jira_content_not_found",
                        "suggestions": ["Check issue key", "Fetch my issues", "Create new issue"]
                    }
                    
            except Exception as e:
                logger.error(f"Error analyzing Jira content for {issue_key}: {e}")
                return {
                    "response": f"❌ Error analyzing Jira content for {issue_key}: {str(e)}",
                    "action_taken": "analyze_jira_content_error",
                    "suggestions": ["Check connection", "Fetch my issues", "Create new issue"]
                }
        else:
            return {
                "response": "I need the issue key to analyze Jira content. Which issue would you like me to analyze?",
                "action_taken": "analyze_jira_content_info_needed",
                "suggestions": ["Provide issue key", "Fetch my issues", "Create new issue"]
            } 
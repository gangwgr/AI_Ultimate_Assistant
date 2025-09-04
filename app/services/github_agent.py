import re
import logging
from typing import Dict, List, Any
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class GitHubAgent(BaseAgent):
    """Specialized agent for GitHub/PR management"""
    
    def __init__(self):
        super().__init__("GitHubAgent", "github")
        
    def get_capabilities(self) -> List[str]:
        return [
            "list_prs", "create_pr", "review_pr", "merge_pr", "close_pr",
            "search_prs", "get_pr_details", "add_comment", "request_review",
            "check_status", "get_commits", "get_files_changed"
        ]
    
    def get_domain_keywords(self) -> List[str]:
        return [
            "github", "pr", "pull request", "pull requests", "merge", "review",
            "commit", "commits", "branch", "branches", "repo", "repository",
            "gh", "git", "push", "pull", "fork", "clone"
        ]
    
    async def analyze_intent(self, message: str) -> Dict[str, Any]:
        """Analyze GitHub-related intent"""
        message_lower = message.lower()
        
        # PR listing patterns
        if any(phrase in message_lower for phrase in ["list pr", "list pull request", "show pr", "show pull request", "get pr", "get pull request"]):
            return {"intent": "list_prs", "confidence": 0.9, "entities": self._extract_github_entities(message)}
        
        # PR creation patterns
        if any(phrase in message_lower for phrase in ["create pr", "create pull request", "new pr", "new pull request", "make pr", "make pull request"]):
            return {"intent": "create_pr", "confidence": 0.9, "entities": self._extract_github_entities(message)}
        
        # PR review patterns
        if any(phrase in message_lower for phrase in ["review pr", "review pull request", "approve pr", "approve pull request"]):
            return {"intent": "review_pr", "confidence": 0.9, "entities": self._extract_github_entities(message)}
        
        # PR merge patterns
        if any(phrase in message_lower for phrase in ["merge pr", "merge pull request", "squash merge", "rebase merge"]):
            return {"intent": "merge_pr", "confidence": 0.9, "entities": self._extract_github_entities(message)}
        
        # PR search patterns
        if any(phrase in message_lower for phrase in ["search pr", "search pull request", "find pr", "find pull request"]):
            return {"intent": "search_prs", "confidence": 0.8, "entities": self._extract_github_entities(message)}
        
        # PR details patterns
        if any(phrase in message_lower for phrase in ["pr details", "pull request details", "pr info", "pull request info"]):
            return {"intent": "get_pr_details", "confidence": 0.8, "entities": self._extract_github_entities(message)}
        
        # Default to list PRs if no specific intent detected
        return {"intent": "list_prs", "confidence": 0.6, "entities": self._extract_github_entities(message)}
    
    async def handle_intent(self, intent: str, message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GitHub-related intents"""
        if intent == "list_prs":
            return await self._handle_list_prs(message, entities)
        elif intent == "create_pr":
            return await self._handle_create_pr(message, entities)
        elif intent == "review_pr":
            return await self._handle_review_pr(message, entities)
        elif intent == "merge_pr":
            return await self._handle_merge_pr(message, entities)
        elif intent == "search_prs":
            return await self._handle_search_prs(message, entities)
        elif intent == "get_pr_details":
            return await self._handle_get_pr_details(message, entities)
        else:
            return {
                "response": "I can help you with GitHub pull request management. What would you like to do?",
                "action_taken": "github_help",
                "suggestions": ["List PRs", "Create PR", "Review PR", "Merge PR"]
            }
    
    def _extract_github_entities(self, message: str) -> Dict[str, Any]:
        """Extract GitHub-related entities"""
        entities = {}
        message_lower = message.lower()
        
        # Extract PR number
        pr_patterns = [
            r'pr\s+#?(\d+)',  # pr #123
            r'pull request\s+#?(\d+)',  # pull request #123
            r'#(\d+)',  # #123
        ]
        
        for pattern in pr_patterns:
            match = re.search(pattern, message_lower)
            if match:
                entities["pr_number"] = int(match.group(1))
                break
        
        # Extract repository
        repo_patterns = [
            r'repo[:\s]+([^\s,]+/[^\s,]+)',  # repo: owner/repo
            r'repository[:\s]+([^\s,]+/[^\s,]+)',  # repository: owner/repo
            r'([^\s,]+/[^\s,]+)',  # owner/repo
        ]
        
        for pattern in repo_patterns:
            match = re.search(pattern, message_lower)
            if match:
                entities["repository"] = match.group(1)
                break
        
        # Extract branch
        branch_patterns = [
            r'branch[:\s]+([^\s,]+)',  # branch: main
            r'from\s+([^\s,]+)',  # from feature-branch
            r'to\s+([^\s,]+)',  # to main
        ]
        
        for pattern in branch_patterns:
            match = re.search(pattern, message_lower)
            if match:
                entities["branch"] = match.group(1)
                break
        
        # Extract status
        status_patterns = [
            r'status[:\s]+([^\s,]+)',  # status: open
            r'([a-z]+)\s+pr',  # open pr
            r'([a-z]+)\s+pull request',  # closed pull request
        ]
        
        for pattern in status_patterns:
            match = re.search(pattern, message_lower)
            if match:
                status = match.group(1)
                if status in ["open", "closed", "merged", "draft"]:
                    entities["status"] = status
                    break
        
        return entities
    
    async def _handle_list_prs(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle listing PRs"""
        status = entities.get("status", "open")
        repo = entities.get("repository", "all repositories")
        return {
            "response": f"I'll fetch the {status} pull requests from {repo}.",
            "action_taken": "list_prs",
            "suggestions": ["Create PR", "Review PR", "Search PRs", "Get PR details"]
        }
    
    async def _handle_create_pr(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle creating PRs"""
        from_branch = entities.get("branch", "feature-branch")
        to_branch = "main"  # Default target branch
        return {
            "response": f"I'll help you create a pull request from {from_branch} to {to_branch}. What's the title and description?",
            "action_taken": "create_pr",
            "suggestions": ["Add title", "Add description", "Set reviewers", "Set labels"]
        }
    
    async def _handle_review_pr(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle reviewing PRs"""
        pr_number = entities.get("pr_number")
        
        if pr_number:
            return {
                "response": f"I'll help you review pull request #{pr_number}. What would you like to do?",
                "action_taken": "review_pr",
                "suggestions": ["Approve", "Request changes", "Add comment", "Get PR details"]
            }
        else:
            return {
                "response": "I need the PR number to help you review. Which pull request would you like to review?",
                "action_taken": "review_pr_info_needed",
                "suggestions": ["Provide PR number", "List PRs", "Search PRs", "Create PR"]
            }
    
    async def _handle_merge_pr(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle merging PRs"""
        pr_number = entities.get("pr_number")
        
        if pr_number:
            return {
                "response": f"I'll help you merge pull request #{pr_number}. What merge strategy would you prefer?",
                "action_taken": "merge_pr",
                "suggestions": ["Squash merge", "Merge commit", "Rebase merge", "Get PR details"]
            }
        else:
            return {
                "response": "I need the PR number to help you merge. Which pull request would you like to merge?",
                "action_taken": "merge_pr_info_needed",
                "suggestions": ["Provide PR number", "List PRs", "Search PRs", "Create PR"]
            }
    
    async def _handle_search_prs(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle searching PRs"""
        return {
            "response": "I'll help you search for pull requests. What criteria would you like to search by?",
            "action_taken": "search_prs",
            "suggestions": ["Search by author", "Search by label", "Search by status", "Search by title"]
        }
    
    async def _handle_get_pr_details(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle getting PR details"""
        pr_number = entities.get("pr_number")
        
        if pr_number:
            return {
                "response": f"I'll fetch the details for pull request #{pr_number}.",
                "action_taken": "get_pr_details",
                "suggestions": ["Review PR", "Merge PR", "Add comment", "Request review"]
            }
        else:
            return {
                "response": "I need the PR number to get details. Which pull request would you like to see?",
                "action_taken": "get_pr_details_info_needed",
                "suggestions": ["Provide PR number", "List PRs", "Search PRs", "Create PR"]
            } 
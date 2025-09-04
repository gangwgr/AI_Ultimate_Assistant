import os
import logging
import asyncio
import aiohttp
import base64
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import re

logger = logging.getLogger(__name__)

class GitHubService:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.base_headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Ultimate-Assistant/1.0"
        }
    
    def _get_token(self) -> Optional[str]:
        """Get GitHub token from secure config or environment"""
        try:
            from .secure_config import secure_config
            return secure_config.get_github_token()
        except Exception as e:
            logger.warning(f"Failed to get token from secure config: {e}")
            return os.getenv("GITHUB_TOKEN")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with current token"""
        headers = self.base_headers.copy()
        token = self._get_token()
        if token:
            headers["Authorization"] = f"token {token}"
        return headers
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to GitHub API"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        async with aiohttp.ClientSession() as session:
            try:
                if method.upper() == "GET":
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            logger.error(f"GitHub API error {response.status}: {error_text}")
                            return {"error": f"GitHub API error {response.status}", "details": error_text}
                
                elif method.upper() == "POST":
                    async with session.post(url, headers=headers, json=data) as response:
                        if response.status in [200, 201]:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            logger.error(f"GitHub API error {response.status}: {error_text}")
                            return {"error": f"GitHub API error {response.status}", "details": error_text}
                
                elif method.upper() == "PUT":
                    async with session.put(url, headers=headers, json=data) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            logger.error(f"GitHub API error {response.status}: {error_text}")
                            return {"error": f"GitHub API error {response.status}", "details": error_text}
                
                elif method.upper() == "PATCH":
                    async with session.patch(url, headers=headers, json=data) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            logger.error(f"GitHub API error {response.status}: {error_text}")
                            return {"error": f"GitHub API error {response.status}", "details": error_text}
                
                elif method.upper() == "DELETE":
                    async with session.delete(url, headers=headers) as response:
                        if response.status == 204:  # No content for successful deletion
                            return {"success": True, "message": "Resource deleted successfully"}
                        else:
                            error_text = await response.text()
                            logger.error(f"GitHub API error {response.status}: {error_text}")
                            return {"error": f"GitHub API error {response.status}", "details": error_text}
                            
            except Exception as e:
                logger.error(f"Request error: {e}")
                return {"error": str(e)}
    
    async def get_user_info(self) -> Dict[str, Any]:
        """Get authenticated user information"""
        if not self._get_token():
            return {"error": "GitHub token not configured"}
        
        return await self._make_request("GET", "/user")
    
    async def list_repositories(self, username: Optional[str] = None) -> List[Dict[str, Any]]:
        """List repositories for user or authenticated user"""
        if username:
            endpoint = f"/users/{username}/repos"
        else:
            endpoint = "/user/repos"
        
        result = await self._make_request("GET", endpoint)
        if "error" in result:
            return []
        
        return result if isinstance(result, list) else []
    
    async def get_pull_requests(self, owner: str, repo: str, state: str = "open") -> List[Dict[str, Any]]:
        """Get pull requests for a repository"""
        endpoint = f"/repos/{owner}/{repo}/pulls"
        params = f"?state={state}&sort=updated&direction=desc"
        
        result = await self._make_request("GET", endpoint + params)
        if "error" in result:
            return []
        
        return result if isinstance(result, list) else []
    
    async def get_user_pull_requests(self, state: str = "open") -> List[Dict[str, Any]]:
        """Get pull requests created by the authenticated user across all repositories"""
        # Use GitHub search API to find PRs created by the authenticated user
        user_info = await self.get_user_info()
        if "error" in user_info:
            return []
        
        username = user_info.get("login")
        if not username:
            return []
        
        # Search for PRs created by the user
        query = f"author:{username} is:pr state:{state}"
        endpoint = f"/search/issues?q={query}&sort=updated&order=desc"
        
        result = await self._make_request("GET", endpoint)
        if "error" in result:
            return []
        
        items = result.get("items", [])
        return items
    
    async def get_pull_requests_needing_review(self, state: str = "open") -> List[Dict[str, Any]]:
        """Get pull requests where the authenticated user is a reviewer"""
        # Use GitHub search API to find PRs where user is requested as reviewer
        user_info = await self.get_user_info()
        if "error" in user_info:
            return []
        
        username = user_info.get("login")
        if not username:
            return []
        
        # Search for PRs where user is requested as reviewer
        query = f"review-requested:{username} is:pr state:{state}"
        endpoint = f"/search/issues?q={query}&sort=updated&order=desc"
        
        result = await self._make_request("GET", endpoint)
        if "error" in result:
            return []
        
        items = result.get("items", [])
        return items
        
        result = await self._make_request("GET", endpoint + params)
        if "error" in result:
            return []
        
        return result if isinstance(result, list) else []
    
    async def get_pull_request(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """Get specific pull request details"""
        endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}"
        logger.info(f"Making GitHub API request to: {endpoint}")
        result = await self._make_request("GET", endpoint)
        logger.info(f"GitHub API response type: {type(result)}")
        logger.info(f"GitHub API response: {result}")
        return result
    
    async def get_pull_request_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """Get pull request diff in unified format"""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        headers = {**self._get_headers(), "Accept": "application/vnd.github.v3.diff"}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.error(f"Failed to get diff: {response.status}")
                        return ""
            except Exception as e:
                logger.error(f"Error getting diff: {e}")
                return ""
    
    async def get_pull_request_files(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """Get files changed in pull request"""
        endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}/files"
        result = await self._make_request("GET", endpoint)
        
        if "error" in result:
            return []
        
        return result if isinstance(result, list) else []

    async def get_file_content(self, owner: str, repo: str, pr_number: int, filename: str) -> Dict[str, Any]:
        """Get content of a specific file from a pull request"""
        try:
            # First get the PR details to get the base and head refs
            pr_details = await self.get_pull_request(owner, repo, pr_number)
            if "error" in pr_details:
                return {"error": f"Failed to get PR details: {pr_details['error']}"}
            
            # Get the head ref (the branch with changes)
            head_ref = pr_details.get("head", {}).get("ref", "")
            if not head_ref:
                return {"error": "Could not determine head ref"}
            
            # Get file content from the head branch
            endpoint = f"/repos/{owner}/{repo}/contents/{filename}?ref={head_ref}"
            result = await self._make_request("GET", endpoint)
            
            if "error" in result:
                logger.error(f"Failed to get file content for {filename}: {result['error']}")
                return {"error": f"Failed to get file content: {result['error']}"}
            
            # Decode content if it's base64 encoded
            if "content" in result and result.get("encoding") == "base64":
                import base64
                try:
                    decoded_content = base64.b64decode(result["content"]).decode('utf-8')
                    result["content"] = decoded_content
                except Exception as e:
                    logger.error(f"Failed to decode base64 content: {e}")
                    return {"error": f"Failed to decode file content: {e}"}
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting file content for {filename}: {e}")
            return {"error": str(e)}
    
    async def get_pull_request_comments(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """Get comments on pull request"""
        endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        result = await self._make_request("GET", endpoint)
        
        if "error" in result:
            return []
        
        return result if isinstance(result, list) else []
    
    async def add_pull_request_comment(self, owner: str, repo: str, pr_number: int, 
                                     body: str, commit_id: str = None, path: str = None, 
                                     line: int = None) -> Dict[str, Any]:
        """Add comment to pull request. For inline comments, commit_id, path, and line are required."""
        endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        comment_data = {"body": body}
        # Add specific line comment if provided
        if commit_id is not None and path is not None and line is not None:
            comment_data["commit_id"] = str(commit_id)
            comment_data["path"] = str(path)
            comment_data["line"] = int(line)
        elif any([commit_id, path, line]):
            raise ValueError("All of commit_id, path, and line must be provided for inline comments.")
        return await self._make_request("POST", endpoint, comment_data)
    
    async def add_inline_comment(self, owner: str, repo: str, pr_number: int, commit_id: str, path: str, line: int, body: str) -> Dict[str, Any]:
        """Add an inline comment to a pull request at a specific line"""
        return await self.add_pull_request_comment(
            owner, repo, pr_number, body, commit_id=commit_id, path=path, line=line
        )
    
    async def add_issue_comment(self, owner: str, repo: str, pr_number: int, body: str) -> Dict[str, Any]:
        """Add general comment to pull request (as issue comment)"""
        endpoint = f"/repos/{owner}/{repo}/issues/{pr_number}/comments"
        return await self._make_request("POST", endpoint, {"body": body})
    
    async def get_issue_comments(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """Get all comments for a pull request"""
        endpoint = f"/repos/{owner}/{repo}/issues/{pr_number}/comments"
        result = await self._make_request("GET", endpoint)
        
        if "error" in result:
            return []
        
        return result if isinstance(result, list) else []
    
    async def update_issue_comment(self, owner: str, repo: str, comment_id: int, body: str) -> Dict[str, Any]:
        """Update an existing comment"""
        endpoint = f"/repos/{owner}/{repo}/issues/comments/{comment_id}"
        return await self._make_request("PATCH", endpoint, {"body": body})
    
    async def delete_issue_comment(self, owner: str, repo: str, comment_id: int) -> Dict[str, Any]:
        """Delete a comment"""
        endpoint = f"/repos/{owner}/{repo}/issues/comments/{comment_id}"
        return await self._make_request("DELETE", endpoint)
    
    async def merge_pull_request(self, owner: str, repo: str, pr_number: int, 
                               merge_method: str = "merge", title: Optional[str] = None, 
                               message: Optional[str] = None) -> Dict[str, Any]:
        """Merge pull request"""
        endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}/merge"
        
        merge_data = {"merge_method": merge_method}
        if title:
            merge_data["commit_title"] = title
        if message:
            merge_data["commit_message"] = message
        
        return await self._make_request("PUT", endpoint, merge_data)
    
    async def close_pull_request(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """Close pull request without merging"""
        endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}"
        return await self._make_request("POST", endpoint, {"state": "closed"})
    
    async def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository information"""
        endpoint = f"/repos/{owner}/{repo}"
        return await self._make_request("GET", endpoint)
    
    async def add_labels_to_issue(self, owner: str, repo: str, issue_number: int, labels: List[str]) -> Dict[str, Any]:
        """Add labels to an issue or pull request"""
        endpoint = f"/repos/{owner}/{repo}/issues/{issue_number}/labels"
        return await self._make_request("POST", endpoint, {"labels": labels})
    
    async def remove_label_from_issue(self, owner: str, repo: str, issue_number: int, label_name: str) -> Dict[str, Any]:
        """Remove a specific label from an issue or pull request"""
        endpoint = f"/repos/{owner}/{repo}/issues/{issue_number}/labels/{label_name}"
        return await self._make_request("DELETE", endpoint)
    
    async def get_issue_labels(self, owner: str, repo: str, issue_number: int) -> List[Dict[str, Any]]:
        """Get labels for an issue or pull request"""
        endpoint = f"/repos/{owner}/{repo}/issues/{issue_number}/labels"
        result = await self._make_request("GET", endpoint)
        
        if "error" in result:
            return []
        
        return result if isinstance(result, list) else []
    
    async def create_pull_request_review(self, owner: str, repo: str, pr_number: int, 
                                       event: str = "COMMENT", body: str = "", 
                                       commit_id: str = None) -> Dict[str, Any]:
        """Create a pull request review (approve, request changes, or comment)"""
        endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        
        review_data = {
            "event": event,  # APPROVE, REQUEST_CHANGES, or COMMENT
            "body": body
        }
        
        if commit_id:
            review_data["commit_id"] = commit_id
        
        return await self._make_request("POST", endpoint, review_data)
    
    async def approve_pull_request(self, owner: str, repo: str, pr_number: int, 
                                 body: str = "LGTM") -> Dict[str, Any]:
        """Approve a pull request"""
        return await self.create_pull_request_review(
            owner, repo, pr_number, event="APPROVE", body=body
        )
    
    async def request_changes(self, owner: str, repo: str, pr_number: int, 
                            body: str) -> Dict[str, Any]:
        """Request changes on a pull request"""
        return await self.create_pull_request_review(
            owner, repo, pr_number, event="REQUEST_CHANGES", body=body
        )
    
    async def add_lgtm_label(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """Add LGTM label to a pull request"""
        return await self.add_labels_to_issue(owner, repo, pr_number, ["lgtm"])
    
    async def add_approved_label(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """Add approved label to a pull request"""
        return await self.add_labels_to_issue(owner, repo, pr_number, ["approved"])
    
    async def get_pull_request_reviews(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """Get reviews for a pull request"""
        endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        result = await self._make_request("GET", endpoint)
        
        if "error" in result:
            return []
        
        return result if isinstance(result, list) else []

class PullRequestAnalyzer:
    def __init__(self):
        self.github = GitHubService()
    
    async def analyze_pull_request(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """Comprehensive analysis of a pull request"""
        logger.info(f"Analyzing PR #{pr_number} in {owner}/{repo}")
        
        # Get PR details
        pr_info = await self.github.get_pull_request(owner, repo, pr_number)
        if "error" in pr_info:
            return {"error": "Failed to fetch PR information", "details": pr_info}
        
        # Get files changed
        files = await self.github.get_pull_request_files(owner, repo, pr_number)
        
        # Get diff
        diff = await self.github.get_pull_request_diff(owner, repo, pr_number)
        
        # Get existing comments
        comments = await self.github.get_pull_request_comments(owner, repo, pr_number)
        
        # Analyze the changes
        analysis = {
            "pr_info": {
                "number": pr_info.get("number"),
                "title": pr_info.get("title"),
                "description": pr_info.get("body", ""),
                "author": pr_info.get("user", {}).get("login"),
                "state": pr_info.get("state"),
                "created_at": pr_info.get("created_at"),
                "updated_at": pr_info.get("updated_at"),
                "mergeable": pr_info.get("mergeable"),
                "mergeable_state": pr_info.get("mergeable_state"),
                "base_branch": pr_info.get("base", {}).get("ref"),
                "head_branch": pr_info.get("head", {}).get("ref"),
                "commits": pr_info.get("commits", 0),
                "additions": pr_info.get("additions", 0),
                "deletions": pr_info.get("deletions", 0),
                "changed_files": pr_info.get("changed_files", 0)
            },
            "files_analysis": self._analyze_files(files),
            "diff_analysis": self._analyze_diff(diff),
            "existing_comments": len(comments),
            "issues_detected": [],
            "recommendations": [],
            "complexity_score": self._calculate_complexity_score(files, diff),
            "security_concerns": self._detect_security_issues(files, diff),
            "performance_concerns": self._detect_performance_issues(files, diff)
        }
        
        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(analysis)
        
        return analysis
    
    def _analyze_files(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze changed files"""
        file_types = {}
        large_files = []
        
        for file in files:
            filename = file.get("filename", "")
            extension = os.path.splitext(filename)[1].lower()
            changes = file.get("changes", 0)
            
            # Count file types
            file_types[extension] = file_types.get(extension, 0) + 1
            
            # Identify large changes
            if changes > 100:
                large_files.append({
                    "filename": filename,
                    "changes": changes,
                    "additions": file.get("additions", 0),
                    "deletions": file.get("deletions", 0)
                })
        
        return {
            "total_files": len(files),
            "file_types": file_types,
            "large_files": large_files,
            "languages_detected": list(file_types.keys())
        }
    
    def _analyze_diff(self, diff: str) -> Dict[str, Any]:
        """Analyze diff content for patterns and issues"""
        if not diff:
            return {"error": "No diff content available"}
        
        lines = diff.split('\n')
        added_lines = [line for line in lines if line.startswith('+') and not line.startswith('+++')]
        removed_lines = [line for line in lines if line.startswith('-') and not line.startswith('---')]
        
        analysis = {
            "total_lines": len(lines),
            "added_lines": len(added_lines),
            "removed_lines": len(removed_lines),
            "patterns_detected": {
                "debug_statements": self._find_debug_statements(added_lines),
                "hardcoded_values": self._find_hardcoded_values(added_lines),
                "potential_secrets": self._find_potential_secrets(added_lines),
                "code_smells": self._find_code_smells(added_lines),
                "todo_comments": self._find_todo_comments(added_lines)
            }
        }
        
        return analysis
    
    def _find_debug_statements(self, lines: List[str]) -> List[str]:
        """Find debug/console statements"""
        debug_patterns = [
            r'console\.log',
            r'print\(',
            r'printf\(',
            r'System\.out\.println',
            r'debugger;',
            r'console\.debug',
            r'alert\('
        ]
        
        found = []
        for line in lines:
            for pattern in debug_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    found.append(line.strip())
                    break
        
        return found
    
    def _find_hardcoded_values(self, lines: List[str]) -> List[str]:
        """Find potential hardcoded values"""
        patterns = [
            r'["\'][^"\']*(?:password|token|key|secret)[^"\']*["\']',
            r'["\'](?:http://|https://)[^"\']+["\']',
            r'["\'][A-Za-z0-9+/]{20,}={0,2}["\']'  # Base64-like strings
        ]
        
        found = []
        for line in lines:
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    found.append(line.strip())
                    break
        
        return found
    
    def _find_potential_secrets(self, lines: List[str]) -> List[str]:
        """Find potential secrets or credentials"""
        secret_patterns = [
            r'(?i)api[_\s]*key[_\s]*[:=][_\s]*["\'][^"\']+["\']',
            r'(?i)secret[_\s]*[:=][_\s]*["\'][^"\']+["\']',
            r'(?i)password[_\s]*[:=][_\s]*["\'][^"\']+["\']',
            r'(?i)token[_\s]*[:=][_\s]*["\'][^"\']+["\']',
            r'["\'][A-Za-z0-9]{20,}["\']'  # Long alphanumeric strings
        ]
        
        found = []
        for line in lines:
            for pattern in secret_patterns:
                if re.search(pattern, line):
                    found.append(line.strip())
                    break
        
        return found
    
    def _find_code_smells(self, lines: List[str]) -> List[str]:
        """Find code smell indicators"""
        smell_patterns = [
            r'//\s*TODO',
            r'//\s*FIXME',
            r'//\s*HACK',
            r'//\s*XXX',
            r'catch\s*\(\s*\)\s*\{',  # Empty catch blocks
            r'catch\s*\([^)]+\)\s*\{\s*\}',
            r'if\s*\(\s*true\s*\)',  # Always true conditions
            r'if\s*\(\s*false\s*\)'  # Always false conditions
        ]
        
        found = []
        for line in lines:
            for pattern in smell_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    found.append(line.strip())
                    break
        
        return found
    
    def _find_todo_comments(self, lines: List[str]) -> List[str]:
        """Find TODO/FIXME comments"""
        todo_pattern = r'//.*(?:TODO|FIXME|HACK|XXX).*'
        
        found = []
        for line in lines:
            if re.search(todo_pattern, line, re.IGNORECASE):
                found.append(line.strip())
        
        return found
    
    def _calculate_complexity_score(self, files: List[Dict[str, Any]], diff: str) -> int:
        """Calculate PR complexity score (0-100)"""
        score = 0
        
        # File count factor
        file_count = len(files)
        score += min(file_count * 2, 20)
        
        # Changes factor
        total_changes = sum(file.get("changes", 0) for file in files)
        score += min(total_changes // 10, 30)
        
        # File type diversity
        extensions = set(os.path.splitext(file.get("filename", ""))[1] for file in files)
        score += min(len(extensions) * 5, 20)
        
        # Large files factor
        large_files = [f for f in files if f.get("changes", 0) > 100]
        score += len(large_files) * 10
        
        return min(score, 100)
    
    def _detect_security_issues(self, files: List[Dict[str, Any]], diff: str) -> List[str]:
        """Detect potential security issues"""
        issues = []
        
        # Check for common security-sensitive files
        security_files = [
            r'\.env',
            r'config\.py',
            r'settings\.py',
            r'\.yml',
            r'\.yaml',
            r'Dockerfile'
        ]
        
        for file in files:
            filename = file.get("filename", "")
            for pattern in security_files:
                if re.search(pattern, filename, re.IGNORECASE):
                    issues.append(f"Security-sensitive file modified: {filename}")
        
        # Check diff for security patterns
        if diff:
            security_patterns = [
                (r'password\s*=', "Potential password assignment"),
                (r'secret\s*=', "Potential secret assignment"),
                (r'token\s*=', "Potential token assignment"),
                (r'http://', "Non-HTTPS URL found"),
                (r'eval\s*\(', "Use of eval() function"),
                (r'exec\s*\(', "Use of exec() function")
            ]
            
            for pattern, message in security_patterns:
                if re.search(pattern, diff, re.IGNORECASE):
                    issues.append(message)
        
        return issues
    
    def _detect_performance_issues(self, files: List[Dict[str, Any]], diff: str) -> List[str]:
        """Detect potential performance issues"""
        issues = []
        
        if diff:
            performance_patterns = [
                (r'for.*in.*range\s*\(.*len\s*\(', "Inefficient loop pattern"),
                (r'\.append\s*\(.*\)\s*$', "Multiple appends (consider list comprehension)"),
                (r'time\.sleep\s*\(', "Blocking sleep operation"),
                (r'SELECT\s+\*\s+FROM', "SELECT * query (consider specific columns)"),
                (r'\.find_all\s*\(', "Potentially inefficient DOM traversal")
            ]
            
            for pattern, message in performance_patterns:
                if re.search(pattern, diff, re.IGNORECASE):
                    issues.append(message)
        
        return issues
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        # Complexity recommendations
        complexity = analysis.get("complexity_score", 0)
        if complexity > 70:
            recommendations.append("Consider breaking this PR into smaller, focused changes")
        
        # File-based recommendations
        files_analysis = analysis.get("files_analysis", {})
        if len(files_analysis.get("large_files", [])) > 0:
            recommendations.append("Review large file changes carefully - consider if they can be split")
        
        # Pattern-based recommendations
        diff_analysis = analysis.get("diff_analysis", {})
        patterns = diff_analysis.get("patterns_detected", {})
        
        if patterns.get("debug_statements"):
            recommendations.append("Remove debug statements before merging")
        
        if patterns.get("potential_secrets"):
            recommendations.append("Review potential hardcoded secrets/credentials")
        
        if patterns.get("todo_comments"):
            recommendations.append("Address TODO/FIXME comments or create follow-up issues")
        
        # Security recommendations
        security_concerns = analysis.get("security_concerns", [])
        if security_concerns:
            recommendations.append("Review security-sensitive changes carefully")
        
        # Performance recommendations
        performance_concerns = analysis.get("performance_concerns", [])
        if performance_concerns:
            recommendations.append("Consider performance implications of the changes")
        
        # Mergability recommendations
        pr_info = analysis.get("pr_info", {})
        if not pr_info.get("mergeable"):
            recommendations.append("Resolve merge conflicts before proceeding")
        
        return recommendations

# Global analyzer instance
github_service = GitHubService()
pr_analyzer = PullRequestAnalyzer() 
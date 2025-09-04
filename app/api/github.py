from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging

from app.services.github_service import github_service, pr_analyzer, GitHubService
from app.services.code_review_ai import ai_code_reviewer
from app.services.secure_config import secure_config

logger = logging.getLogger(__name__)

github_router = APIRouter()

class PRReviewRequest(BaseModel):
    owner: str
    repo: str
    pr_number: int
    model_preference: Optional[str] = "granite"
    auto_comment: bool = False
    preview_only: bool = False

class PRActionRequest(BaseModel):
    owner: str
    repo: str
    pr_number: int
    action: str  # "merge", "close", "comment"
    merge_method: Optional[str] = "merge"  # "merge", "squash", "rebase"
    commit_title: Optional[str] = None
    commit_message: Optional[str] = None
    comment_body: Optional[str] = None
    confirmation: bool = False  # User confirmation required for destructive actions

class PRCommentRequest(BaseModel):
    owner: str
    repo: str
    pr_number: int
    comment_body: str

class RepoListRequest(BaseModel):
    username: Optional[str] = None

class GitHubTokenRequest(BaseModel):
    token: str

class GitHubConfigRequest(BaseModel):
    token: Optional[str] = None
    action: str  # "set", "remove", "test"

class InlineComment(BaseModel):
    file: str
    line: int
    body: str

@github_router.get("/user")
async def get_github_user():
    """Get authenticated GitHub user information"""
    try:
        user_info = await github_service.get_user_info()
        if "error" in user_info:
            raise HTTPException(status_code=401, detail=user_info["error"])
        return {"user": user_info}
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@github_router.post("/repositories")
async def list_repositories(request: RepoListRequest):
    """List repositories for user"""
    try:
        repos = await github_service.list_repositories(request.username)
        return {
            "repositories": repos,
            "count": len(repos)
        }
    except Exception as e:
        logger.error(f"Failed to list repositories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@github_router.get("/repos/{owner}/{repo}/pulls")
async def get_pull_requests(owner: str, repo: str, state: str = "open"):
    """Get pull requests for a repository"""
    try:
        pulls = await github_service.get_pull_requests(owner, repo, state)
        return {
            "pull_requests": pulls,
            "count": len(pulls),
            "repository": f"{owner}/{repo}",
            "state": state
        }
    except Exception as e:
        logger.error(f"Failed to get pull requests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@github_router.get("/repos/{owner}/{repo}/pulls/{pr_number}")
async def get_pull_request_details(owner: str, repo: str, pr_number: int):
    """Get detailed information about a specific pull request"""
    try:
        pr_info = await github_service.get_pull_request(owner, repo, pr_number)
        if "error" in pr_info:
            raise HTTPException(status_code=404, detail=pr_info["error"])
        
        # Get additional details
        files = await github_service.get_pull_request_files(owner, repo, pr_number)
        comments = await github_service.get_pull_request_comments(owner, repo, pr_number)
        
        return {
            "pull_request": pr_info,
            "files": files,
            "comments": comments,
            "files_count": len(files),
            "comments_count": len(comments)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get PR details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@github_router.post("/repos/{owner}/{repo}/pulls/{pr_number}/analyze")
async def analyze_pull_request(owner: str, repo: str, pr_number: int):
    """Perform technical analysis of a pull request"""
    try:
        analysis = await pr_analyzer.analyze_pull_request(owner, repo, pr_number)
        if "error" in analysis:
            raise HTTPException(status_code=400, detail=analysis["error"])
        
        return {
            "analysis": analysis,
            "repository": f"{owner}/{repo}",
            "pr_number": pr_number
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze PR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@github_router.post("/repos/{owner}/{repo}/pulls/{pr_number}/ai-review")
async def ai_review_pull_request(owner: str, repo: str, pr_number: int, request: PRReviewRequest):
    """Perform comprehensive AI-powered code review"""
    try:
        # Override request params with path params for consistency
        request.owner = owner
        request.repo = repo
        request.pr_number = pr_number
        
        logger.info(f"Starting AI review for PR #{pr_number} in {owner}/{repo}")
        
        review_result = await ai_code_reviewer.comprehensive_review(
            owner, repo, pr_number, request.model_preference
        )
        
        if "error" in review_result:
            raise HTTPException(status_code=400, detail=review_result["error"])
        
        return {
            "ai_review": review_result,
            "repository": f"{owner}/{repo}",
            "pr_number": pr_number,
            "model_used": request.model_preference or "granite"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform AI review: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@github_router.post("/repos/{owner}/{repo}/pulls/{pr_number}/review-comment")
async def generate_review_comment(owner: str, repo: str, pr_number: int, request: PRReviewRequest):
    """Generate and optionally post AI review comment"""
    try:
        # Override request params with path params for consistency
        request.owner = owner
        request.repo = repo
        request.pr_number = pr_number
        
        logger.info(f"Generating review comment for PR #{pr_number} in {owner}/{repo} (preview_only: {request.preview_only})")
        
        if request.preview_only:
            # Generate comments for preview only, don't post to GitHub
            comments = await ai_code_reviewer.generate_review_comments_preview(
                owner, repo, pr_number, request.model_preference
            )
            
            if "error" in comments:
                raise HTTPException(status_code=400, detail=comments["error"])
            
            return {
                "comments": comments,
                "repository": f"{owner}/{repo}",
                "pr_number": pr_number,
                "preview_mode": True
            }
        else:
            # Original behavior - generate and post comment
            comment_result = await ai_code_reviewer.generate_review_comment(
                owner, repo, pr_number, request.model_preference, request.auto_comment
            )
            
            if "error" in comment_result:
                raise HTTPException(status_code=400, detail=comment_result["error"])
            
            return {
                "comment_result": comment_result,
                "repository": f"{owner}/{repo}",
                "pr_number": pr_number,
                "auto_posted": comment_result.get("auto_posted", False)
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate review comment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@github_router.post("/repos/{owner}/{repo}/pulls/{pr_number}/comment")
async def add_pr_comment(owner: str, repo: str, pr_number: int, request: PRCommentRequest):
    """Add a comment to a pull request"""
    try:
        if not request.comment_body:
            raise HTTPException(status_code=400, detail="Comment body is required")
        
        comment_result = await github_service.add_issue_comment(
            owner, repo, pr_number, request.comment_body
        )
        
        if "error" in comment_result:
            raise HTTPException(status_code=400, detail=comment_result["error"])
        
        return {
            "comment": comment_result,
            "repository": f"{owner}/{repo}",
            "pr_number": pr_number
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add comment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@github_router.get("/repos/{owner}/{repo}/pulls/{pr_number}/comments")
async def get_pr_comments(owner: str, repo: str, pr_number: int):
    """Get all comments for a pull request"""
    try:
        comments = await github_service.get_issue_comments(owner, repo, pr_number)
        
        if "error" in comments:
            raise HTTPException(status_code=400, detail=comments["error"])
        
        return {
            "comments": comments,
            "repository": f"{owner}/{repo}",
            "pr_number": pr_number,
            "count": len(comments) if isinstance(comments, list) else 0
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get comments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class CommentUpdateRequest(BaseModel):
    owner: str
    repo: str
    pr_number: int
    comment_id: int
    comment_body: str

@github_router.patch("/repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id}")
async def update_pr_comment(owner: str, repo: str, pr_number: int, comment_id: int, request: CommentUpdateRequest):
    """Update a comment on a pull request"""
    try:
        if not request.comment_body:
            raise HTTPException(status_code=400, detail="Comment body is required")
        
        comment_result = await github_service.update_issue_comment(
            owner, repo, comment_id, request.comment_body
        )
        
        if "error" in comment_result:
            raise HTTPException(status_code=400, detail=comment_result["error"])
        
        return {
            "comment": comment_result,
            "repository": f"{owner}/{repo}",
            "pr_number": pr_number,
            "comment_id": comment_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update comment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class CommentDeleteRequest(BaseModel):
    owner: str
    repo: str
    pr_number: int
    comment_id: int

@github_router.delete("/repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id}")
async def delete_pr_comment(owner: str, repo: str, pr_number: int, comment_id: int, request: CommentDeleteRequest):
    """Delete a comment from a pull request"""
    try:
        delete_result = await github_service.delete_issue_comment(
            owner, repo, comment_id
        )
        
        if "error" in delete_result:
            raise HTTPException(status_code=400, detail=delete_result["error"])
        
        return {
            "success": True,
            "message": "Comment deleted successfully",
            "repository": f"{owner}/{repo}",
            "pr_number": pr_number,
            "comment_id": comment_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete comment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@github_router.post("/repos/{owner}/{repo}/pulls/{pr_number}/merge")
async def merge_pull_request(owner: str, repo: str, pr_number: int, request: PRActionRequest):
    """Merge a pull request with user confirmation"""
    try:
        # Require confirmation for destructive actions
        if not request.confirmation:
            # First, get PR info to show user what they're about to merge
            pr_info = await github_service.get_pull_request(owner, repo, pr_number)
            if "error" in pr_info:
                raise HTTPException(status_code=404, detail=pr_info["error"])
            
            return {
                "confirmation_required": True,
                "action": "merge",
                "pr_info": {
                    "number": pr_info.get("number"),
                    "title": pr_info.get("title"),
                    "author": pr_info.get("user", {}).get("login"),
                    "base_branch": pr_info.get("base", {}).get("ref"),
                    "head_branch": pr_info.get("head", {}).get("ref"),
                    "mergeable": pr_info.get("mergeable"),
                    "mergeable_state": pr_info.get("mergeable_state")
                },
                "merge_method": request.merge_method,
                "message": f"⚠️ Are you sure you want to merge PR #{pr_number}? This action cannot be undone.",
                "instructions": "Set 'confirmation: true' in your request to proceed with the merge."
            }
        
        # User confirmed - proceed with merge
        logger.info(f"Merging PR #{pr_number} in {owner}/{repo} with method: {request.merge_method}")
        
        merge_result = await github_service.merge_pull_request(
            owner, repo, pr_number, 
            request.merge_method or "merge",
            request.commit_title or None,
            request.commit_message or None
        )
        
        if "error" in merge_result:
            raise HTTPException(status_code=400, detail=merge_result["error"])
        
        return {
            "merge_result": merge_result,
            "repository": f"{owner}/{repo}",
            "pr_number": pr_number,
            "action": "merged",
            "merge_method": request.merge_method or "merge"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to merge PR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@github_router.post("/repos/{owner}/{repo}/pulls/{pr_number}/close")
async def close_pull_request(owner: str, repo: str, pr_number: int, request: PRActionRequest):
    """Close a pull request with user confirmation"""
    try:
        # Require confirmation for destructive actions
        if not request.confirmation:
            # First, get PR info to show user what they're about to close
            pr_info = await github_service.get_pull_request(owner, repo, pr_number)
            if "error" in pr_info:
                raise HTTPException(status_code=404, detail=pr_info["error"])
            
            return {
                "confirmation_required": True,
                "action": "close",
                "pr_info": {
                    "number": pr_info.get("number"),
                    "title": pr_info.get("title"),
                    "author": pr_info.get("user", {}).get("login"),
                    "state": pr_info.get("state")
                },
                "message": f"⚠️ Are you sure you want to close PR #{pr_number} without merging?",
                "instructions": "Set 'confirmation: true' in your request to proceed with closing."
            }
        
        # User confirmed - proceed with close
        logger.info(f"Closing PR #{pr_number} in {owner}/{repo}")
        
        close_result = await github_service.close_pull_request(owner, repo, pr_number)
        
        if "error" in close_result:
            raise HTTPException(status_code=400, detail=close_result["error"])
        
        return {
            "close_result": close_result,
            "repository": f"{owner}/{repo}",
            "pr_number": pr_number,
            "action": "closed"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to close PR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@github_router.get("/repos/{owner}/{repo}/info")
async def get_repository_info(owner: str, repo: str):
    """Get repository information"""
    try:
        repo_info = await github_service.get_repository_info(owner, repo)
        if "error" in repo_info:
            raise HTTPException(status_code=404, detail=repo_info["error"])
        
        return {
            "repository": repo_info,
            "owner": owner,
            "repo": repo
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get repository info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@github_router.get("/test")
async def test_github_connection():
    """Test GitHub connection and token validity"""
    try:
        user_info = await github_service.get_user_info()
        if "error" in user_info:
            raise HTTPException(status_code=401, detail=user_info["error"])
        
        return {
            "success": True,
            "message": "GitHub connection test successful",
            "user_info": {
                "login": user_info.get("login"),
                "name": user_info.get("name"),
                "email": user_info.get("email")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GitHub connection test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@github_router.get("/health")
async def github_health_check():
    """Check GitHub service health and configuration"""
    try:
        user_info = await github_service.get_user_info()
        
        if "error" in user_info:
            return {
                "status": "unhealthy",
                "github_token_configured": bool(github_service._get_token()),
                "error": user_info["error"]
            }
        
        return {
            "status": "healthy",
            "github_token_configured": True,
            "authenticated_user": user_info.get("login"),
            "api_rate_limit": user_info.get("public_repos", "unknown")
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "github_token_configured": bool(github_service._get_token()),
            "error": str(e)
        }

@github_router.get("/config")
async def get_github_config():
    """Get GitHub configuration status"""
    try:
        config_status = secure_config.get_github_config_status()
        return {
            "github_config": config_status,
            "integration_status": "configured" if config_status["token_configured"] else "not_configured"
        }
    except Exception as e:
        logger.error(f"Failed to get GitHub config: {e}")
        return {
            "github_config": {
                "token_configured": False,
                "token_source": "none",
                "token_masked": None
            },
            "integration_status": "error",
            "error": str(e)
        }

@github_router.post("/config")
async def configure_github(request: GitHubConfigRequest):
    """Configure GitHub integration"""
    try:
        if request.action == "set":
            if not request.token:
                raise HTTPException(status_code=400, detail="Token is required for set action")
            
            # Validate token format
            validation = secure_config.validate_github_token(request.token)
            if not validation["valid"]:
                raise HTTPException(status_code=400, detail=f"Invalid token: {validation['error']}")
            
            # Test the token by making a simple API call
            temp_service = GitHubService()
            # Temporarily set token for testing
            old_get_token = temp_service._get_token
            temp_service._get_token = lambda: request.token
            
            user_info = await temp_service.get_user_info()
            if "error" in user_info:
                raise HTTPException(status_code=400, detail=f"Token test failed: {user_info['error']}")
            
            # Save the token
            success = secure_config.set_github_token(request.token)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to save GitHub token")
            
            return {
                "success": True,
                "message": "GitHub token configured successfully",
                "user_info": {
                    "login": user_info.get("login"),
                    "name": user_info.get("name"),
                    "email": user_info.get("email")
                },
                "config_status": secure_config.get_github_config_status()
            }
        
        elif request.action == "remove":
            success = secure_config.remove_github_token()
            if not success:
                raise HTTPException(status_code=500, detail="Failed to remove GitHub token")
            
            return {
                "success": True,
                "message": "GitHub token removed successfully",
                "config_status": secure_config.get_github_config_status()
            }
        
        elif request.action == "test":
            current_token = secure_config.get_github_token()
            if not current_token:
                return {
                    "success": False,
                    "message": "No GitHub token configured",
                    "test_result": "no_token"
                }
            
            # Test current token
            user_info = await github_service.get_user_info()
            if "error" in user_info:
                return {
                    "success": False,
                    "message": f"Token test failed: {user_info['error']}",
                    "test_result": "invalid_token"
                }
            
            return {
                "success": True,
                "message": "GitHub token is working correctly",
                "test_result": "valid",
                "user_info": {
                    "login": user_info.get("login"),
                    "name": user_info.get("name"),
                    "email": user_info.get("email")
                }
            }
        
        else:
            raise HTTPException(status_code=400, detail="Invalid action. Use 'set', 'remove', or 'test'")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring GitHub: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@github_router.post("/config/validate-token")
async def validate_github_token(request: GitHubTokenRequest):
    """Validate GitHub token format and test authentication"""
    try:
        # Validate format
        validation = secure_config.validate_github_token(request.token)
        if not validation["valid"]:
            return {
                "valid": False,
                "error": validation["error"],
                "test_result": "invalid_format"
            }
        
        # Test the token
        temp_service = GitHubService()
        # Temporarily override token for testing
        temp_service._get_token = lambda: request.token
        
        user_info = await temp_service.get_user_info()
        if "error" in user_info:
            return {
                "valid": False,
                "error": user_info["error"],
                "test_result": "authentication_failed"
            }
        
        return {
            "valid": True,
            "test_result": "success",
            "user_info": {
                "login": user_info.get("login"),
                "name": user_info.get("name"),
                "email": user_info.get("email"),
                "public_repos": user_info.get("public_repos"),
                "private_repos": user_info.get("total_private_repos")
            }
        }
    
    except Exception as e:
        logger.error(f"Error validating GitHub token: {e}")
        return {
            "valid": False,
            "error": str(e),
            "test_result": "validation_error"
        } 

@github_router.get("/repos/{owner}/{repo}/pulls/{pr_number}/auto-review")
async def auto_review_preview(owner: str, repo: str, pr_number: int, preview: bool = True):
    """Preview AI-generated inline review comments for a PR (does not post)"""
    try:
        # 1. Fetch changed files and diffs
        pr_files = await github_service.get_pull_request_files(owner, repo, pr_number)
        pr_info = await github_service.get_pull_request(owner, repo, pr_number)
        commit_id = pr_info.get('head', {}).get('sha')
        comments = []
        
        # LIMIT: Only process first 10 files and max 50 lines to prevent infinite loops
        MAX_FILES = 10
        MAX_LINES = 50
        processed_files = 0
        processed_lines = 0
        
        # 2. For each file, parse the patch and generate comments
        for file in pr_files:
            if processed_files >= MAX_FILES:
                break
                
            filename = file.get('filename')
            patch = file.get('patch')
            if not patch:
                continue
                
            processed_files += 1
            
            # Parse the patch to get changed lines
            changed_lines = []
            old_line = 0
            new_line = 0
            for line in patch.split('\n'):
                if line.startswith('@@'):
                    # Example: @@ -1,7 +1,8 @@
                    parts = line.split(' ')
                    new_line_info = parts[2]  # e.g. '+1,8'
                    new_line = int(new_line_info.split(',')[0][1:])
                elif line.startswith('+') and not line.startswith('+++'):
                    changed_lines.append((new_line, line[1:]))
                    new_line += 1
                elif not line.startswith('-'):
                    new_line += 1
            
            # LIMIT: Only process first 50 lines per file
            changed_lines = changed_lines[:MAX_LINES]
            
            # For each changed line, generate an AI review comment
            for line_num, code in changed_lines:
                if processed_lines >= MAX_LINES:
                    break
                    
                # Skip empty lines or very short changes
                if len(code.strip()) < 3:
                    continue
                    
                # Compose prompt for the AI model
                prompt = f"""
Review the following code change for logic, performance, readability, edge cases, and test coverage. Respond with a GitHub-style markdown comment, tied to the specific line, or say 'LGTM' if no issues.

File: {filename}
Line {line_num}:
{code}
"""
                try:
                    # Call your AI model here (replace with your actual call)
                    ai_comment = await ai_code_reviewer.review_code_line(filename, line_num, code, prompt)
                    if ai_comment and ai_comment.strip().lower() != 'lgtm':
                        comments.append({
                            'file': filename,
                            'line': line_num,
                            'body': ai_comment.strip()
                        })
                    processed_lines += 1
                except Exception as e:
                    logger.error(f"Failed to review line {line_num} in {filename}: {e}")
                    continue
                    
            if processed_lines >= MAX_LINES:
                break
                
        return {
            "comments": comments,
            "limits_applied": {
                "max_files": MAX_FILES,
                "max_lines": MAX_LINES,
                "files_processed": processed_files,
                "lines_processed": processed_lines
            }
        }
    except Exception as e:
        logging.exception("Auto review preview failed")
        raise HTTPException(status_code=500, detail=str(e))

class AutoReviewCommentsRequest(BaseModel):
    comments: List[InlineComment]

@github_router.post("/repos/{owner}/{repo}/pulls/{pr_number}/auto-review")
async def auto_review_post(owner: str, repo: str, pr_number: int, request: AutoReviewCommentsRequest):
    """Post AI-generated inline review comments to GitHub"""
    try:
        pr_info = await github_service.get_pull_request(owner, repo, pr_number)
        commit_id = pr_info.get('head', {}).get('sha')
        results = []
        for comment in request.comments:
            # Post each comment as an inline comment
            result = await github_service.add_inline_comment(
                owner, repo, pr_number,
                commit_id=commit_id,
                path=comment.file,
                line=comment.line,
                body=comment.body
            )
            results.append(result)
        return {"posted": len(results), "results": results}
    except Exception as e:
        logging.exception("Auto review post failed")
        raise HTTPException(status_code=500, detail=str(e)) 
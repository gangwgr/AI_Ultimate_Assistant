#!/bin/bash

echo "🚀 GitHub PR Review Integration Demo for AI Ultimate Assistant"
echo "============================================================="
echo

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if server is running
echo -e "${BLUE}1. Checking AI Ultimate Assistant Server Status...${NC}"
curl -s http://localhost:8000/api/github/health | jq .
echo

# Test GitHub integration help
echo -e "${BLUE}2. GitHub Integration Help${NC}"
curl -s -X POST http://localhost:8000/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Help with GitHub"}' | jq -r '.response' | sed 's/<br>/\n/g'
echo

# Test GitHub intent recognition
echo -e "${BLUE}3. Testing GitHub Intent Recognition${NC}"
echo -e "${YELLOW}Testing: 'Review PR #123 in microsoft/vscode'${NC}"
curl -s -X POST http://localhost:8000/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Review PR #123 in microsoft/vscode"}' | jq -r '.response' | sed 's/<br>/\n/g'
echo

echo -e "${YELLOW}Testing: 'List GitHub repositories'${NC}"
curl -s -X POST http://localhost:8000/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "List GitHub repositories"}' | jq -r '.response' | sed 's/<br>/\n/g'
echo

echo -e "${YELLOW}Testing: 'List PRs in openshift/hypershift'${NC}"
curl -s -X POST http://localhost:8000/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "List PRs in openshift/hypershift"}' | jq -r '.response' | sed 's/<br>/\n/g'
echo

echo -e "${YELLOW}Testing: 'Merge PR #456 in owner/repo'${NC}"
curl -s -X POST http://localhost:8000/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Merge PR #456 in owner/repo"}' | jq -r '.response' | sed 's/<br>/\n/g'
echo

# Test GitHub API endpoints directly
echo -e "${BLUE}4. Testing GitHub API Endpoints${NC}"
echo -e "${YELLOW}GET /api/github/health${NC}"
curl -s http://localhost:8000/api/github/health | jq .
echo

echo -e "${YELLOW}Available GitHub API Endpoints:${NC}"
echo "  GET    /api/github/health                              - Health check"
echo "  GET    /api/github/user                                - Get user info"
echo "  POST   /api/github/repositories                        - List repositories"
echo "  GET    /api/github/repos/{owner}/{repo}/pulls          - Get pull requests"
echo "  GET    /api/github/repos/{owner}/{repo}/pulls/{number} - Get PR details"
echo "  POST   /api/github/repos/{owner}/{repo}/pulls/{number}/analyze    - Technical analysis"
echo "  POST   /api/github/repos/{owner}/{repo}/pulls/{number}/ai-review  - AI code review"
echo "  POST   /api/github/repos/{owner}/{repo}/pulls/{number}/merge      - Merge PR (with confirmation)"
echo "  POST   /api/github/repos/{owner}/{repo}/pulls/{number}/close      - Close PR (with confirmation)"
echo "  POST   /api/github/repos/{owner}/{repo}/pulls/{number}/comment    - Add comment"
echo

# Configuration instructions
echo -e "${GREEN}🔧 Configuration Instructions${NC}"
echo "============================================="
echo
echo "To enable full GitHub functionality, configure a GitHub token:"
echo
echo "1. Create a GitHub Personal Access Token:"
echo "   - Go to GitHub → Settings → Developer settings → Personal access tokens"
echo "   - Generate new token (classic)"
echo "   - Select scopes: repo, pull_requests, issues"
echo
echo "2. Add token to environment:"
echo "   export GITHUB_TOKEN='your_token_here'"
echo "   # or add to .env file:"
echo "   echo 'GITHUB_TOKEN=your_token_here' >> .env"
echo
echo "3. Restart the AI Ultimate Assistant server"
echo

echo -e "${GREEN}✨ Features Implemented${NC}"
echo "=========================="
echo "✅ GitHub API Integration"
echo "✅ AI-Powered Code Review (Multi-model: Granite, Gemini, OpenAI, Ollama)"
echo "✅ Pull Request Analysis (Security, Performance, Complexity scoring)"
echo "✅ Intelligent Comment Generation"
echo "✅ Merge/Close with User Confirmation"
echo "✅ Repository and PR Listing"
echo "✅ Natural Language Intent Recognition"
echo "✅ AI Agent Integration"
echo "✅ API Endpoints with Full CRUD Operations"
echo "✅ Error Handling and Fallbacks"
echo "✅ Security-first Design (confirmation required for destructive actions)"
echo

echo -e "${GREEN}🎯 Example Commands for AI Agent${NC}"
echo "=================================="
echo "• 'Review PR #123 in microsoft/vscode using granite'"
echo "• 'List open PRs in openshift/hypershift'"
echo "• 'Show my GitHub repositories'"
echo "• 'Add comment to PR #456: This looks good to merge!'"
echo "• 'Merge PR #789 with squash method'"
echo "• 'Close PR #101 in owner/repo'"
echo "• 'Analyze code quality for PR #555'"
echo

echo -e "${BLUE}Demo completed! GitHub PR Review Integration is ready! 🎉${NC}" 
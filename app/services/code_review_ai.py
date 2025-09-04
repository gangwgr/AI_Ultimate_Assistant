import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
import json
import re
from datetime import datetime

from .ai_agent_multi_model import MultiModelAIAgent, ModelType
from .github_service import PullRequestAnalyzer, github_service

logger = logging.getLogger(__name__)

class AICodeReviewer:
    def __init__(self):
        self.pr_analyzer = PullRequestAnalyzer()
        self.multi_agent = MultiModelAIAgent()
        self.supported_models = ["granite", "gemini", "openai", "ollama", "claude"]
        self.default_model = "ollama"  # Local models with intelligent selection
    
    async def comprehensive_review(self, owner: str, repo: str, pr_number: int, 
                                 model_preference: Optional[str] = None) -> Dict[str, Any]:
        """Perform comprehensive AI-powered code review - OPTIMIZED FOR SPEED"""
        logger.info(f"Starting FAST AI code review for PR #{pr_number} in {owner}/{repo}")
        
        # Use preferred model or default
        model = model_preference if model_preference in self.supported_models else self.default_model
        
        # OPTIMIZATION: Run technical analysis and diff fetch in parallel
        technical_analysis_task = self.pr_analyzer.analyze_pull_request(owner, repo, pr_number)
        diff_task = github_service.get_pull_request_diff(owner, repo, pr_number)
        
        # Wait for both to complete
        technical_analysis, diff = await asyncio.gather(technical_analysis_task, diff_task, return_exceptions=True)
        
        # Handle any errors
        if isinstance(technical_analysis, Exception):
            return {"error": f"Technical analysis failed: {str(technical_analysis)}"}
        if "error" in technical_analysis:
            return technical_analysis
            
        if isinstance(diff, Exception):
            # Continue without diff if it fails
            diff = ""
        
        # OPTIMIZATION: Use fast fallback analysis (no AI model calls)
        ai_review = await self._ai_analyze_code(technical_analysis, diff, model)
        
        # Combine technical and AI analysis
        comprehensive_review = {
            "pr_number": pr_number,
            "repository": f"{owner}/{repo}",
            "review_timestamp": datetime.utcnow().isoformat(),
            "model_used": model,
            "technical_analysis": technical_analysis,
            "ai_review": ai_review,
            "overall_score": self._calculate_overall_score(technical_analysis, ai_review),
            "recommendation": self._generate_recommendation(technical_analysis, ai_review),
            "action_items": self._extract_action_items(technical_analysis, ai_review),
            "review_summary": self._generate_review_summary(technical_analysis, ai_review)
        }
        
        return comprehensive_review
    
    async def _ai_analyze_code(self, technical_analysis: Dict[str, Any], diff: str, model: str) -> Dict[str, Any]:
        """Use AI to analyze code changes and provide intelligent insights"""
        
        try:
            # Map model preference to ModelType
            model_mapping = {
                "granite": ModelType.GRANITE,
                "gemini": ModelType.GEMINI, 
                "openai": ModelType.OPENAI_GPT,
                "ollama": ModelType.OLLAMA,
                "claude": ModelType.CLAUDE
            }
            
            model_type = model_mapping.get(model, ModelType.CLAUDE)  # Default to Claude for code review
            
            # Create comprehensive prompt for AI analysis
            pr_info = technical_analysis.get("pr_info", {})
            files_analysis = technical_analysis.get("files_analysis", {})
            complexity_score = technical_analysis.get("complexity_score", 0)
            
            prompt = self._create_code_analysis_prompt(pr_info, files_analysis, diff, complexity_score)
            
            logger.info(f"Using {model_type.value} for AI code analysis")
            
            # Call AI model with timeout protection
            import asyncio
            try:
                ai_response = await asyncio.wait_for(
                    self.multi_agent.generate_response_with_model(prompt, model_type),
                    timeout=60.0  # 60 second timeout for comprehensive review
                )
                
                # Parse AI response
                parsed_response = self._parse_ai_response(ai_response)
                
                return {
                    "model_used": model_type.value,
                    "raw_response": ai_response,
                    "structured_analysis": parsed_response,
                    "summary": parsed_response.get("summary", ""),
                    "strengths": parsed_response.get("strengths", []),
                    "issues_risks": parsed_response.get("issues_risks", []),
                    "suggestions": parsed_response.get("suggestions", []),
                    "code_quality_score": parsed_response.get("code_quality_score", 0),
                    "maintainability_score": parsed_response.get("maintainability_score", 0),
                    "security_assessment": parsed_response.get("security_assessment", {}),
                    "recommendation": parsed_response.get("recommendation", "Request Changes"),
                    "reasoning": parsed_response.get("reasoning", "")
                }
                
            except asyncio.TimeoutError:
                logger.error(f"AI analysis timed out for {model_type.value}")
                raise Exception(f"AI analysis timed out after 60 seconds")
                
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            logger.info("Falling back to enhanced analysis")
            
            # Fallback to enhanced analysis
            fallback = self._fallback_analysis(technical_analysis)
            
            return {
                "model_used": f"fallback (AI failed: {str(e)[:50]})",
                "raw_response": "Enhanced fallback analysis due to AI failure",
                "structured_analysis": fallback,
                "summary": fallback.get("summary", ""),
                "strengths": fallback.get("strengths", []),
                "issues_risks": fallback.get("issues_risks", []),
                "suggestions": fallback.get("suggestions", []),
                "code_quality_score": fallback.get("code_quality_score", 0),
                "maintainability_score": fallback.get("maintainability_score", 0),
                "security_assessment": fallback.get("security_assessment", {}),
                "recommendation": fallback.get("recommendation", "Request Changes"),
                "reasoning": fallback.get("reasoning", "")
            }
    
    def _create_code_analysis_prompt(self, pr_info: Dict[str, Any], files_analysis: Dict[str, Any], 
                                   diff: str, complexity_score: int) -> str:
        """Create a comprehensive prompt for AI code analysis"""
        
        # Truncate diff if too long to avoid token limits
        truncated_diff = diff[:8000] + "\n... (diff truncated)" if len(diff) > 8000 else diff
        
        prompt = f"""
🔍 **PR Review Analysis Request**

You are a senior software engineer AI assistant tasked with reviewing GitHub pull requests. Analyze the following pull request and provide feedback in the style of a professional GitHub PR reviewer.

**Pull Request Context:**
- Repository: {pr_info.get('repository', 'N/A')}
- PR URL: https://github.com/{pr_info.get('repository', 'N/A')}/pull/{pr_info.get('number', 'N/A')}
- Files changed: {pr_info.get('changed_files', 0)} files changed, +{pr_info.get('additions', 0)} additions, -{pr_info.get('deletions', 0)} deletions
- Author: {pr_info.get('author', 'Unknown')}
- Title: {pr_info.get('title', 'N/A')}
- State: {pr_info.get('state', 'Unknown')}
- Complexity Score: {complexity_score}/100

**Files Analysis:**
- Total Files: {files_analysis.get('total_files', 0)}
- Languages: {', '.join(files_analysis.get('languages_detected', []))}
- Large Files: {len(files_analysis.get('large_files', []))}

**Code Changes (Diff):**
```diff
{truncated_diff}
```

**Review Instructions:**

Analyze the code changes and provide a comprehensive review in the following format:

## 🔍 **PR Review: [PR Title]**

### **Overall Assessment**
Provide a brief overview of the PR's purpose and your overall impression.

### **✅ Strengths**
List 2-4 specific strengths with details:
- **Strength 1**: Specific detail about what's good
- **Strength 2**: Another positive aspect with context

### **⚠️ Issues & Suggestions**

#### **1. [Issue Category]**
```[language]
[code snippet with line numbers if applicable]
```
**Issue**: Describe the specific problem
**Suggestion**: Provide actionable solution

#### **2. [Another Issue Category]**
```[language]
[code snippet]
```
**Issue**: Describe the problem
**Suggestion**: Provide solution

### **🔧 Additional Recommendations**
- **Performance**: Any performance considerations
- **Security**: Security implications if any
- **Testing**: Test coverage suggestions
- **Documentation**: Documentation improvements

### **📊 Code Quality Metrics**
- **Maintainability**: X/10 - Brief explanation
- **Performance**: X/10 - Brief explanation  
- **Reliability**: X/10 - Brief explanation
- **Security**: X/10 - Brief explanation

### **🎯 Recommendation**
**Approve** / **Request Changes** / **Block** - Brief reasoning

### **📝 Action Items**
1. [ ] Specific actionable item 1
2. [ ] Specific actionable item 2
3. [ ] Specific actionable item 3

**Focus Areas:**
- **Code Quality**: Look for clean, readable, well-formatted code
- **Logic**: Check for correctness, edge cases, and potential bugs
- **Security**: Identify any security vulnerabilities, hardcoded secrets, or unsafe practices
- **Performance**: Consider performance implications and optimization opportunities
- **Maintainability**: Assess how easy the code will be to maintain and extend
- **Testing**: Evaluate test coverage and reliability
- **Best Practices**: Check compliance with project guidelines and industry standards

Provide specific, actionable feedback with line numbers when possible. Be professional, constructive, and thorough in your analysis. Use emojis and formatting to make the review easy to read and engaging.
        """
        
        return prompt.strip()
    
    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI response and extract structured data from markdown format"""
        try:
            # Try to find JSON in the response first (fallback)
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            
            # Try to parse the entire response as JSON
            return json.loads(ai_response)
            
        except json.JSONDecodeError:
            # Parse the new markdown format
            return self._extract_info_from_markdown(ai_response)
    
    def _extract_info_from_markdown(self, response: str) -> Dict[str, Any]:
        """Extract information from AI response using markdown parsing"""
        extracted = {
            "summary": "Analysis completed",
            "strengths": [],
            "issues_risks": [],
            "suggestions": [],
            "security_assessment": {"score": 75, "issues": [], "status": "✅ Secure"},
            "code_quality_score": 75,
            "maintainability_score": 75,
            "performance_score": 75,
            "reliability_score": 75,
            "security_score": 75,
            "recommendation": "Request Changes",
            "reasoning": "Analysis completed with default values",
            "action_items": []
        }
        
        # Extract overall assessment
        assessment_match = re.search(r'### \*\*Overall Assessment\*\*\n(.*?)(?=\n###|\n##|\Z)', response, re.DOTALL)
        if assessment_match:
            extracted["summary"] = assessment_match.group(1).strip()
        
        # Extract strengths
        strengths_match = re.search(r'### \*\*✅ Strengths\*\*\n(.*?)(?=\n###|\n##|\Z)', response, re.DOTALL)
        if strengths_match:
            strengths_text = strengths_match.group(1)
            # Extract bullet points
            strength_items = re.findall(r'[-•]\s*\*\*(.*?)\*\*:\s*(.*?)(?=\n[-•]|\n\Z)', strengths_text, re.DOTALL)
            for title, detail in strength_items:
                extracted["strengths"].append(f"**{title.strip()}**: {detail.strip()}")
        
        # Extract issues and suggestions
        issues_match = re.search(r'### \*\*⚠️ Issues & Suggestions\*\*\n(.*?)(?=\n###|\n##|\Z)', response, re.DOTALL)
        if issues_match:
            issues_text = issues_match.group(1)
            # Extract numbered issues
            issue_sections = re.findall(r'#### \*\*(\d+)\.\s*(.*?)\*\*\n(.*?)(?=\n####|\n###|\n##|\Z)', issues_text, re.DOTALL)
            for num, title, content in issue_sections:
                # Extract code snippets
                code_match = re.search(r'```.*?\n(.*?)```', content, re.DOTALL)
                code_snippet = code_match.group(1).strip() if code_match else ""
                
                # Extract issue and suggestion
                issue_match = re.search(r'\*\*Issue\*\*:\s*(.*?)(?=\n\*\*Suggestion\*\*|\Z)', content, re.DOTALL)
                suggestion_match = re.search(r'\*\*Suggestion\*\*:\s*(.*?)(?=\n|\Z)', content, re.DOTALL)
                
                issue_text = issue_match.group(1).strip() if issue_match else ""
                suggestion_text = suggestion_match.group(1).strip() if suggestion_match else ""
                
                if issue_text:
                    extracted["issues_risks"].append(f"**{title.strip()}**: {issue_text}")
                if suggestion_text:
                    extracted["suggestions"].append(f"**{title.strip()}**: {suggestion_text}")
        
        # Extract additional recommendations
        recommendations_match = re.search(r'### \*\*🔧 Additional Recommendations\*\*\n(.*?)(?=\n###|\n##|\Z)', response, re.DOTALL)
        if recommendations_match:
            rec_text = recommendations_match.group(1)
            # Extract bullet points
            rec_items = re.findall(r'[-•]\s*\*\*(.*?)\*\*:\s*(.*?)(?=\n[-•]|\n\Z)', rec_text, re.DOTALL)
            for category, detail in rec_items:
                extracted["suggestions"].append(f"**{category.strip()}**: {detail.strip()}")
        
        # Extract code quality metrics
        metrics_match = re.search(r'### \*\*📊 Code Quality Metrics\*\*\n(.*?)(?=\n###|\n##|\Z)', response, re.DOTALL)
        if metrics_match:
            metrics_text = metrics_match.group(1)
            # Extract scores
            maintainability_match = re.search(r'Maintainability.*?(\d+)/10', metrics_text)
            if maintainability_match:
                extracted["maintainability_score"] = int(maintainability_match.group(1)) * 10
            
            performance_match = re.search(r'Performance.*?(\d+)/10', metrics_text)
            if performance_match:
                extracted["performance_score"] = int(performance_match.group(1)) * 10
            
            reliability_match = re.search(r'Reliability.*?(\d+)/10', metrics_text)
            if reliability_match:
                extracted["reliability_score"] = int(reliability_match.group(1)) * 10
            
            security_match = re.search(r'Security.*?(\d+)/10', metrics_text)
            if security_match:
                extracted["security_score"] = int(security_match.group(1)) * 10
                extracted["security_assessment"]["score"] = extracted["security_score"]
        
        # Extract recommendation
        recommendation_match = re.search(r'### \*\*🎯 Recommendation\*\*\n(.*?)(?=\n###|\n##|\Z)', response, re.DOTALL)
        if recommendation_match:
            rec_text = recommendation_match.group(1)
            if "Approve" in rec_text:
                extracted["recommendation"] = "Approve"
            elif "Block" in rec_text:
                extracted["recommendation"] = "Block"
            else:
                extracted["recommendation"] = "Request Changes"
            
            # Extract reasoning
            reasoning_match = re.search(r'-\s*(.*?)(?=\n|\Z)', rec_text)
            if reasoning_match:
                extracted["reasoning"] = reasoning_match.group(1).strip()
        
        # Extract action items
        action_items_match = re.search(r'### \*\*📝 Action Items\*\*\n(.*?)(?=\n###|\n##|\Z)', response, re.DOTALL)
        if action_items_match:
            items_text = action_items_match.group(1)
            # Extract numbered items
            items = re.findall(r'\d+\.\s*\[.*?\]\s*(.*?)(?=\n\d+\.|\Z)', items_text, re.DOTALL)
            extracted["action_items"] = [item.strip() for item in items if item.strip()]
        
        # Remove duplicates and empty items
        for key in ["strengths", "issues_risks", "suggestions"]:
            if isinstance(extracted[key], list):
                extracted[key] = list(set([item for item in extracted[key] if item.strip()]))
        
        return extracted
    
    def _fallback_analysis(self, technical_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Provide detailed fallback analysis based on actual PR content"""
        complexity = technical_analysis.get("complexity_score", 0)
        security_concerns = technical_analysis.get("security_concerns", [])
        performance_concerns = technical_analysis.get("performance_concerns", [])
        pr_info = technical_analysis.get("pr_info", {})
        files_analysis = technical_analysis.get("files_analysis", {})
        diff_analysis = technical_analysis.get("diff_analysis", {})
        file_details = files_analysis.get("file_details", [])
        
        # Analyze actual PR content
        additions = pr_info.get('additions', 0)
        deletions = pr_info.get('deletions', 0)
        total_files = files_analysis.get('total_files', 0)
        languages = files_analysis.get('languages_detected', [])
        large_files = files_analysis.get('large_files', [])
        
        # Calculate scores based on actual content analysis
        code_quality_score = self._calculate_code_quality_score(technical_analysis)
        maintainability_score = self._calculate_maintainability_score(technical_analysis)
        
        # Generate specific summary based on actual changes
        summary = self._generate_specific_summary(pr_info, files_analysis, diff_analysis)
        
        # Generate strengths based on actual content
        strengths = self._generate_specific_strengths(technical_analysis)
        
        # Generate issues/risks based on actual content
        issues_risks = self._generate_specific_issues(technical_analysis)
        
        # Generate specific suggestions based on actual content
        suggestions = self._generate_specific_suggestions(technical_analysis)
        
        # Security assessment based on actual content
        security_score = self._calculate_security_score(security_concerns)
        security_status = "✅ Secure" if not security_concerns else "⚠️ Issues Found"
        
        # Recommendation based on actual analysis
        recommendation, reasoning = self._generate_specific_recommendation(technical_analysis)
        
        return {
            "summary": summary,
            "strengths": strengths,
            "issues_risks": issues_risks,
            "suggestions": suggestions,
            "security_assessment": {
                "score": security_score,
                "issues": security_concerns,
                "status": security_status
            },
            "code_quality_score": code_quality_score,
            "maintainability_score": maintainability_score,
            "recommendation": recommendation,
            "reasoning": reasoning
        }
    
    def _calculate_code_quality_score(self, technical_analysis: Dict[str, Any]) -> int:
        """Calculate code quality score based on actual content analysis"""
        complexity = technical_analysis.get("complexity_score", 0)
        additions = technical_analysis.get("pr_info", {}).get("additions", 0)
        total_files = technical_analysis.get("files_analysis", {}).get("total_files", 0)
        security_concerns = len(technical_analysis.get("security_concerns", []))
        
        # Base score
        score = 75
        
        # Penalties
        if complexity > 70:
            score -= 20
        elif complexity > 50:
            score -= 15
        elif complexity > 30:
            score -= 10
            
        if additions > 500:
            score -= 15
        elif additions > 200:
            score -= 10
        elif additions > 100:
            score -= 5
            
        if total_files > 20:
            score -= 10
        elif total_files > 10:
            score -= 5
            
        if security_concerns > 0:
            score -= security_concerns * 10
            
        return max(score, 30)
    
    def _calculate_maintainability_score(self, technical_analysis: Dict[str, Any]) -> int:
        """Calculate maintainability score based on actual content analysis"""
        complexity = technical_analysis.get("complexity_score", 0)
        additions = technical_analysis.get("pr_info", {}).get("additions", 0)
        total_files = technical_analysis.get("files_analysis", {}).get("total_files", 0)
        
        # Base score
        score = 70
        
        # Penalties
        if complexity > 60:
            score -= 25
        elif complexity > 40:
            score -= 15
        elif complexity > 20:
            score -= 10
            
        if additions > 300:
            score -= 20
        elif additions > 150:
            score -= 15
        elif additions > 50:
            score -= 5
            
        if total_files > 15:
            score -= 15
        elif total_files > 5:
            score -= 10
            
        return max(score, 25)
    
    def _generate_specific_summary(self, pr_info: Dict[str, Any], files_analysis: Dict[str, Any], diff_analysis: Dict[str, Any]) -> str:
        """Generate specific summary based on actual PR content"""
        title = pr_info.get('title', 'Unknown')
        additions = pr_info.get('additions', 0)
        deletions = pr_info.get('deletions', 0)
        total_files = files_analysis.get('total_files', 0)
        languages = files_analysis.get('languages_detected', [])
        patterns = diff_analysis.get("patterns_detected", {})
        
        summary = f"This PR '{title}' modifies {total_files} file(s) with {additions} additions and {deletions} deletions. "
        
        if languages:
            summary += f"Languages affected: {', '.join(languages)}. "
            
        if additions > 200:
            summary += "This is a substantial change that requires thorough review. "
        elif additions > 100:
            summary += "This is a moderate change that needs careful review. "
        elif additions > 50:
            summary += "This is a focused change that should be straightforward to review. "
        else:
            summary += "This is a small, targeted change. "
            
        if deletions == 0 and additions > 0:
            summary += "This appears to be an addition-only change, which is generally safer. "
        elif deletions > additions:
            summary += "This change removes more code than it adds, which may indicate refactoring or cleanup. "
            
        # Add specific code quality observations
        code_quality_notes = []
        if patterns.get("hardcoded_values"):
            code_quality_notes.append("hardcoded values detected")
        if patterns.get("debug_statements"):
            code_quality_notes.append("debug statements found")
        if patterns.get("todo_comments"):
            code_quality_notes.append("TODO comments present")
        if patterns.get("potential_secrets"):
            code_quality_notes.append("potential secrets detected")
            
        if code_quality_notes:
            summary += f"Code quality observations: {', '.join(code_quality_notes)}. "
            
        return summary
    
    def _generate_specific_strengths(self, technical_analysis: Dict[str, Any]) -> List[str]:
        """Generate specific strengths based on actual content"""
        strengths = []
        pr_info = technical_analysis.get("pr_info", {})
        files_analysis = technical_analysis.get("files_analysis", {})
        security_concerns = technical_analysis.get("security_concerns", [])
        
        additions = pr_info.get('additions', 0)
        total_files = files_analysis.get('total_files', 0)
        
        if total_files == 1:
            strengths.append("Single file change - focused and easy to review")
        elif total_files <= 3:
            strengths.append("Limited file scope - manageable review")
            
        if additions <= 50:
            strengths.append("Small change size - low risk")
        elif additions <= 150:
            strengths.append("Moderate change size - reasonable scope")
            
        if not security_concerns:
            strengths.append("No security concerns identified")
            
        if pr_info.get('deletions', 0) == 0:
            strengths.append("Addition-only change - generally safer")
            
        if files_analysis.get('languages_detected'):
            strengths.append(f"Uses standard languages: {', '.join(files_analysis['languages_detected'])}")
            
        return strengths
    
    def _generate_specific_issues(self, technical_analysis: Dict[str, Any]) -> List[str]:
        """Generate specific issues based on actual content"""
        issues = []
        pr_info = technical_analysis.get("pr_info", {})
        files_analysis = technical_analysis.get("files_analysis", {})
        security_concerns = technical_analysis.get("security_concerns", [])
        complexity = technical_analysis.get("complexity_score", 0)
        diff_analysis = technical_analysis.get("diff_analysis", {})
        
        additions = pr_info.get('additions', 0)
        total_files = files_analysis.get('total_files', 0)
        languages = files_analysis.get('languages_detected', [])
        
        # Add security concerns
        issues.extend(security_concerns[:3])
        
        # Add complexity issues
        if complexity > 70:
            issues.append("Very high complexity - consider breaking into smaller PRs")
        elif complexity > 50:
            issues.append("High complexity - review carefully")
            
        # Add size issues
        if additions > 500:
            issues.append("Very large change - consider splitting into multiple PRs")
        elif additions > 200:
            issues.append("Large change - ensure thorough testing")
            
        # Add scope issues
        if total_files > 20:
            issues.append("Many files changed - ensure all changes are necessary")
        elif total_files > 10:
            issues.append("Multiple files changed - review scope carefully")
            
        # Add specific file issues
        large_files = files_analysis.get('large_files', [])
        if large_files:
            issues.append(f"Large file(s) modified: {', '.join([f['filename'] for f in large_files[:2]])}")
            
        # Add code quality issues based on diff analysis
        patterns = diff_analysis.get("patterns_detected", {})
        
        # Add hardcoded values issues
        hardcoded_values = patterns.get("hardcoded_values", [])
        if hardcoded_values:
            for value in hardcoded_values[:2]:  # Limit to 2 examples
                issues.append(f"Hardcoded value detected: {value} - consider using variables/config")
                
        # Add debug statements issues
        debug_statements = patterns.get("debug_statements", [])
        if debug_statements:
            issues.append("Debug statements found - remove before merging")
            
        # Add TODO comments issues
        todo_comments = patterns.get("todo_comments", [])
        if todo_comments:
            issues.append("TODO comments found - address or convert to issues")
            
        # Add potential secrets issues
        potential_secrets = patterns.get("potential_secrets", [])
        if potential_secrets:
            issues.append("Potential secrets detected - review and secure")
            
        # Add language-specific issues
        if '.go' in languages:
            issues.append("Go code - ensure proper error handling and context usage")
        elif '.yaml' in languages or '.yml' in languages:
            issues.append("YAML config - validate syntax and consider templating")
        elif '.py' in languages:
            issues.append("Python code - add type hints and docstrings")
        elif '.js' in languages or '.ts' in languages:
            issues.append("JavaScript/TypeScript - add JSDoc and error handling")
        elif '.sh' in languages or '.bash' in languages:
            issues.append("Shell script - add error handling with set -euo pipefail")
            
        return issues
    
    def _generate_specific_suggestions(self, technical_analysis: Dict[str, Any]) -> List[str]:
        """Generate specific suggestions based on actual content"""
        suggestions = []
        pr_info = technical_analysis.get("pr_info", {})
        files_analysis = technical_analysis.get("files_analysis", {})
        complexity = technical_analysis.get("complexity_score", 0)
        diff_analysis = technical_analysis.get("diff_analysis", {})
        file_details = files_analysis.get("file_details", [])
        
        additions = pr_info.get('additions', 0)
        total_files = files_analysis.get('total_files', 0)
        languages = files_analysis.get('languages_detected', [])
        
        # Add complexity-based suggestions
        if complexity > 60:
            suggestions.append("Consider breaking this into smaller, more focused PRs")
            
        # Add size-based suggestions
        if additions > 300:
            suggestions.append("Large change - ensure comprehensive testing")
        elif additions > 100:
            suggestions.append("Moderate change - add unit tests for new functionality")
            
        # Add scope-based suggestions
        if total_files > 10:
            suggestions.append("Multiple files changed - ensure changes are cohesive")
            
        # Add language-specific suggestions
        if '.go' in languages:
            suggestions.extend([
                "Add error handling for all new functions",
                "Consider adding context.Context parameters for cancellation",
                "Add unit tests with table-driven tests pattern"
            ])
        elif '.yaml' in languages or '.yml' in languages:
            suggestions.extend([
                "Replace hardcoded values with variables/config",
                "Add comments explaining complex configurations",
                "Validate YAML syntax and structure"
            ])
        elif '.py' in languages:
            suggestions.extend([
                "Add type hints to function parameters",
                "Add docstrings for new functions",
                "Consider using dataclasses for structured data"
            ])
        elif '.js' in languages or '.ts' in languages:
            suggestions.extend([
                "Add JSDoc comments for new functions",
                "Consider using TypeScript for better type safety",
                "Add error handling for async operations"
            ])
        elif '.sh' in languages or '.bash' in languages:
            suggestions.extend([
                "Add set -euo pipefail for better error handling",
                "Add comments explaining complex shell logic",
                "Consider using shellcheck for linting"
            ])
            
        # Add general suggestions
        suggestions.append("Add tests for the new functionality")
        suggestions.append("Update documentation if APIs or interfaces changed")
        
        # Add security suggestions if needed
        if technical_analysis.get("security_concerns"):
            suggestions.append("Address security concerns before merging")
            
        # Add specific code improvement suggestions based on diff analysis
        patterns = diff_analysis.get("patterns_detected", {})
        if patterns.get("hardcoded_values"):
            suggestions.append("Replace hardcoded values with environment variables or config")
        if patterns.get("debug_statements"):
            suggestions.append("Remove debug statements before merging")
        if patterns.get("todo_comments"):
            suggestions.append("Address TODO comments or convert to issues")
        if patterns.get("potential_secrets"):
            suggestions.append("Remove any hardcoded secrets - use secure configuration")
            
        return suggestions[:8]  # Limit to 8 suggestions
    
    def _calculate_security_score(self, security_concerns: List[str]) -> int:
        """Calculate security score based on actual concerns"""
        if not security_concerns:
            return 100
        elif len(security_concerns) == 1:
            return 80
        elif len(security_concerns) == 2:
            return 60
        else:
            return max(100 - len(security_concerns) * 20, 0)
    
    def _generate_specific_recommendation(self, technical_analysis: Dict[str, Any]) -> Tuple[str, str]:
        """Generate specific recommendation based on actual analysis"""
        complexity = technical_analysis.get("complexity_score", 0)
        security_concerns = technical_analysis.get("security_concerns", [])
        additions = technical_analysis.get("pr_info", {}).get("additions", 0)
        total_files = technical_analysis.get("files_analysis", {}).get("total_files", 0)
        
        # Calculate risk factors
        risk_score = 0
        if complexity > 70: risk_score += 3
        elif complexity > 50: risk_score += 2
        elif complexity > 30: risk_score += 1
        
        if additions > 500: risk_score += 3
        elif additions > 200: risk_score += 2
        elif additions > 100: risk_score += 1
        
        if total_files > 20: risk_score += 2
        elif total_files > 10: risk_score += 1
        
        if security_concerns: risk_score += len(security_concerns) * 2
        
        # Generate recommendation
        if risk_score == 0:
            return "Approve", "Low risk changes with no significant issues"
        elif risk_score <= 2:
            return "Approve", "Good changes with minor considerations"
        elif risk_score <= 4:
            return "Request Changes", "Moderate issues that should be addressed"
        else:
            return "Block", "Significant issues must be resolved before merge"
    
    def _calculate_overall_score(self, technical_analysis: Dict[str, Any], ai_review: Dict[str, Any]) -> int:
        """Calculate overall PR score combining technical and AI analysis"""
        # Technical factors (40% weight)
        complexity_score = technical_analysis.get("complexity_score", 50)
        technical_score = max(100 - complexity_score, 0)
        
        # AI factors (60% weight)
        ai_analysis = ai_review.get("structured_analysis", {})
        code_quality = ai_analysis.get("code_quality_score", 75)
        maintainability = ai_analysis.get("maintainability_score", 75)
        ai_score = (code_quality + maintainability) / 2
        
        # Critical issues penalty
        critical_issues = len(ai_analysis.get("critical_issues", []))
        penalty = min(critical_issues * 10, 30)
        
        # Security concerns penalty
        security_concerns = len(technical_analysis.get("security_concerns", []))
        security_penalty = min(security_concerns * 15, 25)
        
        overall_score = (technical_score * 0.4 + ai_score * 0.6) - penalty - security_penalty
        
        return max(int(overall_score), 0)
    
    def _generate_recommendation(self, technical_analysis: Dict[str, Any], ai_review: Dict[str, Any]) -> str:
        """Generate overall recommendation for the PR"""
        overall_score = self._calculate_overall_score(technical_analysis, ai_review)
        
        ai_analysis = ai_review.get("structured_analysis", {})
        critical_issues = ai_analysis.get("critical_issues", [])
        security_concerns = technical_analysis.get("security_concerns", [])
        
        if overall_score >= 85 and not critical_issues and not security_concerns:
            return "✅ **APPROVE** - High quality changes ready for merge"
        elif overall_score >= 70 and len(critical_issues) <= 1:
            return "⚠️ **APPROVE WITH SUGGESTIONS** - Good changes with minor improvements needed"
        elif overall_score >= 50:
            return "🔄 **REQUEST CHANGES** - Moderate issues that should be addressed"
        else:
            return "❌ **BLOCK** - Significant issues must be resolved before merge"
    
    def _extract_action_items(self, technical_analysis: Dict[str, Any], ai_review: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract prioritized action items"""
        action_items = []
        
        # Critical issues (High priority)
        ai_analysis = ai_review.get("structured_analysis", {})
        for issue in ai_analysis.get("critical_issues", []):
            action_items.append({
                "priority": "High",
                "type": "Critical Issue",
                "description": issue,
                "category": "bug_fix"
            })
        
        # Security concerns (High priority)
        for concern in technical_analysis.get("security_concerns", []):
            action_items.append({
                "priority": "High",
                "type": "Security",
                "description": concern,
                "category": "security"
            })
        
        # Performance concerns (Medium priority)
        for concern in technical_analysis.get("performance_concerns", []):
            action_items.append({
                "priority": "Medium",
                "type": "Performance",
                "description": concern,
                "category": "optimization"
            })
        
        # AI suggestions (Low-Medium priority)
        for suggestion in ai_analysis.get("suggestions", [])[:5]:  # Limit to top 5
            action_items.append({
                "priority": "Medium",
                "type": "Improvement",
                "description": suggestion,
                "category": "enhancement"
            })
        
        # Technical recommendations (Low priority)
        for rec in technical_analysis.get("recommendations", [])[:3]:  # Limit to top 3
            action_items.append({
                "priority": "Low",
                "type": "Recommendation",
                "description": rec,
                "category": "best_practice"
            })
        
        return action_items
    
    def _generate_review_summary(self, technical_analysis: Dict[str, Any], ai_review: Dict[str, Any]) -> str:
        """Generate a comprehensive review summary in the new format"""
        pr_info = technical_analysis.get("pr_info", {})
        ai_analysis = ai_review.get("structured_analysis", {})
        overall_score = self._calculate_overall_score(technical_analysis, ai_review)
        
        # Get the raw AI response for better formatting
        raw_response = ai_review.get("raw_response", "")
        if raw_response:
            # If we have the raw response, use it directly
            return raw_response
        
        # Otherwise, generate a structured summary
        summary_parts = [
            f"## 🔍 **PR Review: {pr_info.get('title', 'Code Changes')}**",
            f"",
            f"### **Overall Assessment**",
            f"This PR introduces changes to {pr_info.get('changed_files', 0)} files with {pr_info.get('additions', 0)} additions and {pr_info.get('deletions', 0)} deletions. ",
            f"Overall quality score: **{overall_score}/100**.",
            f"",
            f"### **✅ Strengths**"
        ]
        
        # Add strengths
        strengths = ai_analysis.get("strengths", [])
        if strengths:
            for i, strength in enumerate(strengths[:3], 1):
                summary_parts.append(f"- **Strength {i}**: {strength}")
        else:
            summary_parts.append("- **Good structure**: Code follows project conventions")
            summary_parts.append("- **Clear intent**: Changes are well-documented")
        
        summary_parts.append("")
        summary_parts.append("### **⚠️ Issues & Suggestions**")
        
        # Add issues
        issues = ai_analysis.get("issues_risks", [])
        if issues:
            for i, issue in enumerate(issues[:3], 1):
                summary_parts.extend([
                    f"#### **{i}. {issue.split(':')[0] if ':' in issue else 'Code Quality Issue'}**",
                    f"```",
                    f"// Code snippet would be here",
                    f"```",
                    f"**Issue**: {issue.split(':')[1] if ':' in issue else issue}",
                    f"**Suggestion**: Consider improving code quality and following best practices.",
                    f""
                ])
        else:
            summary_parts.extend([
                "#### **1. Code Quality**",
                "```",
                "// No major issues found",
                "```",
                "**Issue**: No critical issues detected",
                "**Suggestion**: Continue maintaining high code quality standards.",
                ""
            ])
        
        # Add additional recommendations
        summary_parts.extend([
            "### **🔧 Additional Recommendations**",
            "- **Performance**: Monitor performance impact of changes",
            "- **Security**: Ensure no security vulnerabilities introduced",
            "- **Testing**: Add comprehensive test coverage",
            "- **Documentation**: Update documentation as needed",
            ""
        ])
        
        # Add metrics
        summary_parts.extend([
            "### **📊 Code Quality Metrics**",
            f"- **Maintainability**: {ai_analysis.get('maintainability_score', 75)//10}/10 - Code structure is maintainable",
            f"- **Performance**: {ai_analysis.get('performance_score', 75)//10}/10 - No major performance concerns",
            f"- **Reliability**: {ai_analysis.get('reliability_score', 75)//10}/10 - Code appears reliable",
            f"- **Security**: {ai_analysis.get('security_score', 75)//10}/10 - No security issues detected",
            ""
        ])
        
        # Add recommendation
        recommendation = ai_analysis.get("recommendation", "Request Changes")
        reasoning = ai_analysis.get("reasoning", "Analysis completed")
        
        summary_parts.extend([
            "### **🎯 Recommendation**",
            f"**{recommendation}** - {reasoning}",
            ""
        ])
        
        # Add action items
        action_items = ai_analysis.get("action_items", [])
        summary_parts.append("### **📝 Action Items**")
        if action_items:
            for i, item in enumerate(action_items[:5], 1):
                summary_parts.append(f"{i}. [ ] {item}")
        else:
            summary_parts.extend([
                "1. [ ] Review code quality standards",
                "2. [ ] Add comprehensive tests",
                "3. [ ] Update documentation"
            ])
        
        return "\n".join(summary_parts)

    async def generate_review_comment(self, owner: str, repo: str, pr_number: int, 
                                    model_preference: Optional[str] = None, auto_comment: bool = False) -> Dict[str, Any]:
        """Generate and optionally post review comment"""
        
        # Perform comprehensive review
        review_result = await self.comprehensive_review(owner, repo, pr_number, model_preference)
        if "error" in review_result:
            return review_result
        
        # Generate review comment
        comment_body = review_result["review_summary"]
        
        # Add action items section
        action_items = review_result.get("action_items", [])
        if action_items:
            high_priority = [item for item in action_items if item["priority"] == "High"]
            if high_priority:
                comment_body += "\n## 🚨 **High Priority Action Items:**\n"
                for item in high_priority:
                    comment_body += f"- **{item['type']}**: {item['description']}\n"
        
        # Add recommendation
        comment_body += f"\n## 📋 **Recommendation:**\n{review_result['recommendation']}\n"
        
        result = {
            "comment_generated": True,
            "comment_body": comment_body,
            "review_data": review_result,
            "auto_posted": False
        }
        
        # Auto-post comment if requested
        if auto_comment:
            try:
                comment_result = await github_service.add_issue_comment(
                    owner, repo, pr_number, comment_body
                )
                if "error" not in comment_result:
                    result["auto_posted"] = True
                    result["comment_url"] = comment_result.get("html_url")
                else:
                    result["post_error"] = comment_result["error"]
            except Exception as e:
                result["post_error"] = str(e)
        
        return result

    async def generate_review_comments_preview(self, owner: str, repo: str, pr_number: int, 
                                             model_preference: Optional[str] = None) -> List[Dict[str, Any]]:
        """Generate review comments for preview (without posting to GitHub)"""
        try:
            # Get PR files
            files = await github_service.get_pull_request_files(owner, repo, pr_number)
            if "error" in files:
                return {"error": files["error"]}
            
            comments = []
            
            # Review each file
            for file_info in files:
                filename = file_info.get("filename", "")
                if not filename:
                    continue
                
                # Skip binary files and large files
                if file_info.get("binary", False) or file_info.get("changes", 0) > 1000:
                    continue
                
                # Get file content
                try:
                    file_content = await github_service.get_file_content(owner, repo, pr_number, filename)
                    if "error" in file_content:
                        continue
                    
                    # Split content into lines
                    lines = file_content.get("content", "").split('\n')
                    
                    # Review each changed line
                    for patch in file_info.get("patch", "").split('\n'):
                        if patch.startswith('@@'):
                            # Parse line numbers from patch header
                            line_match = re.search(r'@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@', patch)
                            if line_match:
                                start_line = int(line_match.group(1))
                                # Review the next few lines
                                for i in range(min(5, len(lines) - start_line + 1)):
                                    line_num = start_line + i
                                    if line_num <= len(lines):
                                        code_line = lines[line_num - 1]
                                        
                                        # Generate review comment for this line
                                        review_comment = await self.review_code_line(
                                            filename, line_num, code_line, 
                                            f"Review this line from {filename}", model_preference
                                        )
                                        
                                        if review_comment and "Review timed out" not in review_comment and "Unable to generate" not in review_comment:
                                            comments.append({
                                                "file": filename,
                                                "line": line_num,
                                                "body": review_comment
                                            })
                                        
                                        # Limit comments per file to avoid spam
                                        if len([c for c in comments if c["file"] == filename]) >= 3:
                                            break
                                
                except Exception as e:
                    logger.error(f"Error reviewing file {filename}: {e}")
                    continue
            
            # Limit total comments to avoid overwhelming the user
            return comments[:10] if len(comments) > 10 else comments
            
        except Exception as e:
            logger.error(f"Error generating review comments preview: {e}")
            return {"error": str(e)}

    async def review_code_line(self, filename: str, line_num: int, code: str, prompt: str, model: Optional[str] = None) -> str:
        """Generate an AI review comment for a single code line change"""
        try:
            # Use Ollama by default, or use specified model
            model_mapping = {
                "granite": ModelType.GRANITE,
                "gemini": ModelType.GEMINI, 
                "openai": ModelType.OPENAI_GPT,
                "ollama": ModelType.OLLAMA
            }
            model_type = ModelType.OLLAMA if not model else model_mapping.get(model, ModelType.OLLAMA)
            
            # Create a focused prompt for code review
            review_prompt = f"""Review this code line from file {filename} (line {line_num}):

Code: {code}

Context: {prompt}

Provide a concise, specific review comment focusing on:
1. Code quality
2. Potential issues
3. Suggestions for improvement

Keep the response focused and actionable."""
            
            # Add timeout to prevent hanging
            import asyncio
            try:
                ai_response = await asyncio.wait_for(
                    self.multi_agent.generate_response_with_model(review_prompt, model_type),
                    timeout=15.0  # 15 second timeout for line reviews
                )
                return ai_response.strip()
            except asyncio.TimeoutError:
                logger.error(f"AI review_code_line timed out for {filename}:{line_num}")
                return "Review timed out. Please check the code manually."
                
        except Exception as e:
            logger.error(f"AI review_code_line failed: {e}")
            return "Unable to generate review comment. Please check the code manually."

# Global AI code reviewer instance
ai_code_reviewer = AICodeReviewer() 
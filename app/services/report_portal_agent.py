import logging
import asyncio
import requests
import json
import urllib3
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import re

from .ai_agent_multi_model import MultiModelAIAgent, ModelType

# Disable SSL warnings for internal systems
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class IssueCategory(Enum):
    """Categories for test failures"""
    SYSTEM_ISSUE = "system_issue"
    PRODUCTION_BUG = "production_bug"
    TEST_ENVIRONMENT = "test_environment"
    INFRASTRUCTURE = "infrastructure"
    NETWORK = "network"
    DATA_ISSUE = "data_issue"
    CONFIGURATION = "configuration"
    TIMEOUT = "timeout"
    RACE_CONDITION = "race_condition"
    UNKNOWN = "unknown"

@dataclass
class TestFailure:
    """Represents a test failure with analysis"""
    test_id: str
    test_name: str
    failure_message: str
    stack_trace: str
    timestamp: datetime
    duration: float
    category: IssueCategory
    confidence: float
    ai_analysis: str
    suggested_fix: str
    priority: str  # "high", "medium", "low"
    tags: List[str]

class ReportPortalAgent:
    """Agent for analyzing test failures and updating Report Portal"""
    
    def __init__(self, rp_url: str, rp_token: str, project: str, ssl_verify: bool = True):
        self.rp_url = rp_url.rstrip('/')
        self.rp_token = rp_token
        self.project = project
        self.ssl_verify = ssl_verify  # Allow SSL verification to be disabled
        self.multi_agent = MultiModelAIAgent()
        self.headers = {
            'Authorization': f'Bearer {rp_token}',
            'Content-Type': 'application/json'
        }
        logger.info(f"ReportPortalAgent initialized with SSL verify: {self.ssl_verify}")
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make HTTP request with SSL verification control"""
        # Add SSL verification control
        kwargs['verify'] = self.ssl_verify
        
        # Debug logging
        logger.debug(f"Making {method} request to {url} with SSL verify: {self.ssl_verify}")
        
        # Add timeout if not specified
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 30
        
        # Add headers if not specified
        if 'headers' not in kwargs:
            kwargs['headers'] = self.headers
        
        return requests.request(method, url, **kwargs)
    
    async def analyze_failures(self, hours_back: int = 24, components: Optional[List[str]] = None, 
                             versions: Optional[List[str]] = None, statuses: Optional[List[str]] = None,
                             defect_types: Optional[List[str]] = None, max_tests: int = 100,
                             batch_size: int = 50) -> List[TestFailure]:
        """
        Analyze failed tests from Report Portal with advanced filtering.
        
        Args:
            hours_back: Number of hours to look back for failures
            components: Optional list of component names to filter by (e.g., ["API_Server", "STORAGE"])
            versions: Optional list of versions to filter by (e.g., ["4.19", "4.20"])
            statuses: Optional list of statuses to filter by (e.g., ["FAILED", "INTERRUPTED"])
            defect_types: Optional list of defect types to filter by (e.g., ["ti001", "ti_1hrghcxlbgshc"])
        """
        logger.info(f"Starting failure analysis for last {hours_back} hours")
        if components:
            logger.info(f"Filtering by components: {components}")
        if versions:
            logger.info(f"Filtering by versions: {versions}")
        if statuses:
            logger.info(f"Filtering by statuses: {statuses}")
        if defect_types:
            logger.info(f"Filtering by defect types: {defect_types}")
        
        # Get failed tests from Report Portal
        failed_tests = await self._get_failed_tests(hours_back, components, versions, statuses, defect_types)
        
        # Limit the number of tests to analyze
        if len(failed_tests) > max_tests:
            logger.info(f"Limiting analysis to {max_tests} tests out of {len(failed_tests)} total failures")
            failed_tests = failed_tests[:max_tests]
        
        # Analyze each failure with timeout and batch processing
        analyzed_failures = []
        total_tests = len(failed_tests)
        
        logger.info(f"Starting analysis of {total_tests} failed tests in batches of {batch_size}")
        
        for batch_start in range(0, total_tests, batch_size):
            batch_end = min(batch_start + batch_size, total_tests)
            batch_tests = failed_tests[batch_start:batch_end]
            
            logger.info(f"Processing batch {batch_start//batch_size + 1}: tests {batch_start+1}-{batch_end}")
            
            # Process batch with concurrent analysis (limited concurrency)
            import asyncio
            semaphore = asyncio.Semaphore(3)  # Reduced from 5 to 3 concurrent analyses to prevent overwhelming
            
            async def analyze_test_with_semaphore(test, index):
                async with semaphore:
                    try:
                        # Add timeout for each individual analysis
                        failure = await asyncio.wait_for(
                            self._analyze_single_failure(test),
                            timeout=30.0  # Reduced timeout per test for faster processing
                        )
                        logger.info(f"Analyzed test {batch_start + index + 1}/{total_tests}: {test.get('name', 'Unknown')}")
                        return failure
                    except asyncio.TimeoutError:
                        logger.error(f"Timeout analyzing test: {test.get('name', 'Unknown')}")
                        # Create a fallback failure object
                        return TestFailure(
                            test_id=test.get('id', 'unknown'),
                            test_name=test.get('name', 'Unknown Test'),
                            failure_message=test.get('issue', {}).get('message', ''),
                            stack_trace=test.get('issue', {}).get('stackTrace', ''),
                            timestamp=datetime.now(),
                            duration=test.get('duration', 0),
                            category=IssueCategory.UNKNOWN,
                            confidence=0.0,
                            ai_analysis="Analysis timeout",
                            suggested_fix="Manual investigation required",
                            priority="medium",
                            tags=["timeout", "manual-review"]
                        )
                    except Exception as e:
                        logger.error(f"Error analyzing test {test.get('name', 'Unknown')}: {e}")
                        # Create a fallback failure object
                        return TestFailure(
                            test_id=test.get('id', 'unknown'),
                            test_name=test.get('name', 'Unknown Test'),
                            failure_message=test.get('issue', {}).get('message', ''),
                            stack_trace=test.get('issue', {}).get('stackTrace', ''),
                            timestamp=datetime.now(),
                            duration=test.get('duration', 0),
                            category=IssueCategory.UNKNOWN,
                            confidence=0.0,
                            ai_analysis=f"Analysis error: {str(e)}",
                            suggested_fix="Manual investigation required",
                            priority="medium",
                            tags=["error", "manual-review"]
                        )
            
            # Process batch concurrently
            batch_tasks = [analyze_test_with_semaphore(test, i) for i, test in enumerate(batch_tests)]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Add successful results to analyzed_failures
            for result in batch_results:
                if isinstance(result, TestFailure):
                    analyzed_failures.append(result)
                else:
                    logger.error(f"Batch processing error: {result}")
            
            logger.info(f"Completed batch {batch_start//batch_size + 1}: {len([r for r in batch_results if isinstance(r, TestFailure)])} tests analyzed")
        
        return analyzed_failures
    
    async def _get_failed_tests(self, hours_back: int, components: Optional[List[str]] = None, 
                                versions: Optional[List[str]] = None, statuses: Optional[List[str]] = None,
                                defect_types: Optional[List[str]] = None) -> List[Dict]:
        """Fetch failed tests from Report Portal API with optional component filtering"""
        try:
            # Calculate time range
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)
            
            # Report Portal API endpoint for test results - using the working endpoint we discovered
            url = f"{self.rp_url}/api/v1/{self.project}/launch"
            
            params = {
                'filter.gte.startTime': start_time.isoformat(),
                'filter.lte.startTime': end_time.isoformat(),
                'page.size': 100
            }
            
            # Note: Report Portal API doesn't support direct filtering by component/version
            # We'll apply filtering after fetching the data

            response = self._make_request('GET', url, params=params)
            response.raise_for_status()
            
            launches = response.json().get('content', [])
            
            # Get test items from launches
            failed_tests = []
            for launch in launches:
                launch_id = launch['id']
                test_items = await self._get_test_items(launch_id, 'FAILED')
                failed_tests.extend(test_items)
            
            # Apply advanced filtering
            filtered_tests = []
            for test in failed_tests:
                include_test = True
                
                # Filter by components (check in test name, launch name, or launch description)
                if components:
                    test_name = test.get('name', '').upper()
                    launch_name = test.get('launchName', '').upper()
                    launch_description = test.get('launchDescription', '').upper()
                    
                    # Check if any component is found in the test data
                    component_found = False
                    for component in components:
                        component_upper = component.upper()
                        if (component_upper in test_name or 
                            component_upper in launch_name or 
                            component_upper in launch_description):
                            component_found = True
                            break
                    
                    if not component_found:
                        include_test = False
                
                # Filter by versions (check in test name, launch name, or launch description)
                if include_test and versions:
                    test_name = test.get('name', '').upper()
                    launch_name = test.get('launchName', '').upper()
                    launch_description = test.get('launchDescription', '').upper()
                    
                    # Check if any version is found in the test data
                    version_found = False
                    for version in versions:
                        version_upper = version.upper()
                        if (version_upper in test_name or 
                            version_upper in launch_name or 
                            version_upper in launch_description):
                            version_found = True
                            break
                    
                    if not version_found:
                        include_test = False
                
                # Filter by statuses
                if include_test and statuses:
                    test_status = test.get('status', '').upper()
                    if test_status not in [s.upper() for s in statuses]:
                        include_test = False
                
                # Filter by defect types
                if include_test and defect_types:
                    defect_type = test.get('issue', {}).get('issueType', '').upper()
                    if defect_type and defect_type not in [dt.upper() for dt in defect_types]:
                        include_test = False
                
                if include_test:
                    filtered_tests.append(test)
            
            failed_tests = filtered_tests
            
            # Log filtering results
            filter_info = []
            if components:
                filter_info.append(f"components: {components}")
            if versions:
                filter_info.append(f"versions: {versions}")
            if statuses:
                filter_info.append(f"statuses: {statuses}")
            if defect_types:
                filter_info.append(f"defect_types: {defect_types}")
            
            if filter_info:
                logger.info(f"Filtered to {len(failed_tests)} tests matching: {', '.join(filter_info)}")
            else:
                logger.info(f"Found {len(failed_tests)} failed tests")
            
            return failed_tests
            
        except Exception as e:
            logger.error(f"Failed to fetch failed tests: {e}")
            return []
    
    async def _get_test_items(self, launch_id: str, status: str) -> List[Dict]:
        """Get test items from a specific launch"""
        try:
            # Try the standard endpoint first
            url = f"{self.rp_url}/api/v1/{self.project}/item"
            params = {
                'filter.eq.launchId': launch_id,
                'filter.eq.status': status,
                'page.size': 100
            }
            
            response = self._make_request('GET', url, params=params)
            
            # If that fails, try alternative endpoints
            if response.status_code == 404:
                # Try without project prefix
                alt_url = f"{self.rp_url}/api/v1/item"
                alt_response = self._make_request('GET', alt_url, params=params)
                
                if alt_response.status_code == 200:
                    return alt_response.json().get('content', [])
                else:
                    # Try testitem endpoint
                    testitem_url = f"{self.rp_url}/api/v1/{self.project}/testitem"
                    testitem_response = self._make_request('GET', testitem_url, params=params)
                    
                    if testitem_response.status_code == 200:
                        return testitem_response.json().get('content', [])
            
            response.raise_for_status()
            return response.json().get('content', [])
            
        except Exception as e:
            logger.error(f"Failed to get test items for launch {launch_id}: {e}")
            return []
    
    async def _analyze_single_failure(self, test_data: Dict) -> TestFailure:
        """Analyze a single test failure using AI"""
        
        # Extract test information
        test_id = test_data.get('id', 'unknown')
        test_name = test_data.get('name', 'Unknown Test')
        
        # Use extracted failure message and logs if available
        failure_message = test_data.get('extracted_failure_message', test_data.get('issue', {}).get('message', ''))
        stack_trace = test_data.get('extracted_logs', test_data.get('issue', {}).get('stackTrace', ''))
        # Handle different date formats
        start_time_str = test_data.get('startTime', datetime.now().isoformat())
        
        # Convert to string if it's an integer (timestamp)
        if isinstance(start_time_str, int):
            start_time_str = str(start_time_str)
        elif not isinstance(start_time_str, str):
            start_time_str = datetime.now().isoformat()
        
        try:
            # Try ISO format first
            timestamp = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        except ValueError:
            try:
                # Try parsing with timezone info
                from dateutil import parser
                timestamp = parser.parse(start_time_str)
            except:
                # Fallback to current time
                timestamp = datetime.now()
        duration = test_data.get('duration', 0)
        
        # Create AI prompt for analysis
        prompt = self._create_analysis_prompt(test_name, failure_message, stack_trace)
        
        # Get AI analysis with timeout
        try:
            ai_response = await asyncio.wait_for(
                self.multi_agent.generate_response_with_model(
                    prompt, ModelType.OLLAMA
                ),
                timeout=30.0  # 30 second timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"AI analysis timeout for test: {test_name}")
            ai_response = "Analysis timeout - using fallback"
        except Exception as ai_error:
            logger.error(f"AI analysis error for test {test_name}: {ai_error}")
            ai_response = f"Analysis error: {str(ai_error)}"
        
        # Parse AI response
        analysis_result = self._parse_ai_analysis(ai_response)
        
        return TestFailure(
            test_id=test_id,
            test_name=test_name,
            failure_message=failure_message,
            stack_trace=stack_trace,
            timestamp=timestamp,
            duration=duration,
            category=analysis_result['category'],
            confidence=analysis_result['confidence'],
            ai_analysis=analysis_result['analysis'],
            suggested_fix=analysis_result['suggested_fix'],
            priority=analysis_result['priority'],
            tags=analysis_result['tags']
        )
    
    def _create_analysis_prompt(self, test_name: str, failure_message: str, stack_trace: str) -> str:
        """Create AI prompt for test failure analysis"""
        
        prompt = f"""
🔍 **Test Failure Analysis Request**

You are an expert QA engineer analyzing test failures. Analyze the following test failure and categorize it appropriately.

**Test Information:**
- Test Name: {test_name}
- Failure Message: {failure_message}
- Stack Trace: {stack_trace}

**Analysis Instructions:**

1. **Categorize the failure** into one of these categories:
   - SYSTEM_ISSUE: Infrastructure, environment, or system-level problems
   - PRODUCTION_BUG: Actual bugs in the application code
   - TEST_ENVIRONMENT: Test environment configuration issues
   - INFRASTRUCTURE: Network, database, or service connectivity issues
   - NETWORK: Network timeouts, connectivity problems
   - DATA_ISSUE: Test data problems, missing data, corrupted data
   - CONFIGURATION: Configuration errors, missing settings
   - TIMEOUT: Test timeouts, slow performance
   - RACE_CONDITION: Timing-related issues, concurrency problems
   - UNKNOWN: Cannot determine category

2. **Provide detailed analysis** explaining why this category was chosen

3. **Suggest a fix** with specific actionable steps

4. **Assign priority** (high/medium/low) based on impact

5. **Add relevant tags** for filtering and organization

Return your analysis in this JSON format:

```json
{{
    "category": "SYSTEM_ISSUE",
    "confidence": 0.85,
    "analysis": "Detailed explanation of why this is a system issue...",
    "suggested_fix": "Specific steps to resolve the issue...",
    "priority": "high",
    "tags": ["infrastructure", "timeout", "network"]
}}
```

Focus on:
- **Root cause analysis** - what actually caused the failure
- **Impact assessment** - how critical is this issue
- **Actionable solutions** - specific steps to fix
- **Prevention strategies** - how to avoid similar issues
        """
        
        return prompt.strip()
    
    def _parse_ai_analysis(self, ai_response: str) -> Dict[str, Any]:
        """Parse AI response and extract structured data"""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                result = json.loads(json_str)
            else:
                # Try to parse the entire response as JSON
                result = json.loads(ai_response)
            
            # Validate and set defaults
            category_name = result.get('category', 'UNKNOWN')
            try:
                category = IssueCategory(category_name.lower())
            except ValueError:
                category = IssueCategory.UNKNOWN
            
            return {
                'category': category,
                'confidence': result.get('confidence', 0.5),
                'analysis': result.get('analysis', 'Analysis not available'),
                'suggested_fix': result.get('suggested_fix', 'No fix suggested'),
                'priority': result.get('priority', 'medium'),
                'tags': result.get('tags', [])
            }
            
        except Exception as e:
            logger.error(f"Failed to parse AI analysis: {e}")
            return {
                'category': IssueCategory.UNKNOWN,
                'confidence': 0.0,
                'analysis': 'Failed to analyze failure',
                'suggested_fix': 'Manual investigation required',
                'priority': 'medium',
                'tags': ['manual-review']
            }
    
    async def update_test_comments(self, failures: List[TestFailure]) -> Dict[str, Any]:
        """Update test comments in Report Portal with AI analysis"""
        logger.info(f"Updating comments for {len(failures)} test failures")
        
        results = {
            'updated': 0,
            'failed': 0,
            'errors': []
        }
        
        for failure in failures:
            try:
                await self._update_single_test_comment(failure)
                results['updated'] += 1
            except Exception as e:
                logger.error(f"Failed to update comment for test {failure.test_id}: {e}")
                results['failed'] += 1
                results['errors'].append({
                    'test_id': failure.test_id,
                    'error': str(e)
                })
        
        return results
    
    async def _update_single_test_comment(self, failure: TestFailure):
        """Update comment for a single test failure"""
        
        # Create comment content
        comment = self._create_test_comment(failure)
        
        # Report Portal API endpoint for adding comments
        url = f"{self.rp_url}/api/v1/{self.project}/item/{failure.test_id}/comment"
        
        payload = {
            'message': comment,
            'level': 'INFO'
        }
        
        response = self._make_request('POST', url, json=payload)
        response.raise_for_status()
        
        logger.info(f"Updated comment for test {failure.test_id}")
    
    def _create_test_comment(self, failure: TestFailure) -> str:
        """Create a formatted comment for the test failure"""
        
        # Map category to emoji
        category_emoji = {
            IssueCategory.SYSTEM_ISSUE: "🖥️",
            IssueCategory.PRODUCTION_BUG: "🐛",
            IssueCategory.TEST_ENVIRONMENT: "🧪",
            IssueCategory.INFRASTRUCTURE: "🏗️",
            IssueCategory.NETWORK: "🌐",
            IssueCategory.DATA_ISSUE: "📊",
            IssueCategory.CONFIGURATION: "⚙️",
            IssueCategory.TIMEOUT: "⏰",
            IssueCategory.RACE_CONDITION: "🏃",
            IssueCategory.UNKNOWN: "❓"
        }
        
        emoji = category_emoji.get(failure.category, "❓")
        
        comment = f"""
🤖 **AI Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**

{emoji} **Category**: {failure.category.value.replace('_', ' ').title()}
🎯 **Confidence**: {failure.confidence:.1%}
🚨 **Priority**: {failure.priority.upper()}

📋 **Analysis**:
{failure.ai_analysis}

🔧 **Suggested Fix**:
{failure.suggested_fix}

🏷️ **Tags**: {', '.join(failure.tags)}

---
*This analysis was automatically generated by AI*
        """
        
        return comment.strip()
    
    async def update_test_status(self, failures: List[TestFailure]) -> Dict[str, Any]:
        """Update test status based on AI analysis"""
        logger.info(f"Updating status for {len(failures)} test failures")
        
        results = {
            'updated': 0,
            'failed': 0,
            'errors': []
        }
        
        for failure in failures:
            try:
                await self._update_single_test_status(failure)
                results['updated'] += 1
            except Exception as e:
                logger.error(f"Failed to update status for test {failure.test_id}: {e}")
                results['failed'] += 1
                results['errors'].append({
                    'test_id': failure.test_id,
                    'error': str(e)
                })
        
        return results
    
    async def _update_single_test_status(self, failure: TestFailure):
        """Update status for a single test failure"""
        
        # Determine new status based on category
        new_status = self._determine_status_from_category(failure.category)
        
        # Report Portal API endpoint for updating test status
        url = f"{self.rp_url}/api/v1/{self.project}/item/{failure.test_id}"
        
        payload = {
            'status': new_status,
            'issue': {
                'issueType': failure.category.value,
                'comment': f"AI categorized as {failure.category.value}"
            }
        }
        
        response = self._make_request('PUT', url, json=payload)
        response.raise_for_status()
        
        logger.info(f"Updated status for test {failure.test_id} to {new_status}")
    
    def _determine_status_from_category(self, category: IssueCategory) -> str:
        """Determine test status based on failure category"""
        
        # Map categories to status
        status_mapping = {
            IssueCategory.SYSTEM_ISSUE: 'TO_INVESTIGATE',
            IssueCategory.PRODUCTION_BUG: 'BUG',
            IssueCategory.TEST_ENVIRONMENT: 'TO_INVESTIGATE',
            IssueCategory.INFRASTRUCTURE: 'TO_INVESTIGATE',
            IssueCategory.NETWORK: 'TO_INVESTIGATE',
            IssueCategory.DATA_ISSUE: 'TO_INVESTIGATE',
            IssueCategory.CONFIGURATION: 'TO_INVESTIGATE',
            IssueCategory.TIMEOUT: 'TO_INVESTIGATE',
            IssueCategory.RACE_CONDITION: 'BUG',
            IssueCategory.UNKNOWN: 'TO_INVESTIGATE'
        }
        
        return status_mapping.get(category, 'TO_INVESTIGATE')
    
    async def generate_failure_report(self, failures: List[TestFailure]) -> str:
        """Generate a comprehensive failure analysis report"""
        
        if not failures:
            return "No test failures found in the specified time range."
        
        # Group failures by category
        category_groups = {}
        for failure in failures:
            category = failure.category.value
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(failure)
        
        # Generate report
        report = f"""
🔍 **Test Failure Analysis Report**
📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📊 Total Failures: {len(failures)}

## 📈 **Summary by Category**

"""
        
        for category, category_failures in category_groups.items():
            report += f"### {category.replace('_', ' ').title()} ({len(category_failures)} failures)\n"
            
            # Group by priority
            priority_groups = {}
            for failure in category_failures:
                priority = failure.priority
                if priority not in priority_groups:
                    priority_groups[priority] = []
                priority_groups[priority].append(failure)
            
            for priority, priority_failures in priority_groups.items():
                report += f"\n**{priority.upper()} Priority ({len(priority_failures)}):**\n"
                for failure in priority_failures[:5]:  # Show top 5
                    report += f"- {failure.test_name}\n"
                if len(priority_failures) > 5:
                    report += f"- ... and {len(priority_failures) - 5} more\n"
            
            report += "\n"
        
        # Add recommendations
        report += """
## 🎯 **Recommendations**

"""
        
        high_priority_failures = [f for f in failures if f.priority == 'high']
        if high_priority_failures:
            report += f"🚨 **Immediate Action Required:** {len(high_priority_failures)} high-priority failures need immediate attention.\n\n"
        
        system_issues = [f for f in failures if f.category == IssueCategory.SYSTEM_ISSUE]
        if system_issues:
            report += f"🖥️ **System Issues:** {len(system_issues)} infrastructure-related failures detected.\n\n"
        
        production_bugs = [f for f in failures if f.category == IssueCategory.PRODUCTION_BUG]
        if production_bugs:
            report += f"🐛 **Production Bugs:** {len(production_bugs)} actual code bugs identified.\n\n"
        
        report += """
## 📋 **Next Steps**

1. **Review High Priority Failures** - Address critical issues first
2. **Investigate System Issues** - Check infrastructure and environment
3. **Fix Production Bugs** - Assign to development team
4. **Update Test Environment** - Resolve configuration issues
5. **Monitor Trends** - Track failure patterns over time

---
*Report generated by AI-powered test failure analyzer*
        """
        
        return report.strip()

    async def get_available_components(self, hours_back: int = 24) -> List[str]:
        """Get list of available components from recent test data"""
        try:
            # Get all tests (not just failed ones) to discover components
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)
            
            url = f"{self.rp_url}/api/v1/{self.project}/launch"
            params = {
                'filter.gte.startTime': start_time.isoformat(),
                'filter.lte.startTime': end_time.isoformat(),
                'page.size': 100
            }
            
            response = self._make_request('GET', url, params=params)
            response.raise_for_status()
            
            launches = response.json().get('content', [])
            
            # Collect all test names to extract components
            all_test_names = set()
            for launch in launches:
                launch_id = launch['id']
                test_items = await self._get_test_items(launch_id, None)  # Get all statuses
                for test in test_items:
                    test_name = test.get('name', '')
                    if test_name:
                        all_test_names.add(test_name)
            
            # Extract unique components (assuming component names are in test names)
            components = set()
            for test_name in all_test_names:
                # Common component patterns in OpenShift tests
                if 'STORAGE' in test_name.upper():
                    components.add('STORAGE')
                if 'NETWORK' in test_name.upper():
                    components.add('NETWORK')
                if 'NODE' in test_name.upper():
                    components.add('NODE')
                if 'AUTH' in test_name.upper() or 'AUTHENTICATION' in test_name.upper():
                    components.add('AUTH')
                if 'API' in test_name.upper():
                    components.add('API')
                if 'CONFIG' in test_name.upper() or 'CONFIGURATION' in test_name.upper():
                    components.add('CONFIG')
                if 'PERFORMANCE' in test_name.upper():
                    components.add('PERFORMANCE')
                if 'SECURITY' in test_name.upper():
                    components.add('SECURITY')
                if 'UPGRADE' in test_name.upper():
                    components.add('UPGRADE')
                if 'INSTALL' in test_name.upper() or 'INSTALLATION' in test_name.upper():
                    components.add('INSTALL')
                if 'MONITORING' in test_name.upper():
                    components.add('MONITORING')
                if 'LOGGING' in test_name.upper():
                    components.add('LOGGING')
                if 'BACKUP' in test_name.upper():
                    components.add('BACKUP')
                if 'RESTORE' in test_name.upper():
                    components.add('RESTORE')
                if 'SCALING' in test_name.upper():
                    components.add('SCALING')
                if 'ROUTING' in test_name.upper():
                    components.add('ROUTING')
                if 'PERSISTENCE' in test_name.upper():
                    components.add('PERSISTENCE')
                if 'MIGRATION' in test_name.upper():
                    components.add('MIGRATION')
            
            return sorted(list(components))
            
        except Exception as e:
            logger.error(f"Failed to get available components: {e}")
            return []

    async def get_component_statistics(self, hours_back: int = 24) -> Dict[str, Dict[str, int]]:
        """Get statistics for each component (total tests, failed tests, success rate)"""
        try:
            components = await self.get_available_components(hours_back)
            stats = {}
            
            for component in components:
                # Get all tests for this component
                all_tests = await self._get_failed_tests(hours_back, [component])
                
                # Get failed tests for this component
                failed_tests = await self._get_failed_tests(hours_back, [component])
                
                stats[component] = {
                    'total_tests': len(all_tests),
                    'failed_tests': len(failed_tests),
                    'success_rate': round(((len(all_tests) - len(failed_tests)) / len(all_tests) * 100) if all_tests else 0, 2)
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get component statistics: {e}")
            return {}

    async def get_available_versions(self, hours_back: int = 24) -> List[str]:
        """Get list of available versions from recent test data"""
        try:
            # Get all tests to discover versions
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)
            
            url = f"{self.rp_url}/api/v1/{self.project}/launch"
            params = {
                'filter.gte.startTime': start_time.isoformat(),
                'filter.lte.startTime': end_time.isoformat(),
                'page.size': 100
            }
            
            response = self._make_request('GET', url, params=params)
            response.raise_for_status()
            
            launches = response.json().get('content', [])
            
            # Collect all test names and launch names to extract versions
            all_test_names = set()
            all_launch_names = set()
            for launch in launches:
                launch_name = launch.get('name', '')
                if launch_name:
                    all_launch_names.add(launch_name)
                
                launch_id = launch['id']
                test_items = await self._get_test_items(launch_id, None)  # Get all statuses
                for test in test_items:
                    test_name = test.get('name', '')
                    if test_name:
                        all_test_names.add(test_name)
            
            # Extract unique versions (common patterns in OpenShift test names)
            versions = set()
            for name in list(all_test_names) + list(all_launch_names):
                # Look for version patterns like 4.19, 4.20, etc.
                import re
                version_patterns = [
                    r'4\.\d{2}',  # 4.19, 4.20, etc.
                    r'4\.\d{1}',  # 4.9, 4.8, etc.
                    r'release-4\.\d{2}',  # release-4.19
                    r'release-4\.\d{1}',  # release-4.9
                ]
                
                for pattern in version_patterns:
                    matches = re.findall(pattern, name)
                    for match in matches:
                        if 'release-' in match:
                            versions.add(match)
                        else:
                            versions.add(match)
            
            return sorted(list(versions))
            
        except Exception as e:
            logger.error(f"Failed to get available versions: {e}")
            return []

    async def get_available_defect_types(self, hours_back: int = 24) -> List[str]:
        """Get list of available defect types from recent test data"""
        try:
            # Get all tests to discover defect types
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)
            
            url = f"{self.rp_url}/api/v1/{self.project}/launch"
            params = {
                'filter.gte.startTime': start_time.isoformat(),
                'filter.lte.startTime': end_time.isoformat(),
                'page.size': 100
            }
            
            response = self._make_request('GET', url, params=params)
            response.raise_for_status()
            
            launches = response.json().get('content', [])
            
            # Collect all defect types
            defect_types = set()
            for launch in launches:
                launch_id = launch['id']
                test_items = await self._get_test_items(launch_id, None)  # Get all statuses
                for test in test_items:
                    issue = test.get('issue', {})
                    issue_type = issue.get('issueType')
                    if issue_type:
                        defect_types.add(issue_type)
            
            return sorted(list(defect_types))
            
        except Exception as e:
            logger.error(f"Failed to get available defect types: {e}")
            return []

    async def get_filtered_statistics(self, hours_back: int = 24, components: Optional[List[str]] = None,
                                    versions: Optional[List[str]] = None, statuses: Optional[List[str]] = None,
                                    defect_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get statistics for filtered test data"""
        try:
            # Get filtered failures
            failures = await self._get_failed_tests(hours_back, components, versions, statuses, defect_types)
            
            # Calculate statistics
            total_failures = len(failures)
            
            # Count by category
            categories = {}
            priorities = {}
            versions_found = set()
            components_found = set()
            
            for failure in failures:
                # Category counting
                category = failure.category.value
                categories[category] = categories.get(category, 0) + 1
                
                # Priority counting
                priority = failure.priority
                priorities[priority] = priorities.get(priority, 0) + 1
                
                # Extract version and component from test name
                test_name = failure.test_name.upper()
                for version in versions or []:
                    if version.upper() in test_name:
                        versions_found.add(version)
                
                for component in components or []:
                    if component.upper() in test_name:
                        components_found.add(component)
            
            return {
                'total_failures': total_failures,
                'categories': categories,
                'priorities': priorities,
                'versions_found': list(versions_found),
                'components_found': list(components_found),
                'filter_applied': {
                    'components': components,
                    'versions': versions,
                    'statuses': statuses,
                    'defect_types': defect_types
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get filtered statistics: {e}")
            return {}

    async def get_test_cases(self, hours_back: int = 24, components: Optional[List[str]] = None,
                           versions: Optional[List[str]] = None, statuses: Optional[List[str]] = None,
                           defect_types: Optional[List[str]] = None, limit: int = 100) -> List[Dict]:
        """Get available test cases with filtering options - following Ruby script pattern"""
        
        try:
            logger.info(f"Getting test cases for last {hours_back} hours with filters")
            
            # Calculate time range
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)
            
            # Build API request - following Ruby script pattern
            params = {
                'page.size': limit,
                'isLatest': 'false'  # Get all launches, not just latest
            }
            
            # Add time filter only if not specifically looking for 4.20 data
            # (4.20 launches have future timestamps)
            if not versions or '4.20' not in versions:
                params.update({
                    'filter.gte.startTime': start_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                    'filter.lte.startTime': end_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z',
                })
            
            # Get launches first - following Ruby script pattern
            launches_url = f"{self.rp_url}/api/v1/{self.project}/launch"
            
            # If specifically looking for 4.20, search for it directly
            if versions and '4.20' in versions:
                params['filter.cnt.name'] = '4.20'
            
            response = self._make_request('GET', launches_url, params=params)
            
            test_cases = []
            
            if response.status_code == 200:
                response_data = response.json()
                if 'content' in response_data and response_data['content']:
                    logger.info(f"Found {len(response_data['content'])} launches")
                    
                    # Process each launch
                    for launch in response_data['content']:
                        launch_id = launch['id']
                        launch_name = launch.get('name', 'Unknown')
                        
                        # Get test items for this launch - following Ruby script pattern
                        test_items_url = f"{self.rp_url}/api/v1/{self.project}/item"
                        test_params = {
                            'filter.eq.launchId': launch_id,
                            'filter.eq.hasChildren': 'false',  # Only get leaf items (actual test steps)
                            'page.size': 1000,  # Get all items for this launch
                            'isLatest': 'false'
                        }
                        
                        # Add status filter if specified
                        if statuses:
                            status_filter = ','.join(statuses)
                            test_params['filter.in.status'] = status_filter
                        
                        test_response = self._make_request('GET', test_items_url, params=test_params)
                        
                        if test_response.status_code == 200:
                            test_response_data = test_response.json()
                            if 'content' in test_response_data:
                                logger.info(f"Found {len(test_response_data['content'])} test items for launch {launch_id}")
                                
                                for item in test_response_data['content']:
                                    # Extract component and version
                                    component = self._extract_component(item.get('name', ''))
                                    version = self._extract_version(launch_name)
                                    
                                    # Add component and version to the item for filtering
                                    item['component'] = component
                                    item['version'] = version
                                    
                                    # Apply filters
                                    if self._should_include_test_case(item, components, versions, statuses, defect_types):
                                        test_case = {
                                            'id': item['id'],
                                            'name': item['name'],
                                            'status': item.get('status', 'UNKNOWN'),
                                            'start_time': item.get('startTime'),
                                            'end_time': item.get('endTime'),
                                            'duration': item.get('duration'),
                                            'launch_id': launch_id,
                                            'launch_name': launch_name,
                                            'component': component,
                                            'version': version,
                                            'defect_type': item.get('issue', {}).get('issueType', ''),
                                            'has_children': item.get('hasChildren', False),
                                            'type': item.get('type', 'STEP')
                                        }
                                        test_cases.append(test_case)
                                        
                                        if len(test_cases) >= limit:
                                            break
                        
                        if len(test_cases) >= limit:
                            break
                else:
                    logger.warning("No launches found in response content")
            else:
                logger.warning(f"No launches found, status code: {response.status_code}")
            
            # Only use real test cases, no mock data fallback
            if not test_cases:
                logger.warning("No real test cases found from Report Portal")
                return []
            
            logger.info(f"Found {len(test_cases)} test cases")
            return test_cases
            
        except Exception as e:
            logger.error(f"Failed to get test cases: {e}")
            # Return empty list instead of mock data
            logger.warning("Returning empty list due to error")
            return []

    def _create_mock_test_cases(self, limit: int = 10) -> List[Dict]:
        """Create mock test cases for demonstration purposes"""
        
        # Base mock test cases based on real Report Portal data
        base_test_cases = [
            {
                'id': 'test_001',
                'name': 'OCP-41664:dpunia:API_Server:[sig-api-machinery] API_Server Check deprecated APIs to be removed in next release and next EUS release',
                'status': 'FAILED',
                'start_time': '2025-08-08T10:00:00Z',
                'end_time': '2025-08-08T10:00:20Z',
                'duration': 20000,
                'launch_id': 'launch_001',
                'launch_name': 'periodic-ci-openshift-openshift-tests-private-release-4.20-multi-nightly-gcp-short-cert-rotation-arm-f7',
                'component': 'API_Server',
                'version': '4.20',
                'defect_type': 'Predicted System Issue',
                'has_children': False,
                'type': 'STEP'
            },
            {
                'id': 'test_002',
                'name': 'OCP-39601:zxiao:API_Server:[sig-api-machinery] API_Server Examine critical errors in openshift-kube-apiserver related log files',
                'status': 'FAILED',
                'start_time': '2025-08-08T11:00:00Z',
                'end_time': '2025-08-08T11:01:06Z',
                'duration': 66000,
                'launch_id': 'launch_002',
                'launch_name': 'periodic-ci-openshift-openshift-tests-private-release-4.20-amd64-nightly-aws-rosa-sts-shared-vpc-stage-f7',
                'component': 'API_Server',
                'version': '4.20',
                'defect_type': 'Predicted Automation Bug',
                'has_children': False,
                'type': 'STEP'
            },
            {
                'id': 'test_003',
                'name': 'OCP-41664:dpunia:API_Server:[sig-api-machinery] API_Server Check deprecated APIs to be removed in next release and next EUS release',
                'status': 'FAILED',
                'start_time': '2025-08-08T12:00:00Z',
                'end_time': '2025-08-08T12:00:13Z',
                'duration': 13000,
                'launch_id': 'launch_003',
                'launch_name': 'periodic-ci-openshift-openshift-tests-private-release-4.20-amd64-nightly-azure-ipi-ingress-controller-arm-mixarch-f7',
                'component': 'API_Server',
                'version': '4.20',
                'defect_type': 'To Investigate',
                'has_children': False,
                'type': 'STEP'
            },
            {
                'id': 'test_004',
                'name': 'OCP-39601:zxiao:API_Server:[sig-api-machinery] API_Server Examine critical errors in openshift-kube-apiserver related log files',
                'status': 'FAILED',
                'start_time': '2025-08-08T13:00:00Z',
                'end_time': '2025-08-08T13:01:07Z',
                'duration': 67000,
                'launch_id': 'launch_004',
                'launch_name': 'periodic-ci-openshift-openshift-tests-private-release-4.20-amd64-nightly-aws-rosa-sts-shared-vpc-stage-f7',
                'component': 'API_Server',
                'version': '4.20',
                'defect_type': 'Predicted Automation Bug',
                'has_children': False,
                'type': 'STEP'
            },
            {
                'id': 'test_005',
                'name': 'OCP-41664:dpunia:API_Server:[sig-api-machinery] API_Server Check deprecated APIs to be removed in next release and next EUS release',
                'status': 'FAILED',
                'start_time': '2025-08-08T14:00:00Z',
                'end_time': '2025-08-08T14:00:16Z',
                'duration': 16000,
                'launch_id': 'launch_005',
                'launch_name': 'periodic-ci-openshift-openshift-tests-private-release-4.20-amd64-nightly-aws-rosa-advanced-stage-f7',
                'component': 'API_Server',
                'version': '4.20',
                'defect_type': 'To Investigate',
                'has_children': False,
                'type': 'STEP'
            },
            {
                'id': 'test_006',
                'name': 'OCP-39601:zxiao:API_Server:[sig-api-machinery] API_Server Examine critical errors in openshift-kube-apiserver related log files',
                'status': 'FAILED',
                'start_time': '2025-08-08T15:00:00Z',
                'end_time': '2025-08-08T15:01:07Z',
                'duration': 67000,
                'launch_id': 'launch_006',
                'launch_name': 'periodic-ci-openshift-openshift-tests-private-release-4.20-amd64-nightly-aws-rosa-advanced-stage-f7',
                'component': 'API_Server',
                'version': '4.20',
                'defect_type': 'To Investigate',
                'has_children': False,
                'type': 'STEP'
            },
            {
                'id': 'test_007',
                'name': 'OCP-41664:dpunia:API_Server:[sig-api-machinery] API_Server Check deprecated APIs to be removed in next release and next EUS release',
                'status': 'FAILED',
                'start_time': '2025-08-08T16:00:00Z',
                'end_time': '2025-08-08T16:00:05Z',
                'duration': 5000,
                'launch_id': 'launch_007',
                'launch_name': 'periodic-ci-openshift-openshift-tests-private-release-4.20-amd64-nightly-aws-rosa-non-sts-advanced-stage-f7',
                'component': 'API_Server',
                'version': '4.20',
                'defect_type': 'To Investigate',
                'has_children': False,
                'type': 'STEP'
            },
            {
                'id': 'test_008',
                'name': 'OCP-41664:dpunia:API_Server:[sig-api-machinery] API_Server Check deprecated APIs to be removed in next release and next EUS release',
                'status': 'FAILED',
                'start_time': '2025-08-08T17:00:00Z',
                'end_time': '2025-08-08T17:00:07Z',
                'duration': 7000,
                'launch_id': 'launch_008',
                'launch_name': 'periodic-ci-openshift-openshift-tests-private-release-4.20-amd64-nightly-aws-rosa-sts-localzone-f7',
                'component': 'API_Server',
                'version': '4.20',
                'defect_type': 'Predicted System Issue',
                'has_children': False,
                'type': 'STEP'
            },
            {
                'id': 'test_009',
                'name': 'OCP-39601:zxiao:API_Server:[sig-api-machinery] API_Server Examine critical errors in openshift-kube-apiserver related log files',
                'status': 'FAILED',
                'start_time': '2025-08-08T18:00:00Z',
                'end_time': '2025-08-08T18:01:04Z',
                'duration': 64000,
                'launch_id': 'launch_009',
                'launch_name': 'periodic-ci-openshift-openshift-tests-private-release-4.20-amd64-nightly-aws-rosa-sts-localzone-f7',
                'component': 'API_Server',
                'version': '4.20',
                'defect_type': 'Predicted Automation Bug',
                'has_children': False,
                'type': 'STEP'
            },
            {
                'id': 'test_010',
                'name': 'OCP-41664:dpunia:API_Server:[sig-api-machinery] API_Server Check deprecated APIs to be removed in next release and next EUS release',
                'status': 'FAILED',
                'start_time': '2025-08-08T19:00:00Z',
                'end_time': '2025-08-08T19:00:14Z',
                'duration': 14000,
                'launch_id': 'launch_010',
                'launch_name': 'periodic-ci-openshift-openshift-tests-private-release-4.20-amd64-nightly-aws-rosa-advanced-stage-f7',
                'component': 'API_Server',
                'version': '4.20',
                'defect_type': 'Predicted System Issue',
                'has_children': False,
                'type': 'STEP'
            },
            {
                'id': 'test_011',
                'name': 'OCP-39601:zxiao:API_Server:[sig-api-machinery] API_Server Examine critical errors in openshift-kube-apiserver related log files',
                'status': 'FAILED',
                'start_time': '2025-08-08T20:00:00Z',
                'end_time': '2025-08-08T20:01:09Z',
                'duration': 69000,
                'launch_id': 'launch_011',
                'launch_name': 'periodic-ci-openshift-openshift-tests-private-release-4.20-amd64-nightly-aws-rosa-advanced-stage-f7',
                'component': 'API_Server',
                'version': '4.20',
                'defect_type': 'Predicted System Issue',
                'has_children': False,
                'type': 'STEP'
            },
            {
                'id': 'test_012',
                'name': 'OCP-11887:dpunia:API_Server:[sig-api-machinery] API_Server Could delete all the resource when deleting the project [Serial]',
                'status': 'FAILED',
                'start_time': '2025-08-08T21:00:00Z',
                'end_time': '2025-08-08T21:00:30Z',
                'duration': 30000,
                'launch_id': 'launch_012',
                'launch_name': 'periodic-ci-openshift-openshift-tests-private-release-4.20-multi-nightly-gcp-ipi-custom-masternameprefix-tp-amd-f28-destructive',
                'component': 'API_Server',
                'version': '4.20',
                'defect_type': 'Predicted System Issue',
                'has_children': False,
                'type': 'STEP'
            },
            {
                'id': 'test_003',
                'name': 'NETWORK Test OCP-77919: [Apiserver] HPA/oc scale and DeploymenConfig Should be working [Disruptive] [Serial]',
                'status': 'FAILED',
                'start_time': '2025-08-08T12:00:00Z',
                'end_time': '2025-08-08T12:00:04Z',
                'duration': 4000,
                'launch_id': 'launch_003',
                'launch_name': 'periodic-ci-openshift-openshift-tests-private-release-4.19-amd64-nightly-aws-rosa-sts-shared-vpc-stage-f7',
                'component': 'NETWORK',
                'version': '4.19',
                'defect_type': 'ti003',
                'has_children': False,
                'type': 'STEP'
            },
            {
                'id': 'test_004',
                'name': 'NODE Test OCP-11887: Could delete all the resource when deleting the project [Serial]',
                'status': 'INTERRUPTED',
                'start_time': '2025-08-08T13:00:00Z',
                'end_time': '2025-08-08T13:00:04Z',
                'duration': 4000,
                'launch_id': 'launch_004',
                'launch_name': 'periodic-ci-openshift-openshift-tests-private-release-4.19-amd64-nightly-aws-rosa-sts-shared-vpc-stage-f7',
                'component': 'NODE',
                'version': '4.19',
                'defect_type': 'ti004',
                'has_children': False,
                'type': 'STEP'
            },
            {
                'id': 'test_005',
                'name': 'API_Server Test OCP-55494: [Apiserver] When using webhooks fails to rollout latest deploymentconfig [Disruptive] [Serial]',
                'status': 'FAILED',
                'start_time': '2025-08-08T14:00:00Z',
                'end_time': '2025-08-08T14:15:00Z',
                'duration': 900000,
                'launch_id': 'launch_005',
                'launch_name': 'periodic-ci-openshift-openshift-tests-private-release-4.19-amd64-nightly-aws-rosa-sts-shared-vpc-stage-f7',
                'component': 'API_Server',
                'version': '4.19',
                'defect_type': 'ti005',
                'has_children': False,
                'type': 'STEP'
            }
        ]
        
        # Generate additional test cases to meet the limit
        mock_test_cases = base_test_cases.copy()
        
        # Add more test cases with different components and versions
        components = ['API_Server', 'STORAGE', 'NETWORK', 'NODE', 'OLM', 'Workloads', 'SDN', 'PSAP', 'OAP', 'UserInterface']
        versions = ['4.19', '4.20', '4.21']
        statuses = ['FAILED', 'INTERRUPTED']
        
        for i in range(6, limit + 1):
            component = components[i % len(components)]
            version = versions[i % len(versions)]
            status = statuses[i % len(statuses)]
            
            test_case = {
                'id': f'test_{i:03d}',
                'name': f'{component} Test OCP-{50000 + i}: {component} component test case {i}',
                'status': status,
                'start_time': f'2025-08-08T{10 + (i % 14):02d}:{i % 60:02d}:00Z',
                'end_time': f'2025-08-08T{10 + (i % 14):02d}:{(i % 60) + 5:02d}:00Z',
                'duration': (i % 60 + 1) * 1000,
                'launch_id': f'launch_{i:03d}',
                'launch_name': f'periodic-ci-openshift-openshift-tests-private-release-{version}-amd64-nightly-aws-ipi-disc-priv-localzone-fips-f7-nokubeadmin',
                'component': component,
                'version': version,
                'defect_type': f'ti{i:03d}',
                'has_children': False,
                'type': 'STEP'
            }
            mock_test_cases.append(test_case)
        
        # Return only the requested number of test cases
        return mock_test_cases[:limit]

    def _should_include_test_case(self, item: Dict, components: Optional[List[str]] = None,
                                 versions: Optional[List[str]] = None, statuses: Optional[List[str]] = None,
                                 defect_types: Optional[List[str]] = None) -> bool:
        """Check if test case should be included based on filters - following Ruby script pattern"""
        
        # Extract component and version from the item
        component = item.get('component', '')
        version = item.get('version', '')
        

        
        # Component filtering - following Ruby script pattern with regex matching
        if components:
            component_mapping = {
                'API': ['API_Server', 'API'],
                'STORAGE': ['STORAGE', 'Storage'],
                'NETWORK': ['NETWORK', 'Network', 'SDN'],
                'NODE': ['NODE', 'Node'],
                'OLM': ['OLM', 'Operator'],
                'WORKLOADS': ['Workloads', 'Workload'],
                'SDN': ['SDN', 'Network'],
                'PSAP': ['PSAP'],
                'OAP': ['OAP'],
                'USERINTERFACE': ['UserInterface', 'UI'],
                'AUTHENTICATION': ['Authentication', 'Auth'],
                'CLUSTER_INFRASTRUCTURE': ['Cluster_Infrastructure', 'Infrastructure'],
                'CLUSTER_OBSERVABILITY': ['Cluster_Observability', 'Observability'],
                'SECURITY_AND_COMPLIANCE': ['Security_and_Compliance', 'Security'],
                'CONTAINER_ENGINE_TOOLS': ['Container_Engine_Tools', 'Container'],
                'LOGGING': ['LOGGING', 'Logging'],
                'IMAGE_REGISTRY': ['Image_Registry', 'Registry'],
                'NETWORK_EDGE': ['Network_Edge', 'Edge'],
                'NETWORK_OBSERVABILITY': ['Network_Observability', 'NetObs'],
                'MCO': ['MCO'],
                'OTA': ['OTA'],
                'ETCD': ['ETCD', 'Etcd'],
                'CFE': ['CFE'],
                'OPERATOR_SDK': ['Operator_SDK', 'SDK'],
                'CYPESS': ['Cypress', 'UI'],
                'INSTALLER': ['INSTALLER', 'Installer'],
                'PERFSCALE': ['PerfScale', 'Performance']
            }
            
            component_match = False
            for comp in components:
                comp_upper = comp.upper()
                if comp_upper in component_mapping:
                    # Check if any of the mapped components match
                    for mapped_comp in component_mapping[comp_upper]:
                        if mapped_comp.lower() in component.lower():
                            component_match = True
                            break
                    if component_match:
                        break
                else:
                    # Direct match - more flexible like Ruby script
                    if comp.lower() in component.lower() or component.lower() in comp.lower():
                        component_match = True
                        break
            
            if not component_match:
                return False
        
        # Version filtering - exact match for version numbers
        if versions:
            version_match = False
            for ver in versions:
                # Exact version matching to avoid 4.17 matching 4.20
                if ver.strip() == version.strip():
                    version_match = True
                    break
            if not version_match:
                return False
        
        # Status filtering - following Ruby script pattern
        if statuses:
            item_status = item.get('status', '').upper()
            status_match = False
            for status in statuses:
                if status.upper() in item_status or item_status in status.upper():
                    status_match = True
                    break
            if not status_match:
                return False
        
        # Defect type filtering
        if defect_types:
            item_defect_type = item.get('issue', {}).get('issueType', '').upper()
            defect_match = False
            for defect_type in defect_types:
                if defect_type.upper() in item_defect_type:
                    defect_match = True
                    break
            if not defect_match:
                return False
        
        return True

    def _extract_component(self, test_name: str) -> str:
        """Extract component from test name - following Ruby script pattern"""
        # Common patterns for component extraction based on Ruby script
        test_name_upper = test_name.upper()
        
        # Check for specific component patterns
        if 'API_SERVER' in test_name_upper or '[SIG-API-MACHINERY]' in test_name_upper:
            return 'API_Server'
        elif 'STORAGE' in test_name_upper or '[SIG-STORAGE]' in test_name_upper:
            return 'STORAGE'
        elif 'NETWORK' in test_name_upper or 'SDN' in test_name_upper or '[SIG-NETWORK]' in test_name_upper:
            return 'NETWORK'
        elif 'NODE' in test_name_upper or '[SIG-NODE]' in test_name_upper:
            return 'NODE'
        elif 'OLM' in test_name_upper or 'OPERATOR' in test_name_upper:
            return 'OLM'
        elif 'WORKLOADS' in test_name_upper or '[SIG-APPS]' in test_name_upper:
            return 'Workloads'
        elif 'PSAP' in test_name_upper:
            return 'PSAP'
        elif 'OAP' in test_name_upper:
            return 'OAP'
        elif 'USERINTERFACE' in test_name_upper or 'UI' in test_name_upper or 'CYPRESS' in test_name_upper:
            return 'UserInterface'
        elif 'AUTHENTICATION' in test_name_upper or 'AUTH' in test_name_upper:
            return 'Authentication'
        elif 'CLUSTER_INFRASTRUCTURE' in test_name_upper or 'INFRASTRUCTURE' in test_name_upper:
            return 'Cluster_Infrastructure'
        elif 'CLUSTER_OBSERVABILITY' in test_name_upper or 'OBSERVABILITY' in test_name_upper:
            return 'Cluster_Observability'
        elif 'SECURITY_AND_COMPLIANCE' in test_name_upper or 'SECURITY' in test_name_upper:
            return 'Security_and_Compliance'
        elif 'CONTAINER_ENGINE_TOOLS' in test_name_upper or 'CONTAINER' in test_name_upper:
            return 'Container_Engine_Tools'
        elif 'LOGGING' in test_name_upper:
            return 'LOGGING'
        elif 'IMAGE_REGISTRY' in test_name_upper or 'REGISTRY' in test_name_upper:
            return 'Image_Registry'
        elif 'NETWORK_EDGE' in test_name_upper or 'EDGE' in test_name_upper:
            return 'Network_Edge'
        elif 'NETWORK_OBSERVABILITY' in test_name_upper or 'NETOBS' in test_name_upper:
            return 'Network_Observability'
        elif 'MCO' in test_name_upper:
            return 'MCO'
        elif 'OTA' in test_name_upper:
            return 'OTA'
        elif 'ETCD' in test_name_upper:
            return 'ETCD'
        elif 'CFE' in test_name_upper:
            return 'CFE'
        elif 'OPERATOR_SDK' in test_name_upper or 'SDK' in test_name_upper:
            return 'Operator_SDK'
        elif 'INSTALLER' in test_name_upper:
            return 'INSTALLER'
        elif 'PERFSCALE' in test_name_upper or 'PERFORMANCE' in test_name_upper:
            return 'PerfScale'
        else:
            return 'UNKNOWN'

    def _extract_version(self, launch_name: str) -> str:
        """Extract version from launch name"""
        # Common patterns for version extraction
        import re
        version_match = re.search(r'(\d+\.\d+)', launch_name)
        if version_match:
            return version_match.group(1)
        return 'UNKNOWN'

    async def analyze_selected_test_cases(self, test_ids: List[str], update_comments: bool = True,
                                        update_status: bool = True, generate_report: bool = True) -> List[TestFailure]:
        """Analyze only selected test cases"""
        
        try:
            logger.info(f"Starting analysis of {len(test_ids)} selected test cases")
            
            failures = []
            
            # Process each selected test case
            for i, test_id in enumerate(test_ids, 1):
                try:
                    logger.info(f"Analyzing test case {i}/{len(test_ids)}: {test_id}")
                    
                    # Check if this is a mock test case (for testing purposes)
                    if test_id.startswith('test_'):
                        # Create mock analysis for testing
                        mock_failure = await self._create_mock_failure(test_id)
                        if mock_failure:
                            failures.append(mock_failure)
                        continue
                    
                    # Get test case details
                    test_details = await self._get_test_case_details(test_id)
                    if not test_details:
                        logger.warning(f"Could not get details for test case {test_id}")
                        continue
                    
                    # Analyze the test case
                    failure = await self._analyze_single_failure(test_details)
                    if failure:
                        failures.append(failure)
                        
                        # Update Report Portal if requested
                        if update_comments or update_status:
                            await self._update_test_case_in_report_portal(test_id, failure, update_comments, update_status)
                    
                except Exception as e:
                    logger.error(f"Failed to analyze test case {test_id}: {e}")
                    continue
            
            logger.info(f"Successfully analyzed {len(failures)} out of {len(test_ids)} test cases")
            return failures
            
        except Exception as e:
            logger.error(f"Failed to analyze selected test cases: {e}")
            return []

    async def _get_test_case_details(self, test_id: str) -> Optional[Dict]:
        """Get detailed information about a specific test case"""
        
        try:
            # Get test item details
            test_url = f"{self.rp_url}/api/v1/{self.project}/item/{test_id}"
            response = self._make_request('GET', test_url)
            
            if response and response.status_code == 200:
                test_data = response.json()
                
                # Extract failure message and logs from issue.comment
                failure_message = "No failure message available"
                logs = "No logs available"
                external_log_links = []
                
                # Get launch details to extract external log links
                launch_id = test_data.get('launchId')
                if launch_id:
                    try:
                        launch_url = f"{self.rp_url}/api/v1/{self.project}/launch/{launch_id}"
                        launch_response = self._make_request('GET', launch_url)
                        if launch_response and launch_response.status_code == 200:
                            launch_data = launch_response.json()
                            if launch_data.get('description'):
                                external_log_links.append(launch_data['description'])
                    except Exception as e:
                        logger.warning(f"Failed to get launch details for {launch_id}: {e}")
                
                if test_data.get('issue') and test_data['issue'].get('comment'):
                    comment = test_data['issue']['comment']
                    
                    # Check if comment contains TFA-R similarity results
                    if 'TFA-R' in comment and 'Similarity Score' in comment:
                        # Extract failure message from TFA-R results
                        lines = comment.split('\n')
                        for line in lines:
                            if line.strip() and not line.startswith('|') and not line.startswith('TFA-R'):
                                failure_message = line.strip()
                                break
                        
                        # Extract TFA-R similarity URLs for more detailed information
                        similarity_urls = []
                        if 'TFA-R[Similar_Results]' in comment:
                            # Parse TFA-R similarity results
                            import re
                            url_pattern = r'https://[^\s,]+'
                            urls = re.findall(url_pattern, comment)
                            similarity_urls = urls
                        
                        # Use the TFA-R results as logs
                        logs = f"Report Portal Analysis Results:\n{comment}\n\n"
                        
                        if similarity_urls:
                            logs += f"Similar Test Cases (for detailed logs):\n"
                            for i, url in enumerate(similarity_urls, 1):
                                logs += f"{i}. {url}\n"
                            logs += "\n"
                        
                        logs += "Note: Click on the similarity URLs above to view detailed logs from similar test cases."
                    else:
                        # Use the comment as both failure message and logs
                        failure_message = comment
                        logs = comment
                
                # Add external log links to logs
                if external_log_links:
                    logs += f"\n\nExternal Log Links:\n"
                    for link in external_log_links:
                        logs += f"- {link}\n"
                    logs += "\nNote: These external links contain the detailed test execution logs from the CI system."
                    logs += "\nTo view actual logs:"
                    logs += "\n1. Click on the external log links above (requires CI system access)"
                    logs += "\n2. Or click on the TFA-R similarity URLs to see logs from similar test cases"
                    logs += "\n3. The external links contain the complete test execution output including error messages, stack traces, and debug information"
                
                # Add extracted information to test data
                test_data['extracted_failure_message'] = failure_message
                test_data['extracted_logs'] = logs
                
                return test_data
            else:
                logger.warning(f"No details found for test case {test_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get test case details for {test_id}: {e}")
            return None

    async def _update_test_case_in_report_portal(self, test_id: str, failure: TestFailure,
                                               update_comments: bool, update_status: bool):
        """Update test case in Report Portal with analysis results"""
        
        try:
            update_data = {}
            
            if update_comments:
                update_data['issue'] = {
                    'comment': failure.ai_analysis, # Use ai_analysis from TestFailure
                    'issueType': failure.category.value
                }
            
            if update_status:
                update_data['status'] = failure.category.value.upper()
            
            if update_data:
                update_url = f"{self.rp_url}/api/v1/{self.project}/item/{test_id}"
                await self._make_request('PUT', update_url, json=update_data)
                logger.info(f"Updated test case {test_id} in Report Portal")
                
        except Exception as e:
            logger.error(f"Failed to update test case {test_id} in Report Portal: {e}")

    async def _create_mock_failure(self, test_id: str) -> Optional[TestFailure]:
        """Create a mock test failure for testing purposes"""
        
        try:
            from datetime import datetime
            
            # Create mock test data based on test_id
            if test_id == "test_001":
                test_name = "API_Server Test OCP-41664: Check deprecated APIs to be removed in next release"
                category = IssueCategory.SYSTEM_ISSUE
                priority = "medium"
                analysis = "This test failure is related to deprecated API usage in the API Server component. The test is checking for APIs that should be removed in the next release. The failure indicates that the APIRequestCounts resource has no items, which suggests the deprecated API tracking is not working as expected."
                failure_message = "Total number of APIRequestCounts items: 0"
                stack_trace = """fail [github.com/openshift/openshift-tests-private/test/extended/apiserverauth/apiserver.go:1530]: Total number of APIRequestCounts items: 0

2025-08-03 03:16:04
I0801 15:17:45.400096 219201 openshift-tests.go:202] Is kubernetes cluster: no, is external OIDC cluster: no
I0801 15:17:45.400194 219201 test_context.go:563] The --provider flag is not set. Continuing as if --provider=skeleton had been used.
I0801 15:17:45.843630 219201 client.go:1013] Running 'oc --kubeconfig=/tmp/kubeconfig-3124643851 get node -l node-role.kubernetes.io/worker -o=jsonpath={.items[*].metadata.name}'
[1754061462] openshift extended e2e - 1/1 specs I0801 15:17:46.400984 219201 apiserver.go:48] The cluster should be healthy before running case.
I0801 15:17:46.401146 219201 client.go:1013] Running 'oc --kubeconfig=/tmp/kubeconfig-3124643851 get node'
I0801 15:17:46.593853 219201 client.go:1013] Running 'oc --kubeconfig=/tmp/kubeconfig-3124643851 get co'
I0801 15:17:46.795466 219201 client.go:1013] Running 'oc --kubeconfig=/tmp/kubeconfig-3124643851 new-project azw0lfeo --skip-config-write'
Project "azw0lfeo" created on server "https://api.ci-op-j24kb223-7df0d.qe.devcluster.openshift.com:6443".

To switch to this project and start adding applications, use:

    oc project azw0lfeo
I0801 15:17:47.036311 219201 client.go:1013] Running 'oc --kubeconfig=/tmp/kubeconfig-3124643851 delete project azw0lfeo --ignore-not-found'
project.project.openshift.io "azw0lfeo" deleted
I0801 15:17:55.663129 219201 apiserver_util.go:1796] Cluster sanity check passed
STEP: 1) Get current cluster version 08/01/25 15:17:55.663
I0801 15:17:55.663569 219201 client.go:1013] Running 'oc --kubeconfig=/tmp/kubeconfig-3124643851 get clusterversion -o jsonpath={..desired.version}'
I0801 15:17:55.828603 219201 apiserver.go:1504] Cluster Version: 4.19
STEP: 2.1) Get current Kubernetes version 08/01/25 15:17:55.828
I0801 15:17:55.828916 219201 client.go:1013] Running 'oc --kubeconfig=/tmp/kubeconfig-3124643851 get co/kube-apiserver -o jsonpath='{.status.versions[?(@.name=="kube-apiserver")].version}''
I0801 15:17:55.995416 219201 apiserver.go:1514] Current Release: 1.32, Next Release: 1.33
STEP: 2.2) Checking if 'apirequestcounts' has any items 08/01/25 15:17:55.995
I0801 15:17:55.995605 219201 client.go:1013] Running 'oc --kubeconfig=/tmp/kubeconfig-3124643851 get apirequestcounts -o json'
Aug  1 15:17:56.171: INFO: test dir /tmp/-OCP-apisever-cases-cqe62185/ is cleaned up

• [FAILED] [9.773 seconds]
[sig-api-machinery] API_Server [It] Author:dpunia-NonHyperShiftHOST-ROSA-ARO-OSD_CCS-High-41664-Check deprecated APIs to be removed in next release and next EUS release
/go/src/github.com/openshift/openshift-tests-private/test/extended/apiserverauth/apiserver.go:1375

[FAILED] Total number of APIRequestCounts items: 0
In [It] at: /go/src/github.com/openshift/openshift-tests-private/test/extended/apiserverauth/apiserver.go:1530 @ 08/01/25 15:17:56.171

Summarizing 1 Failure:
[FAIL] [sig-api-machinery] API_Server [It] Author:dpunia-NonHyperShiftHOST-ROSA-ARO-OSD_CCS-High-41664-Check deprecated APIs to be removed in next release and next EUS release
/go/src/github.com/openshift/openshift-tests-private/test/extended/apiserverauth/apiserver.go:1530

Ran 1 of 1 Specs in 9.773 seconds
FAIL! -- 0 Passed | 1 Failed | 0 Pending | 0 Skipped
fail [github.com/openshift/openshift-tests-private/test/extended/apiserverauth/apiserver.go:1530]: Total number of APIRequestCounts items: 0"""
            elif test_id == "test_002":
                test_name = "STORAGE Test OCP-39601: Examine critical errors in openshift-kube-apiserver related log files"
                category = IssueCategory.INFRASTRUCTURE
                priority = "high"
                analysis = "This test failure indicates critical errors in the storage infrastructure. The test examines storage-related log files for error patterns and found critical storage backend issues."
                failure_message = "Critical storage infrastructure error detected in kube-apiserver logs"
                stack_trace = """ERROR: Critical storage backend connection failure
2025-08-03 03:16:04
I0801 15:17:45.400096 219201 storage.go:202] Storage backend connection attempt
I0801 15:17:45.400194 219201 storage.go:563] Attempting to connect to storage backend
I0801 15:17:45.843630 219201 client.go:1013] Running storage health check
I0801 15:17:46.400984 219201 storage.go:48] Storage backend health check failed
I0801 15:17:46.401146 219201 client.go:1013] Running 'oc --kubeconfig=/tmp/kubeconfig-3124643851 get storageclass'
I0801 15:17:46.593853 219201 client.go:1013] Running 'oc --kubeconfig=/tmp/kubeconfig-3124643851 get pv'
I0801 15:17:46.795466 219201 client.go:1013] Running 'oc --kubeconfig=/tmp/kubeconfig-3124643851 get pvc'
I0801 15:17:47.036311 219201 storage_util.go:1796] Storage backend connection timeout
STEP: 1) Check storage backend connectivity 08/01/25 15:17:47.036
STEP: 2) Verify storage class availability 08/01/25 15:17:47.036
STEP: 3) Test persistent volume creation 08/01/25 15:17:47.036

• [FAILED] [30.773 seconds]
[sig-storage] STORAGE [It] Author:storage-team-Critical-39601-Examine critical errors in openshift-kube-apiserver related log files
/go/src/github.com/openshift/openshift-tests-private/test/extended/storage/storage.go:1375

[FAILED] Storage backend connection failed: timeout after 30 seconds
In [It] at: /go/src/github.com/openshift/openshift-tests-private/test/extended/storage/storage.go:1530 @ 08/01/25 15:17:56.171

Summarizing 1 Failure:
[FAIL] [sig-storage] STORAGE [It] Author:storage-team-Critical-39601-Examine critical errors in openshift-kube-apiserver related log files
/go/src/github.com/openshift/openshift-tests-private/test/extended/storage/storage.go:1530

Ran 1 of 1 Specs in 30.773 seconds
FAIL! -- 0 Passed | 1 Failed | 0 Pending | 0 Skipped
fail [github.com/openshift/openshift-tests-private/test/extended/storage/storage.go:1530]: Storage backend connection failed: timeout after 30 seconds"""
            else:
                test_name = f"Mock Test {test_id}"
                category = IssueCategory.UNKNOWN
                priority = "medium"
                analysis = "This is a mock test case created for testing purposes."
                failure_message = "Mock test failure for demonstration"
                stack_trace = "Mock stack trace for testing"
            
            # Create mock failure with all required fields
            failure = TestFailure(
                test_id=test_id,
                test_name=test_name,
                failure_message=failure_message,
                stack_trace=stack_trace,
                timestamp=datetime.now(),
                duration=5.0,  # 5 seconds
                category=category,
                confidence=0.85,
                ai_analysis=analysis,
                suggested_fix="Review the specific error logs and implement appropriate fixes based on the failure pattern.",
                priority=priority,
                tags=["mock", "test"]
            )
            
            return failure
            
        except Exception as e:
            logger.error(f"Failed to create mock failure for {test_id}: {e}")
            return None

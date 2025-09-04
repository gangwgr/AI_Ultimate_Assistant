import logging
import asyncio
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime

from app.services.report_portal_agent import ReportPortalAgent, TestFailure, IssueCategory

logger = logging.getLogger(__name__)

report_portal_router = APIRouter(tags=["Report Portal"])

# Pydantic models for API requests/responses
class ReportPortalConfig(BaseModel):
    rp_url: str
    rp_token: str
    project: str
    ssl_verify: bool = False  # Default to False for Red Hat internal systems with self-signed certificates

class AnalysisRequest(BaseModel):
    hours_back: int = 24
    components: Optional[List[str]] = None  # Filter by component names (e.g., ["API_Server", "STORAGE"])
    versions: Optional[List[str]] = None  # Filter by versions (e.g., ["4.19", "4.20"])
    statuses: Optional[List[str]] = None  # Filter by statuses (e.g., ["FAILED", "INTERRUPTED"])
    defect_types: Optional[List[str]] = None  # Filter by defect types (e.g., ["ti001", "ti_1hrghcxlbgshc"])
    update_comments: bool = True
    update_status: bool = True
    generate_report: bool = True
    max_tests: int = 100  # Limit number of tests to analyze
    batch_size: int = 50  # Number of tests per batch

class AnalysisResponse(BaseModel):
    total_failures: int
    analyzed_failures: int
    categories: Dict[str, int]
    priorities: Dict[str, int]
    comments_updated: int
    status_updated: int
    report: Optional[str] = None
    errors: List[Dict[str, Any]] = []

class TestFailureResponse(BaseModel):
    test_id: str
    test_name: str
    category: str
    confidence: float
    priority: str
    analysis: str
    suggested_fix: str
    tags: List[str]

# Global agent instance (you might want to make this configurable)
report_portal_agent: Optional[ReportPortalAgent] = None

def get_report_portal_agent() -> ReportPortalAgent:
    """Get or create Report Portal agent instance"""
    global report_portal_agent
    if report_portal_agent is None:
        # You can make this configurable via environment variables
        raise HTTPException(
            status_code=500, 
            detail="Report Portal agent not configured. Please configure RP_URL, RP_TOKEN, and PROJECT."
        )
    return report_portal_agent

@report_portal_router.post("/configure")
async def configure_report_portal(config: ReportPortalConfig):
    """Configure Report Portal connection"""
    global report_portal_agent
    
    # Debug logging
    logger.info(f"Configuring Report Portal with SSL verify: {config.ssl_verify}")
    logger.info(f"Config object received: {config}")
    
    try:
        # Test connection
        test_agent = ReportPortalAgent(
            config.rp_url, 
            config.rp_token, 
            config.project, 
            ssl_verify=config.ssl_verify
        )
        
        # Try to fetch a small sample to verify connection
        test_failures = await test_agent.analyze_failures(hours_back=1)
        
        # If successful, set the global agent
        report_portal_agent = test_agent
        
        return {
            "status": "success",
            "message": f"Successfully connected to Report Portal project: {config.project}",
            "test_failures_found": len(test_failures),
            "ssl_verify": config.ssl_verify
        }
        
    except Exception as e:
        logger.error(f"Failed to configure Report Portal: {e}")
        
        # Provide specific error messages for common issues
        error_msg = str(e)
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            detail = f"Authentication failed. Please check your API token. Error: {error_msg}"
        elif "404" in error_msg:
            detail = f"Project '{config.project}' not found. Please check the project name. Error: {error_msg}"
        elif "ssl" in error_msg.lower() or "certificate" in error_msg.lower():
            detail = f"SSL certificate issue. Try setting ssl_verify=False for internal Red Hat systems. Error: {error_msg}"
        elif "timeout" in error_msg.lower():
            detail = f"Connection timeout. Check network connectivity and try again. Error: {error_msg}"
        else:
            detail = f"Failed to connect to Report Portal: {error_msg}"
        
        raise HTTPException(status_code=400, detail=detail)

@report_portal_router.post("/analyze-failures")
async def analyze_test_failures(
    request: AnalysisRequest,
    agent: ReportPortalAgent = Depends(get_report_portal_agent)
):
    """Analyze test failures and optionally update Report Portal"""
    
    try:
        logger.info(f"Starting test failure analysis for last {request.hours_back} hours")
        
        # Analyze failures with advanced filtering and timeout
        try:
            # Calculate timeout based on max_tests and hours_back - more conservative approach
            base_timeout = 600.0  # 10 minutes base (increased from 5)
            timeout_multiplier = max(1, request.hours_back / 24)  # Scale with time range
            test_timeout_multiplier = max(1, request.max_tests / 50)  # Scale with number of tests (reduced from 100)
            total_timeout = base_timeout * timeout_multiplier * test_timeout_multiplier
            
            # Cap the timeout at 30 minutes to prevent excessive waits
            total_timeout = min(total_timeout, 1800.0)
            
            logger.info(f"Starting analysis with {total_timeout:.1f} second timeout for {request.max_tests} tests")
            
            failures = await asyncio.wait_for(
                agent.analyze_failures(
                    request.hours_back, 
                    request.components, 
                    request.versions, 
                    request.statuses, 
                    request.defect_types,
                    max_tests=request.max_tests,
                    batch_size=request.batch_size
                ),
                timeout=total_timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Analysis timeout after {total_timeout:.1f} seconds")
            raise HTTPException(status_code=408, detail=f"Analysis timeout after {total_timeout:.1f} seconds - try reducing hours_back or components")
        
        if not failures:
            return AnalysisResponse(
                total_failures=0,
                analyzed_failures=0,
                categories={},
                priorities={},
                comments_updated=0,
                status_updated=0,
                report="No test failures found in the specified time range."
            )
        
        # Count categories and priorities
        categories = {}
        priorities = {}
        for failure in failures:
            category = failure.category.value
            categories[category] = categories.get(category, 0) + 1
            
            priority = failure.priority
            priorities[priority] = priorities.get(priority, 0) + 1
        
        # Update comments if requested
        comments_result = {"updated": 0, "failed": 0, "errors": []}
        if request.update_comments:
            comments_result = await agent.update_test_comments(failures)
        
        # Update status if requested
        status_result = {"updated": 0, "failed": 0, "errors": []}
        if request.update_status:
            status_result = await agent.update_test_status(failures)
        
        # Generate report if requested
        report = None
        if request.generate_report:
            report = await agent.generate_failure_report(failures)
        
        return AnalysisResponse(
            total_failures=len(failures),
            analyzed_failures=len(failures),
            categories=categories,
            priorities=priorities,
            comments_updated=comments_result["updated"],
            status_updated=status_result["updated"],
            report=report,
            errors=comments_result["errors"] + status_result["errors"]
        )
        
    except Exception as e:
        logger.error(f"Failed to analyze test failures: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze test failures: {str(e)}"
        )

@report_portal_router.get("/failures")
async def get_analyzed_failures(
    hours_back: int = 24,
    agent: ReportPortalAgent = Depends(get_report_portal_agent)
):
    """Get analyzed test failures without updating Report Portal"""
    
    try:
        failures = await agent.analyze_failures(hours_back)
        
        # Convert to response format
        failure_responses = []
        for failure in failures:
            failure_responses.append(TestFailureResponse(
                test_id=failure.test_id,
                test_name=failure.test_name,
                category=failure.category.value,
                confidence=failure.confidence,
                priority=failure.priority,
                analysis=failure.ai_analysis,
                suggested_fix=failure.suggested_fix,
                tags=failure.tags
            ))
        
        return {
            "failures": failure_responses,
            "total": len(failure_responses),
            "categories": {
                failure.category.value: len([f for f in failures if f.category == failure.category])
                for failure in failures
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get analyzed failures: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get analyzed failures: {str(e)}"
        )

@report_portal_router.post("/update-comments")
async def update_test_comments(
    test_ids: List[str],
    agent: ReportPortalAgent = Depends(get_report_portal_agent)
):
    """Update comments for specific test failures"""
    
    try:
        # Get failures for the specified test IDs
        all_failures = await agent.analyze_failures(hours_back=168)  # Last week
        target_failures = [f for f in all_failures if f.test_id in test_ids]
        
        if not target_failures:
            raise HTTPException(
                status_code=404,
                detail=f"No test failures found for the specified test IDs: {test_ids}"
            )
        
        # Update comments
        result = await agent.update_test_comments(target_failures)
        
        return {
            "message": f"Updated comments for {result['updated']} tests",
            "updated": result["updated"],
            "failed": result["failed"],
            "errors": result["errors"]
        }
        
    except Exception as e:
        logger.error(f"Failed to update test comments: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update test comments: {str(e)}"
        )

@report_portal_router.post("/update-status")
async def update_test_status(
    test_ids: List[str],
    agent: ReportPortalAgent = Depends(get_report_portal_agent)
):
    """Update status for specific test failures"""
    
    try:
        # Get failures for the specified test IDs
        all_failures = await agent.analyze_failures(hours_back=168)  # Last week
        target_failures = [f for f in all_failures if f.test_id in test_ids]
        
        if not target_failures:
            raise HTTPException(
                status_code=404,
                detail=f"No test failures found for the specified test IDs: {test_ids}"
            )
        
        # Update status
        result = await agent.update_test_status(target_failures)
        
        return {
            "message": f"Updated status for {result['updated']} tests",
            "updated": result["updated"],
            "failed": result["failed"],
            "errors": result["errors"]
        }
        
    except Exception as e:
        logger.error(f"Failed to update test status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update test status: {str(e)}"
        )

@report_portal_router.get("/report")
async def generate_failure_report(
    hours_back: int = 24,
    agent: ReportPortalAgent = Depends(get_report_portal_agent)
):
    """Generate a comprehensive failure analysis report"""
    
    try:
        failures = await agent.analyze_failures(hours_back)
        report = await agent.generate_failure_report(failures)
        
        return {
            "report": report,
            "total_failures": len(failures),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate failure report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate failure report: {str(e)}"
        )

@report_portal_router.get("/categories")
async def get_failure_categories():
    """Get available failure categories"""
    
    categories = [
        {
            "value": category.value,
            "name": category.value.replace('_', ' ').title(),
            "description": get_category_description(category)
        }
        for category in IssueCategory
    ]
    
    return {"categories": categories}

def get_category_description(category: IssueCategory) -> str:
    """Get description for a failure category"""
    
    descriptions = {
        IssueCategory.SYSTEM_ISSUE: "Infrastructure, environment, or system-level problems",
        IssueCategory.PRODUCTION_BUG: "Actual bugs in the application code",
        IssueCategory.TEST_ENVIRONMENT: "Test environment configuration issues",
        IssueCategory.INFRASTRUCTURE: "Network, database, or service connectivity issues",
        IssueCategory.NETWORK: "Network timeouts, connectivity problems",
        IssueCategory.DATA_ISSUE: "Test data problems, missing data, corrupted data",
        IssueCategory.CONFIGURATION: "Configuration errors, missing settings",
        IssueCategory.TIMEOUT: "Test timeouts, slow performance",
        IssueCategory.RACE_CONDITION: "Timing-related issues, concurrency problems",
        IssueCategory.UNKNOWN: "Cannot determine category"
    }
    
    return descriptions.get(category, "Unknown category")

@report_portal_router.get("/health")
async def health_check():
    """Health check for Report Portal integration"""
    
    if report_portal_agent is None:
        return {
            "status": "not_configured",
            "message": "Report Portal agent not configured",
            "ssl_status": "Not configured"
        }
    
    try:
        # Try to fetch a small sample to verify connection
        test_failures = await report_portal_agent.analyze_failures(hours_back=1)
        
        return {
            "status": "healthy",
            "message": "Report Portal integration is working",
            "test_failures_found": len(test_failures),
            "ssl_status": f"SSL verify: {report_portal_agent.ssl_verify}"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Report Portal integration error: {str(e)}",
            "ssl_status": f"SSL verify: {report_portal_agent.ssl_verify}" if report_portal_agent else "Not configured"
        }

@report_portal_router.get("/setup-instructions")
async def get_setup_instructions():
    """Get setup instructions for Red Hat internal Report Portal"""
    
    return {
        "title": "Red Hat Internal Report Portal Setup",
        "instructions": [
            {
                "step": 1,
                "title": "Access Report Portal in Browser",
                "description": "Open https://reportportal-openshift.apps.dno.ocp-hub.prod.psi.redhat.com in your browser",
                "action": "Navigate to the URL and log in with your Red Hat credentials"
            },
            {
                "step": 2,
                "title": "Generate API Token",
                "description": "Generate an API token from Report Portal UI",
                "action": "Go to User Settings → API Tokens → Generate new token"
            },
            {
                "step": 3,
                "title": "Configure Connection",
                "description": "Use the API token instead of username/password",
                "action": "Set ssl_verify=False for internal Red Hat systems"
            },
            {
                "step": 4,
                "title": "Test Connection",
                "description": "Verify the connection works",
                "action": "Use the /configure endpoint with your API token"
            }
        ],
        "configuration": {
            "rp_url": "https://reportportal-openshift.apps.dno.ocp-hub.prod.psi.redhat.com",
            "project": "PROW",
            "ssl_verify": False,
            "auth_method": "API Token (not username/password)"
        }
    }

@report_portal_router.get("/components")
async def get_available_components(
    hours_back: int = 24,
    agent: ReportPortalAgent = Depends(get_report_portal_agent)
):
    """Get list of available components from recent test data"""
    try:
        components = await agent.get_available_components(hours_back)
        return {
            "success": True,
            "components": components,
            "total_components": len(components),
            "hours_back": hours_back
        }
    except Exception as e:
        logger.error(f"Failed to get available components: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get available components: {str(e)}"
        )

@report_portal_router.get("/component-statistics")
async def get_component_statistics(
    hours_back: int = 24,
    agent: ReportPortalAgent = Depends(get_report_portal_agent)
):
    """Get statistics for each component (total tests, failed tests, success rate)"""
    try:
        stats = await agent.get_component_statistics(hours_back)
        return {
            "success": True,
            "statistics": stats,
            "total_components": len(stats),
            "hours_back": hours_back
        }
    except Exception as e:
        logger.error(f"Failed to get component statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get component statistics: {str(e)}"
        )

@report_portal_router.get("/versions")
async def get_available_versions(
    hours_back: int = 24,
    agent: ReportPortalAgent = Depends(get_report_portal_agent)
):
    """Get list of available versions from recent test data"""
    try:
        versions = await agent.get_available_versions(hours_back)
        return {
            "success": True,
            "versions": versions,
            "total_versions": len(versions),
            "hours_back": hours_back
        }
    except Exception as e:
        logger.error(f"Failed to get available versions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get available versions: {str(e)}"
        )

@report_portal_router.get("/defect-types")
async def get_available_defect_types(
    hours_back: int = 24,
    agent: ReportPortalAgent = Depends(get_report_portal_agent)
):
    """Get list of available defect types from recent test data"""
    try:
        defect_types = await agent.get_available_defect_types(hours_back)
        return {
            "success": True,
            "defect_types": defect_types,
            "total_defect_types": len(defect_types),
            "hours_back": hours_back
        }
    except Exception as e:
        logger.error(f"Failed to get available defect types: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get available defect types: {str(e)}"
        )

@report_portal_router.get("/filtered-statistics")
async def get_filtered_statistics(
    hours_back: int = 24,
    components: Optional[str] = None,
    versions: Optional[str] = None,
    statuses: Optional[str] = None,
    defect_types: Optional[str] = None,
    agent: ReportPortalAgent = Depends(get_report_portal_agent)
):
    """Get statistics for filtered test data"""
    try:
        # Parse comma-separated strings into lists
        components_list = components.split(',') if components else None
        versions_list = versions.split(',') if versions else None
        statuses_list = statuses.split(',') if statuses else None
        defect_types_list = defect_types.split(',') if defect_types else None
        
        stats = await agent.get_filtered_statistics(
            hours_back, components_list, versions_list, statuses_list, defect_types_list
        )
        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Failed to get filtered statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get filtered statistics: {str(e)}"
        )

@report_portal_router.get("/test-cases")
async def get_test_cases(
    hours_back: int = 24,
    components: Optional[str] = None,
    versions: Optional[str] = None,
    statuses: Optional[str] = None,
    defect_types: Optional[str] = None,
    limit: int = 100,
    agent: ReportPortalAgent = Depends(get_report_portal_agent)
):
    """Get available test cases with filtering options"""
    
    try:
        # Parse filter parameters
        component_list = components.split(',') if components else None
        version_list = versions.split(',') if versions else None
        status_list = statuses.split(',') if statuses else None
        defect_list = defect_types.split(',') if defect_types else None
        
        # Get test cases from Report Portal
        test_cases = await agent.get_test_cases(
            hours_back=hours_back,
            components=component_list,
            versions=version_list,
            statuses=status_list,
            defect_types=defect_list,
            limit=limit
        )
        
        return {
            "total_found": len(test_cases),
            "test_cases": test_cases,
            "filters_applied": {
                "hours_back": hours_back,
                "components": component_list,
                "versions": version_list,
                "statuses": status_list,
                "defect_types": defect_list
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get test cases: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get test cases: {str(e)}"
        )

@report_portal_router.post("/analyze-selected")
async def analyze_selected_test_cases(
    request: dict,  # Accept raw JSON dict
    agent: ReportPortalAgent = Depends(get_report_portal_agent)
):
    """Analyze only selected test cases"""
    
    try:
        test_ids = request.get("test_ids", [])
        update_comments = request.get("update_comments", True)
        update_status = request.get("update_status", True)
        generate_report = request.get("generate_report", True)
        
        logger.info(f"Starting analysis of {len(test_ids)} selected test cases")
        
        # Analyze selected test cases
        failures = await agent.analyze_selected_test_cases(
            test_ids=test_ids,
            update_comments=update_comments,
            update_status=update_status,
            generate_report=generate_report
        )
        
        if not failures:
            return AnalysisResponse(
                total_failures=0,
                analyzed_failures=0,
                categories={},
                priorities={},
                comments_updated=0,
                status_updated=0,
                report="No test failures found in the selected test cases."
            )
        
        # Count categories and priorities
        categories = {}
        priorities = {}
        for failure in failures:
            category = failure.category.value
            categories[category] = categories.get(category, 0) + 1
            
            priority = failure.priority
            priorities[priority] = priorities.get(priority, 0) + 1
        
        # Update comments if requested
        comments_result = {"updated": 0, "failed": 0, "errors": []}
        if update_comments:
            comments_result = await agent.update_test_comments(failures)
        
        # Update status if requested
        status_result = {"updated": 0, "failed": 0, "errors": []}
        if update_status:
            status_result = await agent.update_test_status(failures)
        
        # Generate report if requested
        report = None
        if generate_report:
            report = await agent.generate_failure_report(failures)
        
        # Convert failures to response format for frontend
        failure_responses = []
        for failure in failures:
            failure_responses.append({
                "test_id": failure.test_id,
                "test_name": failure.test_name,
                "category": failure.category.value,
                "confidence": failure.confidence,
                "ai_analysis": failure.ai_analysis,
                "suggested_fix": failure.suggested_fix,
                "priority": failure.priority,
                "tags": failure.tags,
                "duration": failure.duration,
                "failure_message": failure.failure_message,
                "stack_trace": failure.stack_trace
            })
        
        return {
            "total_failures": len(failures),
            "analyzed_failures": len(failures),
            "categories": categories,
            "priorities": priorities,
            "comments_updated": comments_result["updated"],
            "status_updated": status_result["updated"],
            "report": report,
            "errors": comments_result["errors"] + status_result["errors"],
            "failures": failure_responses  # Add detailed failures for frontend
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze selected test cases: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze selected test cases: {str(e)}"
        )

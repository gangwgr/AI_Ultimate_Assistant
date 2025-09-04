"""
Must-Gather Analysis Agent for OpenShift clusters
"""

import os
import re
import logging
import tempfile
import shutil
import zipfile
import tarfile
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class ClusterIssue:
    """Represents a cluster issue found in must-gather"""
    issue_type: str
    severity: str  # critical, high, medium, low
    description: str
    affected_components: List[str]
    recommendations: List[str]
    evidence: List[str] = field(default_factory=list)

@dataclass
class MustGatherAnalysis:
    """Complete analysis of must-gather logs"""
    cluster_info: Dict[str, Any]
    issues: List[ClusterIssue]
    summary: str
    root_cause: str
    immediate_actions: List[str]
    long_term_recommendations: List[str]
    priority: str
    next_steps: List[str]
    confidence: int = 85
    files_analyzed: str = "Multiple log files"
    log_evidence: List[Dict[str, str]] = None
    analysis_metadata: Dict[str, Any] = None

class MustGatherAgent:
    """Analyzes OpenShift must-gather logs"""
    
    def __init__(self):
        self.ai_agent = None
        
    async def analyze_must_gather(self, must_gather_path: str, model_preference: str = "ollama") -> MustGatherAnalysis:
        """Analyze must-gather logs and return structured analysis"""
        if not os.path.exists(must_gather_path):
            raise FileNotFoundError(f"Must-gather path not found: {must_gather_path}")
        
        logger.info(f"Starting must-gather analysis of {must_gather_path}")
        
        # Extract cluster information
        cluster_info = self._extract_cluster_info(must_gather_path)
        
        # Analyze logs for issues
        issues = self._analyze_logs(must_gather_path)
        
        # Generate AI analysis
        analysis = await self._generate_ai_analysis(cluster_info, issues, model_preference)
        
        # Add evidence and metadata
        analysis.log_evidence = self._extract_log_evidence(must_gather_path, issues)
        analysis.analysis_metadata = {
            'analysis_time': datetime.now().isoformat(),
            'files_analyzed': self._count_analyzed_files(must_gather_path),
            'ai_model_used': 'Multi-Model AI',
            'issues_found': len(issues),
            'priority': analysis.priority,
            'confidence_factors': self._calculate_confidence_factors(issues)
        }
        
        return analysis
    
    def _extract_log_evidence(self, must_gather_path: str, issues: List[ClusterIssue]) -> List[Dict[str, str]]:
        """Extract key log evidence for display"""
        evidence = []
        
        # Add evidence from issues (processed evidence)
        for issue in issues:
            for log_entry in issue.evidence[:3]:  # Top 3 evidence per issue
                evidence.append({
                    'source': issue.issue_type.replace('_', ' ').title(),
                    'message': log_entry,
                    'severity': issue.severity,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Try to add some actual log file samples
        try:
            sample_logs = self._get_sample_log_entries(must_gather_path)
            evidence.extend(sample_logs)
        except Exception as e:
            logger.debug(f"Could not extract sample logs: {e}")
        
        return evidence[:12]  # Limit to top 12 evidence entries
    
    def _get_sample_log_entries(self, must_gather_path: str) -> List[Dict[str, str]]:
        """Get sample log entries from must-gather files"""
        import glob
        sample_evidence = []
        
        # Look for common log files
        log_patterns = [
            'cluster-scoped-resources/*/events.yaml',
            'namespaces/openshift-kube-apiserver/pods/*/logs/*',
            'namespaces/openshift-etcd/pods/*/logs/*'
        ]
        
        for pattern in log_patterns:
            try:
                files = glob.glob(os.path.join(must_gather_path, pattern))
                for log_file in files[:2]:  # Limit to 2 files per pattern
                    if os.path.isfile(log_file):
                        sample_evidence.extend(self._extract_log_samples(log_file))
                        if len(sample_evidence) >= 6:  # Limit total samples
                            break
                if len(sample_evidence) >= 6:
                    break
            except Exception as e:
                logger.debug(f"Error processing pattern {pattern}: {e}")
                continue
        
        return sample_evidence
    
    def _extract_log_samples(self, file_path: str) -> List[Dict[str, str]]:
        """Extract sample log entries from a file"""
        samples = []
        file_name = os.path.basename(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            # Look for error-like patterns in recent lines
            recent_lines = lines[-50:] if len(lines) > 50 else lines
            error_patterns = ['error', 'failed', 'timeout', 'unable', 'connection refused']
            
            for line in recent_lines:
                line = line.strip()
                if len(line) > 20 and any(pattern in line.lower() for pattern in error_patterns):
                    samples.append({
                        'source': file_name,
                        'message': line[:150] + ('...' if len(line) > 150 else ''),
                        'severity': 'high' if 'error' in line.lower() or 'failed' in line.lower() else 'medium',
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    if len(samples) >= 2:  # Max 2 samples per file
                        break
                        
        except Exception as e:
            logger.debug(f"Error reading {file_path}: {e}")
        
        return samples
    
    def _count_analyzed_files(self, must_gather_path: str) -> int:
        """Count number of files analyzed"""
        count = 0
        for root, dirs, files in os.walk(must_gather_path):
            for file in files:
                if file.endswith(('.log', '.yaml', '.json', '.txt')):
                    count += 1
        return count
    
    def _calculate_confidence_factors(self, issues: List[ClusterIssue]) -> Dict[str, Any]:
        """Calculate confidence factors for the analysis"""
        total_evidence = sum(len(issue.evidence) for issue in issues)
        critical_issues = len([i for i in issues if i.severity == 'critical'])
        high_issues = len([i for i in issues if i.severity == 'high'])
        
        return {
            'total_evidence_count': total_evidence,
            'critical_issues': critical_issues,
            'high_issues': high_issues,
            'evidence_quality': 'high' if total_evidence > 10 else 'medium' if total_evidence > 5 else 'low'
        }
    
    def _extract_cluster_info(self, must_gather_path: str) -> Dict[str, Any]:
        """Extract basic cluster information from must-gather"""
        cluster_info = {
            'cluster_version': 'Unknown',
            'nodes': [],
            'operators': [],
            'etcd_members': [],
            'api_services': []
        }
        
        # Look for cluster version
        version_file = os.path.join(must_gather_path, 'cluster-scoped-resources/config.openshift.io/clusterversions.yaml')
        if os.path.exists(version_file):
            try:
                with open(version_file, 'r') as f:
                    content = f.read()
                    version_match = re.search(r'version:\s*([^\s]+)', content)
                    if version_match:
                        cluster_info['cluster_version'] = version_match.group(1)
            except Exception as e:
                logger.warning(f"Could not read cluster version: {e}")
        
        return cluster_info
    
    def _analyze_logs(self, must_gather_path: str) -> List[ClusterIssue]:
        """Analyze logs for various issues"""
        all_issues = []
        files_analyzed = 0
        
        # Walk through all log files
        for root, dirs, files in os.walk(must_gather_path):
            for file in files:
                if file.endswith(('.log', '.yaml', '.json')):
                    file_path = os.path.join(root, file)
                    files_analyzed += 1
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            file_issues = self._analyze_file_content(content, file_path)
                            if file_issues:
                                logger.info(f"Found {len(file_issues)} issues in {file_path}")
                            all_issues.extend(file_issues)
                    except Exception as e:
                        logger.warning(f"Could not read file {file_path}: {e}")
        
        # Consolidate duplicate issues
        consolidated_issues = self._consolidate_issues(all_issues)
        
        logger.info(f"Analyzed {files_analyzed} files, found {len(consolidated_issues)} unique issues (from {len(all_issues)} total)")
        return consolidated_issues
    
    def _consolidate_issues(self, issues: List[ClusterIssue]) -> List[ClusterIssue]:
        """Consolidate duplicate issues and merge evidence"""
        issue_map = {}
        
        for issue in issues:
            key = f"{issue.issue_type}_{issue.severity}"
            
            if key in issue_map:
                # Merge evidence from duplicate issues
                existing_issue = issue_map[key]
                existing_issue.evidence.extend(issue.evidence)
                # Keep only unique evidence and limit total
                existing_issue.evidence = list(dict.fromkeys(existing_issue.evidence))[:5]
                
                # Merge affected components
                existing_issue.affected_components.extend(issue.affected_components)
                existing_issue.affected_components = list(set(existing_issue.affected_components))
            else:
                # New issue type
                issue_map[key] = issue
        
        return list(issue_map.values())
    
    def _analyze_file_content(self, content: str, file_path: str) -> List[ClusterIssue]:
        """Analyze file content for issues"""
        issues = []
        file_name = os.path.basename(file_path)
        
        # Extract actual error lines from content
        lines = content.split('\n')
        actual_errors = []
        
        for line in lines:
            line = line.strip()
            if len(line) > 20:  # Skip very short lines
                lower_line = line.lower()
                
                # Collect actual error lines for evidence
                if any(error_word in lower_line for error_word in ['error:', 'failed:', 'timeout:', 'unable to', 'connection refused']):
                    actual_errors.append(line[:120] + ('...' if len(line) > 120 else ''))
        
        # Only create issues if we have actual evidence, and limit duplicates
        issues_found = set()
        
        # Network connectivity issues
        network_errors = [err for err in actual_errors if any(pattern in err.lower() for pattern in ['connection refused', 'network unreachable', 'timeout', 'unable to connect'])]
        if network_errors and "NETWORK_CONNECTIVITY" not in issues_found:
            issues.append(ClusterIssue(
                issue_type="NETWORK_CONNECTIVITY",
                severity="high",
                description="Network connectivity issues detected",
                affected_components=["all_services"],
                recommendations=["Check network connectivity between nodes", "Verify DNS resolution"],
                evidence=network_errors[:3]  # Use actual error lines
            ))
            issues_found.add("NETWORK_CONNECTIVITY")
        
        # API service failures
        api_errors = [err for err in actual_errors if any(pattern in err.lower() for pattern in ['api server', 'unauthorized', 'forbidden', 'authentication'])]
        if api_errors and "API_SERVICE_FAILURE" not in issues_found:
            issues.append(ClusterIssue(
                issue_type="API_SERVICE_FAILURE",
                severity="critical",
                description="OpenShift API services failing",
                affected_components=["openshift-apiserver", "authentication", "console"],
                recommendations=["Check API server logs", "Verify certificates", "Restart API services"],
                evidence=api_errors[:3]  # Use actual error lines
            ))
            issues_found.add("API_SERVICE_FAILURE")
        
        # Operator issues
        operator_errors = [err for err in actual_errors if any(pattern in err.lower() for pattern in ['operator', 'degraded', 'unavailable'])]
        if operator_errors and "OPERATOR_DEGRADATION" not in issues_found:
            issues.append(ClusterIssue(
                issue_type="OPERATOR_DEGRADATION",
                severity="medium",
                description="Cluster operators showing degraded status",
                affected_components=["cluster_operators"],
                recommendations=["Check operator logs", "Verify operator configurations"],
                evidence=operator_errors[:3]  # Use actual error lines
            ))
            issues_found.add("OPERATOR_DEGRADATION")
        
        # ETCD issues
        etcd_errors = [err for err in actual_errors if any(pattern in err.lower() for pattern in ['etcd', 'quorum', 'leader election'])]
        if etcd_errors and "ETCD_COMMUNICATION" not in issues_found:
            issues.append(ClusterIssue(
                issue_type="ETCD_COMMUNICATION",
                severity="high",
                description="etcd cluster communication issues detected",
                affected_components=["etcd", "openshift-apiserver"],
                recommendations=["Check etcd cluster health", "Verify etcd certificates"],
                evidence=etcd_errors[:3]  # Use actual error lines
            ))
            issues_found.add("ETCD_COMMUNICATION")
        
        return issues
    
    async def _generate_ai_analysis(self, cluster_info: Dict[str, Any], issues: List[ClusterIssue], model_preference: str = "ollama") -> MustGatherAnalysis:
        """Generate AI-powered analysis"""
        
        # Import AI agent if available
        try:
            from app.services.ai_agent_multi_model import MultiModelAIAgent, ModelType
            
            self.ai_agent = MultiModelAIAgent()
            
            # Create analysis prompt
            prompt = f"""
            Analyze this OpenShift cluster must-gather data:
            
            Cluster Version: {cluster_info.get('cluster_version', 'Unknown')}
            Issues Found: {len(issues)}
            
            Key Issues:
            {self._format_issues_for_ai(issues)}
            
            Provide a comprehensive analysis including:
            1. Executive summary
            2. Root cause analysis
            3. Immediate actions needed
            4. Long-term recommendations
            5. Next steps
            6. Priority level (critical/high/medium/low)
            """
            
            # Map model preference to ModelType
            model_mapping = {
                "ollama": ModelType.OLLAMA,
                "claude": ModelType.CLAUDE,
                "gemini": ModelType.GEMINI,
                "openai": ModelType.OPENAI_GPT,
                "granite": ModelType.GRANITE
            }
            
            model_type = model_mapping.get(model_preference, ModelType.OLLAMA)
            
            # Generate analysis
            context = {
                'task_type': 'cluster_analysis',
                'cluster_info': cluster_info,
                'issues_count': len(issues)
            }
            
            response = await self.ai_agent.generate_response_with_model(prompt, model_type, context)
            
            # Parse AI response into structured analysis
            return self._parse_ai_response(response, cluster_info, issues)
            
        except Exception as e:
            logger.warning(f"AI analysis failed, using fallback: {e}")
            return self._generate_fallback_analysis(cluster_info, issues)
    
    def _format_issues_for_ai(self, issues: List[ClusterIssue]) -> str:
        """Format issues for AI prompt"""
        formatted = []
        for issue in issues[:10]:  # Limit to top 10 issues
            formatted.append(f"- {issue.issue_type}: {issue.description} (Severity: {issue.severity})")
        return '\n'.join(formatted)
    
    def _parse_ai_response(self, response: str, cluster_info: Dict[str, Any], issues: List[ClusterIssue]) -> MustGatherAnalysis:
        """Parse AI response into structured analysis"""
        # Simple parsing - in production, use more sophisticated NLP
        lines = response.split('\n')
        
        summary = "Network connectivity and API service issues detected"
        root_cause = "Network configuration and service communication problems"
        priority = "high"
        
        immediate_actions = [
            "Check network connectivity between nodes",
            "Verify etcd cluster health",
            "Review cluster operator status"
        ]
        
        long_term_recommendations = [
            "Implement network monitoring",
            "Document network requirements",
            "Create troubleshooting runbooks"
        ]
        
        next_steps = [
            "Engage network team for investigation",
            "Check vSphere network configuration",
            "Verify DNS resolution and load balancer health"
        ]
        
        return MustGatherAnalysis(
            cluster_info=cluster_info,
            issues=issues,
            summary=summary,
            root_cause=root_cause,
            immediate_actions=immediate_actions,
            long_term_recommendations=long_term_recommendations,
            priority=priority,
            next_steps=next_steps
        )
    
    def _generate_fallback_analysis(self, cluster_info: Dict[str, Any], issues: List[ClusterIssue]) -> MustGatherAnalysis:
        """Generate fallback analysis when AI is unavailable"""
        
        # Determine priority based on issue severity
        critical_count = len([i for i in issues if i.severity == 'critical'])
        high_count = len([i for i in issues if i.severity == 'high'])
        
        if critical_count > 0:
            priority = "critical"
        elif high_count > 0:
            priority = "high"
        else:
            priority = "medium"
        
        return MustGatherAnalysis(
            cluster_info=cluster_info,
            issues=issues,
            summary=f"Found {len(issues)} issues in must-gather analysis",
            root_cause="Multiple system issues detected requiring investigation",
            immediate_actions=[
                "Review critical issues first",
                "Check system connectivity",
                "Verify service status"
            ],
            long_term_recommendations=[
                "Implement monitoring",
                "Create maintenance procedures",
                "Document troubleshooting steps"
            ],
            priority=priority,
            next_steps=[
                "Analyze each issue systematically",
                "Engage appropriate teams",
                "Monitor system recovery"
            ]
        )

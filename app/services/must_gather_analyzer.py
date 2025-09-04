import os
import json
import logging
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml
import tempfile
import shutil
from datetime import datetime

logger = logging.getLogger(__name__)

class MustGatherAnalyzer:
    def __init__(self):
        self.supported_analyses = [
            "cluster_health",
            "etcd_analysis", 
            "node_analysis",
            "pod_issues",
            "operator_status",
            "network_issues",
            "storage_issues",
            "kms_encryption",
            "certificate_issues",
            "performance_analysis"
        ]
        
    async def analyze_must_gather(self, must_gather_path: str, analysis_type: str = "full") -> Dict[str, Any]:
        """Analyze must-gather data and return structured results"""
        try:
            if not os.path.exists(must_gather_path):
                return {"error": f"Must-gather path not found: {must_gather_path}"}
            
            results = {
                "timestamp": datetime.now().isoformat(),
                "must_gather_path": must_gather_path,
                "analysis_type": analysis_type,
                "findings": {},
                "recommendations": [],
                "critical_issues": [],
                "warnings": []
            }
            
            # Perform different types of analysis
            if analysis_type == "full" or analysis_type == "cluster_health":
                results["findings"]["cluster_health"] = await self._analyze_cluster_health(must_gather_path)
            
            if analysis_type == "full" or analysis_type == "etcd_analysis":
                results["findings"]["etcd"] = await self._analyze_etcd(must_gather_path)
            
            if analysis_type == "full" or analysis_type == "node_analysis":
                results["findings"]["nodes"] = await self._analyze_nodes(must_gather_path)
            
            if analysis_type == "full" or analysis_type == "pod_issues":
                results["findings"]["pods"] = await self._analyze_pods(must_gather_path)
            
            if analysis_type == "full" or analysis_type == "operator_status":
                results["findings"]["operators"] = await self._analyze_cluster_operators(must_gather_path)
            
            if analysis_type == "full" or analysis_type == "kms_encryption":
                results["findings"]["kms"] = await self._analyze_kms_encryption(must_gather_path)
            
            # Generate summary and recommendations
            results["summary"] = self._generate_summary(results["findings"])
            results["ai_recommendations"] = await self._generate_ai_recommendations(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing must-gather: {e}")
            return {"error": str(e)}
    
    async def _analyze_cluster_health(self, must_gather_path: str) -> Dict[str, Any]:
        """Analyze overall cluster health"""
        health_data = {
            "cluster_version": None,
            "cluster_operators": [],
            "infrastructure": {},
            "overall_status": "unknown"
        }
        
        try:
            # Analyze cluster version
            cv_path = Path(must_gather_path) / "cluster-scoped-resources" / "config.openshift.io" / "clusterversions"
            if cv_path.exists():
                for cv_file in cv_path.glob("*.yaml"):
                    with open(cv_file, 'r') as f:
                        cv_data = yaml.safe_load(f)
                        if cv_data and cv_data.get('kind') == 'ClusterVersion':
                            health_data["cluster_version"] = {
                                "version": cv_data.get('status', {}).get('desired', {}).get('version'),
                                "conditions": cv_data.get('status', {}).get('conditions', [])
                            }
            
            # Analyze infrastructure
            infra_path = Path(must_gather_path) / "cluster-scoped-resources" / "config.openshift.io" / "infrastructures"
            if infra_path.exists():
                for infra_file in infra_path.glob("*.yaml"):
                    with open(infra_file, 'r') as f:
                        infra_data = yaml.safe_load(f)
                        if infra_data and infra_data.get('kind') == 'Infrastructure':
                            health_data["infrastructure"] = {
                                "platform": infra_data.get('status', {}).get('platform'),
                                "platform_status": infra_data.get('status', {}).get('platformStatus', {})
                            }
            
            return health_data
            
        except Exception as e:
            logger.error(f"Error analyzing cluster health: {e}")
            return {"error": str(e)}
    
    async def _analyze_etcd(self, must_gather_path: str) -> Dict[str, Any]:
        """Analyze etcd cluster health"""
        etcd_data = {
            "endpoint_health": [],
            "endpoint_status": [],
            "member_list": [],
            "issues": []
        }
        
        try:
            etcd_info_path = Path(must_gather_path) / "etcd_info"
            
            # Check endpoint health
            health_file = etcd_info_path / "endpoint_health.json"
            if health_file.exists():
                with open(health_file, 'r') as f:
                    etcd_data["endpoint_health"] = json.load(f)
            
            # Check endpoint status
            status_file = etcd_info_path / "endpoint_status.json"
            if status_file.exists():
                with open(status_file, 'r') as f:
                    etcd_data["endpoint_status"] = json.load(f)
            
            # Check member list
            members_file = etcd_info_path / "member_list.json"
            if members_file.exists():
                with open(members_file, 'r') as f:
                    etcd_data["member_list"] = json.load(f)
            
            # Analyze for issues
            for endpoint in etcd_data["endpoint_health"]:
                if not endpoint.get("health", False):
                    etcd_data["issues"].append(f"Endpoint {endpoint.get('endpoint')} is unhealthy")
            
            return etcd_data
            
        except Exception as e:
            logger.error(f"Error analyzing etcd: {e}")
            return {"error": str(e)}
    
    async def _analyze_nodes(self, must_gather_path: str) -> Dict[str, Any]:
        """Analyze node status and health"""
        nodes_data = {
            "total_nodes": 0,
            "ready_nodes": 0,
            "not_ready_nodes": 0,
            "node_details": [],
            "issues": []
        }
        
        try:
            nodes_path = Path(must_gather_path) / "cluster-scoped-resources" / "core" / "nodes"
            
            if nodes_path.exists():
                for node_file in nodes_path.glob("*.yaml"):
                    with open(node_file, 'r') as f:
                        node_data = yaml.safe_load(f)
                        if node_data and node_data.get('kind') == 'Node':
                            nodes_data["total_nodes"] += 1
                            
                            conditions = node_data.get('status', {}).get('conditions', [])
                            ready_condition = next((c for c in conditions if c.get('type') == 'Ready'), None)
                            
                            node_info = {
                                "name": node_data.get('metadata', {}).get('name'),
                                "ready": ready_condition.get('status') == 'True' if ready_condition else False,
                                "conditions": conditions,
                                "capacity": node_data.get('status', {}).get('capacity', {}),
                                "allocatable": node_data.get('status', {}).get('allocatable', {})
                            }
                            
                            nodes_data["node_details"].append(node_info)
                            
                            if node_info["ready"]:
                                nodes_data["ready_nodes"] += 1
                            else:
                                nodes_data["not_ready_nodes"] += 1
                                nodes_data["issues"].append(f"Node {node_info['name']} is not ready")
            
            return nodes_data
            
        except Exception as e:
            logger.error(f"Error analyzing nodes: {e}")
            return {"error": str(e)}
    
    async def _analyze_pods(self, must_gather_path: str) -> Dict[str, Any]:
        """Analyze pod status across all namespaces"""
        pods_data = {
            "total_pods": 0,
            "running_pods": 0,
            "failed_pods": 0,
            "pending_pods": 0,
            "problematic_pods": [],
            "namespace_summary": {}
        }
        
        try:
            namespaces_path = Path(must_gather_path) / "namespaces"
            
            if namespaces_path.exists():
                for ns_dir in namespaces_path.iterdir():
                    if ns_dir.is_dir():
                        namespace = ns_dir.name
                        pods_path = ns_dir / "core" / "pods"
                        
                        if pods_path.exists():
                            ns_pods = {"total": 0, "running": 0, "failed": 0, "pending": 0}
                            
                            for pod_file in pods_path.glob("*.yaml"):
                                with open(pod_file, 'r') as f:
                                    pod_data = yaml.safe_load(f)
                                    if pod_data and pod_data.get('kind') == 'Pod':
                                        pods_data["total_pods"] += 1
                                        ns_pods["total"] += 1
                                        
                                        phase = pod_data.get('status', {}).get('phase', 'Unknown')
                                        
                                        if phase == 'Running':
                                            pods_data["running_pods"] += 1
                                            ns_pods["running"] += 1
                                        elif phase == 'Failed':
                                            pods_data["failed_pods"] += 1
                                            ns_pods["failed"] += 1
                                            pods_data["problematic_pods"].append({
                                                "name": pod_data.get('metadata', {}).get('name'),
                                                "namespace": namespace,
                                                "phase": phase,
                                                "reason": pod_data.get('status', {}).get('reason', 'Unknown')
                                            })
                                        elif phase == 'Pending':
                                            pods_data["pending_pods"] += 1
                                            ns_pods["pending"] += 1
                                            pods_data["problematic_pods"].append({
                                                "name": pod_data.get('metadata', {}).get('name'),
                                                "namespace": namespace,
                                                "phase": phase,
                                                "reason": pod_data.get('status', {}).get('reason', 'Unknown')
                                            })
                            
                            pods_data["namespace_summary"][namespace] = ns_pods
            
            return pods_data
            
        except Exception as e:
            logger.error(f"Error analyzing pods: {e}")
            return {"error": str(e)}
    
    async def _analyze_cluster_operators(self, must_gather_path: str) -> Dict[str, Any]:
        """Analyze cluster operator status"""
        operators_data = {
            "total_operators": 0,
            "available_operators": 0,
            "degraded_operators": 0,
            "progressing_operators": 0,
            "operator_details": [],
            "critical_issues": []
        }
        
        try:
            co_path = Path(must_gather_path) / "cluster-scoped-resources" / "config.openshift.io" / "clusteroperators"
            
            if co_path.exists():
                for co_file in co_path.glob("*.yaml"):
                    with open(co_file, 'r') as f:
                        co_data = yaml.safe_load(f)
                        if co_data and co_data.get('kind') == 'ClusterOperator':
                            operators_data["total_operators"] += 1
                            
                            conditions = co_data.get('status', {}).get('conditions', [])
                            available = next((c for c in conditions if c.get('type') == 'Available'), None)
                            degraded = next((c for c in conditions if c.get('type') == 'Degraded'), None)
                            progressing = next((c for c in conditions if c.get('type') == 'Progressing'), None)
                            
                            operator_info = {
                                "name": co_data.get('metadata', {}).get('name'),
                                "available": available.get('status') == 'True' if available else False,
                                "degraded": degraded.get('status') == 'True' if degraded else False,
                                "progressing": progressing.get('status') == 'True' if progressing else False,
                                "conditions": conditions
                            }
                            
                            operators_data["operator_details"].append(operator_info)
                            
                            if operator_info["available"]:
                                operators_data["available_operators"] += 1
                            if operator_info["degraded"]:
                                operators_data["degraded_operators"] += 1
                                operators_data["critical_issues"].append(f"Operator {operator_info['name']} is degraded")
                            if operator_info["progressing"]:
                                operators_data["progressing_operators"] += 1
            
            return operators_data
            
        except Exception as e:
            logger.error(f"Error analyzing cluster operators: {e}")
            return {"error": str(e)}
    
    async def _analyze_kms_encryption(self, must_gather_path: str) -> Dict[str, Any]:
        """Analyze KMS encryption configuration and issues"""
        kms_data = {
            "encryption_config": None,
            "kms_plugins": [],
            "encryption_status": "unknown",
            "issues": [],
            "recommendations": []
        }
        
        try:
            # Check for encryption configuration
            secrets_path = Path(must_gather_path) / "cluster-scoped-resources" / "core" / "secrets"
            
            if secrets_path.exists():
                for secret_file in secrets_path.glob("*encryption-config*.yaml"):
                    with open(secret_file, 'r') as f:
                        secret_data = yaml.safe_load(f)
                        if secret_data and 'encryption-config' in secret_data.get('metadata', {}).get('name', ''):
                            kms_data["encryption_config"] = secret_data
            
            # Check for KMS plugin pods
            kms_ns_path = Path(must_gather_path) / "namespaces" / "openshift-kube-apiserver" / "core" / "pods"
            if kms_ns_path.exists():
                for pod_file in kms_ns_path.glob("*kms*.yaml"):
                    with open(pod_file, 'r') as f:
                        pod_data = yaml.safe_load(f)
                        if pod_data and 'kms' in pod_data.get('metadata', {}).get('name', ''):
                            kms_data["kms_plugins"].append({
                                "name": pod_data.get('metadata', {}).get('name'),
                                "phase": pod_data.get('status', {}).get('phase'),
                                "conditions": pod_data.get('status', {}).get('conditions', [])
                            })
            
            # Analyze KMS issues
            if not kms_data["encryption_config"]:
                kms_data["issues"].append("No encryption configuration found")
                kms_data["recommendations"].append("Enable KMS encryption if required")
            
            for plugin in kms_data["kms_plugins"]:
                if plugin["phase"] != "Running":
                    kms_data["issues"].append(f"KMS plugin {plugin['name']} is not running")
            
            return kms_data
            
        except Exception as e:
            logger.error(f"Error analyzing KMS encryption: {e}")
            return {"error": str(e)}
    
    def _generate_summary(self, findings: Dict[str, Any]) -> str:
        """Generate a human-readable summary of findings"""
        summary_parts = []
        
        # Cluster health summary
        if "cluster_health" in findings:
            ch = findings["cluster_health"]
            if ch.get("cluster_version"):
                summary_parts.append(f"Cluster version: {ch['cluster_version'].get('version', 'Unknown')}")
        
        # Node summary
        if "nodes" in findings:
            nodes = findings["nodes"]
            summary_parts.append(f"Nodes: {nodes['ready_nodes']}/{nodes['total_nodes']} ready")
        
        # Pod summary
        if "pods" in findings:
            pods = findings["pods"]
            summary_parts.append(f"Pods: {pods['running_pods']} running, {pods['failed_pods']} failed, {pods['pending_pods']} pending")
        
        # Operator summary
        if "operators" in findings:
            ops = findings["operators"]
            summary_parts.append(f"Operators: {ops['degraded_operators']} degraded out of {ops['total_operators']}")
        
        return " | ".join(summary_parts) if summary_parts else "Analysis completed"
    
    async def _generate_ai_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate AI-powered recommendations based on analysis"""
        recommendations = []
        
        findings = analysis_results.get("findings", {})
        
        # Node recommendations
        if "nodes" in findings and findings["nodes"]["not_ready_nodes"] > 0:
            recommendations.append("Investigate not-ready nodes: Check node conditions and resource availability")
        
        # Pod recommendations
        if "pods" in findings:
            failed_pods = findings["pods"]["failed_pods"]
            pending_pods = findings["pods"]["pending_pods"]
            
            if failed_pods > 0:
                recommendations.append(f"Investigate {failed_pods} failed pods: Check logs and events")
            if pending_pods > 0:
                recommendations.append(f"Investigate {pending_pods} pending pods: Check resource constraints and scheduling")
        
        # Operator recommendations
        if "operators" in findings and findings["operators"]["degraded_operators"] > 0:
            recommendations.append("Address degraded cluster operators: Check operator logs and conditions")
        
        # etcd recommendations
        if "etcd" in findings and findings["etcd"].get("issues"):
            recommendations.append("Address etcd issues: Check etcd member health and connectivity")
        
        # KMS recommendations
        if "kms" in findings and findings["kms"].get("issues"):
            recommendations.extend(findings["kms"].get("recommendations", []))
        
        return recommendations

    async def quick_health_check(self, must_gather_path: str) -> Dict[str, Any]:
        """Perform a quick health check of the cluster"""
        try:
            results = await self.analyze_must_gather(must_gather_path, "cluster_health")
            
            # Simple health scoring
            health_score = 100
            issues = []
            
            if "findings" in results:
                findings = results["findings"]
                
                if "nodes" in findings:
                    nodes = findings["nodes"]
                    if nodes["not_ready_nodes"] > 0:
                        health_score -= (nodes["not_ready_nodes"] * 20)
                        issues.append(f"{nodes['not_ready_nodes']} nodes not ready")
                
                if "operators" in findings:
                    ops = findings["operators"]
                    if ops["degraded_operators"] > 0:
                        health_score -= (ops["degraded_operators"] * 15)
                        issues.append(f"{ops['degraded_operators']} cluster operators degraded")
                
                if "pods" in findings:
                    pods = findings["pods"]
                    failed_ratio = pods["failed_pods"] / max(pods["total_pods"], 1)
                    if failed_ratio > 0.05:  # More than 5% failed
                        health_score -= 30
                        issues.append(f"High pod failure rate: {pods['failed_pods']}/{pods['total_pods']}")
            
            health_score = max(0, health_score)
            
            if health_score >= 90:
                status = "Healthy"
            elif health_score >= 70:
                status = "Warning"
            elif health_score >= 50:
                status = "Degraded"
            else:
                status = "Critical"
            
            return {
                "health_score": health_score,
                "status": status,
                "issues": issues,
                "summary": results.get("summary", ""),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in quick health check: {e}")
            return {"error": str(e)}

# Global analyzer instance
must_gather_analyzer = MustGatherAnalyzer() 
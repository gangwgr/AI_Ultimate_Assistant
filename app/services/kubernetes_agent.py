import re
import logging
from typing import Dict, List, Any
from .base_agent import BaseAgent
from app.services.ai_agent_multi_model import MultiModelAIAgent

logger = logging.getLogger(__name__)

class KubernetesAgent(BaseAgent):
    """Specialized agent for Kubernetes/OpenShift commands"""
    
    def __init__(self):
        super().__init__("KubernetesAgent", "kubernetes")
        self.ai_agent = MultiModelAIAgent()
        
    def get_capabilities(self) -> List[str]:
        return [
            "list_pods", "list_namespaces", "list_services", "list_deployments",
            "describe_pod", "get_logs", "exec_pod", "port_forward", "kubernetes_help",
            "apply_yaml", "delete_resource", "scale_deployment", "get_events"
        ]
    
    def get_domain_keywords(self) -> List[str]:
        return [
            "pod", "pods", "namespace", "ns", "service", "svc", "deployment", "deploy",
            "node", "nodes", "kubectl", "oc", "kubernetes", "k8s", "openshift", 
            "project", "projects", "get", "describe", "logs", "exec", "port-forward",
            "apply", "delete", "create", "scale"
        ]
    
    async def analyze_intent(self, message: str) -> Dict[str, Any]:
        """Analyze Kubernetes/OpenShift intent"""
        message_lower = message.lower()
        
        # Check for specific Kubernetes patterns first
        kubernetes_patterns = {
            "list_pods": [
                "list pods", "get pods", "show pods", "kubectl get pods", "oc get pods",
                "how to list pod", "how to get pod", "pod list", "pods list"
            ],
            "list_namespaces": [
                "list namespace", "get namespace", "show namespace", "kubectl get namespace", 
                "oc get namespace", "list namespaces", "get namespaces", "show namespaces",
                "kubectl get namespaces", "oc get namespaces", "how to list namespace",
                "how to get namespace", "namespace list", "namespaces list", "oc get projects",
                "kubectl get projects", "list projects", "get projects", "how to list pod in ns"
            ],
            "list_services": [
                "list service", "get service", "show service", "kubectl get service", 
                "oc get service", "list services", "get services", "show services",
                "kubectl get services", "oc get services", "how to list service",
                "how to get service", "service list", "services list"
            ],
            "list_deployments": [
                "list deployment", "get deployment", "show deployment", "kubectl get deployment",
                "oc get deployment", "list deployments", "get deployments", "show deployments",
                "kubectl get deployments", "oc get deployments", "how to list deployment",
                "how to get deployment", "deployment list", "deployments list"
            ],
            "describe_pod": [
                "describe pod", "kubectl describe pod", "oc describe pod", "pod details",
                "pod info", "get pod details", "get pod info"
            ],
            "get_logs": [
                "get logs", "kubectl logs", "oc logs", "pod logs", "container logs",
                "how to get logs", "how to see logs", "view logs"
            ],
            "exec_pod": [
                "exec pod", "kubectl exec", "oc exec", "execute pod", "shell pod",
                "how to exec pod", "how to shell pod", "connect to pod"
            ],
            "port_forward": [
                "port forward", "kubectl port-forward", "oc port-forward", "forward port",
                "how to port forward", "how to forward port"
            ],
            "deploy_pods": [
                "deploy pod", "deploy pods", "create pod", "create pods", "how to deploy pod", 
                "how to deploy pods", "how to create pod", "how to create pods", "deploy in ocp",
                "deploy in openshift", "deploy in kubernetes", "create deployment", "apply yaml",
                "kubectl apply", "oc apply", "kubectl create", "oc create", "deploy application",
                "oc new-app", "kubectl run", "oc run"
            ],
            "kubernetes_help": [
                "kubectl", "oc", "kubernetes help", "openshift help", "k8s help",
                "kubernetes command", "openshift command", "k8s command"
            ]
        }
        
        # Sort patterns by length (longest first) to ensure more specific matches
        for intent, patterns in kubernetes_patterns.items():
            sorted_patterns = sorted(patterns, key=len, reverse=True)
            for pattern in sorted_patterns:
                if pattern in message_lower:
                    logger.info(f"DEBUG: Matched Kubernetes pattern '{pattern}' for intent '{intent}' in message: '{message}'")
                    return {
                        "intent": intent,
                        "confidence": 0.9,
                        "entities": self._extract_kubernetes_entities(message)
                    }
        
        # Check for partial matches (more flexible) - but only if it's clearly a Kubernetes command
        kubernetes_keywords = ["pod", "pods", "namespace", "ns", "service", "svc", "deployment", "deploy", "node", "nodes", "kubectl", "oc", "kubernetes", "k8s", "openshift", "project", "projects"]
        if any(keyword in message_lower for keyword in kubernetes_keywords):
            # Only match if it's clearly a Kubernetes command (not just containing the word)
            if any(cmd_word in message_lower for cmd_word in ["get", "describe", "logs", "exec", "port-forward", "apply", "delete", "create"]):
                # Check for question patterns
                if any(word in message_lower for word in ["how", "what", "which", "where", "when", "why"]):
                    logger.info(f"DEBUG: Matched Kubernetes question pattern in message: '{message}'")
                    return {
                        "intent": "kubernetes_help",
                        "confidence": 0.7,
                        "entities": self._extract_kubernetes_entities(message)
                    }
        
        # Default to help if no specific intent detected
        return {"intent": "kubernetes_help", "confidence": 0.5, "entities": self._extract_kubernetes_entities(message)}
    
    async def handle_intent(self, intent: str, message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Kubernetes/OpenShift intents"""
        if intent == "list_pods":
            return await self._handle_list_pods(message, entities)
        elif intent == "list_namespaces":
            return await self._handle_list_namespaces(message, entities)
        elif intent == "list_services":
            return await self._handle_list_services(message, entities)
        elif intent == "list_deployments":
            return await self._handle_list_deployments(message, entities)
        elif intent == "describe_pod":
            return await self._handle_describe_pod(message, entities)
        elif intent == "get_logs":
            return await self._handle_get_logs(message, entities)
        elif intent == "exec_pod":
            return await self._handle_exec_pod(message, entities)
        elif intent == "port_forward":
            return await self._handle_port_forward(message, entities)
        elif intent == "deploy_pods":
            return await self._handle_deploy_pods(message, entities)
        elif intent == "kubernetes_help":
            return await self._handle_kubernetes_help(message, entities)
        else:
            return {
                "response": "I can help you with Kubernetes and OpenShift commands. What would you like to do?",
                "action_taken": "kubernetes_help",
                "suggestions": ["List pods", "List namespaces", "Get pod logs", "Describe pod"]
            }
    
    def _extract_kubernetes_entities(self, message: str) -> Dict[str, Any]:
        """Extract Kubernetes/OpenShift entities"""
        entities = {}
        message_lower = message.lower()
        
        # Extract namespace
        namespace_patterns = [
            r'-n\s+([^\s]+)',  # -n namespace
            r'--namespace\s+([^\s]+)',  # --namespace namespace
            r'in\s+namespace\s+([^\s]+)',  # in namespace namespace
            r'namespace\s+([^\s]+)'  # namespace namespace
        ]
        
        for pattern in namespace_patterns:
            match = re.search(pattern, message_lower)
            if match:
                entities["namespace"] = match.group(1)
                break
        
        # Extract resource type
        resource_patterns = [
            r'get\s+([^\s]+)',  # get pods
            r'list\s+([^\s]+)',  # list pods
            r'describe\s+([^\s]+)',  # describe pod
            r'logs\s+([^\s]+)'  # logs pod
        ]
        
        for pattern in resource_patterns:
            match = re.search(pattern, message_lower)
            if match:
                resource = match.group(1)
                if resource in ["pod", "pods", "service", "services", "deployment", "deployments", "namespace", "namespaces"]:
                    entities["resource_type"] = resource
                    break
        
        # Extract command type
        command_patterns = [
            r'(get|list|describe|logs|exec|port-forward|apply|delete|create)',
            r'kubectl\s+([^\s]+)',  # kubectl get
            r'oc\s+([^\s]+)'  # oc get
        ]
        
        for pattern in command_patterns:
            match = re.search(pattern, message_lower)
            if match:
                entities["command_type"] = match.group(1)
                break
        
        # Extract resource name (more sophisticated)
        name_patterns = [
            r'(?:pod|service|deployment)\s+([a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?)',  # pod my-pod
            r'([a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?)\s+(?:pod|service|deployment)',  # my-pod pod
            r'-it\s+([a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?)',  # -it my-pod
            r'logs\s+([a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?)',  # logs my-pod
            r'describe\s+([a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?)'  # describe my-pod
        ]
        
        # Skip list to prevent common command words from being extracted as names
        skip_words = {'get', 'list', 'describe', 'logs', 'exec', 'port-forward', 'apply', 'delete', 'create', 'pod', 'pods', 'service', 'services', 'deployment', 'deployments', 'namespace', 'namespaces', 'my', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        for pattern in name_patterns:
            match = re.search(pattern, message_lower)
            if match:
                potential_name = match.group(1)
                if potential_name not in skip_words and len(potential_name) > 1:
                    entities["resource_name"] = potential_name
                    break
        
        return entities
    
    async def _handle_list_pods(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle listing pods using AI model"""
        namespace = entities.get("namespace", "<namespace>")
        resource_name = entities.get("resource_name")
        
        # Create a prompt for the AI model
        prompt = f"""You are a Kubernetes/OpenShift expert. The user asked: "{message}"

Context:
- Namespace: {namespace}
- Resource name: {resource_name if resource_name else 'Not specified'}

Please provide a comprehensive, helpful response that includes:
1. The exact kubectl/oc commands they need
2. OpenShift-specific commands if relevant
3. Additional useful options and flags
4. Practical tips and best practices
5. Examples for their specific case

Make the response detailed, accurate, and immediately actionable. Use markdown formatting with code blocks for commands."""
        
        try:
            # Generate response using AI model
            ai_result = await self.ai_agent.process_message_smart(prompt)
            ai_response = ai_result.get("response", "I couldn't generate a response at this time.")
            
            return {
                "response": ai_response,
                "action_taken": "list_pods",
                "suggestions": ["List services", "List deployments", "Describe pod", "Get pod logs"]
            }
        except Exception as e:
            logger.error(f"Error generating AI response for list_pods: {e}")
            # Fallback to template response
            return {
                "response": f"**📋 List Pods Commands**\n\n```bash\n# List all pods in current namespace\nkubectl get pods\noc get pods\n\n# List pods in specific namespace\nkubectl get pods -n {namespace}\noc get pods -n {namespace}\n\n# List pods with more details\nkubectl get pods -o wide -n {namespace}\noc get pods -o wide -n {namespace}\n\n# List pods with labels\nkubectl get pods --show-labels -n {namespace}\noc get pods --show-labels -n {namespace}\n\n# Watch pods in real-time\nkubectl get pods -w -n {namespace}\noc get pods -w -n {namespace}\n```\n\n**💡 Tips:**\n- Use `-n` to specify namespace\n- Use `-o wide` for more details\n- Use `-w` to watch for changes\n- Use `--show-labels` to see pod labels",
                "action_taken": "list_pods",
                "suggestions": ["List services", "List deployments", "Describe pod", "Get pod logs"]
            }
    
    async def _handle_list_namespaces(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle listing namespaces"""
        return {
            "response": "**📋 List Namespaces/Projects Commands**\n\n```bash\n# List all namespaces (Kubernetes)\nkubectl get namespaces\nkubectl get ns\n\n# List all projects (OpenShift)\noc get projects\n\n# List namespaces with more details\nkubectl get namespaces -o wide\n\n# List namespaces with labels\nkubectl get namespaces --show-labels\n\n# List pods in specific namespace\nkubectl get pods -n <namespace>\noc get pods -n <namespace>\n```\n\n**💡 Tips:**\n- Use `kubectl get namespaces` for Kubernetes\n- Use `oc get projects` for OpenShift\n- Use `-n <namespace>` to work with resources in a specific namespace\n- Use `-o wide` for more details",
            "action_taken": "list_namespaces",
            "suggestions": ["List pods", "List services", "List deployments", "Kubernetes help"]
        }
    
    async def _handle_list_services(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle listing services"""
        namespace = entities.get("namespace", "<namespace>")
        return {
            "response": f"**📋 List Services Commands**\n\n```bash\n# List all services in current namespace\nkubectl get services\nkubectl get svc\noc get services\noc get svc\n\n# List services in specific namespace\nkubectl get services -n {namespace}\nkubectl get svc -n {namespace}\noc get services -n {namespace}\noc get svc -n {namespace}\n\n# List services with more details\nkubectl get services -o wide -n {namespace}\noc get services -o wide -n {namespace}\n\n# List services with endpoints\nkubectl get services,endpoints -n {namespace}\noc get services,endpoints -n {namespace}\n```\n\n**💡 Tips:**\n- Use `svc` as shorthand for services\n- Use `-o wide` for more details\n- Use `endpoints` to see service endpoints\n- Use `-n` to specify namespace",
            "action_taken": "list_services",
            "suggestions": ["List pods", "List deployments", "Describe service", "Port forward"]
        }
    
    async def _handle_list_deployments(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle listing deployments"""
        namespace = entities.get("namespace", "<namespace>")
        return {
            "response": f"**📋 List Deployments Commands**\n\n```bash\n# List all deployments in current namespace\nkubectl get deployments\nkubectl get deploy\noc get deployments\noc get deploy\n\n# List deployments in specific namespace\nkubectl get deployments -n {namespace}\nkubectl get deploy -n {namespace}\noc get deployments -n {namespace}\noc get deploy -n {namespace}\n\n# List deployments with more details\nkubectl get deployments -o wide -n {namespace}\noc get deployments -o wide -n {namespace}\n\n# List deployments with labels\nkubectl get deployments --show-labels -n {namespace}\noc get deployments --show-labels -n {namespace}\n\n# Scale deployment\nkubectl scale deployment <deployment-name> --replicas=3 -n {namespace}\noc scale deployment <deployment-name> --replicas=3 -n {namespace}\n```\n\n**💡 Tips:**\n- Use `deploy` as shorthand for deployments\n- Use `-o wide` for more details\n- Use `--show-labels` to see deployment labels\n- Use `scale` to change replica count",
            "action_taken": "list_deployments",
            "suggestions": ["List pods", "List services", "Describe deployment", "Scale deployment"]
        }
    
    async def _handle_kubernetes_help(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle Kubernetes help"""
        return {
            "response": "**🔧 Kubernetes/OpenShift Command Reference**\n\n**📋 Basic Commands:**\n```bash\n# List resources\nkubectl get pods -n <namespace>\nkubectl get services -n <namespace>\nkubectl get deployments -n <namespace>\nkubectl get namespaces\n\n# Describe resources\nkubectl describe pod <pod-name> -n <namespace>\nkubectl describe service <service-name> -n <namespace>\n\n# Get logs\nkubectl logs <pod-name> -n <namespace>\nkubectl logs -f <pod-name> -n <namespace>  # Follow logs\n\n# Exec into pod\nkubectl exec -it <pod-name> -n <namespace> -- /bin/bash\n```\n\n**🔄 OpenShift Equivalents:**\n```bash\n# Replace kubectl with oc\noc get pods -n <namespace>\noc describe pod <pod-name> -n <namespace>\noc logs <pod-name> -n <namespace>\noc exec -it <pod-name> -n <namespace> -- /bin/bash\n```\n\n**🔍 Useful Options:**\n```bash\n# Show more details\nkubectl get pods -o wide -n <namespace>\n\n# Watch resources\nkubectl get pods -w -n <namespace>\n\n# Show labels\nkubectl get pods --show-labels -n <namespace>\n\n# Filter by label\nkubectl get pods -l app=myapp -n <namespace>\n```\n\n**📚 Common Patterns:**\n- `kubectl get <resource> -n <namespace>` - List resources\n- `kubectl describe <resource> <name> -n <namespace>` - Get details\n- `kubectl logs <pod-name> -n <namespace>` - View logs\n- `kubectl exec -it <pod-name> -n <namespace> -- <command>` - Execute command\n\n**💡 Tips:**\n- Use `-n` for namespace (or `--namespace`)\n- Use `-o wide` for more details\n- Use `-w` to watch for changes\n- Use `-f` to follow logs in real-time",
            "action_taken": "kubernetes_help",
            "suggestions": ["List pods", "List services", "List deployments", "Get pod logs"]
        }
    
    async def _handle_describe_pod(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle describing pods"""
        pod_name = entities.get("resource_name", "<pod-name>")
        namespace = entities.get("namespace", "<namespace>")
        return {
            "response": f"**📋 Describe Pod Commands**\n\n```bash\n# Describe pod in current namespace\nkubectl describe pod {pod_name}\noc describe pod {pod_name}\n\n# Describe pod in specific namespace\nkubectl describe pod {pod_name} -n {namespace}\noc describe pod {pod_name} -n {namespace}\n\n# Describe pod with events\nkubectl describe pod {pod_name} -n {namespace} --show-events=true\noc describe pod {pod_name} -n {namespace} --show-events=true\n\n# Get pod YAML\nkubectl get pod {pod_name} -n {namespace} -o yaml\noc get pod {pod_name} -n {namespace} -o yaml\n```\n\n**💡 Tips:**\n- Use `describe` to get detailed information about a pod\n- Use `--show-events=true` to see pod events\n- Use `-o yaml` to get the pod definition\n- Use `-n` to specify namespace",
            "action_taken": "describe_pod",
            "suggestions": ["Get pod logs", "Exec into pod", "List pods", "Port forward"]
        }
    
    async def _handle_get_logs(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle getting logs using AI model"""
        pod_name = entities.get("resource_name", "<pod-name>")
        namespace = entities.get("namespace", "<namespace>")
        
        # Create a prompt for the AI model
        prompt = f"""You are a Kubernetes/OpenShift expert. The user asked: "{message}"

Context:
- Pod name: {pod_name}
- Namespace: {namespace}

Please provide a comprehensive, helpful response that includes:
1. The exact kubectl/oc commands they need to check pod logs
2. OpenShift-specific commands if relevant
3. Additional useful options and flags (like -f for follow, --previous, --timestamps)
4. Practical tips and best practices for log analysis
5. Examples for their specific case
6. Troubleshooting tips for common log issues

Make the response detailed, accurate, and immediately actionable. Use markdown formatting with code blocks for commands."""
        
        try:
            # Generate response using AI model
            ai_result = await self.ai_agent.process_message_smart(prompt)
            ai_response = ai_result.get("response", "I couldn't generate a response at this time.")
            
            return {
                "response": ai_response,
                "action_taken": "get_logs",
                "suggestions": ["Describe pod", "Exec into pod", "List pods", "Port forward"]
            }
        except Exception as e:
            logger.error(f"Error generating AI response for get_logs: {e}")
            # Fallback to template response
            return {
                "response": f"**📋 Get Logs Commands**\n\n```bash\n# Get logs from pod in current namespace\nkubectl logs {pod_name}\noc logs {pod_name}\n\n# Get logs from pod in specific namespace\nkubectl logs {pod_name} -n {namespace}\noc logs {pod_name} -n {namespace}\n\n# Follow logs in real-time\nkubectl logs -f {pod_name} -n {namespace}\noc logs -f {pod_name} -n {namespace}\n\n# Get logs from previous container restart\nkubectl logs --previous {pod_name} -n {namespace}\noc logs --previous {pod_name} -n {namespace}\n\n# Get logs with timestamps\nkubectl logs --timestamps {pod_name} -n {namespace}\noc logs --timestamps {pod_name} -n {namespace}\n\n# Get logs from specific container in multi-container pod\nkubectl logs {pod_name} -c <container-name> -n {namespace}\noc logs {pod_name} -c <container-name> -n {namespace}\n```\n\n**💡 Tips:**\n- Use `-f` to follow logs in real-time\n- Use `--previous` to get logs from previous container restart\n- Use `--timestamps` to add timestamps to log entries\n- Use `-c` to specify container in multi-container pods\n- Use `-n` to specify namespace",
                "action_taken": "get_logs",
                "suggestions": ["Describe pod", "Exec into pod", "List pods", "Port forward"]
            }
    
    async def _handle_exec_pod(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle executing into pods"""
        pod_name = entities.get("resource_name", "<pod-name>")
        namespace = entities.get("namespace", "<namespace>")
        return {
            "response": f"**📋 Exec into Pod Commands**\n\n```bash\n# Exec into pod in current namespace\nkubectl exec -it {pod_name} -- /bin/bash\noc exec -it {pod_name} -- /bin/bash\n\n# Exec into pod in specific namespace\nkubectl exec -it {pod_name} -n {namespace} -- /bin/bash\noc exec -it {pod_name} -n {namespace} -- /bin/bash\n\n# Exec into specific container in multi-container pod\nkubectl exec -it {pod_name} -c <container-name> -n {namespace} -- /bin/bash\noc exec -it {pod_name} -c <container-name> -n {namespace} -- /bin/bash\n\n# Run a single command\nkubectl exec {pod_name} -n {namespace} -- ls -la\noc exec {pod_name} -n {namespace} -- ls -la\n\n# Copy files to/from pod\nkubectl cp {pod_name}:/path/to/file /local/path -n {namespace}\nkubectl cp /local/path {pod_name}:/path/to/file -n {namespace}\n```\n\n**💡 Tips:**\n- Use `-it` for interactive terminal\n- Use `--` to separate kubectl/oc options from the command\n- Use `-c` to specify container in multi-container pods\n- Use `kubectl cp` to copy files to/from pods\n- Use `-n` to specify namespace",
            "action_taken": "exec_pod",
            "suggestions": ["Get pod logs", "Describe pod", "List pods", "Port forward"]
        }
    
    async def _handle_port_forward(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle port forwarding"""
        resource_name = entities.get("resource_name", "<resource-name>")
        namespace = entities.get("namespace", "<namespace>")
        return {
            "response": f"**📋 Port Forward Commands**\n\n```bash\n# Port forward pod\nkubectl port-forward {resource_name} 8080:80 -n {namespace}\noc port-forward {resource_name} 8080:80 -n {namespace}\n\n# Port forward service\nkubectl port-forward service/<service-name> 8080:80 -n {namespace}\noc port-forward service/<service-name> 8080:80 -n {namespace}\n\n# Port forward deployment\nkubectl port-forward deployment/<deployment-name> 8080:80 -n {namespace}\noc port-forward deployment/<deployment-name> 8080:80 -n {namespace}\n\n# Port forward with specific local port\nkubectl port-forward {resource_name} 3000:80 -n {namespace}\noc port-forward {resource_name} 3000:80 -n {namespace}\n```\n\n**💡 Tips:**\n- Format: `local-port:container-port`\n- Use `service/<name>` for services\n- Use `deployment/<name>` for deployments\n- Use `-n` to specify namespace\n- Press Ctrl+C to stop port forwarding",
            "action_taken": "port_forward",
            "suggestions": ["List pods", "List services", "Describe pod", "Exec into pod"]
        }
    
    async def _handle_deploy_pods(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle deploying pods and applications"""
        namespace = entities.get("namespace", "<namespace>")
        # Create a prompt for the AI model
        prompt = f"""You are a Kubernetes/OpenShift expert. The user asked: "{message}"

Context:
- Namespace: {namespace}

Please provide a comprehensive, helpful response that includes:
1. The exact kubectl/oc commands they need to deploy pods/applications
2. OpenShift-specific deployment commands (oc new-app, etc.)
3. YAML examples for deployments
4. Additional useful options and flags
5. Practical tips and best practices for deployment
6. Examples for their specific case
7. Deployment management commands (scale, rollback, etc.)

Make the response detailed, accurate, and immediately actionable. Use markdown formatting with code blocks for commands."""
        
        try:
            # Generate response using AI model
            ai_result = await self.ai_agent.process_message_smart(prompt)
            ai_response = ai_result.get("response", "I couldn't generate a response at this time.")
            
            return {
                "response": ai_response,
                "action_taken": "deploy_pods",
                "suggestions": ["List deployments", "Scale deployment", "Update deployment", "Rollback deployment"]
            }
        except Exception as e:
            logger.error(f"Error generating AI response for deploy_pods: {e}")
            # Fallback to template response
            return {
                "response": "**🚀 Deploy Pods/Applications in OpenShift/Kubernetes**\n\n**📋 Basic Deployment Commands:**\n```bash\n# Deploy from YAML file\nkubectl apply -f deployment.yaml -n <namespace>\noc apply -f deployment.yaml -n <namespace>\n\n# Create deployment from YAML\nkubectl create -f deployment.yaml -n <namespace>\noc create -f deployment.yaml -n <namespace>\n\n# Deploy from image directly\nkubectl run my-app --image=nginx:latest -n <namespace>\noc run my-app --image=nginx:latest -n <namespace>\n\n# Create deployment with specific replicas\nkubectl create deployment my-app --image=nginx:latest --replicas=3 -n <namespace>\noc create deployment my-app --image=nginx:latest --replicas=3 -n <namespace>\n```\n\n**🔄 OpenShift Specific Commands:**\n```bash\n# Deploy using OpenShift CLI\noc new-app nginx:latest -n <namespace>\noc new-app https://github.com/user/repo.git -n <namespace>\noc new-app --strategy=docker https://github.com/user/repo.git -n <namespace>\n\n# Deploy from template\noc process -f template.yaml | oc apply -f - -n <namespace>\noc new-app --template=my-template -n <namespace>\n\n# Deploy with environment variables\noc new-app nginx:latest -e ENV_VAR=value -n <namespace>\n```\n\n**📝 Example YAML for Deployment:**\n```yaml\napiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: my-app\n  namespace: <namespace>\nspec:\n  replicas: 3\n  selector:\n    matchLabels:\n      app: my-app\n  template:\n    metadata:\n      labels:\n        app: my-app\n    spec:\n      containers:\n      - name: my-app\n        image: nginx:latest\n        ports:\n        - containerPort: 80\n```\n\n**🔍 Useful Deployment Commands:**\n```bash\n# Check deployment status\nkubectl get deployments -n <namespace>\noc get deployments -n <namespace>\n\n# Describe deployment\nkubectl describe deployment <deployment-name> -n <namespace>\noc describe deployment <deployment-name> -n <namespace>\n\n# Scale deployment\nkubectl scale deployment <deployment-name> --replicas=5 -n <namespace>\noc scale deployment <deployment-name> --replicas=5 -n <namespace>\n\n# Update deployment image\nkubectl set image deployment/<deployment-name> <container-name>=new-image:tag -n <namespace>\noc set image deployment/<deployment-name> <container-name>=new-image:tag -n <namespace>\n\n# Rollback deployment\nkubectl rollout undo deployment/<deployment-name> -n <namespace>\noc rollout undo deployment/<deployment-name> -n <namespace>\n```\n\n**💡 Tips:**\n- Use `kubectl apply` for declarative deployments\n- Use `oc new-app` for quick OpenShift deployments\n- Use `-f` to specify YAML file\n- Use `-n` to specify namespace\n- Use `--replicas` to set number of pods\n- Use `--image` to specify container image\n- Use `-e` to set environment variables in OpenShift",
                "action_taken": "deploy_pods",
                "suggestions": ["List deployments", "Scale deployment", "Update deployment", "Rollback deployment"]
            }
import logging
from typing import Dict, List, Any, Optional, Tuple
from .base_agent import BaseAgent
from .gmail_agent import GmailAgent
from .jira_agent import JiraAgent
from .kubernetes_agent import KubernetesAgent
from .github_agent import GitHubAgent
from .calendar_agent import CalendarAgent
from .general_agent import GeneralAgent
from .must_gather_agent import MustGatherAgent
import re

logger = logging.getLogger(__name__)

class MultiAgentOrchestrator:
    """Orchestrates routing to specialized agents based on message content"""
    
    def __init__(self):
        self.agents = {
            'gmail': GmailAgent(),
            'jira': JiraAgent(),
            'kubernetes': KubernetesAgent(),
            'github': GitHubAgent(),
            'calendar': CalendarAgent(),
            'must_gather': MustGatherAgent(),
            'general': GeneralAgent()
        }
        
        # Keywords for routing to specific agents
        self.email_keywords = [
            'email', 'gmail', 'mail', 'inbox', 'send', 'compose', 'reply', 'forward',
            'attachment', 'draft', 'template', 'schedule', 'meeting', 'calendar',
            'unread', 'read', 'mark', 'delete', 'search', 'filter', 'sort',
            'notification', 'alert', 'spam', 'trash', 'archive', 'label', 'folder',
            'signature', 'cc', 'bcc', 'subject', 'body', 'recipient', 'sender',
            'follow up', 'follow-up', 'followup', 'team'
        ]
        
        self.jira_keywords = [
            'jira', 'issue', 'bug', 'story', 'task', 'epic', 'sprint', 'project',
            'status', 'assign', 'comment', 'create', 'update', 'fetch', 'search',
            'ocpqe', 'ocpbugs', 'api', 'openshift', 'post new', 'post_new'
        ]
        
        self.kubernetes_keywords = [
            'kubernetes', 'k8s', 'pod', 'deployment', 'service', 'configmap',
            'secret', 'namespace', 'node', 'cluster', 'openshift', 'oc', 'kubectl',
            'get', 'describe', 'logs', 'exec', 'port-forward', 'scale', 'rollout',
            'ingress', 'route', 'pvc', 'pv', 'storage', 'network', 'rbac'
        ]
        
        self.github_keywords = [
            'github', 'git', 'repo', 'repository', 'pull request', 'pr', 'issue',
            'commit', 'branch', 'merge', 'fork', 'clone', 'push', 'pull', 'code review',
            'security', 'vulnerability', 'dependency', 'workflow', 'action'
        ]
        
        self.calendar_keywords = [
            'calendar', 'event', 'meeting', 'schedule', 'appointment', 'reminder',
            'invite', 'attendee', 'agenda', 'duration', 'timezone', 'recurring',
            'availability', 'busy', 'free', 'out of office', 'vacation'
        ]
        
        self.must_gather_keywords = [
            'must-gather', 'mustgather', 'gather', 'logs', 'analysis', 'cluster',
            'openshift', 'pods', 'events', 'resources', 'network', 'storage',
            'security', 'performance', 'troubleshoot', 'debug', 'report', 'compare',
            'extract', 'analyze'
        ]
        
        # Priority order for agent selection (highest to lowest)
        self.agent_priority = ["jira", "kubernetes", "github", "gmail", "calendar", "general"]
        
        # Track conversation context
        self.conversation_context = {}
        
    async def process_message(self, message: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Process a message by routing it to the appropriate agent"""
        try:
            logger.info(f"DEBUG: MultiAgentOrchestrator.process_message called with message: '{message}'")
            # Determine which agent should handle this message
            selected_agent_name, selected_agent_domain, confidence = self._select_agent(message)
            
            # Set context for the selected agent
            if user_id:
                self.conversation_context[user_id] = {
                    "last_agent": selected_agent_name,
                    "last_domain": selected_agent_domain,
                    "timestamp": self._get_current_timestamp()
                }
            
            # Process the message with the selected agent
            response = await self.agents[selected_agent_name].process_message(message, self.conversation_context.get(user_id))
            
            # Add orchestrator metadata
            response.update({
                "orchestrator": {
                    "selected_agent": selected_agent_name,
                    "agent_domain": selected_agent_domain,
                    "available_agents": list(self.agents.keys()),
                    "confidence": response.get("confidence", 0.0)
                }
            })
            
            logger.info(f"Message processed by {selected_agent_name} (domain: {selected_agent_domain})")
            return response
            
        except Exception as e:
            logger.error(f"Error in multi-agent orchestrator: {e}")
            # Fallback to general agent
            general_agent = self.agents["general"]
            return await general_agent.process_message(message)
    
    def _select_agent(self, message: str) -> Tuple[str, str, float]:
        """Select the most appropriate agent for the message"""
        message_lower = message.lower()
        
        # Check for Jira issue keys first (highest priority)
        import re
        jira_issue_pattern = r'[A-Z]+-\d+'
        if re.search(jira_issue_pattern, message):
            # If Jira issue key is found, prioritize Jira agent
            logger.debug(f"Jira issue key detected, prioritizing Jira agent")
            return "jira", "jira", 0.95
        
        # Context-aware routing - check for domain-specific keywords
        email_keywords = ["email", "emails", "gmail", "mail", "inbox", "unread", "sender", "subject", "template", "draft", "sentiment", "translate", "group", "remind", "reminder", "follow up", "follow-up", "followup", "thank you", "thank-you", "thankyou", "thanks", "reply", "respond", "compose", "write"]
        jira_keywords = ["jira", "issue", "bug", "story", "task", "epic", "sprint", "ocpqe", "ocpbugs"]
        kubernetes_keywords = ["kubectl", "oc", "pod", "pods", "namespace", "deployment", "service", "kubernetes", "openshift", "ocp", "deploy", "deploying", "list", "get", "describe", "logs", "exec", "scale", "rollout", "ingress", "route", "pvc", "pv", "storage", "network", "rbac", "configmap", "secret", "node", "cluster"]
        github_keywords = ["github", "pr", "pull request", "commit", "repository", "repo"]
        calendar_keywords = ["calendar", "cal", "schedule meeting", "schedule call", "meeting", "event", "appointment", "agenda", "show my calendar", "show calendar", "my calendar", "accept meeting", "accept invite", "book call", "set up call", "meeting reminder", "send invite", "send meeting", "invitation"]
        must_gather_keywords = ["must-gather", "mustgather", "gather", "analysis", "cluster", "troubleshoot", "debug", "report", "compare", "extract", "analyze", "diagnostic", "diagnostics"]
        
        # Check for explicit domain keywords and prioritize accordingly
        # Must-gather should be checked first to avoid conflicts with other keywords
        logger.debug(f"Checking must-gather keywords: {must_gather_keywords}")
        logger.debug(f"Message lower: {message_lower}")
        if any(keyword in message_lower for keyword in must_gather_keywords):
            logger.debug(f"Must-gather keyword found, routing to must_gather agent")
            return "must_gather", "must_gather", 0.9
        
        if any(keyword in message_lower for keyword in email_keywords):
            return "gmail", "email", 0.9
        
        if any(keyword in message_lower for keyword in jira_keywords):
            return "jira", "jira", 0.9
        
        if any(keyword in message_lower for keyword in kubernetes_keywords):
            return "kubernetes", "kubernetes", 0.9
        
        if any(keyword in message_lower for keyword in github_keywords):
            return "github", "github", 0.9
        
        if any(keyword in message_lower for keyword in calendar_keywords):
            return "calendar", "calendar", 0.9
        
        # If no explicit domain keywords, use priority-based scoring
        agent_scores = {}
        
        for agent_name, agent in self.agents.items():
            score = agent.should_handle(message)
            agent_scores[agent_name] = score
        
        # Select agent with highest score
        if agent_scores:
            best_agent = max(agent_scores.items(), key=lambda x: x[1])
            return best_agent[0], self.agents[best_agent[0]].get_domain_keywords()[0], best_agent[1]
        
        # Fallback to general agent
        return "general", "general", 0.5
    
    def _calculate_agent_score(self, agent: BaseAgent, message_lower: str) -> float:
        """Calculate a score for how well an agent matches the message"""
        score = 0.0
        
        # Check domain keywords
        domain_keywords = agent.get_domain_keywords()
        for keyword in domain_keywords:
            if keyword in message_lower:
                score += 1.0
        
        # Special scoring for specific patterns
        if agent.domain == "jira":
            # High score for Jira issue keys
            import re
            if re.search(r'[A-Z]+-\d+', message_lower):
                score += 5.0
            if any(word in message_lower for word in ["ocpqe", "ocpbugs", "api-"]):
                score += 3.0
        
        elif agent.domain == "kubernetes":
            # High score for kubectl/oc commands
            if any(cmd in message_lower for cmd in ["kubectl", "oc"]):
                score += 5.0
            if any(word in message_lower for word in ["pod", "pods", "namespace", "service", "deployment", "deploy", "deploying", "list", "get", "describe", "logs", "exec"]):
                score += 3.0
            if any(word in message_lower for word in ["openshift", "ocp", "kubernetes", "k8s"]):
                score += 2.0
        
        elif agent.domain == "github":
            # High score for GitHub/PR related terms
            if any(word in message_lower for word in ["pr", "pull request", "merge", "review"]):
                score += 3.0
            if "#" in message_lower and any(char.isdigit() for char in message_lower):
                score += 2.0
        
        elif agent.domain == "gmail":
            # High score for email related terms
            if any(word in message_lower for word in ["email", "gmail", "inbox", "send", "read"]):
                score += 2.0
        
        # General agent gets a base score
        if agent.domain == "general":
            score += 0.1
        
        return score
    
    def get_agent_capabilities(self) -> Dict[str, List[str]]:
        """Get capabilities of all agents"""
        capabilities = {}
        for agent_name, agent in self.agents.items():
            capabilities[agent_name] = agent.get_capabilities()
        return capabilities
    
    def get_agent_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all agents"""
        agent_info = {}
        for agent_name, agent in self.agents.items():
            agent_info[agent_name] = {
                "name": agent.name,
                "domain": agent.domain,
                "capabilities": agent.get_capabilities(),
                "domain_keywords": agent.get_domain_keywords()
            }
        return agent_info
    
    def get_conversation_history(self, agent_name: str, limit: int = 10) -> List[Dict]:
        """Get conversation history for a specific agent"""
        if agent_name in self.agents:
            return self.agents[agent_name].get_conversation_history(limit)
        return []
    
    def clear_conversation_history(self, agent_name: Optional[str] = None):
        """Clear conversation history for specific agent or all agents"""
        if agent_name:
            if agent_name in self.agents:
                self.agents[agent_name].clear_conversation_history()
        else:
            for agent in self.agents.values():
                agent.clear_conversation_history()
    
    def set_agent_context(self, agent_name: str, context: Dict[str, Any]):
        """Set context for a specific agent"""
        if agent_name in self.agents:
            self.agents[agent_name].set_context(context)
    
    def get_agent_context(self, agent_name: str) -> Dict[str, Any]:
        """Get context for a specific agent"""
        if agent_name in self.agents:
            return self.agents[agent_name].get_context()
        return {}
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as string"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def test_agent_routing(self, test_messages: List[str]) -> Dict[str, Any]:
        """Test agent routing with sample messages"""
        results = {}
        
        for message in test_messages:
            selected_agent_name, selected_agent_domain, confidence = self._select_agent(message)
            response = await self.agents[selected_agent_name].process_message(message)
            
            results[message] = {
                "selected_agent": selected_agent_name,
                "agent_domain": selected_agent_domain,
                "intent": response.get("action_taken", "unknown"),
                "confidence": response.get("confidence", 0.0)
            }
        
        return results 

    def _get_agent_priority(self, message: str, agent_scores: Dict[str, float]) -> str:
        """Get the highest priority agent based on scores and context"""
        message_lower = message.lower()
        
        # Check for Jira issue keys (e.g., OCPQE-30241, OCPBUGS-12345)
        jira_issue_pattern = r'[A-Z]+-\d+'
        if re.search(jira_issue_pattern, message):
            # If Jira issue key is found, prioritize Jira agent
            if 'jira' in agent_scores:
                logger.debug(f"Jira issue key detected, prioritizing Jira agent")
                return 'jira'
        
        # Check for specific domain keywords that should override general scoring
        if any(word in message_lower for word in ['jira', 'issue', 'bug', 'story', 'task', 'ocpqe', 'ocpbugs']) and 'jira' in agent_scores:
            logger.debug(f"Jira-specific keywords detected, prioritizing Jira agent")
            return 'jira'
        
        # Check for email-specific keywords
        if any(word in message_lower for word in ['email', 'gmail', 'inbox', 'unread', 'send', 'compose']) and 'gmail' in agent_scores:
            logger.debug(f"Email-specific keywords detected, prioritizing Gmail agent")
            return 'gmail'
        
        # Check for calendar-specific keywords
        if any(word in message_lower for word in ['calendar', 'meeting', 'schedule', 'appointment', 'event']) and 'calendar' in agent_scores:
            logger.debug(f"Calendar-specific keywords detected, prioritizing Calendar agent")
            return 'calendar'
        
        # Check for Kubernetes/OpenShift keywords
        if any(word in message_lower for word in ['kubectl', 'oc', 'pod', 'service', 'deployment', 'namespace', 'kubernetes', 'openshift']) and 'kubernetes' in agent_scores:
            logger.debug(f"Kubernetes-specific keywords detected, prioritizing Kubernetes agent")
            return 'kubernetes'
        
        # Check for GitHub keywords
        if any(word in message_lower for word in ['github', 'repo', 'repository', 'pull request', 'pr', 'commit']) and 'github' in agent_scores:
            logger.debug(f"GitHub-specific keywords detected, prioritizing GitHub agent")
            return 'github'
        
        # Default to highest scoring agent
        if agent_scores:
            best_agent = max(agent_scores.items(), key=lambda x: x[1])[0]
            logger.debug(f"Defaulting to highest scoring agent: {best_agent}")
            return best_agent
        
        return 'general' 
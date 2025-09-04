# Training System Guide - Multi-Agent Architecture

## Overview

The AI Ultimate Assistant uses a sophisticated **permanent training system** that works seamlessly with the new multi-agent architecture. This system allows the AI to learn from every interaction and continuously improve its understanding of user intent.

## How Training Works

### 1. **Pattern-Based Learning**

The training system uses a **Pattern Trainer** that stores and learns from natural language patterns:

```python
# Example: Learning a new pattern
pattern_trainer.add_pattern(
    intent="update_jira_status",
    pattern="update status of jira [ISSUE_KEY] [STATUS]",
    entities={"issue_key": "OCPQE-30241", "status": "TODO"},
    confidence=0.8
)
```

### 2. **Multi-Agent Integration**

Each specialized agent can learn domain-specific patterns:

- **JiraAgent**: Learns Jira issue patterns, status updates, comments
- **KubernetesAgent**: Learns kubectl/oc command patterns
- **GmailAgent**: Learns email-related patterns
- **GitHubAgent**: Learns PR and repository patterns
- **GeneralAgent**: Learns general conversation patterns

### 3. **Automatic Learning Process**

#### Step 1: Pattern Detection
```python
# When user sends: "Update status of jira OCPQE-30241 TO DO"
# System detects: JiraAgent should handle this
# Pattern extracted: "update status of jira [ISSUE_KEY] [STATUS]"
```

#### Step 2: Intent Recognition
```python
# Pattern matches existing training data
# Intent detected: "update_jira_status"
# Confidence: 0.9
```

#### Step 3: Learning from Interaction
```python
# After successful interaction, system learns:
pattern_trainer.learn_from_interaction(
    message="Update status of jira OCPQE-30241 TO DO",
    detected_intent="update_jira_status",
    actual_intent="update_jira_status",
    entities={"issue_key": "OCPQE-30241", "status": "TODO"},
    success=True
)
```

## Training Components

### 1. **Pattern Trainer** (`app/services/pattern_trainer.py`)

**Core Functions:**
- `add_pattern()` - Add new patterns manually
- `learn_from_interaction()` - Learn from user interactions
- `get_patterns_for_intent()` - Retrieve patterns for specific intents
- `export_patterns()` / `import_patterns()` - Backup and restore training data

**Pattern Storage:**
```json
{
  "patterns": {
    "update_jira_status_1": {
      "intent": "update_jira_status",
      "pattern": "update status of jira [ISSUE_KEY] [STATUS]",
      "entities": {"issue_key": "OCPQE-30241", "status": "TODO"},
      "confidence": 0.8,
      "success_rate": 0.95,
      "usage_count": 15,
      "created": "2025-07-25T12:30:00"
    }
  },
  "intents": {
    "update_jira_status": ["update_jira_status_1", "update_jira_status_2"]
  },
  "interactions": [
    {
      "message": "Update status of jira OCPQE-30241 TO DO",
      "detected_intent": "update_jira_status",
      "actual_intent": "update_jira_status",
      "success": true,
      "timestamp": "2025-07-25T12:30:00"
    }
  ]
}
```

### 2. **Training API** (`app/api/training.py`)

**Available Endpoints:**
- `GET /api/training/stats` - Get training statistics
- `POST /api/training/patterns` - Add new patterns
- `GET /api/training/patterns/{intent}` - Get patterns for intent
- `POST /api/training/interactions` - Record interactions
- `POST /api/training/export` - Export training data
- `POST /api/training/import` - Import training data

### 3. **Training Interface** (`frontend/training_interface.html`)

**Web-based interface for:**
- Viewing training statistics
- Adding new patterns manually
- Recording interactions
- Exporting/importing training data
- Monitoring success rates

## Training Methods

### 1. **Automatic Learning**

**How it works:**
1. User sends a message
2. Multi-agent orchestrator selects appropriate agent
3. Agent analyzes intent and responds
4. System records the interaction
5. Pattern trainer learns from the interaction
6. Future similar messages get better recognition

**Example:**
```
User: "Update status of jira OCPQE-30241 TO DO"
↓
JiraAgent selected
↓
Intent: update_jira_status (confidence: 0.9)
↓
Response: "I'll update the status of OCPQE-30241 to TODO"
↓
System learns: This pattern works well for Jira status updates
```

### 2. **Manual Training**

**Adding patterns manually:**
```python
# Via API
POST /api/training/patterns
{
  "intent": "list_pods",
  "pattern": "show me pods in [NAMESPACE]",
  "entities": {"namespace": "kube-system"},
  "confidence": 0.8
}

# Via web interface
# Navigate to /training-interface.html
# Use the "Add Pattern" form
```

### 3. **Correction Learning**

**When the system makes mistakes:**
```python
# User corrects: "That's not what I meant"
# System learns: This pattern needs adjustment
pattern_trainer.learn_from_interaction(
    message="Update status of jira OCPQE-30241 TO DO",
    detected_intent="kubernetes_help",  # Wrong!
    actual_intent="update_jira_status", # Correct!
    success=False
)
```

## Training Statistics

### **Key Metrics:**
- **Total Patterns**: Number of learned patterns
- **Total Intents**: Number of different intents
- **Total Interactions**: Number of user interactions
- **Success Rate**: Percentage of successful intent detections
- **Last Updated**: When training data was last modified

### **Example Statistics:**
```json
{
  "total_patterns": 156,
  "total_intents": 23,
  "total_interactions": 1247,
  "success_rate": 94.2,
  "last_updated": "2025-07-25T12:30:00"
}
```

## Domain-Specific Training

### **Jira Training**
```python
# Jira patterns learn:
- Issue key formats: OCPQE-12345, OCPBUGS-67890
- Status values: TODO, IN_PROGRESS, DONE, BLOCKED
- Action verbs: update, create, assign, comment
```

### **Kubernetes Training**
```python
# Kubernetes patterns learn:
- Command structures: kubectl get, oc describe
- Resource types: pods, services, deployments
- Namespace patterns: -n kube-system, --namespace default
```

### **Email Training**
```python
# Email patterns learn:
- Email addresses: user@domain.com
- Action verbs: send, read, search, find
- Categories: important, spam, attachments
```

### **GitHub Training**
```python
# GitHub patterns learn:
- PR references: #123, PR #456
- Repository names: owner/repo
- Actions: merge, review, approve
```

## Training Data Management

### **Backup and Restore**
```bash
# Export training data
curl -X POST http://localhost:8000/api/training/export

# Import training data
curl -X POST http://localhost:8000/api/training/import \
  -H "Content-Type: application/json" \
  -d '{"filepath": "backup_patterns.json"}'
```

### **Training Data Location**
- **Primary**: `trained_patterns.json` (in app root)
- **Backups**: `exports/` directory
- **Logs**: Application logs show training activities

### **Data Persistence**
- Training data is automatically saved after each interaction
- Patterns persist across application restarts
- No data loss during updates or maintenance

## Best Practices

### **1. Regular Monitoring**
- Check training statistics weekly
- Monitor success rates for each domain
- Review failed interactions for improvement opportunities

### **2. Pattern Quality**
- Use specific, actionable patterns
- Include entity placeholders: `[ISSUE_KEY]`, `[NAMESPACE]`
- Avoid overly generic patterns

### **3. Domain Separation**
- Keep patterns domain-specific
- Don't mix Jira patterns with Kubernetes patterns
- Use appropriate confidence levels for each domain

### **4. Continuous Learning**
- Let the system learn from natural interactions
- Correct mistakes when they occur
- Add manual patterns for edge cases

## Troubleshooting

### **Common Issues:**

**1. Low Success Rate**
- Check for conflicting patterns
- Review failed interactions
- Add more specific patterns

**2. Wrong Agent Selection**
- Verify domain keywords are correct
- Check agent priority settings
- Review scoring algorithm

**3. Training Data Corruption**
- Restore from backup
- Check file permissions
- Verify JSON format

### **Debug Commands:**
```python
# Check training statistics
GET /api/training/stats

# View patterns for specific intent
GET /api/training/patterns/update_jira_status

# Export current training data
POST /api/training/export

# Test pattern matching
# Use the training interface to test patterns
```

## Future Enhancements

### **Planned Features:**
- **Machine Learning Integration**: Use ML models for better pattern recognition
- **Cross-Domain Learning**: Learn patterns that work across multiple domains
- **User Feedback Integration**: Learn from explicit user feedback
- **A/B Testing**: Test different pattern strategies
- **Performance Analytics**: Detailed performance metrics per domain

### **Advanced Training:**
- **Contextual Learning**: Learn from conversation context
- **Temporal Patterns**: Learn time-based patterns
- **User-Specific Learning**: Personalized patterns per user
- **Collaborative Learning**: Share patterns across instances

## Conclusion

The training system in the multi-agent architecture provides:

✅ **Permanent Learning**: Patterns persist and improve over time  
✅ **Domain Specialization**: Each agent learns domain-specific patterns  
✅ **Automatic Improvement**: System learns from every interaction  
✅ **Manual Control**: Ability to add and modify patterns manually  
✅ **Data Management**: Backup, restore, and monitoring capabilities  
✅ **Transparency**: Clear visibility into training statistics and patterns  

This creates a continuously improving AI assistant that gets better at understanding user intent with every interaction, while maintaining clear separation between different domains. 
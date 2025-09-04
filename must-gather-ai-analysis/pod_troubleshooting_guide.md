# Troubleshooting Pods Stuck in Pending State

## Step-by-Step Troubleshooting Guide

### 1. Check Pod Status and Events
```bash
# Get detailed pod information
oc describe pod <pod-name> -n <namespace>

# Check pod events specifically
oc get events --field-selector involvedObject.name=<pod-name> -n <namespace>
```

### 2. Check Node Status and Resources
```bash
# Check all nodes status
oc get nodes

# Check specific node details (replace <node-name> with actual node)
oc describe node <node-name>

# Check resource usage across all nodes
oc top nodes
```

### 3. Check Resource Requests vs Available Resources
```bash
# Check pod resource requests
oc get pod <pod-name> -o yaml | grep -A 10 resources:

# Check node allocatable resources
oc describe node <node-name> | grep -A 5 "Allocatable\|Allocated resources"
```

### 4. Check for Common Issues

#### A. Image Pull Issues
```bash
# Check if image exists and is accessible
oc get pod <pod-name> -o jsonpath='{.spec.containers[*].image}'

# Check image pull secrets
oc get pod <pod-name> -o yaml | grep -A 5 imagePullSecrets
```

#### B. Node Taints and Tolerations
```bash
# Check node taints
oc describe node <node-name> | grep Taints

# Check pod tolerations
oc get pod <pod-name> -o yaml | grep -A 10 tolerations
```

#### C. Node Selectors and Affinity
```bash
# Check if pod has node selector
oc get pod <pod-name> -o yaml | grep -A 5 nodeSelector

# Check node affinity rules
oc get pod <pod-name> -o yaml | grep -A 10 affinity
```

#### D. Storage Issues
```bash
# Check PVC status if pod uses persistent storage
oc get pvc -n <namespace>

# Check storage class availability
oc get storageclass
```

### 5. Check Cluster-Level Issues

#### A. Resource Quotas
```bash
# Check namespace resource quota
oc get quota -n <namespace>
oc describe quota -n <namespace>
```

#### B. Limit Ranges
```bash
# Check limit ranges that might block pod creation
oc get limitrange -n <namespace>
oc describe limitrange -n <namespace>
```

### 6. Solutions Based on Common Causes

#### A. Insufficient Resources
- Scale up cluster or add more nodes
- Reduce resource requests in pod spec
- Remove unused pods to free up resources

#### B. Node Taints
```bash
# Remove taint from node (if appropriate)
oc adm taint nodes <node-name> <taint-key>-

# Or add toleration to pod spec
tolerations:
- key: "<taint-key>"
  operator: "Equal"
  value: "<taint-value>"
  effect: "NoSchedule"
```

#### C. Node Selector Issues
```bash
# Check node labels
oc get nodes --show-labels

# Update node selector in pod spec or add appropriate labels to nodes
oc label nodes <node-name> <key>=<value>
```

#### D. Storage Issues
```bash
# Check PVC events
oc describe pvc <pvc-name> -n <namespace>

# Ensure storage class exists and is configured correctly
oc get storageclass <storage-class-name> -o yaml
```

### 7. Force Scheduling (Use with Caution)
```bash
# Delete and recreate pod
oc delete pod <pod-name> -n <namespace>

# Or use pod disruption budget bypass (emergency only)
oc delete pod <pod-name> --grace-period=0 --force -n <namespace>
```

## Key Commands Summary

```bash
# Essential troubleshooting commands
oc describe pod <pod-name> -n <namespace>
oc get events -n <namespace>
oc get nodes
oc describe node <node-name>
oc top nodes
oc get quota -n <namespace>
oc get limitrange -n <namespace>
```

## Prevention Tips

1. **Resource Planning**: Always set appropriate resource requests and limits
2. **Node Labeling**: Use consistent node labeling strategy
3. **Storage**: Ensure storage classes are properly configured
4. **Monitoring**: Set up monitoring for node resources and cluster capacity
5. **Testing**: Test pod scheduling in non-production environments first 
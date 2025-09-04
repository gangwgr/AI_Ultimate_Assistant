#!/usr/bin/env python3
"""
KMS Model Service - Provides correct KMS responses based on expert knowledge
"""

import re

class KMSModelService:
    def __init__(self):
        self.kms_keywords = [
            "kms", "key management", "encryption", "aws kms", "keyarn", 
            "feature gate", "kmsencryptionprovider", "encrypt", "decrypt",
            "featuregate", "enable kms"
        ]
        
    def is_kms_question(self, question):
        """Check if the question is related to KMS"""
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in self.kms_keywords)
    
    def generate_response(self, question):
        """Generate correct KMS response based on expert knowledge"""
        question_lower = question.lower()
        
        # Main KMS enablement question
        if any(phrase in question_lower for phrase in ["enable kms", "how to enable kms", "kms encryption", "setup kms"]):
            return self._get_kms_enablement_guide()
        
        # Feature gate questions
        elif any(phrase in question_lower for phrase in ["feature gate", "featuregate", "kmsencryptionprovider"]):
            return self._get_feature_gate_guide()
        
        # AWS region error
        elif "region" in question_lower and ("required" in question_lower or "error" in question_lower):
            return self._get_region_error_solution()
        
        # General KMS questions
        else:
            return self._get_kms_enablement_guide()
    
    def _get_kms_enablement_guide(self):
        """Complete KMS enablement guide"""
        return """To enable KMS encryption on OpenShift, follow these steps:

**Step 1: Enable KMS Feature Gate**
First, enable the KMS encryption feature gate:
```bash
oc patch featuregate/cluster --type=merge -p '{"spec":{"featureSet":"CustomNoUpgrade","customNoUpgrade":{"enabled":["KMSEncryptionProvider"]}}}'
```

**Step 2: Configure KMS Encryption**
Configure the API server with KMS encryption (note: include the region):
```bash
oc patch apiserver cluster --type=merge -p '{
  "spec": {
    "encryption": {
      "type": "KMS",
      "kms": {
        "type": "AWS",
        "aws": {
          "keyARN": "arn:aws:kms:us-east-1:101010101010:key/9a512e29-0d9c-4cf5-8174-fc1a5b22cd6a",
          "region": "us-east-1"
        }
      }
    }
  }
}'
```

**Common Issues:**
- **Missing Region Error**: The region field is required in the aws section
- **Invalid keyARN**: Ensure the KMS key ARN format is correct
- **Permissions**: Ensure the cluster has proper IAM permissions for the KMS key

 **Verification:**
 Check if KMS encryption is working by examining etcd data patterns:
 - KMS encrypted: `k8s:enc:kms:v2`
 - Non-KMS encrypted: `k8s:enc:aescbc:v1`"""

    def _get_feature_gate_guide(self):
        """Feature gate specific guide"""
        return """To enable the KMS feature gate on OpenShift:

**Command:**
```bash
oc patch featuregate/cluster --type=merge -p '{"spec":{"featureSet":"CustomNoUpgrade","customNoUpgrade":{"enabled":["KMSEncryptionProvider"]}}}'
```

**What this does:**
- Enables the KMSEncryptionProvider feature gate
- Uses CustomNoUpgrade feature set to allow experimental features
- This is a prerequisite before configuring KMS encryption

**After enabling the feature gate:**
1. Wait for the feature gate to be applied
2. Configure the API server with KMS encryption settings
3. Include the AWS region in your configuration to avoid validation errors"""

    def _get_region_error_solution(self):
        """Solution for region required error"""
        return """The "region: Required value" error occurs because the AWS region is mandatory for KMS configuration.

**Error:**
```
The APIServer "cluster" is invalid: 
* spec.encryption.kms.aws.region: Required value
```

**Solution:**
Include the region in your KMS configuration:
```bash
oc patch apiserver cluster --type=merge -p '{
  "spec": {
    "encryption": {
      "type": "KMS",
      "kms": {
        "type": "AWS",
        "aws": {
          "keyARN": "arn:aws:kms:us-east-1:101010101010:key/9a512e29-0d9c-4cf5-8174-fc1a5b22cd6a",
          "region": "us-east-1"
        }
      }
    }
  }
}'
```

**Key Points:**
- The region must match the region in your keyARN
- Extract the region from your KMS key ARN (e.g., us-east-1 from the example above)
- Both keyARN and region are required fields"""

# Global instance
kms_service = None

def get_kms_response(question):
    """Get response from KMS service if it's a KMS question"""
    global kms_service
    
    if kms_service is None:
        kms_service = KMSModelService()
    
    if kms_service.is_kms_question(question):
        return kms_service.generate_response(question)
    
    return None

if __name__ == "__main__":
    # Test the service
    service = KMSModelService()
    test_questions = [
        "How do I enable KMS encryption on OpenShift?",
        "What is the feature gate for KMS?",
        "I'm getting a region required error"
    ]
    
    for question in test_questions:
        if service.is_kms_question(question):
            response = service.generate_response(question)
            print(f"Question: {question}")
            print(f"Response: {response}")
            print("-" * 50)
        else:
            print(f"Not a KMS question: {question}") 
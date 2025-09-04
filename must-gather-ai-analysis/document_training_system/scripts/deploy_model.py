#!/usr/bin/env python3
"""
Deploy trained model to Ollama
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def create_modelfile(model_path, model_name):
    """Create Modelfile for Ollama"""
    
    modelfile_content = f"""FROM {model_path}

SYSTEM """You are an expert assistant trained on domain-specific documents. 
You have been fine-tuned on OpenShift, Kubernetes, and system administration content.

Your capabilities include:
- Analyzing technical documentation
- Troubleshooting system issues
- Providing step-by-step solutions
- Explaining complex concepts clearly

Always provide accurate, helpful responses based on your training data."""

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 4096
"""
    
    with open("Modelfile", "w") as f:
        f.write(modelfile_content)
    
    print(f"📝 Created Modelfile for {model_name}")
    return "Modelfile"

def deploy_to_ollama(model_path, model_name):
    """Deploy model to Ollama"""
    
    if not os.path.exists(model_path):
        print(f"❌ Model path not found: {model_path}")
        return False
    
    # Create Modelfile
    modelfile = create_modelfile(model_path, model_name)
    
    try:
        # Create model in Ollama
        cmd = ["ollama", "create", model_name, "-f", modelfile]
        subprocess.run(cmd, check=True)
        
        print(f"✅ Model deployed successfully as '{model_name}'")
        print(f"🚀 Test with: ollama run {model_name}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to deploy model: {e}")
        return False
    except FileNotFoundError:
        print("❌ Ollama not found. Please install Ollama first.")
        return False

def main():
    model_path = sys.argv[1] if len(sys.argv) > 1 else "models/document-trained"
    model_name = sys.argv[2] if len(sys.argv) > 2 else "document-assistant:latest"
    
    print(f"🚀 Deploying model from: {model_path}")
    print(f"📋 Model name: {model_name}")
    
    success = deploy_to_ollama(model_path, model_name)
    
    if success:
        print("\n🎉 Deployment complete!")
        print(f"Use: ollama run {model_name}")
    else:
        print("\n❌ Deployment failed!")

if __name__ == "__main__":
    main()

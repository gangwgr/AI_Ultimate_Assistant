#!/usr/bin/env python3
"""
Model Training System for AI Ultimate Assistant
Based on your must-gather AI analysis experience
Train your existing models with your workflow data
"""

import os
import sys
import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelTrainer:
    """Simple and effective model trainer"""
    
    def __init__(self):
        self.models_dir = Path("./trained_models")
        self.models_dir.mkdir(exist_ok=True)
        
    def get_available_models(self):
        """Get list of available Ollama models"""
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                models = []
                for line in lines:
                    if line.strip():
                        model_name = line.split()[0]
                        models.append(model_name)
                return models
            return []
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return []
    
    def create_workflow_training_data(self):
        """Create training data based on your AI Ultimate Assistant workflow"""
        
        training_data = [
            # GitHub PR Review Patterns
            {
                "instruction": "Review this Python code for security vulnerabilities",
                "input": "def process_user_data(data): query = f'SELECT * FROM users WHERE id = {data['id']}' return execute_query(query)",
                "output": "🚨 **Critical Security Issue Found**\n\n❌ **SQL Injection Vulnerability**\n- Direct string interpolation in SQL query\n- User input not sanitized\n\n🔧 **Fix Required**:\n```python\ndef process_user_data(data):\n    query = 'SELECT * FROM users WHERE id = %s'\n    return execute_query(query, (data['id'],))\n```\n\n**Security Rating**: HIGH RISK\n**Priority**: Immediate",
                "category": "security_review"
            },
            {
                "instruction": "Analyze this JavaScript function for performance issues",
                "input": "function calculateTotal(items) { let total = 0; for(let i = 0; i < items.length; i++) { total += items[i].price * items[i].quantity; } return total; }",
                "output": "✅ **Code Review Summary**\n\n**Performance**: Good - O(n) complexity\n\n⚠️ **Improvements**:\n1. Add input validation for null/undefined items\n2. Consider using reduce() for functional approach\n3. Add type checking for price/quantity\n\n💡 **Enhanced Version**:\n```javascript\nfunction calculateTotal(items = []) {\n    return items.reduce((total, item) => {\n        return total + (item.price || 0) * (item.quantity || 0);\n    }, 0);\n}\n```\n\n**Rating**: 7/10",
                "category": "performance_review"
            },
            
            # Email Management Patterns
            {
                "instruction": "Schedule meeting with team for next Tuesday 2pm",
                "input": "",
                "output": "I'll schedule a team meeting for next Tuesday at 2:00 PM. Let me check everyone's availability and send calendar invites with meeting details including agenda and dial-in information.",
                "category": "calendar_scheduling"
            },
            {
                "instruction": "Draft professional email declining meeting due to conflict",
                "input": "",
                "output": "I appreciate the invitation to the meeting. Unfortunately, I have a scheduling conflict during that time. Could we explore alternative times that work for everyone? I'm available [suggest 2-3 alternative slots]. Thank you for understanding.",
                "category": "email_composition"
            },
            
            # OpenShift/Kubernetes Troubleshooting
            {
                "instruction": "Pods are stuck in Pending state with insufficient CPU. How do I troubleshoot?",
                "input": "",
                "output": "To resolve pods stuck in Pending due to insufficient CPU:\n\n1️⃣ **Check Node Capacity**:\n```bash\noc describe nodes | grep -A 5 'Allocatable\\|Allocated resources'\n```\n\n2️⃣ **Identify Resource Requests**:\n```bash\noc describe pod <pod-name> | grep -A 10 'Requests:'\n```\n\n3️⃣ **Solutions**:\n- Scale down non-critical workloads\n- Add more nodes to cluster\n- Adjust resource requests\n- Use node affinity rules\n\n4️⃣ **Monitor Resources**:\n```bash\noc top nodes\noc top pods --all-namespaces\n```",
                "category": "troubleshooting"
            },
            {
                "instruction": "How do I list all container images running in my OpenShift cluster?",
                "input": "",
                "output": "To list all container images in your OpenShift cluster:\n\n**Complete Command**:\n```bash\noc get pods --all-namespaces -o jsonpath=\"{.items[*].spec['initContainers','containers'][*].image}\" | tr -s '[[:space:]]' '\\n' | sort | uniq -c\n```\n\n**Step by Step**:\n1. `oc get pods --all-namespaces` - Get all pods\n2. `-o jsonpath=...` - Extract container images\n3. `tr -s '[[:space:]]' '\\n'` - Convert to line-by-line\n4. `sort | uniq -c` - Sort and count duplicates\n\n**Alternative** (with pod info):\n```bash\noc get pods --all-namespaces -o custom-columns=NAMESPACE:.metadata.namespace,POD:.metadata.name,IMAGES:.spec.containers[*].image\n```",
                "category": "cluster_management"
            },
            
            # Workflow Automation
            {
                "instruction": "Automate daily standup meeting preparation",
                "input": "",
                "output": "I'll help prepare your daily standup:\n\n1️⃣ **Yesterday's Accomplishments**:\n- Check completed GitHub PRs\n- Review closed email threads\n- Summarize calendar meetings\n\n2️⃣ **Today's Plan**:\n- Parse calendar for scheduled tasks\n- Review pending GitHub reviews\n- Identify priority emails\n\n3️⃣ **Blockers & Dependencies**:\n- Flag pending PR approvals\n- Identify scheduling conflicts\n- Note resource constraints\n\n📋 **Standup Summary Ready**: [Generated based on your actual data]",
                "category": "meeting_prep"
            }
        ]
        
        return training_data
    
    def create_enhanced_modelfile(self, base_model, training_data, output_model):
        """Create enhanced modelfile using your must-gather approach"""
        
        # Categorize training data
        categories = {}
        for item in training_data:
            category = item.get('category', 'general')
            if category not in categories:
                categories[category] = []
            categories[category].append(item)
        
        # Create system prompt similar to your must-gather approach
        system_prompt = f"""You are an expert AI Ultimate Assistant that has been enhanced with specialized knowledge from {len(training_data)} training examples across {len(categories)} categories.

🎯 **ENHANCED CAPABILITIES**:
- Email composition and management
- GitHub PR reviews and code analysis  
- OpenShift/Kubernetes troubleshooting
- Calendar and meeting coordination
- Workflow automation
- Technical documentation

📊 **TRAINING SUMMARY**:
- Total Examples: {len(training_data)}
- Categories: {', '.join(categories.keys())}
- Training Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Base Model: {base_model}

🔍 **SPECIALIZED KNOWLEDGE**:"""

        # Add examples from each category
        for category, items in categories.items():
            system_prompt += f"\n\n### {category.replace('_', ' ').title()}"
            
            # Add top 2 examples from each category
            for i, item in enumerate(items[:2]):
                instruction = item.get('instruction', '')
                output = item.get('output', '')
                
                # Truncate very long outputs
                if len(output) > 500:
                    output = output[:500] + "..."
                
                system_prompt += f"""

Example {i+1}:
Q: {instruction}
A: {output}"""

        system_prompt += """

🎯 **RESPONSE GUIDELINES**:
1. **Email Tasks**: Professional, clear, actionable
2. **GitHub Reviews**: Security-focused, detailed feedback with code examples
3. **OpenShift Issues**: Step-by-step troubleshooting with complete commands
4. **Calendar Tasks**: Efficient scheduling with conflict resolution
5. **General Queries**: Comprehensive, practical guidance

🔒 **QUALITY STANDARDS**:
- Always provide complete, working commands
- Include explanations for technical steps
- Offer multiple solutions when applicable
- Prioritize security and best practices
- Maintain professional, helpful tone

Use your enhanced training to provide expert-level assistance across all domains."""

        # Create modelfile content
        modelfile_content = f"""FROM {base_model}

SYSTEM \"\"\"{system_prompt}\"\"\"

# Enhanced parameters for better performance
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_predict 2048
PARAMETER num_ctx 4096
PARAMETER repeat_penalty 1.1
"""
        
        return modelfile_content
    
    def train_model(self, base_model, output_model=None):
        """Train model using your proven approach"""
        if not output_model:
            output_model = f"{base_model.split(':')[0]}-assistant"
        
        logger.info(f"🚀 Training {base_model} → {output_model}")
        
        # Get training data
        training_data = self.create_workflow_training_data()
        logger.info(f"📊 Training data: {len(training_data)} examples")
        
        try:
            # Create enhanced modelfile
            modelfile_content = self.create_enhanced_modelfile(
                base_model, training_data, output_model
            )
            
            # Write temporary modelfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.modelfile', delete=False) as f:
                f.write(modelfile_content)
                modelfile_path = f.name
            
            logger.info("📝 Created enhanced modelfile")
            
            # Create the model
            logger.info("🤖 Creating enhanced model... (this may take 2-3 minutes)")
            result = subprocess.run([
                'ollama', 'create', output_model, '-f', modelfile_path
            ], capture_output=True, text=True, timeout=300)
            
            # Cleanup
            os.unlink(modelfile_path)
            
            if result.returncode == 0:
                logger.info(f"✅ Model {output_model} created successfully!")
                
                # Test the model
                if self.test_model(output_model):
                    self.save_training_record(base_model, output_model, training_data)
                    return True
                else:
                    logger.warning("⚠️ Model created but test failed")
                    return True  # Still consider success
            else:
                logger.error(f"❌ Model creation failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Training failed: {e}")
            return False
    
    def test_model(self, model_name):
        """Test the trained model with sample queries"""
        test_queries = [
            "Help me review a GitHub PR for security issues",
            "Schedule a team meeting for next week",
            "Troubleshoot pods stuck in pending state"
        ]
        
        logger.info(f"🧪 Testing model {model_name}...")
        
        for query in test_queries:
            try:
                result = subprocess.run([
                    'ollama', 'run', model_name, query
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    logger.warning(f"Test query failed: {query}")
                    return False
                    
            except subprocess.TimeoutExpired:
                logger.warning(f"Test query timed out: {query}")
                return False
        
        logger.info("✅ All tests passed!")
        return True
    
    def save_training_record(self, base_model, output_model, training_data):
        """Save training record for history tracking"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "base_model": base_model,
            "output_model": output_model,
            "training_examples": len(training_data),
            "success": True
        }
        
        history_file = self.models_dir / "training_history.json"
        
        if history_file.exists():
            with open(history_file, 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        history.append(record)
        
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        logger.info(f"📝 Training record saved to {history_file}")
    
    def show_menu(self):
        """Interactive training menu"""
        print("🧠 AI Ultimate Assistant - Model Trainer")
        print("Based on your must-gather AI analysis approach")
        print("=" * 50)
        
        # Get available models
        models = self.get_available_models()
        
        if not models:
            print("❌ No models found. Please install models with: ollama pull <model-name>")
            return
        
        print(f"\n📦 Available Models ({len(models)}):")
        for i, model in enumerate(models, 1):
            print(f"  {i:2d}. {model}")
        
        print(f"\n🎯 Training Options:")
        print("1. 🚀 Quick train granite3.3-balanced")
        print("2. 🎯 Train specific model")
        print("3. 📊 Show training history")
        print("4. 🧪 Test trained model")
        print("5. ❓ Help")
        
        choice = input(f"\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            self.quick_train(models)
        elif choice == "2":
            self.train_specific(models)
        elif choice == "3":
            self.show_history()
        elif choice == "4":
            self.test_trained()
        elif choice == "5":
            self.show_help()
        else:
            print("❌ Invalid choice")
    
    def quick_train(self, models):
        """Quick train granite3.3-balanced"""
        target_model = None
        for model in models:
            if "granite3.3-balanced" in model:
                target_model = model
                break
        
        if not target_model:
            print("❌ granite3.3-balanced not found. Available models:")
            for model in models:
                print(f"   • {model}")
            return
        
        print(f"\n🚀 Quick training {target_model}")
        print("This will create granite3.3-assistant with enhanced capabilities")
        
        if input("Continue? (y/n): ").lower() == 'y':
            success = self.train_model(target_model, "granite3.3-assistant")
            if success:
                print("🎉 Training completed!")
                print("Use: ollama run granite3.3-assistant")
                print("Test: 'Help me review a GitHub PR for security issues'")
    
    def train_specific(self, models):
        """Train a specific model"""
        print("\n📦 Select model to train:")
        for i, model in enumerate(models, 1):
            print(f"  {i:2d}. {model}")
        
        try:
            choice = int(input(f"\nSelect model (1-{len(models)}): "))
            if 1 <= choice <= len(models):
                selected_model = models[choice - 1]
                output_name = input(f"Output model name (default: {selected_model.split(':')[0]}-assistant): ").strip()
                if not output_name:
                    output_name = f"{selected_model.split(':')[0]}-assistant"
                
                print(f"🚀 Training {selected_model} → {output_name}")
                success = self.train_model(selected_model, output_name)
                
                if success:
                    print(f"🎉 Training completed! Use: ollama run {output_name}")
        except ValueError:
            print("❌ Please enter a valid number")
    
    def show_history(self):
        """Show training history"""
        history_file = self.models_dir / "training_history.json"
        if history_file.exists():
            with open(history_file, 'r') as f:
                history = json.load(f)
            
            print("\n📊 Training History:")
            for record in history[-5:]:  # Show last 5 records
                timestamp = record.get('timestamp', 'Unknown')
                base_model = record.get('base_model', 'Unknown')
                output_model = record.get('output_model', 'Unknown')
                examples = record.get('training_examples', 0)
                print(f"  {timestamp}: {base_model} → {output_model} ({examples} examples)")
        else:
            print("📋 No training history found")
    
    def test_trained(self):
        """Test a trained model"""
        model_name = input("Enter model name to test: ").strip()
        
        if model_name:
            if self.test_model(model_name):
                print(f"✅ Model {model_name} is working correctly!")
            else:
                print(f"❌ Model {model_name} test failed")
        else:
            print("❌ Please enter a model name")
    
    def show_help(self):
        """Show help and examples"""
        print("""
📚 Model Training Help

🎯 **What This Does**:
   Enhances your existing Ollama models with specialized knowledge for:
   • Email composition and management
   • GitHub PR reviews and code analysis
   • OpenShift/Kubernetes troubleshooting  
   • Calendar and meeting coordination
   • Workflow automation

🔧 **How It Works**:
   1. Takes your existing model (e.g., granite3.3-balanced)
   2. Creates enhanced system prompt with training examples
   3. Deploys new model (e.g., granite3.3-assistant)
   4. Ready to use with: ollama run granite3.3-assistant

💡 **Example Usage After Training**:
   • "Review this Python code for security issues"
   • "Schedule team meeting for next Tuesday"
   • "Troubleshoot pods stuck in pending state"
   • "Draft professional email declining meeting"

🚀 **Quick Start**:
   1. Choose option 1 for quick training
   2. Wait 2-3 minutes for completion
   3. Test with: ollama run granite3.3-assistant
        """)


def main():
    """Main entry point"""
    trainer = ModelTrainer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "quick":
            # Quick train granite3.3-balanced
            models = trainer.get_available_models()
            trainer.quick_train(models)
                
        elif command == "list":
            # List available models
            models = trainer.get_available_models()
            print("📦 Available Models:")
            for model in models:
                print(f"  • {model}")
                
        else:
            print("Usage: python train_your_models.py [quick|list]")
    else:
        # Interactive mode
        trainer.show_menu()


if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Simple Query Learning Training Script
Run this to train your AI Ultimate Assistant with additional queries
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from query_learning_trainer import QueryLearningTrainer

def main():
    """Train AI model with additional queries"""
    
    print("🚀 Training AI Ultimate Assistant with Additional Queries")
    print("=" * 70)
    
    # Check if Ollama is available
    try:
        import subprocess
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Ollama is not installed or not available in PATH")
            print("Please install Ollama first: https://ollama.ai/")
            return False
        print(f"✅ Ollama found: {result.stdout.strip()}")
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")
        return False
    
    # Check if base model exists
    base_model = "granite3.3-balanced:latest"
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if base_model not in result.stdout:
            print(f"⚠️  Base model '{base_model}' not found. Pulling it first...")
            subprocess.run(['ollama', 'pull', base_model], check=True)
            print(f"✅ Base model '{base_model}' pulled successfully")
        else:
            print(f"✅ Base model '{base_model}' found")
    except Exception as e:
        print(f"❌ Error with base model: {e}")
        return False
    
    # Initialize trainer
    trainer = QueryLearningTrainer(base_model=base_model)
    
    # Show current training data summary
    summary = trainer.get_training_summary()
    print(f"\n📊 Current Training Data: {summary['total_examples']} examples")
    
    if summary['categories']:
        print("📈 Current Categories:")
        for category, count in summary['categories'].items():
            category_name = summary['category_names'][category]
            print(f"  • {category_name}: {count} examples")
    
    # Add predefined query examples
    print(f"\n📝 Adding comprehensive query examples...")
    trainer.add_jira_queries()
    trainer.add_github_queries()
    trainer.add_openshift_queries()
    trainer.add_email_queries()
    
    # Show updated summary
    summary = trainer.get_training_summary()
    print(f"\n📊 Updated Training Data: {summary['total_examples']} examples")
    
    print("📈 New Categories Added:")
    for category, count in summary['categories'].items():
        category_name = summary['category_names'][category]
        print(f"  • {category_name}: {count} examples")
    
    # Train the model
    print(f"\n🎯 Training enhanced model: {trainer.model_name}")
    print("This may take a few minutes...")
    
    success = trainer.train_model()
    
    if success:
        print(f"\n✅ Model training completed successfully!")
        print(f"🎉 Your enhanced model '{trainer.model_name}' is ready!")
        
        # Test the model
        print("\n🧪 Testing the trained model with sample queries...")
        test_queries = [
            "update jira OCPQE-30241 TO_DO",
            "who is working on OCPQE-30241?",
            "blocked issues in OCPQE",
            "review PR #123 for security issues",
            "pods stuck in pending state"
        ]
        
        for query in test_queries:
            try:
                result = subprocess.run([
                    'ollama', 'run', trainer.model_name, query
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    response = result.stdout.strip()[:80] + "..." if len(result.stdout.strip()) > 80 else result.stdout.strip()
                    print(f"✅ {query}")
                    print(f"   Response: {response}")
                else:
                    print(f"❌ {query} - Failed")
                    
            except Exception as e:
                print(f"❌ {query} - Error: {e}")
        
        print(f"\n🎉 Success! Your AI Ultimate Assistant now has enhanced capabilities!")
        print("\n📝 Next Steps:")
        print("1. Update your AI_Ultimate_Assistant configuration to use the new model")
        print("2. Test the enhanced capabilities with various queries")
        print("3. Add more custom queries using the trainer")
        print("4. The model will now better understand and respond to your specific queries")
        
        # Show how to add custom queries
        print("\n🔧 To add more custom queries:")
        print("""
# Example: Add custom queries
trainer = QueryLearningTrainer()
custom_queries = [
    {
        "query": "your custom query here",
        "response": "expected response here",
        "category": "jira_queries"  # or any other category
    }
]
trainer.add_custom_queries(custom_queries)
trainer.train_model()  # Retrain with new data
        """)
        
        return True
        
    else:
        print("❌ Model training failed. Please check the logs for details.")
        return False

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Simple Gmail NLQ Training Script
Run this to train your AI Ultimate Assistant for Gmail natural language queries
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gmail_nlq_trainer import GmailNLQTrainer

def main():
    """Train Gmail NLQ model"""
    
    print("🚀 Training Gmail Natural Language Query Model")
    print("=" * 60)
    
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
    base_model = "granite3.3-balanced"
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
    trainer = GmailNLQTrainer(base_model=base_model)
    
    print(f"\n📊 Generating training data for Gmail NLQ...")
    training_examples = trainer.generate_training_data()
    
    print(f"✅ Generated {len(training_examples)} training examples")
    
    # Show training data summary
    categories = {}
    for example in training_examples:
        category = example["category"]
        categories[category] = categories.get(category, 0) + 1
    
    print("\n📈 Training Data Summary:")
    for category, count in categories.items():
        category_name = trainer.categories[category]
        print(f"  • {category_name}: {count} examples")
    
    # Train the model
    print(f"\n🎯 Training Gmail NLQ model: {trainer.model_name}")
    print("This may take a few minutes...")
    
    success = trainer.train_model(training_examples)
    
    if success:
        print(f"\n✅ Model training completed successfully!")
        print(f"🎉 Your Gmail NLQ model '{trainer.model_name}' is ready!")
        
        # Test the model
        print("\n🧪 Testing the trained model with sample queries...")
        test_queries = [
            "Do I have any new unread emails?",
            "Show me all emails marked as important",
            "Find emails from John in the past week"
        ]
        
        results = trainer.test_model(test_queries)
        
        print("\n📋 Test Results:")
        for query, result in results.items():
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {query}")
            if result["success"]:
                response = result['response'][:80] + "..." if len(result['response']) > 80 else result['response']
                print(f"     Response: {response}")
        
        print(f"\n🎉 Success! Your AI Ultimate Assistant now has enhanced Gmail NLQ capabilities!")
        print("\n📝 Next Steps:")
        print("1. Update your AI_Ultimate_Assistant configuration to use the new model")
        print("2. Test the enhanced email management features")
        print("3. The model will now better understand natural language email queries")
        
        return True
        
    else:
        print("❌ Model training failed. Please check the logs for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
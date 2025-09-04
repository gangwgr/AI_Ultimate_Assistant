#!/bin/bash

echo "🧠 Real AI Training System"
echo "=========================="
echo ""
echo "This will do ACTUAL fine-tuning of model weights (not fake prompt engineering)"
echo ""
echo "📊 Training Data: 323 examples ready"
echo "⏰ Time Required: 1-2 hours"
echo "💾 Result: Permanently trained model"
echo ""

read -p "Start REAL training? (y/n): " confirm

if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
    echo ""
    echo "🔧 Installing training dependencies..."
    pip install torch transformers datasets accelerate
    
    echo ""
    echo "🧠 Starting REAL model training..."
    echo "This will update model weights permanently!"
    echo ""
    
    cd document_training_system
    
    # Check if GPU is available
    python3 -c "import torch; print('🎯 GPU Available:', torch.cuda.is_available())"
    
    echo ""
    echo "🚀 Training with 323 examples..."
    echo "Progress will be shown below:"
    echo ""
    
    python scripts/train_on_documents.py training/configs/training_config.yaml processed/real_training_data.jsonl
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 SUCCESS! Model trained with permanent knowledge!"
        echo ""
        echo "📦 Next: Deploy to Ollama:"
        echo "python scripts/deploy_model.py models/document-trained openshift-expert:latest"
    else
        echo ""
        echo "❌ Training failed. Check error messages above."
    fi
else
    echo ""
    echo "ℹ️ Real training cancelled."
    echo ""
    echo "🎯 To train later, run:"
    echo "bash start_real_training.sh"
fi 
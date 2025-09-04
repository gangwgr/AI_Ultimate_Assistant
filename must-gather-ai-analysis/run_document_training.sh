#!/bin/bash

echo "📄 Document Training System for OpenShift AI"
echo "=============================================="
echo ""
echo "This system can process your documents and train AI models on them."
echo ""
echo "Select an option:"
echo "1. 📁 Setup directories and install dependencies"
echo "2. 📄 Process documents (PDF, DOCX, TXT, must-gather)"
echo "3. 🧠 Train model on processed documents"
echo "4. 🚀 Deploy trained model to Ollama"
echo "5. 📊 View processed training data"
echo "6. 🔍 Test trained model"
echo "7. 📋 Show system status"
echo ""

read -p "Enter your choice (1-7): " choice

case $choice in
    1)
        echo "📦 Installing dependencies..."
        pip install -r document_training_system/requirements.txt
        echo "✅ Dependencies installed!"
        echo ""
        echo "📁 Put your documents in these directories:"
        echo "  - PDFs: document_training_system/documents/pdfs/"
        echo "  - Text files: document_training_system/documents/text/"
        echo "  - Must-gather data: document_training_system/documents/must_gather/"
        ;;
    2)
        echo "📄 Processing documents..."
        cd document_training_system
        python scripts/document_processor.py documents processed
        ;;
    3)
        echo "🧠 Training model..."
        cd document_training_system
        python scripts/train_on_documents.py training/configs/training_config.yaml processed/processed_training_data.jsonl
        ;;
    4)
        echo "🚀 Deploying to Ollama..."
        cd document_training_system
        python scripts/deploy_model.py models/document-trained document-assistant:latest
        ;;
    5)
        echo "📊 Viewing training data..."
        cd document_training_system
        if [ -f "processed/processed_training_data.jsonl" ]; then
            wc -l processed/processed_training_data.jsonl
            echo "Sample entries:"
            head -3 processed/processed_training_data.jsonl | python -m json.tool
        else
            echo "No processed data found. Run option 2 first."
        fi
        ;;
    6)
        echo "🔍 Testing trained model..."
        echo "Enter a test prompt:"
        read -p "> " prompt
        ollama run document-assistant:latest "$prompt"
        ;;
    7)
        echo "📋 System Status:"
        echo "=================="
        cd document_training_system
        
        echo "📁 Documents:"
        find documents -type f | wc -l | xargs echo "  Total files:"
        
        echo "📊 Processed Data:"
        if [ -f "processed/processed_training_data.jsonl" ]; then
            wc -l processed/processed_training_data.jsonl | cut -d' ' -f1 | xargs echo "  Training examples:"
        else
            echo "  No processed data found"
        fi
        
        echo "🤖 Models:"
        if [ -d "models/document-trained" ]; then
            echo "  ✅ Trained model available"
        else
            echo "  ❌ No trained model found"
        fi
        
        echo "🦙 Ollama:"
        if command -v ollama &> /dev/null; then
            echo "  ✅ Ollama installed"
            if ollama list | grep -q "document-assistant"; then
                echo "  ✅ document-assistant model deployed"
            else
                echo "  ❌ document-assistant model not deployed"
            fi
        else
            echo "  ❌ Ollama not installed"
        fi
        ;;
    *)
        echo "Invalid choice. Please select 1-7."
        ;;
esac

#!/bin/bash

# Must-Gather AI Analysis Platform - Setup Script
# This script helps set up the project for first-time use

echo "🚀 Setting up Must-Gather AI Analysis Platform..."
echo "================================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip first."
    exit 1
fi

echo "✅ pip3 found"

# Install dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt
pip3 install -r requirements_ai_builder.txt
pip3 install -r requirements_chatbot.txt
pip3 install -r requirements_rag.txt

echo "✅ Dependencies installed"

# Check if Ollama is installed
if command -v ollama &> /dev/null; then
    echo "✅ Ollama found: $(ollama --version)"
    
    # Check if Ollama is running
    if ollama list &> /dev/null; then
        echo "✅ Ollama is running"
        
        # Pull required models
        echo "🤖 Pulling required models..."
        ollama pull granite3.3:latest
        echo "✅ granite3.3:latest model ready"
        
    else
        echo "⚠️  Ollama is not running. Please start it with: ollama serve"
    fi
else
    echo "⚠️  Ollama is not installed. Please install it from: https://ollama.ai"
    echo "    After installation, run: ollama pull granite3.3:latest"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p models/checkpoints
mkdir -p models/final
mkdir -p processed/chunks
mkdir -p processed/extracted
mkdir -p knowledge_base
mkdir -p logs

echo "✅ Directories created"

# Make shell scripts executable
echo "🔧 Making shell scripts executable..."
chmod +x run_*.sh
chmod +x *.sh

echo "✅ Shell scripts are now executable"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📝 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit: Must-Gather AI Analysis Platform"
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

echo ""
echo "🎉 Setup complete!"
echo "==================="
echo ""
echo "🚀 Quick Start:"
echo "  1. Start AI Assistant Builder: ./run_ai_builder.sh"
echo "  2. Start Chatbot: ./run_chatbot.sh"
echo "  3. Access AI Assistant Builder: http://localhost:8504"
echo "  4. Access Chatbot: http://localhost:8502"
echo ""
echo "📚 Documentation:"
echo "  - README.md - Main documentation"
echo "  - REAL_TRAINING_FIXED.md - Real training guide"
echo "  - training_issues_solution.md - Troubleshooting"
echo ""
echo "🔧 Troubleshooting:"
echo "  - Ensure Ollama is running: ollama serve"
echo "  - Check models: ollama list"
echo "  - View logs in terminal output"
echo ""
echo "Ready to analyze must-gather data and build AI assistants! 🎯" 
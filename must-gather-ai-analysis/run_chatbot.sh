#!/bin/bash

echo "Starting OpenShift AI Assistant Chatbot..."
echo "Installing dependencies..."

# Install requirements
pip install -r requirements_chatbot.txt

echo "Launching Enhanced Chatbot UI..."
echo "The chatbot will open in your browser at http://localhost:8501"
echo "Make sure Ollama is running with your models loaded!"

# Run the enhanced chatbot
streamlit run chatbot.py --server.port 8501 --server.headless false 
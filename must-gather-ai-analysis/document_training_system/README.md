# Document Training System

🚀 **Train AI models on your own documents!**

This system can process various document types and train AI models on them, perfect for creating domain-specific assistants.

## 🎯 What It Does

1. **Document Processing**: Extracts text from PDFs, DOCX, TXT, and must-gather data
2. **Training Data Creation**: Converts documents into instruction-response pairs
3. **Model Training**: Fine-tunes language models on your content
4. **Deployment**: Deploys trained models to Ollama for immediate use

## 🗂️ Directory Structure

```
document_training_system/
├── documents/              # Put your documents here
│   ├── pdfs/              # PDF files
│   ├── text/              # Text files
│   └── must_gather/       # Must-gather data
├── processed/             # Processed training data
├── training/              # Training configurations
├── models/                # Trained models
└── scripts/               # Processing scripts
```

## 🚀 Quick Start

1. **Run the main script**:
   ```bash
   ./run_document_training.sh
   ```

2. **Setup (option 1)**:
   - Installs dependencies
   - Creates directories

3. **Add your documents**:
   - PDFs → `document_training_system/documents/pdfs/`
   - Text files → `document_training_system/documents/text/`
   - Must-gather data → `document_training_system/documents/must_gather/`

4. **Process documents (option 2)**:
   - Extracts text from all documents
   - Creates training examples

5. **Train model (option 3)**:
   - Trains AI model on your documents
   - Saves trained model

6. **Deploy to Ollama (option 4)**:
   - Makes model available in Ollama
   - Ready for chat!

## 📄 Supported Document Types

- **PDF**: Technical manuals, guides, documentation
- **DOCX**: Word documents, reports
- **TXT**: Plain text files, logs
- **Markdown**: Documentation files
- **YAML**: Configuration files
- **Must-gather**: OpenShift diagnostic data

## 🧠 Training Process

1. **Text Extraction**: Pulls text from documents
2. **Chunking**: Breaks text into manageable pieces
3. **Example Creation**: Creates instruction-response pairs
4. **Model Training**: Fine-tunes base model
5. **Deployment**: Packages for Ollama

## 🔧 Configuration

Edit `training/configs/training_config.yaml`:

```yaml
model:
  base_model: microsoft/DialoGPT-medium
training:
  epochs: 3
  batch_size: 2
  learning_rate: 5e-5
```

## 📊 Example Use Cases

- **Technical Documentation**: Train on product manuals
- **Troubleshooting Guides**: Create support assistants
- **Company Knowledge**: Internal documentation
- **Educational Content**: Course materials
- **Process Documentation**: Standard operating procedures

## 🎯 Tips for Better Results

1. **Quality Documents**: Use well-structured, clear documents
2. **Variety**: Include different types of content
3. **Size**: More documents = better training
4. **Relevance**: Keep documents focused on your domain
5. **Updates**: Retrain with new documents regularly

## 🔍 Testing Your Model

After training and deployment:

```bash
ollama run document-assistant:latest "How do I troubleshoot pod issues?"
```

## 📈 Monitor Progress

Check system status with option 7:
- Document count
- Training examples created
- Model availability
- Ollama deployment status

---

✅ **Your document training system is ready!**

Add your documents and start training! 🚀

#!/usr/bin/env python3
"""
Document Processor - Extracts text from various document types
"""

import os
import json
import PyPDF2
import docx
from pathlib import Path
import yaml
import logging

class DocumentProcessor:
    def __init__(self):
        self.supported_formats = ['.pdf', '.txt', '.docx', '.md', '.yaml', '.yml', '.log']
        
    def extract_text_from_pdf(self, file_path):
        """Extract text from PDF files"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"Error processing PDF {file_path}: {e}")
            return ""
    
    def extract_text_from_docx(self, file_path):
        """Extract text from DOCX files"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            print(f"Error processing DOCX {file_path}: {e}")
            return ""
    
    def extract_text_from_plain(self, file_path):
        """Extract text from plain text files"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read()
        except Exception as e:
            print(f"Error processing text file {file_path}: {e}")
            return ""
    
    def process_must_gather_data(self, must_gather_dir):
        """Process must-gather data into training examples"""
        examples = []
        
        # Process cluster operators
        co_path = Path(must_gather_dir) / "cluster-scoped-resources" / "config.openshift.io" / "clusteroperators"
        if co_path.exists():
            for co_file in co_path.glob("*.yaml"):
                with open(co_file, 'r') as f:
                    content = f.read()
                    if 'status' in content.lower():
                        examples.append({
                            "instruction": "Analyze this cluster operator status",
                            "input": content[:1000],  # First 1000 chars
                            "output": f"This cluster operator data from {co_file.name} shows the status and conditions. Check the 'status' section for health information."
                        })
        
        # Process node information
        nodes_path = Path(must_gather_dir) / "cluster-scoped-resources" / "core" / "nodes"
        if nodes_path.exists():
            for node_file in nodes_path.glob("*.yaml"):
                with open(node_file, 'r') as f:
                    content = f.read()
                    examples.append({
                        "instruction": "Analyze this node configuration",
                        "input": content[:1000],
                        "output": f"This node data from {node_file.name} contains node status, capacity, and conditions. Check resource usage and node readiness."
                    })
        
        # Process etcd information
        etcd_path = Path(must_gather_dir) / "etcd_info"
        if etcd_path.exists():
            for etcd_file in etcd_path.glob("*.json"):
                with open(etcd_file, 'r') as f:
                    content = f.read()
                    examples.append({
                        "instruction": "Analyze this etcd health data",
                        "input": content[:1000],
                        "output": f"This etcd data from {etcd_file.name} shows cluster health. Check for unhealthy members or connectivity issues."
                    })
        
        return examples
    
    def process_documents(self, docs_dir, output_dir):
        """Process all documents in the directory"""
        print(f"🔄 Processing documents from {docs_dir}")
        
        all_examples = []
        processed_count = 0
        
        for root, dirs, files in os.walk(docs_dir):
            for file in files:
                file_path = Path(root) / file
                
                if file_path.suffix.lower() in self.supported_formats:
                    print(f"  Processing: {file_path}")
                    
                    # Extract text based on file type
                    if file_path.suffix.lower() == '.pdf':
                        text = self.extract_text_from_pdf(file_path)
                    elif file_path.suffix.lower() == '.docx':
                        text = self.extract_text_from_docx(file_path)
                    else:
                        text = self.extract_text_from_plain(file_path)
                    
                    if text.strip():
                        # Create training examples from the document
                        chunks = self.create_chunks(text, 512)
                        
                        for i, chunk in enumerate(chunks):
                            example = {
                                "instruction": f"Answer questions about {file_path.name}",
                                "input": f"What does this document section discuss?",
                                "output": chunk
                            }
                            all_examples.append(example)
                        
                        processed_count += 1
        
        # Check for must-gather data
        must_gather_paths = [
            Path(docs_dir) / "must-gather",
            Path(docs_dir) / "must_gather",
            Path(docs_dir) / "must-gather-data"
        ]
        
        for mg_path in must_gather_paths:
            if mg_path.exists():
                print(f"  📊 Processing must-gather data from: {mg_path}")
                mg_examples = self.process_must_gather_data(mg_path)
                all_examples.extend(mg_examples)
        
        # Save processed examples
        output_file = Path(output_dir) / "processed_training_data.jsonl"
        with open(output_file, 'w') as f:
            for example in all_examples:
                f.write(json.dumps(example) + '\n')
        
        print(f"✅ Processed {processed_count} documents")
        print(f"📝 Created {len(all_examples)} training examples")
        print(f"💾 Saved to: {output_file}")
        
        return output_file
    
    def create_chunks(self, text, chunk_size=512):
        """Split text into chunks for training"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            if len(chunk.strip()) > 50:  # Only keep meaningful chunks
                chunks.append(chunk)
        
        return chunks

def main():
    processor = DocumentProcessor()
    
    # Get input and output directories
    docs_dir = sys.argv[1] if len(sys.argv) > 1 else "documents"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "processed"
    
    if not os.path.exists(docs_dir):
        print(f"❌ Documents directory not found: {docs_dir}")
        print("Please put your documents in the 'documents' directory")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Process documents
    processor.process_documents(docs_dir, output_dir)
    print("\n🎉 Document processing complete!")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
RAG Service - Retrieval-Augmented Generation for OpenShift Knowledge Base
"""

import os
import json
import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
import tempfile
from datetime import datetime

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

# Add document training system to path
import sys
sys.path.append('document_training_system/scripts')

try:
    from document_processor import DocumentProcessor
    DOCUMENT_PROCESSOR_AVAILABLE = True
except ImportError:
    DOCUMENT_PROCESSOR_AVAILABLE = False

class RAGService:
    def __init__(self, knowledge_base_dir="knowledge_base"):
        self.knowledge_base_dir = Path(knowledge_base_dir)
        self.knowledge_base_dir.mkdir(exist_ok=True)
        
        self.embeddings_file = self.knowledge_base_dir / "embeddings.pkl"
        self.documents_file = self.knowledge_base_dir / "documents.json"
        self.index_file = self.knowledge_base_dir / "faiss_index.idx"
        
        # Initialize components
        self.embedder = None
        self.index = None
        self.documents = []
        self.document_processor = None
        
        self._initialize_components()
        self._load_knowledge_base()
    
    def _initialize_components(self):
        """Initialize embedding model and document processor"""
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
                print("✅ Sentence transformer model loaded")
            except Exception as e:
                print(f"❌ Failed to load sentence transformer: {e}")
                self.embedder = None
        
        if DOCUMENT_PROCESSOR_AVAILABLE:
            self.document_processor = DocumentProcessor()
            print("✅ Document processor loaded")
        
        if FAISS_AVAILABLE and self.embedder:
            # Create FAISS index (384 dimensions for all-MiniLM-L6-v2)
            self.index = faiss.IndexFlatIP(384)  # Inner product for cosine similarity
            print("✅ FAISS index initialized")
    
    def _load_knowledge_base(self):
        """Load existing knowledge base"""
        try:
            # Load documents
            if self.documents_file.exists():
                with open(self.documents_file, 'r') as f:
                    self.documents = json.load(f)
                print(f"📚 Loaded {len(self.documents)} documents from knowledge base")
            
            # Load FAISS index
            if self.index_file.exists() and FAISS_AVAILABLE:
                self.index = faiss.read_index(str(self.index_file))
                print(f"🔍 Loaded FAISS index with {self.index.ntotal} embeddings")
        
        except Exception as e:
            print(f"⚠️ Error loading knowledge base: {e}")
            self.documents = []
            if FAISS_AVAILABLE and self.embedder:
                self.index = faiss.IndexFlatIP(384)
    
    def _save_knowledge_base(self):
        """Save knowledge base to disk"""
        try:
            # Save documents
            with open(self.documents_file, 'w') as f:
                json.dump(self.documents, f, indent=2)
            
            # Save FAISS index
            if self.index and FAISS_AVAILABLE:
                faiss.write_index(self.index, str(self.index_file))
            
            print("💾 Knowledge base saved successfully")
        except Exception as e:
            print(f"❌ Error saving knowledge base: {e}")
    
    def chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        if not text.strip():
            return []
        
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)
            if chunk_text.strip():
                chunks.append(chunk_text.strip())
        
        return chunks
    
    def add_document(self, file_name: str, content: str, doc_type: str = "document") -> bool:
        """Add a document to the knowledge base"""
        if not self.embedder or not content.strip():
            return False
        
        try:
            # Create chunks
            chunks = self.chunk_text(content)
            if not chunks:
                return False
            
            # Generate embeddings
            embeddings = self.embedder.encode(chunks)
            
            # Normalize embeddings for cosine similarity  
            embeddings_normalized = embeddings.astype('float32')
            faiss.normalize_L2(embeddings_normalized)
            
            # Add to FAISS index
            if self.index:
                self.index.add(embeddings_normalized.astype('float32'))
            
            # Store document metadata
            doc_id = len(self.documents)
            for i, chunk in enumerate(chunks):
                self.documents.append({
                    "id": f"{doc_id}_{i}",
                    "file_name": file_name,
                    "doc_type": doc_type,
                    "chunk_index": i,
                    "content": chunk,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Save to disk
            self._save_knowledge_base()
            
            print(f"📄 Added document '{file_name}' with {len(chunks)} chunks")
            return True
        
        except Exception as e:
            print(f"❌ Error adding document: {e}")
            return False
    
    def ingest_file(self, uploaded_file, file_type: str) -> bool:
        """Ingest uploaded file into knowledge base"""
        if not self.document_processor:
            return False
        
        try:
            # Save uploaded file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            # Extract text based on file type
            if file_type.lower() == 'pdf':
                text = self.document_processor.extract_text_from_pdf(tmp_file_path)
            elif file_type.lower() in ['docx', 'doc']:
                text = self.document_processor.extract_text_from_docx(tmp_file_path)
            else:
                text = self.document_processor.extract_text_from_plain(tmp_file_path)
            
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
            if not text.strip():
                return False
            
            # Add to knowledge base
            return self.add_document(uploaded_file.name, text, file_type)
        
        except Exception as e:
            print(f"❌ Error ingesting file: {e}")
            return False
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for a query"""
        if not self.embedder or not self.index or self.index.ntotal == 0:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedder.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Search FAISS index
            scores, indices = self.index.search(query_embedding.astype('float32'), min(top_k, self.index.ntotal))
            
            # Retrieve corresponding documents
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.documents):
                    doc = self.documents[idx].copy()
                    doc['relevance_score'] = float(score)
                    results.append(doc)
            
            return results
        
        except Exception as e:
            print(f"❌ Error during retrieval: {e}")
            return []
    
    def generate_rag_response(self, query: str, model: str = "granite3.3-balanced") -> Optional[str]:
        """Generate RAG-enhanced response"""
        # Retrieve relevant context
        relevant_docs = self.retrieve(query, top_k=3)
        
        if not relevant_docs:
            return None  # No context found, use regular response
        
        # Build context from retrieved documents
        context_parts = []
        for doc in relevant_docs:
            context_parts.append(f"From {doc['file_name']}: {doc['content']}")
        
        context = "\n\n".join(context_parts)
        
        # Create RAG prompt
        rag_prompt = f"""Based on the following context from our knowledge base, please answer the question. If the context doesn't contain relevant information, provide a general answer.

CONTEXT:
{context}

QUESTION: {query}

ANSWER:"""
        
        return rag_prompt
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        if not self.documents:
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "file_types": {},
                "recent_files": []
            }
        
        file_types = {}
        files = set()
        
        for doc in self.documents:
            doc_type = doc.get('doc_type', 'unknown')
            file_types[doc_type] = file_types.get(doc_type, 0) + 1
            files.add(doc['file_name'])
        
        recent_files = sorted(
            list(set(doc['file_name'] for doc in self.documents[-10:])),
            reverse=True
        )[:5]
        
        return {
            "total_documents": len(files),
            "total_chunks": len(self.documents),
            "file_types": file_types,
            "recent_files": recent_files,
            "embedder_available": self.embedder is not None,
            "index_size": self.index.ntotal if self.index else 0
        }
    
    def clear_knowledge_base(self):
        """Clear the entire knowledge base"""
        try:
            self.documents = []
            if self.index and FAISS_AVAILABLE:
                self.index = faiss.IndexFlatIP(384)
            
            # Remove files
            for file_path in [self.documents_file, self.index_file, self.embeddings_file]:
                if file_path.exists():
                    file_path.unlink()
            
            print("🗑️ Knowledge base cleared")
            return True
        except Exception as e:
            print(f"❌ Error clearing knowledge base: {e}")
            return False

# Global RAG service instance
rag_service = None

def get_rag_service():
    """Get or create the global RAG service instance"""
    global rag_service
    if rag_service is None:
        rag_service = RAGService()
    return rag_service

def get_rag_response(query: str, model: str = "granite3.3-balanced") -> Optional[str]:
    """Get RAG-enhanced response for a query"""
    try:
        service = get_rag_service()
        return service.generate_rag_response(query, model)
    except Exception as e:
        print(f"❌ RAG service error: {e}")
        return None 
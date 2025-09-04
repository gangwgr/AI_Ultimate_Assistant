import os
import json
from datetime import datetime
import asyncio
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_milvus import Milvus
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
import bs4
from pydantic import SecretStr
import warnings

class URLScrapingRAG:
    def __init__(self, model_name="granite3.3-balanced", base_url="http://localhost:11434/v1"):
        """Initialize the URL scraping and RAG system"""
        self.model_name = model_name
        self.base_url = base_url
        self.api_key = SecretStr("dummy")
        
        # URL validation lists
        self.unreliable_domains = [
            'wikipedia.org',
            'simple.wikipedia.org',
            'en.wikipedia.org',
            'wiki.org'
        ]
        
        self.reliable_technical_domains = [
            'docs.openshift.com',
            'kubernetes.io',
            'access.redhat.com',
            'docs.docker.com',
            'helm.sh',
            'istio.io',
            'prometheus.io'
        ]
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="mixedbread-ai/mxbai-embed-large-v1"
        )
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=self.api_key,
            base_url=base_url,
            temperature=0.1
        )
        
        # Initialize vector store
        self.vectorstore = None
        self.rag_chain = None
        
        # Setup prompt template with content filtering
        self.prompt_template = """
        You are an expert AI assistant specializing in OpenShift, Kubernetes, and technical troubleshooting.
        Use ONLY the technical documentation provided in the context to answer questions.
        
        IMPORTANT CONTENT FILTERING RULES:
        1. Focus ONLY on technical, factual content
        2. Do NOT provide current political information, world leaders, or current events
        3. If asked about non-technical topics, redirect to your technical expertise
        4. Never trust Wikipedia or editable sources for current facts
        5. Always prioritize official documentation and verified technical sources
        
        <context>
        {context}
        </context>
        
        <question>
        {question}
        </question>
        
        Provide a detailed technical answer based only on the context above. If the question is not technical in nature, redirect to OpenShift/Kubernetes assistance and provide useful technical commands instead.
        """
        
        self.prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=self.prompt_template
        )
    
    def validate_url(self, url):
        """Validate URL for reliability and technical content"""
        url_lower = url.lower()
        
        # Check for unreliable domains
        for domain in self.unreliable_domains:
            if domain in url_lower:
                return False, f"⚠️  WARNING: {domain} is not a reliable source for current facts. Consider using official documentation instead."
        
        # Check for reliable technical domains
        for domain in self.reliable_technical_domains:
            if domain in url_lower:
                return True, f"✅ Reliable technical source: {domain}"
        
        # General validation
        if any(keyword in url_lower for keyword in ['docs', 'documentation', 'guide', 'tutorial', 'api']):
            return True, "✅ Appears to be technical documentation"
        
        return True, "⚠️  Please verify this source is reliable for technical content"
    
    def validate_urls(self, urls):
        """Validate a list of URLs and return filtered list with warnings"""
        validated_urls = []
        warnings_list = []
        
        for url in urls:
            is_valid, message = self.validate_url(url)
            if is_valid:
                validated_urls.append(url)
                if "WARNING" in message:
                    warnings_list.append(f"{url}: {message}")
            else:
                warnings_list.append(f"SKIPPED {url}: {message}")
        
        return validated_urls, warnings_list
    
    def scrape_urls(self, urls, chunk_size=2000, chunk_overlap=200):
        """Scrape content from URLs and process into chunks"""
        # Validate URLs first
        validated_urls, warnings_list = self.validate_urls(urls)
        
        print(f"URL Validation Results:")
        for warning in warnings_list:
            print(f"  {warning}")
        
        if not validated_urls:
            raise ValueError("No valid URLs to scrape after validation")
        
        print(f"\nScraping {len(validated_urls)} validated URLs...")
        
        # Set user agent
        os.environ['USER_AGENT'] = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Create loader with validated URLs only
        loader = WebBaseLoader(
            web_paths=validated_urls
        )
        
        # Load documents
        documents = loader.load()
        print(f"Loaded {len(documents)} documents")
        
        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        docs = text_splitter.split_documents(documents)
        print(f"Split into {len(docs)} chunks")
        
        return docs
    
    def create_vectorstore(self, docs, collection_name="scraped_docs"):
        """Create vector store from documents"""
        print("Creating vector store...")
        
        # Fix async event loop issue in Streamlit
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        self.vectorstore = Milvus.from_documents(
            documents=docs,
            embedding=self.embeddings,
            connection_args={
                "uri": "./milvus_demo.db",
            },
            collection_name=collection_name,
            drop_old=True,
            index_params={"index_type": "FLAT", "metric_type": "L2"}
        )
        
        # Verify entries
        if hasattr(self.vectorstore, 'col') and self.vectorstore.col is not None:
            self.vectorstore.col.flush()
            num_entries = self.vectorstore.col.num_entities
            print(f"Vector store created with {num_entries} entries")
        else:
            print("Vector store created successfully")
        
        return self.vectorstore
    
    def setup_rag_chain(self, search_k=3):
        """Setup the RAG chain for question answering"""
        if not self.vectorstore:
            raise ValueError("Vector store not initialized. Call create_vectorstore first.")
        
        # Create retriever
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": search_k})
        
        # Document formatting function
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        # Create RAG chain
        self.rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        
        print("RAG chain initialized")
        return self.rag_chain
    
    def ask_question(self, question):
        """Ask a question and get an answer from the RAG system"""
        if not self.rag_chain:
            raise ValueError("RAG chain not initialized. Call setup_rag_chain first.")
        
        print(f"\nQuestion: {question}")
        print("-" * 50)
        
        response = self.rag_chain.invoke(question)
        print(f"Answer: {response}")
        print("-" * 50)
        
        return response
    
    def get_relevant_docs(self, question, k=3):
        """Get relevant documents for a question"""
        if not self.vectorstore:
            raise ValueError("Vector store not initialized.")
        
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": k})
        docs = retriever.invoke(question)
        
        print(f"\nRelevant documents for: {question}")
        print("-" * 50)
        
        for i, doc in enumerate(docs, 1):
            print(f"Document {i}:")
            print(f"Source: {doc.metadata.get('source', 'N/A')}")
            print(f"Content: {doc.page_content[:200]}...")
            print("-" * 30)
        
        return docs
    
    def generate_training_data(self, questions, output_file="scraped_training_data.jsonl"):
        """Generate training data from scraped content"""
        print(f"Generating training data for {len(questions)} questions...")
        
        training_data = []
        
        for question in questions:
            try:
                answer = self.ask_question(question)
                
                # Create training sample
                training_sample = {
                    "messages": [
                        {
                            "role": "user",
                            "content": question
                        },
                        {
                            "role": "assistant", 
                            "content": answer
                        }
                    ]
                }
                
                training_data.append(training_sample)
                
            except Exception as e:
                print(f"Error processing question '{question}': {e}")
                continue
        
        # Save training data
        with open(output_file, 'w') as f:
            for sample in training_data:
                f.write(json.dumps(sample) + '\n')
        
        print(f"Training data saved to {output_file}")
        return training_data

def main():
    """Example usage of the URL scraping RAG system"""
    
    # Initialize the system
    rag_system = URLScrapingRAG()
    
    # Example URLs (using your existing ones)
    urls = [
        "https://medium.com/@tuhinsharma121/mastering-prompt-engineering-a-beginners-guide-to-ai-interaction-2a28434ccb67",
        "https://medium.com/@rahuljangir2992/graph-based-prompting-revolutionizing-ai-reasoning-f316b7266c1f",
        "https://medium.com/@fassha08/transforming-search-ai-agents-and-multi-vector-intelligence-1bde1dbe66e7",
        "https://medium.com/@harshkumar1146/prompt-chaining-unlocking-the-full-potential-of-ai-assistants-4fdf2f28c1a5",
    ]
    
    # Validate URLs
    validated_urls, warnings_list = rag_system.validate_urls(urls)
    print("\nValidation Results:")
    for warning in warnings_list:
        print(warning)
    
    # Scrape URLs
    docs = rag_system.scrape_urls(validated_urls)
    
    # Create vector store
    rag_system.create_vectorstore(docs)
    
    # Setup RAG chain
    rag_system.setup_rag_chain()
    
    # Example questions
    questions = [
        "What are the advantages of few shot prompting?",
        "How does chain-of-thought prompting work?",
        "What is prompt chaining and how is it used?",
        "What are the limitations of standard few-shot prompting?",
        "How do you implement zero-shot CoT prompting?",
    ]
    
    # Ask questions
    for question in questions:
        rag_system.ask_question(question)
    
    # Generate training data
    rag_system.generate_training_data(questions)

if __name__ == "__main__":
    main() 
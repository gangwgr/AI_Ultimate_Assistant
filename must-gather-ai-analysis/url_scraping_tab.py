import streamlit as st
import json
import os
from datetime import datetime
from url_scraping_integration import URLScrapingRAG

def render_url_scraping_tab():
    """Render the URL scraping tab for the AI Assistant Builder"""
    
    st.header("🌐 URL Scraping & Training Data Generation")
    
    st.markdown("""
    This tool automatically scrapes content from URLs and generates training data for your AI model.
    Perfect for incorporating technical documentation, tutorials, and articles into your training dataset.
    """)
    
    # URL Input Section
    st.subheader("📝 Add URLs to Scrape")
    
    # Multiple URL input methods
    url_input_method = st.radio(
        "Choose input method:",
        ["Single URL", "Multiple URLs (one per line)", "URL List from File"]
    )
    
    urls = []
    
    if url_input_method == "Single URL":
        url = st.text_input("Enter URL:", placeholder="https://example.com/article")
        if url:
            urls = [url]
    
    elif url_input_method == "Multiple URLs (one per line)":
        url_text = st.text_area(
            "Enter URLs (one per line):",
            height=150,
            placeholder="https://example.com/article1\nhttps://example.com/article2\nhttps://example.com/article3"
        )
        if url_text:
            urls = [url.strip() for url in url_text.split('\n') if url.strip()]
    
    elif url_input_method == "URL List from File":
        uploaded_file = st.file_uploader("Upload text file with URLs", type=['txt'])
        if uploaded_file:
            content = uploaded_file.read().decode('utf-8')
            urls = [url.strip() for url in content.split('\n') if url.strip()]
    
    # Display URLs to be scraped with validation warnings
    if urls:
        st.subheader("📋 URLs to Scrape")
        
        # Import validation function
        from url_scraping_integration import URLScrapingRAG
        temp_rag = URLScrapingRAG()
        
        for i, url in enumerate(urls, 1):
            is_valid, message = temp_rag.validate_url(url)
            if "WARNING" in message:
                st.warning(f"{i}. {url} - {message}")
            elif "SKIPPED" in message:
                st.error(f"{i}. {url} - {message}")
            elif "✅" in message:
                st.success(f"{i}. {url} - {message}")
            else:
                st.write(f"{i}. {url}")
    
    # Advanced Settings
    with st.expander("⚙️ Advanced Settings"):
        chunk_size = st.slider("Chunk Size", 500, 4000, 2000, 100)
        chunk_overlap = st.slider("Chunk Overlap", 0, 500, 200, 50)
        search_k = st.slider("Number of Retrieved Documents", 1, 10, 3)
        
        model_choice = st.selectbox(
            "Model to Use",
            ["granite3.3-balanced", "granite3.3", "openshift-ai:latest", "mistral:latest"]
        )
    
    # Question Generation
    st.subheader("❓ Training Questions")
    
    question_method = st.radio(
        "How would you like to provide training questions?",
        ["Auto-generate from content", "Manual input", "Upload question file"]
    )
    
    questions = []
    
    if question_method == "Auto-generate from content":
        if st.button("🤖 Generate Questions from Content"):
            if urls:
                st.info("Auto-generating questions from scraped content...")
                # This would use the RAG system to generate relevant questions
                questions = [
                    "What are the main concepts discussed in this content?",
                    "How can this information be applied in practice?",
                    "What are the key technical details mentioned?",
                    "What examples or case studies are provided?",
                    "What are the benefits and limitations discussed?"
                ]
                st.success(f"Generated {len(questions)} questions")
    
    elif question_method == "Manual input":
        question_text = st.text_area(
            "Enter questions (one per line):",
            height=150,
            placeholder="What is the main topic of this article?\nHow does this technique work?\nWhat are the practical applications?"
        )
        if question_text:
            questions = [q.strip() for q in question_text.split('\n') if q.strip()]
    
    elif question_method == "Upload question file":
        question_file = st.file_uploader("Upload text file with questions", type=['txt'])
        if question_file:
            content = question_file.read().decode('utf-8')
            questions = [q.strip() for q in content.split('\n') if q.strip()]
    
    # Display questions
    if questions:
        st.subheader("📝 Training Questions")
        for i, question in enumerate(questions, 1):
            st.write(f"{i}. {question}")
    
    # Scraping and Training Data Generation
    if st.button("🚀 Start Scraping & Generate Training Data", disabled=not urls):
        if not urls:
            st.error("Please provide at least one URL to scrape")
            return
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Initialize RAG system
            status_text.text("Initializing RAG system...")
            progress_bar.progress(10)
            
            rag_system = URLScrapingRAG(model_name=model_choice)
            
            # Validate and scrape URLs
            status_text.text("Validating URLs...")
            progress_bar.progress(25)
            
            # Show validation results
            validated_urls, warnings_list = rag_system.validate_urls(urls)
            
            if warnings_list:
                st.subheader("🔍 URL Validation Results")
                for warning in warnings_list:
                    if "SKIPPED" in warning:
                        st.error(warning)
                    else:
                        st.info(warning)
            
            if not validated_urls:
                st.error("❌ No valid URLs to scrape after validation. Please provide reliable technical documentation sources.")
                return
            
            status_text.text(f"Scraping {len(validated_urls)} validated URLs...")
            progress_bar.progress(30)
            
            docs = rag_system.scrape_urls(urls, chunk_size, chunk_overlap)
            
            # Create vector store
            status_text.text("Creating vector store...")
            progress_bar.progress(50)
            
            rag_system.create_vectorstore(docs, f"scraped_docs_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            # Setup RAG chain
            status_text.text("Setting up RAG chain...")
            progress_bar.progress(70)
            
            rag_system.setup_rag_chain(search_k)
            
            # Generate training data
            status_text.text("Generating training data...")
            progress_bar.progress(90)
            
            if not questions:
                questions = [
                    "What are the main concepts discussed in this content?",
                    "How can this information be applied in practice?",
                    "What are the key technical details mentioned?"
                ]
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"scraped_training_data_{timestamp}.jsonl"
            
            training_data = rag_system.generate_training_data(questions, output_file)
            
            progress_bar.progress(100)
            status_text.text("✅ Complete!")
            
            # Display results
            st.success(f"Successfully generated {len(training_data)} training samples!")
            
            # Show some sample training data
            st.subheader("📊 Sample Training Data")
            if training_data:
                sample = training_data[0]
                st.json(sample)
            
            # Download options
            st.subheader("💾 Download Training Data")
            
            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    file_content = f.read()
                
                st.download_button(
                    label="📥 Download Training Data (JSONL)",
                    data=file_content,
                    file_name=output_file,
                    mime='application/json'
                )
            
            # Integration with existing training
            st.subheader("🔗 Next Steps")
            st.markdown("""
            1. **Download the training data** using the button above
            2. **Go to the Simple Training tab** to train your model with this data
            3. **Test your improved model** in the chatbot
            """)
            
        except Exception as e:
            st.error(f"Error during scraping: {str(e)}")
            progress_bar.progress(0)
            status_text.text("")
    
    # Example URLs section
    st.subheader("💡 Example URLs")
    st.markdown("""
    **Technical Documentation:**
    - https://kubernetes.io/docs/concepts/overview/components/
    - https://docs.openshift.com/container-platform/latest/architecture/architecture.html
    
    **Tutorial Articles:**
    - https://medium.com/@author/kubernetes-tutorial
    - https://dev.to/author/openshift-guide
    
    **Best Practices:**
    - https://cloud.google.com/kubernetes-engine/docs/best-practices
    - https://docs.aws.amazon.com/eks/latest/best-practices/
    """)

if __name__ == "__main__":
    render_url_scraping_tab() 
import sys
import os
import streamlit as st

# Add the current directory to Python path for Streamlit Cloud
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Now import your modules
from utils.document_loader import DocumentProcessor
from utils.vector_store import VectorStoreManager
from utils.auth import Authentication, AuditLogger
from config import Config
from groq import Groq
import time


# Page configuration
st.set_page_config(
    page_title="Company Knowledge Agent",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
document_processor = DocumentProcessor()
vector_manager = VectorStoreManager()

class RAGSystem:
    def __init__(self):
        try:
            self.client = Groq(api_key=Config.GROQ_API_KEY)
            print("✅ Groq client initialized successfully")
        except Exception as e:
            st.error(f"Failed to initialize Groq client: {e}")
            self.client = None
    
    def generate_response(self, query: str, context_docs: list) -> str:
        if not self.client:
            return "Error: Groq client not initialized. Check your API key.", []
        
        context = "\n\n".join([doc.page_content for doc in context_docs])
        sources = list(set([doc.metadata.get("source", "Unknown") for doc in context_docs]))
        
        prompt = f"""Based on the following company documents, please answer the user's question. 
        If the information is not in the provided context, say you don't know.

        Company Documents Context:
        {context}

        User Question: {query}

        Please provide a helpful answer with citations from the source documents:"""
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful company knowledge assistant. Provide accurate answers based on the given documents."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=Config.GROQ_MODEL,
                temperature=0.1,
                max_tokens=1024
            )
            
            response = chat_completion.choices[0].message.content
            
            # Log the interaction
            if st.session_state.get("authenticated", False):
                AuditLogger.log_query(
                    st.session_state["username"],
                    query,
                    response,
                    sources
                )
            
            return response, sources
            
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            return error_msg, []

def login_section():
    """Display login form"""
    st.sidebar.title("🔐 Login")
    
    with st.sidebar.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")
        
        if login_button:
            if Authentication.login(username, password):
                st.sidebar.success(f"Welcome {username}!")
                st.rerun()
            else:
                st.sidebar.error("Invalid credentials")

def main_application():
    """Main application after login"""
    
    # Check session timeout
    if Authentication.check_session_timeout():
        st.rerun()
    
    # Sidebar
    st.sidebar.title(f"🏢 Company Knowledge Agent")
    st.sidebar.write(f"Welcome, **{st.session_state['username']}**")
    st.sidebar.write(f"Role: **{st.session_state['role']}**")
    st.sidebar.write(f"Department: **{st.session_state['department']}**")
    
    # Search Statistics
    stats = vector_manager.get_search_stats()
    st.sidebar.info(f"📊 Knowledge Base: {stats['total_chunks']} chunks")
    
    # Admin tools in sidebar
    if Authentication.check_permission("view_audit"):
        st.sidebar.header("Admin Tools")
        
        # Add clear database button
        if st.sidebar.button("🗑️ Clear Database"):
            if vector_manager.clear_database():
                st.sidebar.success("Database cleared! Upload new documents.")
                st.rerun()
        
        if st.sidebar.button("View Audit Logs"):
            logs = AuditLogger.get_audit_logs()
            if logs:
                st.sidebar.info(f"Total queries: {len(logs)}")
            else:
                st.sidebar.info("No audit logs yet")
    
    if st.sidebar.button("Logout"):
        Authentication.logout()
        st.rerun()
    
    # Main content
    st.title("🏢 Company Knowledge Agent BY SYED RAHMAN")
    st.markdown("Ask questions about your company documents and get AI-powered answers with citations!")
    
    # Document Upload Section
    if Authentication.check_permission("upload_docs"):
        st.header("📁 Upload Company Documents")
        
        uploaded_files = st.file_uploader(
            "Choose documents",
            type=['pdf', 'txt', 'csv'],
            accept_multiple_files=True,
            help="Upload PDF, TXT, or CSV files"
        )
        
        if uploaded_files:
            st.write(f"Selected {len(uploaded_files)} file(s) for processing")
            
            if st.button("Process Documents", type="primary"):
                with st.spinner("Processing documents..."):
                    all_documents = []
                    for uploaded_file in uploaded_files:
                        documents = document_processor.process_uploaded_file(uploaded_file)
                        all_documents.extend(documents)
                    
                    if all_documents:
                        success = vector_manager.create_vector_store(all_documents)
                        if success:
                            st.success("✅ Documents processed and added to knowledge base!")
                            
                            # Show enhanced stats
                            stats = vector_manager.get_search_stats()
                            st.info(f"📊 Knowledge base now has {stats['total_chunks']} searchable chunks")
                        else:
                            st.error("❌ Failed to process documents")
                    else:
                        st.warning("No documents were processed")
    
    # Query Section
    st.header("💬 Ask Questions")
    
    # Search options
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input(
            "Enter your question about company documents:", 
            placeholder="e.g., What is the vacation policy? How many remote work days?",
            key="query_input"
        )
    with col2:
        result_count = st.selectbox("Results", [2, 4, 6, 8], index=1, help="Number of document chunks to retrieve")
    
    if st.button("🔍 Get AI-Powered Answer", type="primary") and query:
        with st.spinner("🔍 Searching documents..."):
            # Search for relevant documents
            relevant_docs = vector_manager.search_documents(query, k=result_count)
            
            if relevant_docs:
                # Show search stats
                st.info(f"📈 Found {len(relevant_docs)} relevant document chunks")
                
                # Generate response using RAG
                rag_system = RAGSystem()
                response, sources = rag_system.generate_response(query, relevant_docs)
                
                # Display response
                st.subheader("🤖 AI Answer:")
                st.write(response)
                
                # Display sources
                st.subheader("📚 Sources:")
                for source in sources:
                    st.write(f"- {source}")
                
                # Display relevant document snippets
                with st.expander("🔍 View Retrieved Document Chunks", expanded=False):
                    for i, doc in enumerate(relevant_docs):
                        source = doc.metadata.get('source', 'Unknown')
                        doc_type = doc.metadata.get('type', 'Unknown')
                        
                        st.write(f"**Chunk {i+1}** | Source: `{source}` | Type: `{doc_type}`")
                        st.write(f"**Content:** {doc.page_content[:400]}..." if len(doc.page_content) > 400 else f"**Content:** {doc.page_content}")
                        st.divider()
            else:
                st.warning("❌ No relevant documents found. Please upload relevant documents first or try a different query.")
    
    # Enhanced Search Information
    with st.expander("ℹ️ About Our Search Technology"):
        st.markdown("""
        **Enhanced Semantic Search Features:**
        
        - 🔍 **Cosine Similarity**: More accurate semantic matching
        - 🎯 **Quality Filtering**: Automatically removes irrelevant results  
        - 📊 **Optimized Chunking**: Better context preservation
        - ⚡ **Performance Tuned**: Fast and accurate retrieval
        
        *This system retrieves the most relevant document chunks and uses AI to generate comprehensive answers.*
        """)
    
    # Audit Logs Section (for admin users)
    if Authentication.check_permission("view_audit"):
        st.header("📊 Audit Logs")
        
        logs = AuditLogger.get_audit_logs()
        if logs:
            st.write(f"**Total queries logged:** {len(logs)}")
            
            # Show latest logs with enhanced display
            for log in reversed(logs[-5:]):  # Show last 5 logs
                with st.expander(f"🗓️ {time.ctime(log['timestamp'])} | 👤 {log['username']} | ❓ {log['query'][:50]}..."):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**User:** {log['username']} ({log['department']})")
                        st.write(f"**Query:** {log['query']}")
                    with col2:
                        st.write(f"**Sources:** {', '.join(log['sources'])}")
                    st.write(f"**Response:** {log['response']}")
        else:
            st.info("No audit logs available yet. Questions you ask will appear here.")

def main():
    """Main application flow"""
    
    # Check authentication
    if not st.session_state.get("authenticated", False):
        login_section()
        st.title("🏢 Company Knowledge Agent")
        st.markdown("""
        ## Syed Rahmans welcomes you to Your Company's AI Knowledge Base
        This application allows you to:
        - 📁 Upload company documents (PDF, TXT, CSV)
        - 💬 Ask natural language questions  
        - 🔍 Get AI-powered answers with citations
        - 👥 Role-based access control
        - 📊 Audit logging for compliance
        
        **Please login using the sidebar to continue.**
        
        ### Demo Credentials:
        - **Admin**: `admin` / `admin123` (Full access)
        - **Employee**: `employee` / `employee123` (Upload & Query)  
        - **Viewer**: `viewer` / `viewer123` (Query only)
        
        ### 🚀 Enhanced Features:
        - **Better Search**: Cosine similarity with quality filtering
        - **Optimized Processing**: Smart document chunking
        - **Professional UI**: Clean, intuitive interface
        """)
    else:
        main_application()

if __name__ == "__main__":
    main()
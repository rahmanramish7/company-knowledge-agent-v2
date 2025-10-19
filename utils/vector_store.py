import chromadb
# FIXED: Use correct import path
# Try this import instead  
try:
    from langchain.schema import Document
except ImportError:
    from langchain_core.documents import Document
from config import Config
import streamlit as st

class VectorStoreManager:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=Config.VECTOR_DB_PATH)
        self.collection_name = "company_docs"
    def create_vector_store(self, documents: list, collection_name: str = "company_docs"):
        try:
            from utils.document_loader import DocumentProcessor
            processor = DocumentProcessor()
            split_docs = processor.split_documents(documents)
            
            # Handle collection creation/deletion properly
            try:
                # Try to delete existing collection
                self.client.delete_collection(self.collection_name)
                st.info("🔄 Clearing existing documents...")
            except:
                # Collection doesn't exist, that's fine
                pass
            
            # Create fresh collection
            self.collection = self.client.create_collection(self.collection_name)
            
            # Add documents
            for i, doc in enumerate(split_docs):
                self.collection.add(
                    documents=[doc.page_content],
                    metadatas=[doc.metadata],
                    ids=[f"doc_{i}"]
                )
            
            st.success(f"✅ Processed {len(split_docs)} document chunks")
            return True
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            return None
    
    def search_documents(self, query: str, k: int = 2, collection_name: str = "company_docs"):
        try:
            self.collection = self.client.get_collection(self.collection_name)
            results = self.collection.query(
                query_texts=[query],
                n_results=k
            )
            
            docs = []
            if results['documents'] and len(results['documents']) > 0:
                for i in range(len(results['documents'][0])):
                    docs.append(Document(
                        page_content=results['documents'][0][i],
                        metadata=results['metadatas'][0][i] if results['metadatas'] and i < len(results['metadatas'][0]) else {}
                    ))
            return docs
            
        except Exception as e:
            st.error(f"Search error: {str(e)}")
            return []
    
    def get_search_stats(self):
        """Get statistics about the vector store"""
        try:
            self.collection = self.client.get_collection(self.collection_name)
            count = self.collection.count()
            return {
                "total_chunks": count,
                "collection_name": self.collection_name
            }
        except:
            return {"total_chunks": 0, "collection_name": "Not available"}
    
    def clear_database(self):
        """Completely clear the database"""
        try:
            self.client.delete_collection(self.collection_name)
            st.success("✅ Database cleared successfully!")
            return True
        except Exception as e:
            st.error(f"Error clearing database: {str(e)}")
            return False
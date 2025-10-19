import os
import pandas as pd
from PyPDF2 import PdfReader
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List
import streamlit as st
import uuid

class DocumentProcessor:
    def __init__(self):
        # Enhanced chunking for better retrieval
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,  # Smaller chunks for better precision
            chunk_overlap=150,  # More overlap for context
            length_function=len,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
        )
    
    def load_pdf(self, file_path: str) -> List[Document]:
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            # Use original filename
            original_name = os.path.basename(file_path).replace('temp_', '')
            documents = [Document(
                page_content=text,
                metadata={
                    "source": original_name, 
                    "type": "pdf",
                    "pages": len(reader.pages)
                }
            )]
            return documents
        except Exception as e:
            st.error(f"Error loading PDF: {str(e)}")
            return []
    
    def load_txt(self, file_path: str) -> List[Document]:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            
            original_name = os.path.basename(file_path).replace('temp_', '')
            documents = [Document(
                page_content=text,
                metadata={
                    "source": original_name, 
                    "type": "txt",
                    "lines": text.count('\n') + 1
                }
            )]
            return documents
        except Exception as e:
            st.error(f"Error loading text file: {str(e)}")
            return []
    
    def load_csv(self, file_path: str) -> List[Document]:
        try:
            df = pd.read_csv(file_path)
            text = "CSV Data:\n"
            for index, row in df.iterrows():
                text += f"Row {index}: {dict(row)}\n"
            
            original_name = os.path.basename(file_path).replace('temp_', '')
            documents = [Document(
                page_content=text,
                metadata={
                    "source": original_name, 
                    "type": "csv",
                    "rows": len(df),
                    "columns": len(df.columns)
                }
            )]
            return documents
        except Exception as e:
            st.error(f"Error loading CSV: {str(e)}")
            return []
    
    def process_uploaded_file(self, uploaded_file) -> List[Document]:
        # Create unique temp file name
        unique_id = str(uuid.uuid4())[:8]
        file_path = f"temp_{unique_id}_{uploaded_file.name}"
        
        try:
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Load based on file type
            if uploaded_file.name.endswith('.pdf'):
                documents = self.load_pdf(file_path)
            elif uploaded_file.name.endswith('.txt'):
                documents = self.load_txt(file_path)
            elif uploaded_file.name.endswith('.csv'):
                documents = self.load_csv(file_path)
            else:
                st.error(f"Unsupported file type: {uploaded_file.name}")
                documents = []
            
            return documents
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            return []
        finally:
            # Always clean up temp file
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        return self.text_splitter.split_documents(documents)
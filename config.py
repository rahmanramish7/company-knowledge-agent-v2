import os

class Config:
    # Groq API - Use Streamlit secrets
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")  # Simple approach for Streamlit Cloud
    GROQ_MODEL = "llama-3.1-8b-instant"
    
    # Vector Database
    VECTOR_DB_PATH = "chroma_db"
    
    # App Settings
    UPLOAD_FOLDER = "data/uploads"
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'csv'}
    
    # Security
    SESSION_TIMEOUT = 1800

config = Config()
import os
import streamlit as st

class Config:
    # Groq API - EMPTY for GitHub
    GROQ_API_KEY = ""  # ← MUST BE EMPTY STRING
    GROQ_MODEL = "llama-3.1-8b-instant"
    
    # Vector Database
    VECTOR_DB_PATH = "chroma_db"
    
    # App Settings
    UPLOAD_FOLDER = "data/uploads"
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'csv'}
    
    # Security
    SESSION_TIMEOUT = 1800

config = Config()
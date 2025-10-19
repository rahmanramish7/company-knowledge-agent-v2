import streamlit as st
import bcrypt
import time
from typing import Dict, List

# User database
USERS_DB = {
    "admin": {
        "password_hash": bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()),
        "role": "admin",
        "department": "IT"
    },
    "employee": {
        "password_hash": bcrypt.hashpw("employee123".encode('utf-8'), bcrypt.gensalt()),
        "role": "user",
        "department": "HR"
    },
    "viewer": {
        "password_hash": bcrypt.hashpw("viewer123".encode('utf-8'), bcrypt.gensalt()),
        "role": "viewer",
        "department": "Marketing"
    }
}

# Role permissions
ROLE_PERMISSIONS = {
    "admin": ["upload_docs", "query", "view_audit", "manage_users"],
    "user": ["upload_docs", "query"],
    "viewer": ["query"]
}

class Authentication:
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash)
    
    @staticmethod
    def login(username: str, password: str) -> bool:
        if username in USERS_DB:
            user_data = USERS_DB[username]
            if Authentication.verify_password(password, user_data["password_hash"]):
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.session_state["role"] = user_data["role"]
                st.session_state["department"] = user_data["department"]
                st.session_state["login_time"] = time.time()
                return True
        return False
    
    @staticmethod
    def logout():
        for key in ["authenticated", "username", "role", "department", "login_time"]:
            if key in st.session_state:
                del st.session_state[key]
    
    @staticmethod
    def check_permission(permission: str) -> bool:
        if not st.session_state.get("authenticated", False):
            return False
        user_role = st.session_state.get("role", "viewer")
        return permission in ROLE_PERMISSIONS.get(user_role, [])
    
    @staticmethod
    def check_session_timeout():
        if "login_time" in st.session_state:
            if time.time() - st.session_state["login_time"] > 1800:
                Authentication.logout()
                st.error("Session timed out. Please login again.")
                return True
        return False

class AuditLogger:
    @staticmethod
    def log_query(username: str, query: str, response: str, sources: List[str]):
        if "audit_logs" not in st.session_state:
            st.session_state["audit_logs"] = []
        
        log_entry = {
            "timestamp": time.time(),
            "username": username,
            "query": query,
            "response": response[:200] + "..." if len(response) > 200 else response,
            "sources": sources,
            "department": st.session_state.get("department", "Unknown")
        }
        st.session_state["audit_logs"].append(log_entry)
    
    @staticmethod
    def get_audit_logs():
        return st.session_state.get("audit_logs", [])
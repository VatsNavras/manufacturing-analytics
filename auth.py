# auth.py - Authentication module
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import hashlib
from datetime import datetime, timedelta

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash: str, provided_password: str) -> bool:
    """Verify password against stored hash"""
    return stored_hash == hash_password(provided_password)

def get_sheets_client():
    """Initialize and return authenticated Google Sheets client"""
    try:
        credentials_dict = st.secrets.get("google_credentials")
        if not credentials_dict:
            import json
            with open("credentials.json") as f:
                credentials_dict = json.load(f)
        
        creds = Credentials.from_service_account_info(
            credentials_dict,
            scopes=SCOPES
        )
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Failed to authenticate: {e}")
        return None

def load_user_credentials():
    """Load user credentials from Google Sheet"""
    try:
        client = get_sheets_client()
        if not client:
            return None
        
        sheet = client.open("Manufacturing_Analytics_Credentials").worksheet("Users")
        users = sheet.get_all_records()
        return users
    except Exception as e:
        st.warning(f"Could not load credentials: {e}")
        return None

def login(username: str, password: str) -> bool:
    """Authenticate user"""
    if not username or not password:
        return False
    
    try:
        users = load_user_credentials()
        
        if not users:
            return username == "admin" and password == "demo123"
        
        for user in users:
            if user.get("Username", "").strip().lower() == username.lower():
                stored_hash = user.get("PasswordHash", "")
                if verify_password(stored_hash, password):
                    log_login(username, success=True)
                    return True
                else:
                    log_login(username, success=False)
                    return False
        
        log_login(username, success=False, error="User not found")
        return False
    except Exception as e:
        st.error(f"Authentication error: {e}")
        return False

def log_login(username: str, success: bool, error: str = ""):
    """Log authentication attempts"""
    try:
        client = get_sheets_client()
        if not client:
            return
        
        sheet = client.open("Manufacturing_Analytics_Credentials").worksheet("AuditLog")
        sheet.append_row([
            datetime.now().isoformat(),
            username,
            "SUCCESS" if success else "FAILED",
            error,
            "Web"
        ])
    except:
        pass

def initialize_session():
    """Initialize session state variables"""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "login_time" not in st.session_state:
        st.session_state.login_time = None
    if "session_timeout" not in st.session_state:
        st.session_state.session_timeout = timedelta(hours=8)

def is_session_valid():
    """Check if current session is still valid"""
    if not st.session_state.logged_in:
        return False
    
    if st.session_state.login_time:
        elapsed = datetime.now() - st.session_state.login_time
        if elapsed > st.session_state.session_timeout:
            st.session_state.logged_in = False
            st.warning("Session expired. Please log in again.")
            return False
    
    return True

def set_user_authenticated(username: str):
    """Set user as authenticated in session"""
    st.session_state.logged_in = True
    st.session_state.username = username
    st.session_state.login_time = datetime.now()

def logout():
    """Log out current user"""
    username = st.session_state.username
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.login_time = None
    
    try:
        client = get_sheets_client()
        if client:
            sheet = client.open("Manufacturing_Analytics_Credentials").worksheet("AuditLog")
            sheet.append_row([
                datetime.now().isoformat(),
                username,
                "LOGOUT",
                "",
                "Web"
            ])
    except:
        pass
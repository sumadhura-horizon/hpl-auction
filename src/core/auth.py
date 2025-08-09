"""
Authentication utilities for the auction system.
"""
import streamlit as st
import hashlib
import os
from pathlib import Path
from typing import Optional, List, Tuple
from .models import User
from .database import DatabaseManager


class AuthManager:
    """Manages user authentication and session state."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.creds_file = Path("creds.txt")
        self._init_session_state()
    
    def _init_session_state(self) -> None:
        """Initialize session state variables."""
        if "user" not in st.session_state:
            st.session_state.user = None
        if "logged_in" not in st.session_state:
            st.session_state.logged_in = False
    
    def _hash_password(self, password: str) -> str:
        """Hash password for secure comparison."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _load_credentials(self) -> List[Tuple[str, str, str]]:
        """Load credentials from file."""
        credentials = []
        
        if not self.creds_file.exists():
            # Create default credentials file if it doesn't exist
            self.creds_file.write_text("# Auction System Credentials\n# Format: username:password:role\n# WARNING: Keep this file secure and never commit to version control\nauctioneer:Sum@dhura@123@HBL:admin\n")
        
        try:
            with open(self.creds_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split(':')
                        if len(parts) >= 3:
                            username, password, role = parts[0], parts[1], parts[2]
                            credentials.append((username, password, role))
        except Exception as e:
            st.error(f"Error reading credentials file: {e}")
        
        return credentials
    
    def _authenticate_with_file(self, username: str, password: str) -> Optional[User]:
        """Authenticate user against credentials file."""
        credentials = self._load_credentials()
        
        for cred_username, cred_password, cred_role in credentials:
            if cred_username == username and cred_password == password:
                return User(
                    id=1,  # File-based auth doesn't have IDs
                    username=cred_username,
                    password="[PROTECTED]",  # Don't store actual password
                    role=cred_role
                )
        
        return None
    
    def login(self, username: str, password: str) -> bool:
        """Attempt to log in user."""
        if not username or not password:
            return False
        
        # Try file-based authentication first
        user = self._authenticate_with_file(username, password)
        
        # Fallback to database authentication if file auth fails
        if not user:
            user = self.db_manager.authenticate_user(username, password)
        
        if user:
            st.session_state.user = user
            st.session_state.logged_in = True
            return True
        return False
    
    def logout(self) -> None:
        """Log out current user."""
        st.session_state.user = None
        st.session_state.logged_in = False
    
    def is_logged_in(self) -> bool:
        """Check if user is logged in."""
        return st.session_state.logged_in and st.session_state.user is not None
    
    def get_current_user(self) -> Optional[User]:
        """Get current logged in user."""
        return st.session_state.user if self.is_logged_in() else None
    
    def get_user_role(self) -> Optional[str]:
        """Get current user's role."""
        user = self.get_current_user()
        return user.role if user else None
    
    def has_admin_access(self) -> bool:
        """Check if current user has admin access."""
        role = self.get_user_role()
        return role in ["admin", "auctioneer"]

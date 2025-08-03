"""
Authentication utilities for the auction system.
"""
import streamlit as st
from typing import Optional
from .models import User
from .database import DatabaseManager


class AuthManager:
    """Manages user authentication and session state."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._init_session_state()
    
    def _init_session_state(self) -> None:
        """Initialize session state variables."""
        if "user" not in st.session_state:
            st.session_state.user = None
        if "logged_in" not in st.session_state:
            st.session_state.logged_in = False
    
    def login(self, username: str, password: str) -> bool:
        """Attempt to log in user."""
        if not username or not password:
            return False
        
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

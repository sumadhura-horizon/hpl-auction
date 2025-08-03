"""
Badminton League Auction System - Main Application

A comprehensive auction management system built with Streamlit.
Features user authentication, player management, team budgets, and real-time auction updates.
"""

import streamlit as st
import logging
import sys
import traceback
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import custom modules
from src.core.database import DatabaseManager
from src.core.auth import AuthManager
from src.utils.file_manager import FileUploadManager
from src.ui.ui_manager import UIManager
from config.settings import STREAMLIT_CONFIG, LOG_LEVEL, LOG_FORMAT

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Badminton League Auction System",
    page_icon="🏸",
    layout="wide",
    initial_sidebar_state="expanded"
)


class AuctionApp:
    """Main application class for the auction system."""
    
    def __init__(self):
        """Initialize the application components."""
        try:
            self.db_manager = DatabaseManager()
            self.auth_manager = AuthManager(self.db_manager)
            self.file_manager = FileUploadManager(self.db_manager)
            self.ui_manager = UIManager(self.auth_manager, self.db_manager, self.file_manager)
            
            # Load initial data if needed
            self.file_manager.load_initial_data_from_csv()
            
        except Exception as e:
            logger.error(f"Error initializing application: {e}")
            st.error(f"Failed to initialize application: {e}")
            st.stop()
    
    def run(self):
        """Run the main application."""
        try:
            # Render UI components
            self.ui_manager.render_sidebar()
            self._render_main_content()
            
        except Exception as e:
            logger.error(f"Error running application: {e}")
            st.error(f"Application error: {e}")
            with st.expander("Error Details"):
                st.code(traceback.format_exc())
    
    def _render_main_content(self):
        """Render the main content area."""
        # Header
        st.markdown(
            "<h1 style='text-align: center; color: #4CAF50;'>🏸 Badminton League Auction</h1>", 
            unsafe_allow_html=True
        )
        
        # Check if user is logged in
        if not self.auth_manager.is_logged_in():
            self._render_welcome_page()
            return
        
        # Load data
        try:
            players_df, teams_df = self.ui_manager.load_data_with_cache()
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            st.error("Failed to load data. Please try refreshing.")
            return
        
        # Render tabs based on user role
        self._render_tabs(players_df, teams_df)
    
    def _render_welcome_page(self):
        """Render welcome page for non-logged-in users."""
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            ### Welcome to the Badminton League Auction System! 🏸
            
            This platform allows you to:
            - 👥 **Manage Players**: View and auction players
            - 🏆 **Track Teams**: Monitor team rosters and budgets
            - 💰 **Handle Auctions**: Conduct live player auctions
            - 📊 **Generate Reports**: Download player and team data
            
            **Please log in to access the auction system.**
            
            #### User Roles:
            - **Admin**: Full system access including data management
            - **Auctioneer**: Can conduct auctions and manage player assignments
            - **Owner**: View-only access to teams and players
            """)
        
        # Display some basic stats if data is available
        try:
            players_df = self.db_manager.load_players_dataframe()
            teams_df = self.db_manager.load_teams_dataframe()
            
            if not players_df.empty and not teams_df.empty:
                st.markdown("---")
                st.subheader("📊 Quick Stats")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Players", len(players_df))
                
                with col2:
                    st.metric("Total Teams", len(teams_df))
                
                with col3:
                    auctioned_count = len(players_df[players_df["owner"].notnull()])
                    st.metric("Players Auctioned", auctioned_count)
                
                with col4:
                    unauctioned_count = len(players_df[players_df["owner"].isnull()])
                    st.metric("Players Available", unauctioned_count)
                    
        except Exception as e:
            logger.error(f"Error displaying stats: {e}")
    
    def _render_tabs(self, players_df, teams_df):
        """Render tabs based on user role."""
        user_role = self.auth_manager.get_user_role()
        
        if user_role in ["admin", "auctioneer"]:
            tab_names = [
                "🎯 Update Auction",
                "🏆 Teams", 
                "👤 Available Players",
                "✅ Auctioned Players",
                "↩️ Undo Auction",
                "📋 All Players"
            ]
            tabs = st.tabs(tab_names)
            
            with tabs[0]:
                self.ui_manager.render_update_auction_tab(players_df, teams_df)
            
            with tabs[1]:
                self.ui_manager.render_teams_tab(players_df, teams_df)
            
            with tabs[2]:
                self.ui_manager.render_players_list_tab(players_df, "unauctioned")
            
            with tabs[3]:
                self.ui_manager.render_players_list_tab(players_df, "auctioned")
            
            with tabs[4]:
                self.ui_manager.render_undo_auction_tab(players_df)
            
            with tabs[5]:
                self.ui_manager.render_players_list_tab(players_df, "all")
        
        else:  # owner or other roles
            tab_names = [
                "🏆 Teams",
                "👤 Available Players", 
                "✅ Auctioned Players",
                "📋 All Players"
            ]
            tabs = st.tabs(tab_names)
            
            with tabs[0]:
                self.ui_manager.render_teams_tab(players_df, teams_df)
            
            with tabs[1]:
                self.ui_manager.render_players_list_tab(players_df, "unauctioned")
            
            with tabs[2]:
                self.ui_manager.render_players_list_tab(players_df, "auctioned")
            
            with tabs[3]:
                self.ui_manager.render_players_list_tab(players_df, "all")


def main():
    """Main entry point of the application."""
    try:
        app = AuctionApp()
        app.run()
    except Exception as e:
        logger.critical(f"Critical error in main: {e}")
        st.error("A critical error occurred. Please contact the administrator.")
        st.code(traceback.format_exc())


if __name__ == "__main__":
    main()

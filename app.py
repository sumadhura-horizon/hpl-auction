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
            # Check if we should show the login form (default behavior)
            show_login = True
            
            # Render UI components
            self.ui_manager.render_sidebar(show_login_form=show_login)
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
            self._render_public_content()
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
    
    def _render_public_content(self):
        """Render public content for non-logged-in users (captains, observers)."""
        # Add main refresh button for public users
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown("👑 **Public Observer Mode** - Watch the live auction without logging in")
        with col2:
            if st.button("🔄 Refresh All", help="Refresh all auction data", key="main_public_refresh", type="primary"):
                st.rerun()
        
        # Add navigation tabs for public users
        tab_names = ["📺 Live Auction", "🏆 Teams", "👤 Players", "ℹ️ About"]
        tabs = st.tabs(tab_names)
        
        try:
            # Load data for public view
            players_df = self.db_manager.load_players_dataframe()
            teams_df = self.db_manager.load_teams_dataframe()
            
            with tabs[0]:
                if not players_df.empty and not teams_df.empty:
                    # Show the observer interface without login
                    self.ui_manager.render_observer_interface(players_df, teams_df)
                else:
                    st.warning("No auction data available yet.")
            
            with tabs[1]:
                st.markdown("### 🏆 Team Overview")
                if not players_df.empty and not teams_df.empty:
                    self.ui_manager.render_teams_tab(players_df, teams_df)
                else:
                    st.info("Team information will appear here once the auction begins.")
            
            with tabs[2]:
                st.markdown("### 👤 Player Information")
                if not players_df.empty:
                    # Create sub-tabs for different player views
                    player_tabs = st.tabs(["Available", "Auctioned", "All Players"])
                    
                    with player_tabs[0]:
                        self.ui_manager.render_players_list_tab(players_df, "unauctioned")
                    
                    with player_tabs[1]:
                        self.ui_manager.render_players_list_tab(players_df, "auctioned")
                    
                    with player_tabs[2]:
                        self.ui_manager.render_players_list_tab(players_df, "all")
                else:
                    st.info("Player information will appear here once data is loaded.")
            
            with tabs[3]:
                self._render_about_section(players_df, teams_df)
                
        except Exception as e:
            logger.error(f"Error loading public content: {e}")
            st.error("Unable to load auction data. Please refresh the page.")
    
    def _render_about_section(self, players_df, teams_df):
        """Render about section with system info."""
        st.markdown("### Welcome to the Badminton League Auction System! 🏸")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            #### 👑 For Captains & Team Observers
            
            This public interface allows you to:
            - 📺 **Watch Live Auction**: See current player being auctioned in real-time
            - 🏆 **Monitor Teams**: Track team rosters, budgets, and player counts
            - 👤 **View Players**: Browse available and auctioned players with details
            - 💰 **Budget Tracking**: See remaining budgets and maximum bids per team
            
            **🔄 Auto-Refresh**: The page updates automatically when auctioneers make changes.
            
            ---
            
            #### 🔐 For Auctioneers & Admins
            **Please log in using the sidebar** to access auction management features.
            
            **User Roles:**
            - **Admin**: Full system access including data management
            - **Auctioneer**: Conduct auctions and manage player assignments  
            - **Owner**: View-only access to teams and players
            """)
        
        with col2:
            if not players_df.empty and not teams_df.empty:
                st.markdown("#### 📊 Quick Stats")
                
                # Auction progress metrics
                total_players = len(players_df)
                auctioned_count = len(players_df[players_df["owner"].notnull()])
                unauctioned_count = total_players - auctioned_count
                
                st.metric("Total Players", total_players)
                st.metric("Auctioned", auctioned_count)
                st.metric("Available", unauctioned_count)
                st.metric("Teams", len(teams_df))
                
                # Progress bar
                if total_players > 0:
                    progress = auctioned_count / total_players
                    st.progress(progress, f"Auction Progress: {progress:.1%}")
            else:
                st.info("📊 Stats will appear once auction data is loaded.")
    
    def _render_tabs(self, players_df, teams_df):
        """Render tabs based on user role."""
        user_role = self.auth_manager.get_user_role()
        
        if user_role in ["admin", "auctioneer"]:
            tab_names = [
                "🎯 Update Auction",
                "👑 Captain Assignment",
                "🏆 Teams", 
                "👤 Available Players",
                "✅ Auctioned Players",
                "↩️ Undo Auction",
                "📋 All Players",
                "📤 Player Management",
                "📺 Observer View"
            ]
            tabs = st.tabs(tab_names)
            
            with tabs[0]:
                self.ui_manager.render_update_auction_tab(players_df, teams_df)
            
            with tabs[1]:
                self.ui_manager.render_captain_assignment_tab(players_df, teams_df)
            
            with tabs[2]:
                self.ui_manager.render_teams_tab(players_df, teams_df)
            
            with tabs[3]:
                self.ui_manager.render_players_list_tab(players_df, "unauctioned")
            
            with tabs[4]:
                self.ui_manager.render_players_list_tab(players_df, "auctioned")
            
            with tabs[5]:
                self.ui_manager.render_undo_auction_tab(players_df)
            
            with tabs[6]:
                self.ui_manager.render_players_list_tab(players_df, "all")
            
            with tabs[7]:
                self.ui_manager.render_player_upload_tab()
            
            with tabs[8]:
                self.ui_manager.render_observer_interface(players_df, teams_df)
        
        else:  # owner or other roles
            tab_names = [
                "📺 Observer View",
                "🏆 Teams",
                "👤 Available Players", 
                "✅ Auctioned Players",
                "📋 All Players"
            ]
            tabs = st.tabs(tab_names)
            
            with tabs[0]:
                self.ui_manager.render_observer_interface(players_df, teams_df)
            
            with tabs[1]:
                self.ui_manager.render_teams_tab(players_df, teams_df)
            
            with tabs[2]:
                self.ui_manager.render_players_list_tab(players_df, "unauctioned")
            
            with tabs[3]:
                self.ui_manager.render_players_list_tab(players_df, "auctioned")
            
            with tabs[4]:
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

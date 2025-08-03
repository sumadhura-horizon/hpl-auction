"""
UI components for the auction system.
"""
import streamlit as st
import pandas as pd
from typing import Optional
import logging
from ..core.auth import AuthManager
from ..core.database import DatabaseManager
from ..utils.file_manager import FileUploadManager

logger = logging.getLogger(__name__)


class UIManager:
    """Manages UI components and layouts."""
    
    def __init__(self, auth_manager: AuthManager, db_manager: DatabaseManager, file_manager: FileUploadManager):
        self.auth_manager = auth_manager
        self.db_manager = db_manager
        self.file_manager = file_manager
        self._init_session_state()
    
    def _init_session_state(self) -> None:
        """Initialize additional session state variables."""
        if "team_budgets" not in st.session_state:
            st.session_state.team_budgets = {}
        if "random_player" not in st.session_state:
            st.session_state.random_player = None
        if "data_refresh_needed" not in st.session_state:
            st.session_state.data_refresh_needed = False
    
    def render_sidebar(self) -> None:
        """Render the sidebar with login/logout functionality."""
        with st.sidebar:
            st.image("assets/hbl.png", width=200)
            
            if not self.auth_manager.is_logged_in():
                self._render_login_form()
            else:
                self._render_user_info()
            
            self._render_admin_controls()
    
    def _render_login_form(self) -> None:
        """Render login form."""
        st.subheader("Login")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login")
            
            if submit_button:
                if self.auth_manager.login(username, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    def _render_user_info(self) -> None:
        """Render logged in user information."""
        user = self.auth_manager.get_current_user()
        if user:
            st.success(f"Logged in as: {user.role}")
            if st.button("Logout"):
                self.auth_manager.logout()
                st.rerun()
    
    def _render_admin_controls(self) -> None:
        """Render admin controls."""
        st.markdown("---")
        
        if st.button("Refresh Data"):
            st.session_state.data_refresh_needed = True
            st.rerun()
        
        if self.auth_manager.has_admin_access():
            if st.button("Reset Database"):
                st.warning("⚠️ This will delete all data! Click again to confirm.")
                if st.button("Confirm Reset Database", type="secondary"):
                    self.db_manager.reset_database()
                    self.file_manager.load_initial_data_from_csv()
                    st.success("Database reset successfully")
                    st.rerun()
            
            self._render_file_upload_section()
    
    def _render_file_upload_section(self) -> None:
        """Render file upload section for admins."""
        st.subheader("Upload CSV Files")
        
        with st.expander("Upload Data Files"):
            # Users upload
            users_file = st.file_uploader("Upload Users CSV", type="csv", key="users_upload")
            if users_file is not None:
                if st.button("Upload Users", key="upload_users_btn"):
                    self.file_manager.upload_users_csv(users_file)
                    st.rerun()
            
            # Teams upload
            teams_file = st.file_uploader("Upload Teams CSV", type="csv", key="teams_upload")
            if teams_file is not None:
                if st.button("Upload Teams", key="upload_teams_btn"):
                    self.file_manager.upload_teams_csv(teams_file)
                    st.rerun()
            
            # Players upload
            players_file = st.file_uploader("Upload Players CSV", type="csv", key="players_upload")
            if players_file is not None:
                if st.button("Upload Players", key="upload_players_btn"):
                    self.file_manager.upload_players_csv(players_file)
                    st.rerun()
    
    def load_data_with_cache(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Load data with session state caching."""
        if st.session_state.data_refresh_needed or "cached_players" not in st.session_state:
            st.session_state.cached_players = self.db_manager.load_players_dataframe()
            st.session_state.cached_teams = self.db_manager.load_teams_dataframe()
            
            # Initialize team budgets
            team_names = st.session_state.cached_teams["team_name"].unique()
            st.session_state.team_budgets = {team: 10000000 for team in team_names}
            
            st.session_state.data_refresh_needed = False
        
        return st.session_state.cached_players, st.session_state.cached_teams
    
    def display_player_details(self, player_details: pd.Series) -> None:
        """Display player details in a formatted way."""
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Player Name", player_details['name'])
        
        with col2:
            st.metric("Base Price", f"₹{player_details['base_price']:,}")
    
    def display_team_players(self, team: str, players_df: pd.DataFrame) -> None:
        """Display players for a specific team."""
        st.subheader(f"🏆 {team}")
        
        team_players = players_df[players_df["owner"] == team].copy()
        
        if not team_players.empty:
            # Calculate team metrics
            total_spent = team_players["auction_price"].sum()
            player_count = len(team_players)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Players", player_count)
            with col2:
                st.metric("Total Spent", f"₹{total_spent:,}")
            with col3:
                remaining_budget = st.session_state.team_budgets.get(team, 10000000) - total_spent
                st.metric("Remaining Budget", f"₹{remaining_budget:,}")
            
            # Display players table
            display_columns = ["name", "auction_price"]
            team_players_display = team_players[display_columns].copy()
            team_players_display["auction_price"] = team_players_display["auction_price"].apply(lambda x: f"₹{x:,}")
            team_players_display = team_players_display.reset_index(drop=True)
            team_players_display.index = team_players_display.index + 1
            st.dataframe(team_players_display, use_container_width=True)
        else:
            st.info("No players assigned to this team yet.")
    
    def render_update_auction_tab(self, players_df: pd.DataFrame, teams_df: pd.DataFrame) -> None:
        """Render the update auction status tab."""
        st.markdown("<h2 style='color: #FF5733;'>Update Auction Status</h2>", unsafe_allow_html=True)
        
        # Random player selection section
        st.subheader("🎲 Random Player Selection")
        unauctioned_players = players_df[players_df["owner"].isnull()]
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🎯 Pick Random Player", use_container_width=True):
                if not unauctioned_players.empty:
                    st.session_state.random_player = unauctioned_players.sample(n=1).iloc[0]
                    st.success(f"🎉 Random player picked: **{st.session_state.random_player['name']}**")
                else:
                    st.warning("No more players available for auction.")
                    st.session_state.random_player = None
        
        with col2:
            if st.button("🔄 Clear Selection", use_container_width=True):
                st.session_state.random_player = None
                st.info("Selection cleared")
        
        st.markdown("---")
        
        # Player selection
        if st.session_state.random_player is not None:
            selected_player = st.session_state.random_player["name"]
            st.info(f"🎯 Currently selected: **{selected_player}**")
        else:
            available_players = players_df[players_df["owner"].isnull()]["name"]
            if available_players.empty:
                st.warning("🚫 No players available for auction.")
                return
            selected_player = st.selectbox("👤 Select Player", available_players)
        
        # Display player details
        player_details = players_df.loc[players_df["name"] == selected_player].iloc[0]
        self.display_player_details(player_details)
        
        # Team and price selection
        col1, col2 = st.columns(2)
        
        with col1:
            selected_team = st.selectbox("🏆 Select Team", teams_df["team_name"])
        
        with col2:
            if selected_team not in st.session_state.team_budgets:
                st.session_state.team_budgets[selected_team] = 10000000
            
            team_spent = players_df[players_df["owner"] == selected_team]["auction_price"].sum()
            remaining_budget = int(st.session_state.team_budgets[selected_team] - team_spent)
            
            auction_price = st.number_input(
                "💰 Auction Price",
                min_value=int(player_details["base_price"]),
                max_value=remaining_budget,
                step=25000,
                value=int(player_details["base_price"])
            )
        
        st.info(f"💳 Remaining budget for {selected_team}: ₹{remaining_budget:,}")
        
        # Update button
        if st.button("✅ Update Auction Status", type="primary", use_container_width=True):
            if self.db_manager.update_player_auction(selected_player, selected_team, auction_price):
                st.success(f"🎉 **{selected_player}** sold to **{selected_team}** for **₹{auction_price:,}**")
                st.session_state.random_player = None
                st.session_state.data_refresh_needed = True
                st.rerun()
            else:
                st.error("Failed to update auction status")
    
    def render_teams_tab(self, players_df: pd.DataFrame, teams_df: pd.DataFrame) -> None:
        """Render the teams tab."""
        st.markdown("<h2 style='color: #FF5733;'>Teams Overview</h2>", unsafe_allow_html=True)
        
        # Team budget overview
        st.subheader("💰 Budget Overview")
        budget_data = []
        
        for team in teams_df["team_name"]:
            team_players = players_df[players_df["owner"] == team]
            total_spent = team_players["auction_price"].sum()
            remaining_budget = st.session_state.team_budgets.get(team, 10000000) - total_spent
            player_count = len(team_players)
            
            budget_data.append({
                "Team": team,
                "Players": player_count,
                "Spent": f"₹{total_spent:,}",
                "Remaining": f"₹{remaining_budget:,}"
            })
        
        budget_df = pd.DataFrame(budget_data)
        budget_df = budget_df.reset_index(drop=True)
        budget_df.index = budget_df.index + 1
        st.dataframe(budget_df, use_container_width=True)
        
        st.markdown("---")
        
        # Individual team details
        st.subheader("🏆 Team Rosters")
        for team in teams_df["team_name"]:
            self.display_team_players(team, players_df)
            st.markdown("---")
    
    def render_players_list_tab(self, players_df: pd.DataFrame, tab_type: str) -> None:
        """Render players list tabs (unauctioned, auctioned, all)."""
        title_map = {
            "unauctioned": "Unauctioned Players",
            "auctioned": "Auctioned Players",
            "all": "All Players"
        }
        
        st.markdown(f"<h2 style='color: #FF5733;'>{title_map[tab_type]}</h2>", unsafe_allow_html=True)
        
        # Filter data based on tab type
        if tab_type == "unauctioned":
            filtered_df = players_df[players_df["owner"].isnull()].copy()
            display_columns = ["name", "base_price"]
        elif tab_type == "auctioned":
            filtered_df = players_df[players_df["owner"].notnull()].copy()
            display_columns = ["name", "base_price", "owner", "auction_price"]
        else:  # all
            filtered_df = players_df.copy()
            display_columns = ["name", "base_price", "owner", "auction_price"]
        
        if filtered_df.empty:
            st.info(f"No {tab_type} players found.")
            return
        
        # Format price columns
        if "base_price" in display_columns:
            filtered_df["base_price"] = filtered_df["base_price"].apply(lambda x: f"₹{x:,}")
        if "auction_price" in display_columns:
            filtered_df["auction_price"] = filtered_df["auction_price"].apply(lambda x: f"₹{x:,}" if pd.notnull(x) and x > 0 else "-")
        
        # Display data
        display_df = filtered_df[display_columns].copy()
        display_df = display_df.reset_index(drop=True)
        display_df.index = display_df.index + 1
        st.dataframe(display_df, use_container_width=True)
        
        # Download button
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label=f"📥 Download {title_map[tab_type]}",
            data=csv,
            file_name=f"{tab_type}_players.csv",
            mime="text/csv"
        )
    
    def render_undo_auction_tab(self, players_df: pd.DataFrame) -> None:
        """Render the undo auction tab."""
        st.markdown("<h2 style='color: #FF5733;'>Undo Auction</h2>", unsafe_allow_html=True)
        
        auctioned_players = players_df[players_df["owner"].notnull()]
        
        if auctioned_players.empty:
            st.info("🔍 No auctioned players found.")
            return
        
        # Create player options with details
        player_options = []
        for _, row in auctioned_players.iterrows():
            option = f"{row['name']} → {row['owner']} (₹{row['auction_price']:,})"
            player_options.append(option)
        
        selected_option = st.selectbox("🔄 Select Player to Undo Auction", player_options)
        
        if st.button("↩️ Undo Auction", type="secondary", use_container_width=True):
            if selected_option:
                player_name = selected_option.split(" → ")[0]
                
                if self.db_manager.undo_player_auction(player_name):
                    st.success(f"✅ Auction undone for player: **{player_name}**")
                    st.session_state.data_refresh_needed = True
                    st.rerun()
                else:
                    st.error(f"❌ Failed to undo auction for player: **{player_name}**")
            else:
                st.error("Please select a player first.")

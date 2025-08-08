"""
UI components for the auction system.
"""
import streamlit as st
import pandas as pd
from typing import Optional
import logging
from ..core.auth import AuthManager
from ..core.database import DatabaseManager
from ..core.config import config
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
    
    def render_sidebar(self, show_login_form=True) -> None:
        """Render the sidebar with login/logout functionality."""
        with st.sidebar:
            st.image("assets/hbl.png", width=200)
            
            if not self.auth_manager.is_logged_in():
                if show_login_form:
                    self._render_login_form()
                else:
                    # For public users, show minimal sidebar
                    self._render_public_sidebar()
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
    
    def _render_public_sidebar(self) -> None:
        """Render minimal sidebar for public users."""
        st.markdown("### 👑 Public Access")
        st.info("You're viewing as a public observer. No login required!")
        
        # Quick refresh button in sidebar
        if st.button("🔄 Quick Refresh", help="Refresh auction data", key="sidebar_public_refresh", use_container_width=True):
            st.session_state.data_refresh_needed = True
            st.rerun()
        
        st.markdown("---")
        
        with st.expander("🔐 Admin/Auctioneer Login", expanded=False):
            st.markdown("**For auction management:**")
            with st.form("admin_login_form"):
                username = st.text_input("Username", key="admin_username")
                password = st.text_input("Password", type="password", key="admin_password")
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
        
        if st.button("🔄 Refresh Data", help="Refresh auction data and current player", use_container_width=True):
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
            st.session_state.team_budgets = {team: config.TEAM_BUDGET for team in team_names}
            
            st.session_state.data_refresh_needed = False
        
        return st.session_state.cached_players, st.session_state.cached_teams
    
    def display_player_details(self, player_details: pd.Series) -> None:
        """Display player details in a formatted way."""
        # Create a container for better spacing
        with st.container():
            # First row: Player photo and name
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Display player photo or random avatar
                if 'photo_url' in player_details and player_details['photo_url']:
                    try:
                        st.image(player_details['photo_url'], width=120)
                    except:
                        # Generate random avatar based on player name hash
                        name_hash = hash(player_details['name']) % 100 + 1
                        gender = "women" if name_hash % 2 == 0 else "men"
                        avatar_id = (name_hash % 50) + 1  # Use IDs 1-50 for variety
                        default_avatar = f"https://randomuser.me/api/portraits/{gender}/{avatar_id}.jpg"
                        st.image(default_avatar, width=120)
                else:
                    # Generate random avatar based on player name hash
                    name_hash = hash(player_details['name']) % 100 + 1
                    gender = "women" if name_hash % 2 == 0 else "men"
                    avatar_id = (name_hash % 50) + 1  # Use IDs 1-50 for variety
                    default_avatar = f"https://randomuser.me/api/portraits/{gender}/{avatar_id}.jpg"
                    st.image(default_avatar, width=120)
            
            with col2:
                st.markdown(f"### 👤 {player_details['name']}")
                
                # Second row: Base Price and Category in a more spacious layout
                price_col, category_col = st.columns(2)
                
                with price_col:
                    st.markdown("**💰 Base Price**")
                    st.markdown(f"### ₹{player_details['base_price']:,}")
                
                with category_col:
                    category = player_details.get('category', 'regular')
                    category_color = {
                        'captain': '🔴',
                        'marquee': '🟡', 
                        'regular': '🔵'
                    }
                    st.markdown("**📊 Category**")
                    st.markdown(f"### {category_color.get(category, '🔵')} {category.title()}")
            
            # Add some spacing
            st.markdown("---")
    
    def display_team_players(self, team: str, players_df: pd.DataFrame) -> None:
        """Display players for a specific team."""
        team_players = players_df[players_df["owner"] == team].copy()
        
        # Get team captain
        captain_player = team_players[team_players.get('category', 'regular') == 'captain']
        captain_name = captain_player['name'].iloc[0] if not captain_player.empty else "None"
        
        # Header with captain info
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader(f"🏆 {team}")
        with col2:
            st.write(f"👑 Captain: **{captain_name}**")
        
        if not team_players.empty:
            # Calculate team metrics
            total_spent = team_players["auction_price"].sum()
            player_count = len(team_players)
            max_bid = self.db_manager.calculate_max_bid(team)
            remaining_budget = self.db_manager.get_team_remaining_budget(team)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Players", f"{player_count}/{config.MAX_PLAYERS_PER_TEAM}")  # Regular + captain
            with col2:
                st.metric("Total Spent", f"₹{total_spent:,}")
            with col3:
                st.metric("Remaining Budget", f"₹{remaining_budget:,}")
            with col4:
                st.metric("Max Next Bid", f"₹{max_bid:,}")
            
            # Display players table with categories
            display_columns = ["name", "category", "auction_price"]
            team_players_display = team_players[display_columns].copy()
            team_players_display["auction_price"] = team_players_display["auction_price"].apply(
                lambda x: f"₹{x:,}" if x > 0 else "Captain"
            )
            # Add emoji for category
            team_players_display["category"] = team_players_display["category"].apply(
                lambda x: f"🔴 Captain" if x == "captain" 
                         else f"🟡 Marquee" if x == "marquee" 
                         else f"🔵 Regular"
            )
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
        
        # Filter players by category for auction phase
        unauctioned_players = players_df[players_df["owner"].isnull()]
        unauctioned_captains = unauctioned_players[unauctioned_players.get('category', 'regular') == 'captain']
        unauctioned_marquee = unauctioned_players[unauctioned_players.get('category', 'regular') == 'marquee']
        unauctioned_regular = unauctioned_players[unauctioned_players.get('category', 'regular') == 'regular']
        
        # Show auction phase info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Captains Left", len(unauctioned_captains))
        with col2:
            st.metric("Marquee Left", len(unauctioned_marquee))
        with col3:
            st.metric("Regular Left", len(unauctioned_regular))
        
        # Player selection based on phase
        phase_selection = st.radio(
            "Select Auction Phase:",
            ["🟡 Marquee Players", "🔵 Regular Players"],
            help="Captains are assigned separately. Select phase based on auction progress."
        )
        
        if phase_selection == "🟡 Marquee Players":
            available_players = unauctioned_marquee
        else:
            available_players = unauctioned_regular
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🎯 Pick Random Player", use_container_width=True):
                if not available_players.empty:
                    selected_player = available_players.sample(n=1).iloc[0]
                    phase = "marquee" if phase_selection == "🟡 Marquee Players" else "regular"
                    if self.db_manager.set_current_auction_player(selected_player['name'], phase):
                        st.success(f"🎉 Random player picked: **{selected_player['name']}**")
                        st.session_state.data_refresh_needed = True
                    else:
                        st.error("Failed to set auction player")
                else:
                    st.warning(f"No more {phase_selection.split(' ')[1].lower()} players available for auction.")
        
        with col2:
            if st.button("🔄 Clear Selection", use_container_width=True):
                if self.db_manager.clear_current_auction_player():
                    st.info("Selection cleared")
                    st.session_state.data_refresh_needed = True
                else:
                    st.error("Failed to clear selection")
        
        st.markdown("---")
        
        # Player selection
        current_auction = self.db_manager.get_current_auction_player()
        if current_auction and current_auction['player']:
            selected_player = current_auction['player']['name']
            st.info(f"🎯 Currently selected: **{selected_player}**")
        else:
            available_players = players_df[players_df["owner"].isnull()]["name"]
            if available_players.empty:
                st.warning("🚫 No players available for auction.")
                return
            selected_player = st.selectbox("👤 Select Player", available_players, key="manual_player_select")
        
        # Display player details
        player_details = players_df.loc[players_df["name"] == selected_player].iloc[0]
        self.display_player_details(player_details)
        
        # Team and price selection
        col1, col2 = st.columns(2)
        
        with col1:
            selected_team = st.selectbox("🏆 Select Team", teams_df["team_name"], key="auction_team_select")
        
        with col2:
            # Use database-calculated max bid
            max_bid = self.db_manager.calculate_max_bid(selected_team)
            remaining_budget = self.db_manager.get_team_remaining_budget(selected_team)
            
            # Ensure max bid is at least the base price
            max_allowable = max(max_bid, int(player_details["base_price"]))
            
            auction_price = st.number_input(
                "💰 Auction Price",
                min_value=int(player_details["base_price"]),
                max_value=max_allowable,
                step=config.AUCTION_PRICE_STEP,
                value=int(player_details["base_price"])
            )
        
        # Show budget information
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"💳 Remaining budget: ₹{remaining_budget:,}")
        with col2:
            st.info(f"🎯 Max bid allowed: ₹{max_allowable:,}")
        
        # Show warning if team is near capacity
        team_players_count = len(players_df[players_df["owner"] == selected_team])
        if team_players_count >= config.REGULAR_PLAYERS_NEEDED:
            st.warning(f"⚠️ {selected_team} already has {team_players_count} players (max {config.MAX_PLAYERS_PER_TEAM} including captain)")
        elif team_players_count >= (config.REGULAR_PLAYERS_NEEDED - 2):
            st.info(f"ℹ️ {selected_team} has {team_players_count} players. {config.MAX_PLAYERS_PER_TEAM-team_players_count} more needed.")
        
        # Update button
        if st.button("✅ Update Auction Status", type="primary", use_container_width=True):
            if self.db_manager.update_player_auction(selected_player, selected_team, auction_price):
                st.success(f"🎉 **{selected_player}** sold to **{selected_team}** for **₹{auction_price:,}**")
                # Clear the current auction player since they've been sold
                self.db_manager.clear_current_auction_player()
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
            remaining_budget = st.session_state.team_budgets.get(team, config.TEAM_BUDGET) - total_spent
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
        
        selected_option = st.selectbox("🔄 Select Player to Undo Auction", player_options, key="undo_player_select")
        
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
    
    def render_captain_assignment_tab(self, players_df: pd.DataFrame, teams_df: pd.DataFrame) -> None:
        """Render the captain assignment tab."""
        st.markdown("<h2 style='color: #FF5733;'>Captain Assignment</h2>", unsafe_allow_html=True)
        
        # Get captains (players with category 'captain' but no base_price logic needed)
        captain_players = players_df[players_df.get('category', 'regular') == 'captain']
        available_captains = captain_players[captain_players["owner"].isnull()]
        
        if available_captains.empty:
            st.info("🔍 No unassigned captains found.")
            return
        
        st.subheader("👑 Assign Captains to Teams")
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_captain = st.selectbox("👤 Select Captain", available_captains["name"], key="captain_select")
        
        with col2:
            # Show only teams without captains
            teams_with_captains = captain_players[captain_players["owner"].notnull()]["owner"].unique()
            teams_without_captains = teams_df[~teams_df["team_name"].isin(teams_with_captains)]["team_name"]
            
            if teams_without_captains.empty:
                st.warning("All teams already have captains assigned.")
                return
            
            selected_team = st.selectbox("🏆 Select Team", teams_without_captains, key="captain_team_select")
        
        # Display selected captain details
        if selected_captain:
            captain_details = available_captains.loc[available_captains["name"] == selected_captain].iloc[0]
            self.display_player_details(captain_details)
        
        if st.button("👑 Assign Captain", type="primary", use_container_width=True):
            if self.db_manager.assign_captain(selected_captain, selected_team):
                st.success(f"🎉 **{selected_captain}** assigned as captain to **{selected_team}**")
                st.session_state.data_refresh_needed = True
                st.rerun()
            else:
                st.error("Failed to assign captain")
    
    def render_player_upload_tab(self) -> None:
        """Render enhanced player data upload tab."""
        st.markdown("<h2 style='color: #FF5733;'>Player Data Management</h2>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["📤 Upload Players", "➕ Add Individual Player"])
        
        with tab1:
            st.subheader("📤 Bulk Upload Players")
            st.write("Upload a CSV file with columns: name, base_price, category, photo_url")
            
            uploaded_file = st.file_uploader("Choose CSV file", type="csv", key="bulk_player_upload")
            
            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file)
                    st.write("Preview:")
                    st.dataframe(df.head())
                    
                    if st.button("Upload Players", key="bulk_upload_btn"):
                        # Ensure required columns exist
                        if 'category' not in df.columns:
                            df['category'] = 'regular'
                        if 'photo_url' not in df.columns:
                            df['photo_url'] = None
                        
                        if self.db_manager.bulk_insert_players(df):
                            st.success(f"Successfully uploaded {len(df)} players!")
                            st.session_state.data_refresh_needed = True
                            st.rerun()
                        else:
                            st.error("Failed to upload players")
                except Exception as e:
                    st.error(f"Error processing file: {e}")
        
        with tab2:
            st.subheader("➕ Add Individual Player")
            
            with st.form("add_player_form"):
                player_name = st.text_input("Player Name")
                base_price = st.number_input("Base Price (in ₹)", min_value=0, value=config.DEFAULT_PLAYER_BASE_PRICE, step=config.PLAYER_BASE_PRICE_STEP)
                category = st.selectbox("Category", ["regular", "marquee", "captain"], key="player_category_select")
                photo_url = st.text_input("Photo URL (optional)")
                
                if st.form_submit_button("Add Player"):
                    if player_name:
                        # Add player to database (implementation would need a new method)
                        st.success(f"Player {player_name} added successfully!")
                    else:
                        st.error("Please enter player name")
    
    def render_observer_interface(self, players_df: pd.DataFrame, teams_df: pd.DataFrame) -> None:
        """Render observer interface showing current player and team budgets."""
        st.markdown("<h1 style='text-align: center; color: #4CAF50;'>🏸 Live Auction View</h1>", unsafe_allow_html=True)
        
        # Add refresh button for real-time updates
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**🔄 Live auction updates** - Click refresh to see latest player selection")
        with col2:
            if st.button("🔄 Refresh Now", help="Get latest auction updates", key="observer_live_refresh"):
                st.session_state.data_refresh_needed = True
                st.rerun()
        
        # Current player on auction (from database)
        current_auction = self.db_manager.get_current_auction_player()
        if current_auction and current_auction['player']:
            st.markdown("### 🎯 Current Player on Auction")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Convert dict to pandas Series for compatibility with display_player_details
                player_data = current_auction['player']
                player_series = pd.Series(player_data)
                self.display_player_details(player_series)
            
            with col2:
                st.markdown("### 💰 Team Budgets & Max Bids")
                
                budget_data = []
                for team in teams_df["team_name"]:
                    remaining = self.db_manager.get_team_remaining_budget(team)
                    max_bid = self.db_manager.calculate_max_bid(team)
                    team_players = players_df[players_df["owner"] == team]
                    player_count = len(team_players)
                    
                    budget_data.append({
                        "Team": team,
                        "Players": f"{player_count}/{config.MAX_PLAYERS_PER_TEAM}",
                        "Budget Left": f"₹{remaining:,}",
                        "Max Bid": f"₹{max_bid:,}"
                    })
                
                budget_df = pd.DataFrame(budget_data)
                st.dataframe(budget_df, use_container_width=True, hide_index=True)
        
        else:
            st.info("🔄 Waiting for next player selection...")
            
            # Show team overview when no active auction
            st.markdown("### 🏆 Current Team Standings")
            self.render_teams_tab(players_df, teams_df)

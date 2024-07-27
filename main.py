import streamlit as st
import pandas as pd
import sqlite3
import os
from utils import (
    init_db,
    load_data,
    save_data,
    update_auction_status,
    fetch_auctioned_players,
    fetch_unauctioned_players,
    check_table_empty,
    calculate_points,
    load_initial_data,
    add_owner_column
)

# Database path
db_path = "auction.db"

# Initialize session state
if "role" not in st.session_state:
    st.session_state.role = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "team_budgets" not in st.session_state:
    st.session_state.team_budgets = {}

# Function to initialize the database and load initial data
def init_and_load_data():
    init_db(db_path)
    add_owner_column(db_path)
    load_initial_data(db_path)
    
    # Set initial team budgets
    teams_df = load_data(db_path, "teams")
    st.session_state.team_budgets = {
        team: 20000 for team in teams_df["team_name"].unique()
    }

# Initialize and load data when the app starts
init_and_load_data()

# Function to reset the database
def reset_database():
    if os.path.exists(db_path):
        os.remove(db_path)
    init_and_load_data()
    st.experimental_rerun()
    
# Helper function to find the correct column name
def get_column(df, possible_names):
    for name in possible_names:
        if name in df.columns:
            return name
    return None

# Set wider layout
st.set_page_config(layout="wide")

# Sidebar with logo, login, and reset
with st.sidebar:
    st.image("hpl.jpg", width=200)
    
    if not st.session_state.logged_in:
        st.subheader("Login")
        users_df = load_data(db_path, "users")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = users_df[
                (users_df["username"] == username) & (users_df["password"] == password)
            ]
            if not user.empty:
                st.session_state.role = user.iloc[0]["role"]
                st.session_state.logged_in = True
                st.success(f"Logged in as {st.session_state.role}")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")
    else:
        st.success(f"Logged in as {st.session_state.role}")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.role = None
            st.experimental_rerun()

    if st.button("Reset Data"):
        reset_database()

# Main content
st.markdown(
    "<h1 style='text-align: center; color: #4CAF50;'>Horizon Premier League Auction System</h1>",
    unsafe_allow_html=True,
)

# Add refresh button
if st.button("Refresh Data"):
    st.experimental_rerun()

if st.session_state.logged_in:
    def load_all_data():
        add_owner_column(db_path)
        players_df = load_data(db_path, "players")
        teams_df = load_data(db_path, "teams")
        
        if 'owner' not in players_df.columns:
            players_df['owner'] = None
        if 'auction_price' not in players_df.columns:
            players_df['auction_price'] = 0
        if 'points' not in players_df.columns:
            players_df['points'] = players_df.apply(calculate_points, axis=1)
    
        return players_df, teams_df

    players_df, teams_df = load_all_data()

    # Create tabs based on user role
    if st.session_state.role in ["auctioneer", "admin"]:
        tabs = st.tabs(["Update Auction Status", "Teams", "Unauctioned Players", "Auctioned Players", "Point System", "Players List"])
    else:
        tabs = st.tabs(["Teams", "Unauctioned Players", "Auctioned Players", "Point System", "Players List"])

    tab_index = 0
    if st.session_state.role in ["auctioneer", "admin"]:
        with tabs[tab_index]:
            st.markdown("<h2 style='color: #FF5733;'>Update Auction Status</h2>", unsafe_allow_html=True)
            player_type = st.selectbox("Select Player Type", ["Batsman", "Bowler", "All Rounder"])
            
            available_players = players_df[
                (players_df["owner"].isnull()) & (players_df["Skill"] == player_type)
            ]["Name"]
            
            if available_players.empty:
                st.write(f"No {player_type} players available for auction.")
            else:
                selected_player = st.selectbox("Select Player", available_players)
                selected_team = st.selectbox("Select Team", teams_df["team_name"])
                player_price = int(players_df.loc[players_df["Name"] == selected_player, "points"].values[0])
                
                if selected_team not in st.session_state.team_budgets:
                    st.session_state.team_budgets[selected_team] = 20000  # Default budget
                
                remaining_budget = int(
                    st.session_state.team_budgets[selected_team]
                    - players_df[players_df["owner"] == selected_team]["auction_price"].sum()
                )
                auction_price = st.number_input(
                    "Auction Price",
                    min_value=player_price,
                    max_value=remaining_budget,
                    step=100,
                )
                if st.button("Update Auction Status"):
                    update_auction_status(db_path, selected_player, selected_team, auction_price)
                    st.success(f"Auction status updated: {selected_player} bought by {selected_team} for {auction_price} points")
                    players_df, teams_df = load_all_data()  # Refresh data
                    st.experimental_rerun()  # Rerun the app to refresh all sections
        tab_index += 1

    with tabs[tab_index]:
        st.markdown("<h2 style='color: #FF5733;'>Teams and their Players</h2>", unsafe_allow_html=True)
        team_expenses = players_df.groupby("owner")["auction_price"].sum().reset_index()
        team_expenses.columns = ["team", "expenses"]
        team_expenses["expenses"] = team_expenses["expenses"].fillna(0)
        team_expenses["remaining"] = team_expenses["team"].map(st.session_state.team_budgets) - team_expenses["expenses"]
        team_expenses.index = team_expenses.index + 1
        st.dataframe(team_expenses[["team", "expenses", "remaining"]])
        
        for team in teams_df["team_name"].unique():
            st.write(f"**{team}**")
            team_players = players_df[players_df["owner"] == team].copy()
            columns_to_display = ["Name", "Skill", "Preferred Playing Position", "Batting Skill Level", "Bowler Skill Level", "Bowler Type", "Wicket Keeper", "points", "auction_price"]
            team_players = team_players[columns_to_display]
            team_players.index = range(1, len(team_players) + 1)
            st.dataframe(team_players)

    with tabs[tab_index + 1]:
        st.markdown("<h2 style='color: #FF5733;'>Unauctioned Players</h2>", unsafe_allow_html=True)
        unauctioned_players = players_df[players_df["owner"].isnull()].copy()
        columns_to_display = ["Name", "Skill", "Preferred Playing Position", "Batting Skill Level", "Bowler Skill Level", "Bowler Type", "Wicket Keeper", "points"]
        unauctioned_players = unauctioned_players[columns_to_display]
        unauctioned_players.index = range(1, len(unauctioned_players) + 1)
        st.dataframe(unauctioned_players)

    with tabs[tab_index + 2]:
        st.markdown("<h2 style='color: #FF5733;'>Auctioned Players</h2>", unsafe_allow_html=True)
        auctioned_players = players_df[players_df["owner"].notnull()].copy()
        columns_to_display = ["Name", "Skill", "Preferred Playing Position", "Batting Skill Level", "Bowler Skill Level", "Bowler Type", "Wicket Keeper", "points", "owner", "auction_price"]
        auctioned_players = auctioned_players[columns_to_display]
        auctioned_players.index = range(1, len(auctioned_players) + 1)
        st.dataframe(auctioned_players)

    with tabs[tab_index + 3]:
        st.markdown("<h2 style='color: #FF5733;'>Point System</h2>", unsafe_allow_html=True)
        st.markdown("""
        Our auction system uses the following point allocation:

        1. **Preferred Playing Position:**
           - Opener: 100 points
           - Middle Order: 75 points
           - Finisher: 100 points

        2. **Skill:**
           - Batsman: 100 points
           - Bowler: 100 points
           - All Rounder: 150 points

        3. **Batting Skill Level:**
           - Beginner: 25 points
           - Intermediate: 50 points
           - Advanced: 75 points
           - Expert: 100 points

        4. **Bowler Skill Level (only for Bowlers and All rounders):**
           - Beginner: 25 points
           - Intermediate: 50 points
           - Advanced: 75 points
           - Expert: 100 points

        5. **Bowler Type (only for Bowlers and All Runders):**
           - Fast: 75 points
           - Medium: 50 points
           - Spin: 75 points

        6. **Wicket Keeper:**
           - Yes: 50 points
           - No: 0 points

        Players are awarded points based on their attributes in each category. The total points for a player is the sum of points from all applicable categories.

        Note: Bowler Skill Level and Bowler Type points are only awarded to players with the Bowler or All Rounder skill.
        """)

    with tabs[tab_index + 4]:
        st.markdown("<h2 style='color: #FF5733;'>Players List</h2>", unsafe_allow_html=True)
        columns_to_display = ["Name", "Skill", "Preferred Playing Position", "Batting Skill Level", "Bowler Skill Level", "Bowler Type", "Wicket Keeper", "points", "owner", "auction_price"]
        players_list = players_df[columns_to_display].copy()
        players_list = players_list.sort_values("points", ascending=False)
        players_list.index = range(1, len(players_list) + 1)
        st.dataframe(players_list)
        
        csv = players_list.to_csv(index=False)
        st.download_button(
            label="Download Players List",
            data=csv,
            file_name="players_list.csv",
            mime="text/csv",
        )

else:
    st.warning("Please log in to access the auction system.")
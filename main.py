import streamlit as st
import pandas as pd
import random
import logging
from utils import (
    init_db,
    load_data,
    save_data,
    update_auction_status,
    fetch_auctioned_players,
    fetch_unauctioned_players,
    check_collection_empty,
    calculate_points,
    load_initial_data,
    mark_player_status,
    get_players_by_status,
    undo_auction,
)
import subprocess

# Set page config at the very beginning
st.set_page_config(layout="wide")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize session state
if "role" not in st.session_state:
    st.session_state.role = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "team_budgets" not in st.session_state:
    st.session_state.team_budgets = {}
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False
if "random_player" not in st.session_state:
    st.session_state.random_player = None

def init_and_load_data():
    try:
        init_db()
        load_initial_data()
        teams_df = load_data("teams")
        st.session_state.team_budgets = {team: 20000 for team in teams_df["team_name"].unique()}
        logger.info("Data initialized and loaded successfully")
        st.session_state.data_loaded = True
    except Exception as e:
        logger.error(f"Error initializing and loading data: {e}")
        st.error(f"An error occurred while initializing the application: {e}")

def reset_database():
    subprocess.run(["python", "reset_db.py"])
    st.session_state.data_loaded = False
    st.experimental_rerun()

def load_all_data():
    players_df = load_data("players")
    teams_df = load_data("teams")
    for col, default in [("owner", None), ("auction_price", 0), ("auction_status", "regular")]:
        if col not in players_df.columns:
            players_df[col] = default
    if "points" not in players_df.columns:
        players_df["points"] = players_df.apply(calculate_points, axis=1)
    return players_df, teams_df

def display_player_details(player_details):
    for field in ["Name", "Flat No", "Skill", "Preferred Playing Position", "Batting Skill Level", 
                  "Bowler Skill Level", "Bowler Type", "Wicket Keeper", "points"]:
        st.write(f"{field}: {player_details[field]}")

def display_team_players(team, players_df):
    st.write(f"**{team}**")
    team_players = players_df[players_df["owner"] == team].copy()
    columns_to_display = ["Name", "Flat No", "Skill", "Preferred Playing Position", "Batting Skill Level", 
                          "Bowler Skill Level", "Bowler Type", "Wicket Keeper", "points", "auction_price"]
    team_players = team_players[columns_to_display]
    team_players.index = range(1, len(team_players) + 1)
    st.dataframe(team_players)

# Sidebar and main content setup
with st.sidebar:
    st.image("hpl.jpg", width=200)
    if not st.session_state.logged_in:
        st.subheader("Login")
        users_df = load_data("users")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = users_df[(users_df["username"] == username) & (users_df["password"] == password)]
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

st.markdown("<h1 style='text-align: center; color: #4CAF50;'>Horizon Premier League Auction System</h1>", unsafe_allow_html=True)

if st.button("Refresh Data"):
    st.session_state.data_loaded = False
    st.experimental_rerun()

if not st.session_state.data_loaded:
    init_and_load_data()

if st.session_state.logged_in:
    players_df, teams_df = load_all_data()

    tabs = st.tabs(["Update Auction Status", "Mark Players", "Teams", "Unauctioned Players", "Auctioned Players", "Undo Auction", "Point System", "Players List"] 
                   if st.session_state.role in ["auctioneer", "admin"] else 
                   ["Teams", "Unauctioned Players", "Auctioned Players", "Point System", "Players List"])

    def update_auction_status_tab():
        st.markdown("<h2 style='color: #FF5733;'>Update Auction Status</h2>", unsafe_allow_html=True)
        st.subheader("Random Player Selection")
        unauctioned_players = players_df[players_df["owner"].isnull()]
        for status in ["prime", "regular", "end"]:
            player_pool = unauctioned_players[unauctioned_players["auction_status"] == status]
            if not player_pool.empty:
                break
        if st.button("Pick Random Player for Auction"):
            if not player_pool.empty:
                st.session_state.random_player = player_pool.sample(n=1).iloc[0]
                st.success(f"Random player picked for auction: {st.session_state.random_player['Name']} (Flat No: {st.session_state.random_player['Flat No']}, Status: {st.session_state.random_player['auction_status']})")
            else:
                st.warning("No more players available for auction.")
                st.session_state.random_player = None
        st.markdown("<hr>", unsafe_allow_html=True)
        if st.session_state.random_player is not None:
            selected_player = st.session_state.random_player["Name"]
        else:
            player_type = st.selectbox("Select Player Type", ["Batsman", "Bowler", "All Rounder"])
            available_players = players_df[(players_df["owner"].isnull()) & (players_df["Skill"] == player_type)][["Name", "Flat No"]]
            if available_players.empty:
                st.write(f"No {player_type} players available for auction.")
                return
            player_options = [f"{row['Name']} (Flat No: {row['Flat No']})" for _, row in available_players.iterrows()]
            selected_player_with_flat = st.selectbox("Select Player", player_options)
            selected_player = selected_player_with_flat.split(" (Flat No:")[0]
        player_details = players_df.loc[players_df["Name"] == selected_player].iloc[0]
        display_player_details(player_details)
        selected_team = st.selectbox("Select Team", teams_df["team_name"])
        player_price = int(player_details["points"])
        if selected_team not in st.session_state.team_budgets:
            st.session_state.team_budgets[selected_team] = 20000
        remaining_budget = int(st.session_state.team_budgets[selected_team] - players_df[players_df["owner"] == selected_team]["auction_price"].sum())
        auction_price = st.number_input("Auction Price", min_value=player_price, max_value=remaining_budget, step=100)
        if st.button("Update Auction Status"):
            update_auction_status(selected_player, selected_team, auction_price)
            st.success(f"Auction status updated: {selected_player} (Flat No: {player_details['Flat No']}) bought by {selected_team} for {auction_price} points")
            st.session_state.data_loaded = False
            st.session_state.random_player = None
            st.experimental_rerun()

    def mark_players_tab():
        st.markdown("<h2 style='color: #FF5733;'>Mark Players</h2>", unsafe_allow_html=True)
        for status in ["Prime", "End-Auction"]:
            st.subheader(f"Mark {status} Players")
            players = st.multiselect(f"Select {status} Players", players_df[players_df["auction_status"] != status.lower()]["Name"].tolist())
            if st.button(f"Mark as {status}"):
                for player in players:
                    mark_player_status(player, status.lower())
                st.success(f"Players marked as {status.lower()} successfully!")

    def teams_tab():
        st.markdown("<h2 style='color: #FF5733;'>Teams and their Players</h2>", unsafe_allow_html=True)
        team_expenses = players_df.groupby("owner")["auction_price"].sum().reset_index()
        team_expenses.columns = ["team", "expenses"]
        team_expenses["expenses"] = team_expenses["expenses"].fillna(0)
        team_expenses["remaining"] = team_expenses["team"].map(st.session_state.team_budgets) - team_expenses["expenses"]
        team_expenses.index = range(1, len(team_expenses) + 1)
        st.dataframe(team_expenses[["team", "expenses", "remaining"]])
        for team in teams_df["team_name"].unique():
            display_team_players(team, players_df)

    def unauctioned_players_tab():
        st.markdown("<h2 style='color: #FF5733;'>Unauctioned Players</h2>", unsafe_allow_html=True)
        unauctioned_players = players_df[players_df["owner"].isnull()].copy()
        columns_to_display = ["Name", "Flat No", "Skill", "Preferred Playing Position", "Batting Skill Level", 
                              "Bowler Skill Level", "Bowler Type", "Wicket Keeper", "points", "auction_status"]
        unauctioned_players = unauctioned_players[columns_to_display]
        unauctioned_players.index = range(1, len(unauctioned_players) + 1)
        st.dataframe(unauctioned_players)

    def auctioned_players_tab():
        st.markdown("<h2 style='color: #FF5733;'>Auctioned Players</h2>", unsafe_allow_html=True)
        auctioned_players = players_df[players_df["owner"].notnull()].copy()
        columns_to_display = ["Name", "Flat No", "Skill", "Preferred Playing Position", "Batting Skill Level", 
                              "Bowler Skill Level", "Bowler Type", "Wicket Keeper", "points", "owner", "auction_price"]
        auctioned_players = auctioned_players[columns_to_display]
        auctioned_players.index = range(1, len(auctioned_players) + 1)
        st.dataframe(auctioned_players)

    def undo_auction_tab():
        st.markdown("<h2 style='color: #FF5733;'>Undo Auction</h2>", unsafe_allow_html=True)
        auctioned_players = players_df[players_df["owner"].notnull()]
        if not auctioned_players.empty:
            player_options = [f"{row['Name']} (Team: {row['owner']}, Price: {row['auction_price']})" for _, row in auctioned_players.iterrows()]
            selected_player = st.selectbox("Select Player to Undo Auction", player_options)
            if st.button("Undo Auction"):
                player_name = selected_player.split(" (Team:")[0]
                if undo_auction(player_name):
                    st.success(f"Auction undone for player: {player_name}")
                    st.experimental_rerun()
                else:
                    st.error(f"Failed to undo auction for player: {player_name}")
        else:
            st.warning("No auctioned players available.")

    def point_system_tab():
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

        Note: 
        - Bowler Skill Level and Bowler Type points are only awarded to players with the Bowler or All Rounder skill.
        - The final point total is rounded to the nearest 100. For example:
          * 350 points become 400
          * 225 points become 200
          * 375 points become 400
        """)

    def players_list_tab():
        st.markdown("<h2 style='color: #FF5733;'>Players List</h2>", unsafe_allow_html=True)
        columns_to_display = ["Name", "Flat No", "Skill", "Preferred Playing Position", "Batting Skill Level", 
                              "Bowler Skill Level", "Bowler Type", "Wicket Keeper", "points", "owner", "auction_price"]
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

    # Display tabs based on user role
    if st.session_state.role in ["auctioneer", "admin"]:
        tab_functions = [
            update_auction_status_tab,
            mark_players_tab,
            teams_tab,
            unauctioned_players_tab,
            auctioned_players_tab,
            undo_auction_tab,
            point_system_tab,
            players_list_tab
        ]
    else:
        tab_functions = [
            teams_tab,
            unauctioned_players_tab,
            auctioned_players_tab,
            point_system_tab,
            players_list_tab
        ]

    for tab, tab_function in zip(tabs, tab_functions):
        with tab:
            tab_function()

else:
    st.warning("Please log in to access the auction system.")
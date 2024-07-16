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
)

# Database path
db_path = "auction.db"

# Initialize session state for team budgets and roles if not already present
if "role" not in st.session_state:
    st.session_state.role = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "team_budgets" not in st.session_state:
    st.session_state.team_budgets = {}


# Function to initialize the database and load initial data
def init_and_load_data():
    init_db(db_path)
    load_initial_data()


# Load initial data into the database if tables are empty
def load_initial_data():
    users_file_path = "data/users.csv"
    players_file_path = "data/players.csv"
    teams_file_path = "data/teams.csv"

    if check_table_empty(db_path, "users") and os.path.exists(users_file_path):
        users_df = pd.read_csv(users_file_path)
        save_data(db_path, "users", users_df)

    if check_table_empty(db_path, "players") and os.path.exists(players_file_path):
        players_df = pd.read_csv(players_file_path)
        players_df["points"] = players_df.apply(calculate_points, axis=1)
        save_data(db_path, "players", players_df)

    if check_table_empty(db_path, "teams") and os.path.exists(teams_file_path):
        teams_df = pd.read_csv(teams_file_path)
        save_data(db_path, "teams", teams_df)
        # Set initial budgets for teams
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


# Adjust the width of the main div for all screens except login
def set_wide_mode(wide=True):
    if wide:
        st.markdown(
            """
            <style>
            .main .block-container {
                max-width: 90%;
                padding-left: 5%;
                padding-right: 5%;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <style>
            .main .block-container {
                max-width: 80%;
                padding-left: 10%;
                padding-right: 10%;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )


# Title
st.markdown(
    "<h1 style='text-align: center; color: #4CAF50;'>Horizon Premier League Auction System</h1>",
    unsafe_allow_html=True,
)

# Add a reset button
if st.button("Reset Data"):
    reset_database()

# Login
if not st.session_state.logged_in:
    set_wide_mode(False)
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
            st.experimental_rerun()  # Refresh the page after login
        else:
            st.error("Invalid username or password")
else:
    set_wide_mode(True)
    # Load data from the database
    players_df = load_data(db_path, "players")
    teams_df = load_data(db_path, "teams")

    # Ensure team budgets are set if not already initialized
    if not st.session_state.team_budgets:
        st.session_state.team_budgets = {
            team: 20000 for team in teams_df["team_name"].unique()
        }

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(
        ["Update Auction Status", "Teams", "Unauctioned Players", "Auctioned Players"]
    )

    with tab1:
        if st.session_state.role in ["auctioneer", "admin"]:
            st.markdown(
                "<h2 style='color: #FF5733;'>Update Auction Status</h2>",
                unsafe_allow_html=True,
            )
            player_type = st.selectbox(
                "Select Player Type", ["Batsman", "Bowler", "All-rounder"]
            )
            available_players = players_df[
                (players_df["owner"].isnull()) & (players_df["skill"] == player_type)
            ]["name"]
            if available_players.empty:
                st.write(f"No {player_type} players available for auction.")
            else:
                selected_player = st.selectbox("Select Player", available_players)
                selected_team = st.selectbox("Select Team", teams_df["team_name"])
                player_price = int(
                    players_df.loc[
                        players_df["name"] == selected_player, "points"
                    ].values[0]
                )
                remaining_budget = int(
                    st.session_state.team_budgets[selected_team]
                    - players_df[players_df["owner"] == selected_team][
                        "auction_price"
                    ].sum()
                )
                auction_price = st.number_input(
                    "Auction Price",
                    min_value=player_price,
                    max_value=remaining_budget,
                    step=100,
                )

                if st.button("Update Auction Status"):
                    update_auction_status(
                        db_path, selected_player, selected_team, auction_price
                    )
                    st.success(
                        f"Auction status updated: {selected_player} bought by {selected_team} for {auction_price} points"
                    )
                    st.experimental_rerun()  # Refresh the page to update all tabs

    with tab2:
        st.markdown(
            "<h2 style='color: #FF5733;'>Teams and their Players</h2>",
            unsafe_allow_html=True,
        )
        team_expenses = players_df.groupby("owner")["auction_price"].sum().reset_index()
        team_expenses.columns = ["team", "expenses"]
        team_expenses["expenses"] = team_expenses["expenses"].fillna(0)
        team_expenses["remaining"] = (
            team_expenses["team"].map(st.session_state.team_budgets)
            - team_expenses["expenses"]
        )
        team_expenses.index = team_expenses.index + 1  # Start index from 1
        st.dataframe(team_expenses[["team", "expenses", "remaining"]])

        for team in teams_df["team_name"].unique():
            st.write(f"**{team}**")
            team_players = players_df[players_df["owner"] == team].drop(
                columns=["phone_number", "consent_form", "flat_number"]
            )
            team_players.index = team_players.index + 1  # Start index from 1
            st.dataframe(team_players)

    with tab3:
        st.markdown(
            "<h2 style='color: #FF5733;'>Unauctioned Players</h2>",
            unsafe_allow_html=True,
        )
        unauctioned_players = fetch_unauctioned_players(db_path).drop(
            columns=["phone_number", "consent_form", "flat_number"]
        )
        unauctioned_players.index = unauctioned_players.index + 1  # Start index from 1
        st.dataframe(unauctioned_players)

    with tab4:
        st.markdown(
            "<h2 style='color: #FF5733;'>Auctioned Players</h2>", unsafe_allow_html=True
        )
        auctioned_players = fetch_auctioned_players(db_path).drop(
            columns=["phone_number", "consent_form", "flat_number"]
        )
        auctioned_players.index = auctioned_players.index + 1  # Start index from 1
        st.dataframe(auctioned_players)

import os
import ssl
import logging
import pandas as pd
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache_resource
def get_db_connection():
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise ValueError("No MONGODB_URI environment variable set")
    
    logger.info("Attempting to connect to MongoDB")
    
    try:
        client = MongoClient(uri)
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster')
        logger.info("Successfully connected to MongoDB")
        return client
    except (ConnectionFailure, ConfigurationError) as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        raise

def init_db():
    try:
        client = get_db_connection()
        db = client['hpl_auction']
        
        # Create collections if they don't exist
        for collection in ['users', 'players', 'teams']:
            if collection not in db.list_collection_names():
                db.create_collection(collection)

        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

def load_data(collection_name):
    client = get_db_connection()
    db = client['hpl_auction']
    data = list(db[collection_name].find())
    return pd.DataFrame(data)

def save_data(collection_name, data):
    client = get_db_connection()
    db = client['hpl_auction']
    db[collection_name].delete_many({})
    if not data.empty:
        db[collection_name].insert_many(data.to_dict('records'))

def update_auction_status(player_name, team_name, auction_price):
    client = get_db_connection()
    db = client['hpl_auction']
    db.players.update_one(
        {"Name": player_name},
        {"$set": {"owner": team_name, "auction_price": auction_price}}
    )

@st.cache_data(ttl=600)
def fetch_auctioned_players():
    client = get_db_connection()
    db = client['hpl_auction']
    return pd.DataFrame(list(db.players.find({"owner": {"$ne": None}})))

@st.cache_data(ttl=600)
def fetch_unauctioned_players():
    client = get_db_connection()
    db = client['hpl_auction']
    return pd.DataFrame(list(db.players.find({"owner": None})))

def check_collection_empty(collection_name):
    client = get_db_connection()
    db = client['hpl_auction']
    return db[collection_name].count_documents({}) == 0

def mark_player_status(player_name, status):
    client = get_db_connection()
    db = client['hpl_auction']
    db.players.update_one(
        {"Name": player_name},
        {"$set": {"auction_status": status}}
    )

@st.cache_data(ttl=600)
def get_players_by_status(status):
    client = get_db_connection()
    db = client['hpl_auction']
    return pd.DataFrame(list(db.players.find({"auction_status": status})))

def calculate_points(row):
    points = 0

    position_points = {"Opener": 100, "Middle Order": 75, "Finisher": 100}
    skill_points = {"Batsman": 100, "Bowler": 100, "All Rounder": 150}
    batting_skill_points = {"Beginner": 25, "Intermediate": 50, "Advanced": 75, "Expert": 100}
    bowler_skill_points = {"Beginner": 25, "Intermediate": 50, "Advanced": 75, "Expert": 100}
    bowler_type_points = {"Fast": 75, "Medium": 50, "Spin": 75}
    keeper_points = {"Yes": 50, "No": 0}

    points += position_points.get(row.get("Preferred Playing Position"), 0)
    points += skill_points.get(row.get("Skill"), 0)
    points += batting_skill_points.get(row.get("Batting Skill Level"), 0)
    points += bowler_skill_points.get(row.get("Bowler Skill Level"), 0)
    points += bowler_type_points.get(row.get("Bowler Type"), 0)
    points += keeper_points.get(row.get("Wicket Keeper"), 0)

    # Round to nearest 100
    return int(round(points / 100.0) * 100)

def load_initial_data():
    client = get_db_connection()
    db = client['hpl_auction']
    
    if check_collection_empty("users"):
        users_df = pd.read_csv("data/users.csv")
        save_data("users", users_df)

    if check_collection_empty("players"):
        players_df = pd.read_csv("data/players.csv")
        players_df["points"] = players_df.apply(calculate_points, axis=1)
        players_df["owner"] = None
        players_df["auction_price"] = 0
        save_data("players", players_df)

    if check_collection_empty("teams"):
        teams_df = pd.read_csv("data/teams.csv")
        save_data("teams", teams_df)

    logger.info("Initial data loaded successfully.")
    
def reset_auction_data():
    client = get_db_connection()
    db = client['hpl_auction']
    
    # Reset player auction data
    db.players.update_many(
        {},
        {
            "$set": {"owner": None, "auction_price": 0, "auction_status": "regular"}
        }
    )
    
    # Reset team budgets (if you're storing them in the database)
    # If you're not storing team budgets in the database, you can omit this part
    teams = db.teams.find()
    for team in teams:
        db.teams.update_one(
            {"_id": team["_id"]},
            {"$set": {"budget": 20000}}  # Or whatever the initial budget should be
        )
    
    logger.info("Auction data reset successfully.")
    
    
def undo_auction(player_name):
    client = get_db_connection()
    db = client['hpl_auction']
    result = db.players.update_one(
        {"Name": player_name},
        {"$set": {"owner": None, "auction_price": 0, "auction_status": "regular"}}
    )
    if result.modified_count == 1:
        logger.info(f"Auction undone for player: {player_name}")
        return True
    else:
        logger.warning(f"Failed to undo auction for player: {player_name}")
        return False
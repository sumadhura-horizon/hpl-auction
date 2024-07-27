import pandas as pd
from pymongo import MongoClient
from bson import ObjectId

# MongoDB connection
client = MongoClient("mongodb+srv://hpladmin:JBaOfvvuOGaNwD5F@hpl-auction.7xalghe.mongodb.net/?retryWrites=true&w=majority&appName=hpl-auction")
db = client['hpl_auction']

def init_db():
    # Create collections if they don't exist
    if 'users' not in db.list_collection_names():
        db.create_collection('users')
    if 'players' not in db.list_collection_names():
        db.create_collection('players')
    if 'teams' not in db.list_collection_names():
        db.create_collection('teams')

def load_data(collection_name):
    return pd.DataFrame(list(db[collection_name].find()))

def save_data(collection_name, data):
    db[collection_name].delete_many({})
    if not data.empty:
        db[collection_name].insert_many(data.to_dict('records'))

def update_auction_status(player_name, team_name, auction_price):
    db.players.update_one(
        {"Name": player_name},
        {"$set": {"owner": team_name, "auction_price": auction_price}}
    )

def fetch_auctioned_players():
    return pd.DataFrame(list(db.players.find({"owner": {"$ne": None}})))

def fetch_unauctioned_players():
    return pd.DataFrame(list(db.players.find({"owner": None})))

def check_collection_empty(collection_name):
    return db[collection_name].count_documents({}) == 0

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

    return points

def load_initial_data():
    import os
    
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

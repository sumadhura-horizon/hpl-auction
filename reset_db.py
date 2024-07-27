import pandas as pd
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
uri = os.getenv("MONGODB_URI")
client = MongoClient(uri)
db = client['hpl_auction']

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

def reset_database():
    # Reset players
    players_df = pd.read_csv("data/players.csv")
    players_df["points"] = players_df.apply(calculate_points, axis=1)
    players_df["owner"] = None
    players_df["auction_price"] = 0
    players_df["auction_status"] = "regular"
    
    db.players.delete_many({})
    db.players.insert_many(players_df.to_dict('records'))

    # Reset teams
    teams_df = pd.read_csv("data/teams.csv")
    db.teams.delete_many({})
    db.teams.insert_many(teams_df.to_dict('records'))

    # Reset users
    users_df = pd.read_csv("data/users.csv")
    db.users.delete_many({})
    db.users.insert_many(users_df.to_dict('records'))

    print("Database reset successfully.")

if __name__ == "__main__":
    reset_database()
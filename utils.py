import pandas as pd
import sqlite3
import os

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS players (
        Name TEXT PRIMARY KEY,
        "Flat No" TEXT,
        Age INTEGER,
        "Phone Number" TEXT,
        "Preferred Playing Position" TEXT,
        Skill TEXT,
        "Batting Skill Level" TEXT,
        "Bowler Skill Level" TEXT,
        "Bowler Type" TEXT,
        "Wicket Keeper" TEXT,
        owner TEXT,
        auction_price INTEGER,
        points INTEGER
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS teams (
        team_name TEXT PRIMARY KEY
    )
    """
    )

    conn.commit()
    conn.close()

def add_owner_column(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(players)")
    columns = [col[1] for col in cursor.fetchall()]
    if "owner" not in columns:
        cursor.execute("ALTER TABLE players ADD COLUMN owner TEXT")
    if "auction_price" not in columns:
        cursor.execute("ALTER TABLE players ADD COLUMN auction_price INTEGER DEFAULT 0")
    conn.commit()
    conn.close()

def load_data(db_path, table_name):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df

def save_data(db_path, table_name, data):
    conn = sqlite3.connect(db_path)
    data.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()

def update_auction_status(db_path, player_name, team_name, auction_price):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
    UPDATE players
    SET owner = ?, auction_price = ?
    WHERE Name = ?
    """,
        (team_name, auction_price, player_name),
    )
    conn.commit()
    conn.close()

def fetch_auctioned_players(db_path):
    add_owner_column(db_path)
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM players WHERE owner IS NOT NULL", conn)
    conn.close()
    return df

def fetch_unauctioned_players(db_path):
    add_owner_column(db_path)
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM players WHERE owner IS NULL OR owner = ''", conn)
    conn.close()
    return df

def check_table_empty(db_path, table_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    conn.close()
    return count == 0

def calculate_points(row):
    points = 0

    # Preferred Playing Position
    position_points = {
        "Opener": 100,
        "Middle Order": 75,
        "Finisher": 100
    }
    points += position_points.get(row["Preferred Playing Position"], 0)

    # Skill
    skill_points = {
        "Batsman": 100,
        "Bowler": 100,
        "All Rounder": 150
    }
    points += skill_points.get(row["Skill"], 0)

    # Batting Skill Level
    batting_skill_points = {
        "Beginner": 25,
        "Intermediate": 50,
        "Advanced": 75,
        "Expert": 100
    }
    points += batting_skill_points.get(row["Batting Skill Level"], 0)

    # Bowler Skill Level (for all players)
    bowler_skill_points = {
        "Beginner": 25,
        "Intermediate": 50,
        "Advanced": 75,
        "Expert": 100
    }
    points += bowler_skill_points.get(row["Bowler Skill Level"], 0)

    # Bowler Type (for all players)
    bowler_type_points = {
        "Fast": 75,
        "Medium": 50,
        "Spin": 75
    }
    points += bowler_type_points.get(row["Bowler Type"], 0)

    # Wicket Keeper
    keeper_points = {
        "Yes": 50,
        "No": 0
    }
    points += keeper_points.get(row["Wicket Keeper"], 0)

    return points

def load_initial_data(db_path):
    add_owner_column(db_path)
    users_file_path = "data/users.csv"
    players_file_path = "data/players.csv"
    teams_file_path = "data/teams.csv"

    if check_table_empty(db_path, "users") and os.path.exists(users_file_path):
        users_df = pd.read_csv(users_file_path)
        save_data(db_path, "users", users_df)

    if check_table_empty(db_path, "players") and os.path.exists(players_file_path):
        players_df = pd.read_csv(players_file_path)
        players_df["points"] = players_df.apply(calculate_points, axis=1)
        
        # Ensure 'owner' and 'auction_price' columns exist
        if 'owner' not in players_df.columns:
            players_df['owner'] = None
        if 'auction_price' not in players_df.columns:
            players_df['auction_price'] = 0
        
        save_data(db_path, "players", players_df)

    if check_table_empty(db_path, "teams") and os.path.exists(teams_file_path):
        teams_df = pd.read_csv(teams_file_path)
        save_data(db_path, "teams", teams_df)
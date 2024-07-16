import pandas as pd
import sqlite3


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
        name TEXT PRIMARY KEY,
        age INTEGER,
        phone_number TEXT,
        preferred_playing_position TEXT,
        skill TEXT,
        bowler_type TEXT,
        keeper TEXT,
        skill_level TEXT,
        flat_number TEXT,
        consent_form TEXT,
        owner TEXT,
        auction_price INTEGER
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
    WHERE name = ?
    """,
        (team_name, auction_price, player_name),
    )
    conn.commit()
    conn.close()


def fetch_auctioned_players(db_path):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM players WHERE owner IS NOT NULL", conn)
    conn.close()
    return df


def fetch_unauctioned_players(db_path):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM players WHERE owner IS NULL", conn)
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

    skill_points = {"Batsman": 100, "Bowler": 100, "All-rounder": 150}

    batting_position_points = {"Opener": 50, "Middle Order": 50, "Finisher": 50}

    bowler_type_points = {"Fast": 50, "Medium": 40, "Spin": 30}

    keeper_points = {"Yes": 50, "No": 0}

    skill_level_points = {
        "Beginner": 50,
        "Intermediate": 100,
        "Advanced": 150,
        "Expert": 200,
    }

    points += skill_points.get(row["skill"], 0)
    points += batting_position_points.get(row["preferred_playing_position"], 0)
    points += bowler_type_points.get(row["bowler_type"], 0)
    points += keeper_points.get(row["keeper"], 0)
    points += skill_level_points.get(row["skill_level"], 0)

    return points

"""
Database operations for the auction system.
"""
import sqlite3
import pandas as pd
from typing import List, Optional
import logging
from .models import User, Player, Team

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages all database operations."""
    
    def __init__(self, db_path: str = "auction.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self) -> None:
        """Initialize database tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL
                )
            ''')
            
            # Create players table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    base_price INTEGER NOT NULL,
                    owner TEXT,
                    auction_price INTEGER DEFAULT 0
                )
            ''')
            
            # Create teams table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS teams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    team_name TEXT NOT NULL UNIQUE
                )
            ''')
            
            conn.commit()
        logger.info("Database initialized successfully")
    
    def reset_database(self) -> None:
        """Reset all database tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS users")
            cursor.execute("DROP TABLE IF EXISTS players")
            cursor.execute("DROP TABLE IF EXISTS teams")
            conn.commit()
        
        self.init_database()
        logger.info("Database reset successfully")
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user and return user object if valid."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, password, role FROM users WHERE username = ? AND password = ?",
                (username, password)
            )
            row = cursor.fetchone()
            
            if row:
                # Handle both dict-like and tuple-like access
                if hasattr(row, 'keys'):  # Row factory working (dict-like access)
                    return User(
                        id=row['id'],
                        username=row['username'],
                        password=row['password'],
                        role=row['role']
                    )
                else:  # Tuple access (fallback)
                    return User(
                        id=row[0],
                        username=row[1],
                        password=row[2],
                        role=row[3]
                    )
            return None
    
    def load_users_dataframe(self) -> pd.DataFrame:
        """Load users as DataFrame."""
        with self.get_connection() as conn:
            return pd.read_sql_query("SELECT * FROM users", conn)
    
    def load_players_dataframe(self) -> pd.DataFrame:
        """Load players as DataFrame."""
        with self.get_connection() as conn:
            return pd.read_sql_query("SELECT * FROM players", conn)
    
    def load_teams_dataframe(self) -> pd.DataFrame:
        """Load teams as DataFrame."""
        with self.get_connection() as conn:
            return pd.read_sql_query("SELECT * FROM teams", conn)
    
    def update_player_auction(self, player_name: str, team_name: str, auction_price: int) -> bool:
        """Update player auction status."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE players SET owner = ?, auction_price = ? WHERE name = ?",
                    (team_name, auction_price, player_name)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating player auction: {e}")
            return False
    
    def undo_player_auction(self, player_name: str) -> bool:
        """Undo player auction."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE players SET owner = NULL, auction_price = 0 WHERE name = ?",
                    (player_name,)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error undoing player auction: {e}")
            return False
    
    def bulk_insert_users(self, users_df: pd.DataFrame) -> bool:
        """Bulk insert users from DataFrame."""
        try:
            with self.get_connection() as conn:
                # Drop and recreate the users table to ensure proper schema
                cursor = conn.cursor()
                cursor.execute("DROP TABLE IF EXISTS users")
                cursor.execute('''
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL,
                        role TEXT NOT NULL
                    )
                ''')
                
                # Insert data row by row to respect the schema
                for _, row in users_df.iterrows():
                    cursor.execute(
                        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                        (row['username'], row['password'], row['role'])
                    )
                conn.commit()
            logger.info(f"Inserted {len(users_df)} users")
            return True
        except Exception as e:
            logger.error(f"Error inserting users: {e}")
            return False
    
    def bulk_insert_players(self, players_df: pd.DataFrame) -> bool:
        """Bulk insert players from DataFrame."""
        try:
            # Ensure required columns exist
            if 'owner' not in players_df.columns:
                players_df['owner'] = None
            if 'auction_price' not in players_df.columns:
                players_df['auction_price'] = 0
                
            with self.get_connection() as conn:
                players_df.to_sql('players', conn, if_exists='replace', index=False)
            logger.info(f"Inserted {len(players_df)} players")
            return True
        except Exception as e:
            logger.error(f"Error inserting players: {e}")
            return False
    
    def bulk_insert_teams(self, teams_df: pd.DataFrame) -> bool:
        """Bulk insert teams from DataFrame."""
        try:
            with self.get_connection() as conn:
                teams_df.to_sql('teams', conn, if_exists='replace', index=False)
            logger.info(f"Inserted {len(teams_df)} teams")
            return True
        except Exception as e:
            logger.error(f"Error inserting teams: {e}")
            return False
    
    def is_table_empty(self, table_name: str) -> bool:
        """Check if table is empty."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            return count == 0

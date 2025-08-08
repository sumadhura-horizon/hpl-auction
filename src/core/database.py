"""
Database operations for the auction system.
"""
import psycopg2
import psycopg2.extras
import pandas as pd
from typing import List, Optional
import logging
import os
from .models import User, Player, Team
from .config import config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages all database operations."""
    
    def __init__(self):
        # Use configuration from config module
        self.connection_params = config.get_database_params()
        self.init_database()
    
    def get_connection(self):
        """Get database connection with dict cursor."""
        # Try multiple connection strategies for macOS compatibility
        connection_attempts = [
            # Attempt 1: Use specified user/password
            self.connection_params,
            # Attempt 2: Use current system user (for macOS peer authentication)
            {
                'host': self.connection_params['host'],
                'port': self.connection_params['port'], 
                'database': self.connection_params['database'],
                'user': os.getenv('USER', os.getenv('USERNAME', 'postgres'))
            },
            # Attempt 3: Use postgres without password (for peer auth)
            {
                'host': self.connection_params['host'],
                'port': self.connection_params['port'],
                'database': self.connection_params['database'],
                'user': 'postgres'
            }
        ]
        
        last_error = None
        for attempt in connection_attempts:
            try:
                conn = psycopg2.connect(**attempt)
                logger.info(f"Connected to PostgreSQL as user: {attempt['user']}")
                return conn
            except psycopg2.Error as e:
                last_error = e
                logger.debug(f"Connection attempt failed with user {attempt.get('user', 'unknown')}: {e}")
                continue
        
        # If all attempts failed, raise the last error
        raise last_error
    
    def init_database(self) -> None:
        """Initialize database tables."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                
                # Create users table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(255) NOT NULL UNIQUE,
                        password VARCHAR(255) NOT NULL,
                        role VARCHAR(50) NOT NULL
                    )
                ''')
                
                # Create players table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS players (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        base_price INTEGER NOT NULL,
                        owner VARCHAR(255),
                        auction_price INTEGER DEFAULT 0,
                        category VARCHAR(50) DEFAULT 'regular',
                        photo_url TEXT
                    )
                ''')
                
                # Create teams table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS teams (
                        id SERIAL PRIMARY KEY,
                        team_name VARCHAR(255) NOT NULL UNIQUE,
                        budget INTEGER DEFAULT 10000000,
                        spent INTEGER DEFAULT 0,
                        players_count INTEGER DEFAULT 0,
                        captain VARCHAR(255)
                    )
                ''')
                
                # Create auction state table for sharing current auction info across sessions
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS auction_state (
                        id SERIAL PRIMARY KEY,
                        current_player_name VARCHAR(255),
                        auction_phase VARCHAR(50) DEFAULT 'marquee',
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Insert default auction state if table is empty
                cursor.execute("SELECT COUNT(*) FROM auction_state")
                if cursor.fetchone()[0] == 0:
                    cursor.execute("INSERT INTO auction_state (current_player_name, auction_phase) VALUES (NULL, 'marquee')")
                
            conn.commit()
        logger.info("Database initialized successfully")
    
    def reset_database(self) -> None:
        """Reset all database tables."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DROP TABLE IF EXISTS players CASCADE")
                cursor.execute("DROP TABLE IF EXISTS teams CASCADE")
                cursor.execute("DROP TABLE IF EXISTS users CASCADE")
                cursor.execute("DROP TABLE IF EXISTS auction_state CASCADE")
            conn.commit()
        
        self.init_database()
        logger.info("Database reset successfully")
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user and return user object if valid."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT id, username, password, role FROM users WHERE username = %s AND password = %s",
                    (username, password)
                )
                row = cursor.fetchone()
                
                if row:
                    return User(
                        id=row['id'],
                        username=row['username'],
                        password=row['password'],
                        role=row['role']
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
                with conn.cursor() as cursor:
                    
                    # Update player
                    cursor.execute(
                        "UPDATE players SET owner = %s, auction_price = %s WHERE name = %s",
                        (team_name, auction_price, player_name)
                    )
                    
                    # Update team's spent amount and player count
                    cursor.execute(
                        "UPDATE teams SET spent = spent + %s, players_count = players_count + 1 WHERE team_name = %s",
                        (auction_price, team_name)
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
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    
                    # Get player info before undoing
                    cursor.execute("SELECT owner, auction_price FROM players WHERE name = %s", (player_name,))
                    player_info = cursor.fetchone()
                    
                    if player_info and player_info['owner']:
                        # Update team's spent amount and player count
                        cursor.execute(
                            "UPDATE teams SET spent = spent - %s, players_count = players_count - 1 WHERE team_name = %s",
                            (player_info['auction_price'], player_info['owner'])
                        )
                    
                    cursor.execute(
                        "UPDATE players SET owner = NULL, auction_price = 0 WHERE name = %s",
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
                with conn.cursor() as cursor:
                    # Drop and recreate the users table to ensure proper schema
                    cursor.execute("DROP TABLE IF EXISTS users CASCADE")
                    cursor.execute('''
                        CREATE TABLE users (
                            id SERIAL PRIMARY KEY,
                            username VARCHAR(255) NOT NULL UNIQUE,
                            password VARCHAR(255) NOT NULL,
                            role VARCHAR(50) NOT NULL
                        )
                    ''')
                    
                    # Insert data row by row to respect the schema
                    for _, row in users_df.iterrows():
                        cursor.execute(
                            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
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
            if 'category' not in players_df.columns:
                players_df['category'] = 'regular'
            if 'photo_url' not in players_df.columns:
                players_df['photo_url'] = None
                
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Drop and recreate table to ensure proper schema
                    cursor.execute("DROP TABLE IF EXISTS players CASCADE")
                    cursor.execute('''
                        CREATE TABLE players (
                            id SERIAL PRIMARY KEY,
                            name VARCHAR(255) NOT NULL,
                            base_price INTEGER NOT NULL,
                            owner VARCHAR(255),
                            auction_price INTEGER DEFAULT 0,
                            category VARCHAR(50) DEFAULT 'regular',
                            photo_url TEXT
                        )
                    ''')
                    
                    # Insert data row by row to respect the schema
                    for _, row in players_df.iterrows():
                        cursor.execute(
                            "INSERT INTO players (name, base_price, owner, auction_price, category, photo_url) VALUES (%s, %s, %s, %s, %s, %s)",
                            (row['name'], row['base_price'], row.get('owner'), 
                             row.get('auction_price', 0), row.get('category', 'regular'), 
                             row.get('photo_url'))
                        )
                conn.commit()
            logger.info(f"Inserted {len(players_df)} players")
            return True
        except Exception as e:
            logger.error(f"Error inserting players: {e}")
            return False
    
    def bulk_insert_teams(self, teams_df: pd.DataFrame) -> bool:
        """Bulk insert teams from DataFrame."""
        try:
            # Ensure required columns exist
            if 'budget' not in teams_df.columns:
                teams_df['budget'] = config.TEAM_BUDGET  # 1 crore default
            if 'spent' not in teams_df.columns:
                teams_df['spent'] = 0
            if 'players_count' not in teams_df.columns:
                teams_df['players_count'] = 0
            if 'captain' not in teams_df.columns:
                teams_df['captain'] = None
                
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Drop and recreate table to ensure proper schema
                    cursor.execute("DROP TABLE IF EXISTS teams CASCADE")
                    cursor.execute('''
                        CREATE TABLE teams (
                            id SERIAL PRIMARY KEY,
                            team_name VARCHAR(255) NOT NULL UNIQUE,
                            budget INTEGER DEFAULT 10000000,
                            spent INTEGER DEFAULT 0,
                            players_count INTEGER DEFAULT 0,
                            captain VARCHAR(255)
                        )
                    ''')
                    
                    # Insert data row by row to respect the schema
                    for _, row in teams_df.iterrows():
                        cursor.execute(
                            "INSERT INTO teams (team_name, budget, spent, players_count, captain) VALUES (%s, %s, %s, %s, %s)",
                            (row['team_name'], row.get('budget', config.TEAM_BUDGET), 
                             row.get('spent', 0), row.get('players_count', 0), 
                             row.get('captain'))
                        )
                conn.commit()
            logger.info(f"Inserted {len(teams_df)} teams")
            return True
        except Exception as e:
            logger.error(f"Error inserting teams: {e}")
            return False
    
    def is_table_empty(self, table_name: str) -> bool:
        """Check if table is empty."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                return count == 0
    
    def assign_captain(self, player_name: str, team_name: str) -> bool:
        """Assign a captain to a team."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    
                    # Update player as captain and assign to team
                    cursor.execute(
                        "UPDATE players SET owner = %s, category = 'captain' WHERE name = %s",
                        (team_name, player_name)
                    )
                    
                    # Update team's captain and player count
                    cursor.execute(
                        "UPDATE teams SET captain = %s, players_count = players_count + 1 WHERE team_name = %s",
                        (player_name, team_name)
                    )
                    
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error assigning captain: {e}")
            return False
    
    def calculate_max_bid(self, team_name: str) -> int:
        """Calculate maximum bid a team can make based on remaining players to buy."""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    
                    # Get team info
                    cursor.execute(
                        "SELECT budget, spent, players_count FROM teams WHERE team_name = %s",
                        (team_name,)
                    )
                    team_info = cursor.fetchone()
                    
                    if not team_info:
                        return 0
                    
                    remaining_budget = team_info['budget'] - team_info['spent']
                    players_bought = team_info['players_count']
                    players_remaining = config.REGULAR_PLAYERS_NEEDED - players_bought  # Each team needs players (excluding captain)
                    
                    if players_remaining <= 0:
                        return 0
                    
                    # Reserve minimum amount for remaining players (2 lakhs each for regular players)
                    min_reserve = (players_remaining - 1) * config.REGULAR_PLAYER_MIN_PRICE  # Min price for each remaining player except current
                    max_bid = remaining_budget - min_reserve
                    
                    return max(max_bid, 0)
                    
        except Exception as e:
            logger.error(f"Error calculating max bid: {e}")
            return 0
    
    def get_team_remaining_budget(self, team_name: str) -> int:
        """Get remaining budget for a team."""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute(
                        "SELECT budget - spent as remaining FROM teams WHERE team_name = %s",
                        (team_name,)
                    )
                    result = cursor.fetchone()
                    return result['remaining'] if result else 0
        except Exception as e:
            logger.error(f"Error getting remaining budget: {e}")
            return 0
    
    def set_current_auction_player(self, player_name: str, auction_phase: str = 'marquee') -> bool:
        """Set the current player being auctioned (shared across all sessions)."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE auction_state SET current_player_name = %s, auction_phase = %s, last_updated = CURRENT_TIMESTAMP WHERE id = 1",
                        (player_name, auction_phase)
                    )
                conn.commit()
                logger.info(f"Set current auction player: {player_name}")
                return True
        except Exception as e:
            logger.error(f"Error setting current auction player: {e}")
            return False
    
    def get_current_auction_player(self) -> Optional[dict]:
        """Get the current player being auctioned."""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute(
                        "SELECT current_player_name, auction_phase, last_updated FROM auction_state WHERE id = 1"
                    )
                    result = cursor.fetchone()
                    if result and result['current_player_name']:
                        # Get full player details
                        cursor.execute(
                            "SELECT * FROM players WHERE name = %s",
                            (result['current_player_name'],)
                        )
                        player = cursor.fetchone()
                        if player:
                            return {
                                'player': dict(player),
                                'auction_phase': result['auction_phase'],
                                'last_updated': result['last_updated']
                            }
                    return None
        except Exception as e:
            logger.error(f"Error getting current auction player: {e}")
            return None
    
    def clear_current_auction_player(self) -> bool:
        """Clear the current auction player."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE auction_state SET current_player_name = NULL, last_updated = CURRENT_TIMESTAMP WHERE id = 1"
                    )
                conn.commit()
                logger.info("Cleared current auction player")
                return True
        except Exception as e:
            logger.error(f"Error clearing current auction player: {e}")
            return False

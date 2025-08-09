"""
Database operations for the auction system.
"""
import psycopg2
import psycopg2.extras
import pandas as pd
from typing import List, Optional
import logging
import os
import json
from datetime import datetime
from pathlib import Path
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
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    
                    # First validate if the team can afford this bid
                    max_allowed_bid = self.calculate_max_bid(team_name)
                    
                    # Get player details for validation
                    cursor.execute("SELECT base_price, category FROM players WHERE name = %s", (player_name,))
                    player_result = cursor.fetchone()
                    
                    if not player_result:
                        logger.error(f"Player {player_name} not found")
                        return False
                    
                    base_price = player_result['base_price']
                    player_category = player_result['category']
                    
                    # Check team composition limits
                    cursor.execute(
                        "SELECT category, COUNT(*) as count FROM players WHERE owner = %s AND category IN ('marquee', 'captain') GROUP BY category",
                        (team_name,)
                    )
                    team_composition = cursor.fetchall()
                    
                    marquee_count = 0
                    captain_count = 0
                    for row in team_composition:
                        if row['category'] == 'marquee':
                            marquee_count = row['count']
                        elif row['category'] == 'captain':
                            captain_count = row['count']
                    
                    # Validate team composition limits
                    if player_category == 'marquee' and marquee_count >= 3:
                        logger.error(f"Team {team_name} already has {marquee_count} marquee players (max 3)")
                        return False
                    
                    if player_category == 'captain' and captain_count >= 1:
                        logger.error(f"Team {team_name} already has {captain_count} captain (max 1)")
                        return False
                    
                    # Validate auction price
                    if auction_price < base_price:
                        logger.error(f"Auction price {auction_price} is below base price {base_price} for player {player_name}")
                        return False
                    
                    if auction_price > max_allowed_bid:
                        logger.error(f"Auction price {auction_price} exceeds maximum allowed bid {max_allowed_bid} for team {team_name}")
                        return False
                    
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
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    
                    # Check if team already has a captain
                    cursor.execute(
                        "SELECT COUNT(*) as count FROM players WHERE owner = %s AND category = 'captain'",
                        (team_name,)
                    )
                    captain_count = cursor.fetchone()['count']
                    
                    if captain_count >= 1:
                        logger.error(f"Team {team_name} already has a captain (max 1)")
                        return False
                    
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
        """Calculate maximum bid a team can make based on remaining players to buy.
        
        Team requirements: 3 marquee (10L min each) + 6 regular (2L min each) + 1 captain (free)
        Logic: Reserve minimum amounts for remaining required players, rest can be bid on current player
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    
                    # Get team info
                    cursor.execute(
                        "SELECT budget, spent FROM teams WHERE team_name = %s",
                        (team_name,)
                    )
                    team_info = cursor.fetchone()
                    
                    if not team_info:
                        return 0
                    
                    remaining_budget = team_info['budget'] - team_info['spent']
                    
                    # Get count of marquee and regular players already bought by this team
                    cursor.execute(
                        "SELECT category, COUNT(*) as count FROM players WHERE owner = %s AND category IN ('marquee', 'regular') GROUP BY category",
                        (team_name,)
                    )
                    bought_players = cursor.fetchall()
                    
                    bought_marquee = 0
                    bought_regular = 0
                    for row in bought_players:
                        if row['category'] == 'marquee':
                            bought_marquee = row['count']
                        elif row['category'] == 'regular':
                            bought_regular = row['count']
                    
                    # Calculate how many more players we still need to buy (excluding current bid)
                    marquee_still_needed = max(0, 3 - bought_marquee)  # Need 3 total marquee
                    regular_still_needed = max(0, 6 - bought_regular)  # Need 6 total regular
                    total_still_needed = marquee_still_needed + regular_still_needed
                    
                    if total_still_needed <= 0:
                        return 0
                    
                    if total_still_needed == 1:
                        # This is the last player, can spend all remaining budget
                        return remaining_budget
                    
                    # For current bid, reserve minimum for remaining players (after this purchase)
                    # Assume worst case: we'll need to buy remaining marquee and regular at minimum prices
                    remaining_marquee_after_bid = max(0, marquee_still_needed - 1)  # Assume current is marquee
                    remaining_regular_after_bid = regular_still_needed if marquee_still_needed > 0 else max(0, regular_still_needed - 1)
                    
                    # Reserve minimum amounts for players we'll need to buy later
                    min_reserve = (remaining_marquee_after_bid * config.MARQUEE_PLAYER_MIN_PRICE) + (remaining_regular_after_bid * config.REGULAR_PLAYER_MIN_PRICE)
                    
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
    
    def add_individual_player(self, name: str, base_price: int, category: str = 'regular', photo_url: Optional[str] = None) -> bool:
        """Add a single player to the database."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO players (name, base_price, category, photo_url) VALUES (%s, %s, %s, %s)",
                        (name, base_price, category, photo_url)
                    )
                conn.commit()
                logger.info(f"Added player: {name}")
                return True
        except Exception as e:
            logger.error(f"Error adding individual player: {e}")
            return False
    
    def create_backup(self) -> str:
        """Create a complete backup of all auction data."""
        try:
            # Create backups directory if it doesn't exist
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)
            
            # Generate timestamp for backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"auction_backup_{timestamp}.json"
            
            backup_data = {
                "timestamp": timestamp,
                "tables": {},
                "auction_state": {}
            }
            
            with self.get_connection() as conn:
                # Backup players table
                players_df = pd.read_sql_query("SELECT * FROM players", conn)
                backup_data["tables"]["players"] = players_df.to_dict(orient="records")
                
                # Backup teams table
                teams_df = pd.read_sql_query("SELECT * FROM teams", conn)
                backup_data["tables"]["teams"] = teams_df.to_dict(orient="records")
                
                # Backup users table
                users_df = pd.read_sql_query("SELECT * FROM users", conn)
                backup_data["tables"]["users"] = users_df.to_dict(orient="records")
                
                # Backup auction state
                auction_state_df = pd.read_sql_query("SELECT * FROM auction_state", conn)
                backup_data["tables"]["auction_state"] = auction_state_df.to_dict(orient="records")
            
            # Save backup to JSON file
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            logger.info(f"Backup created: {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None
    
    def restore_backup(self, backup_file: str) -> bool:
        """Restore auction data from backup file."""
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_file}")
                return False
            
            # Load backup data
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    
                    # Clear existing data
                    cursor.execute("DELETE FROM auction_state")
                    cursor.execute("DELETE FROM players")
                    cursor.execute("DELETE FROM teams")
                    cursor.execute("DELETE FROM users")
                    
                    # Restore users
                    users_data = backup_data["tables"].get("users", [])
                    for user in users_data:
                        cursor.execute(
                            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                            (user['username'], user['password'], user['role'])
                        )
                    
                    # Restore teams
                    teams_data = backup_data["tables"].get("teams", [])
                    for team in teams_data:
                        cursor.execute(
                            "INSERT INTO teams (team_name, budget, spent, players_count, captain) VALUES (%s, %s, %s, %s, %s)",
                            (team['team_name'], team['budget'], team['spent'], team['players_count'], team.get('captain'))
                        )
                    
                    # Restore players
                    players_data = backup_data["tables"].get("players", [])
                    for player in players_data:
                        cursor.execute(
                            "INSERT INTO players (name, base_price, owner, auction_price, category, photo_url) VALUES (%s, %s, %s, %s, %s, %s)",
                            (player['name'], player['base_price'], player.get('owner'), 
                             player.get('auction_price', 0), player.get('category', 'regular'), 
                             player.get('photo_url'))
                        )
                    
                    # Restore auction state
                    auction_state_data = backup_data["tables"].get("auction_state", [])
                    for state in auction_state_data:
                        cursor.execute(
                            "INSERT INTO auction_state (current_player_name, auction_phase, last_updated) VALUES (%s, %s, %s)",
                            (state.get('current_player_name'), state.get('auction_phase', 'marquee'), 
                             state.get('last_updated'))
                        )
                
                conn.commit()
            
            logger.info(f"Backup restored from: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False
    
    def list_backups(self) -> List[str]:
        """List all available backup files."""
        backup_dir = Path("backups")
        if not backup_dir.exists():
            return []
        
        backup_files = list(backup_dir.glob("auction_backup_*.json"))
        backup_files.sort(reverse=True)  # Most recent first
        return [str(f) for f in backup_files]
    
    def auto_backup(self) -> bool:
        """Create an automatic backup with cleanup of old backups."""
        try:
            # Create backup
            backup_file = self.create_backup()
            if not backup_file:
                return False
            
            # Clean up old backups (keep last 10)
            backups = self.list_backups()
            if len(backups) > 10:
                for old_backup in backups[10:]:
                    try:
                        os.remove(old_backup)
                        logger.info(f"Removed old backup: {old_backup}")
                    except Exception as e:
                        logger.warning(f"Could not remove old backup {old_backup}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in auto backup: {e}")
            return False

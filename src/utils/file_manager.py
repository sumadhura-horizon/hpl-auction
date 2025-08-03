"""
File upload utilities for CSV data management.
"""
import pandas as pd
import streamlit as st
from typing import Dict, Any, Optional
import logging
from ..core.database import DatabaseManager

logger = logging.getLogger(__name__)


class FileUploadManager:
    """Manages CSV file uploads and data validation."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def validate_users_csv(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate users CSV format."""
        required_columns = {'username', 'password', 'role'}
        valid_roles = {'admin', 'auctioneer', 'owner'}
        
        result = {'valid': True, 'errors': []}
        
        # Check required columns
        if not required_columns.issubset(set(df.columns)):
            missing = required_columns - set(df.columns)
            result['valid'] = False
            result['errors'].append(f"Missing required columns: {missing}")
        
        # Check for empty values
        if df.isnull().any().any():
            result['valid'] = False
            result['errors'].append("CSV contains empty values")
        
        # Check valid roles
        if 'role' in df.columns:
            invalid_roles = set(df['role']) - valid_roles
            if invalid_roles:
                result['valid'] = False
                result['errors'].append(f"Invalid roles found: {invalid_roles}")
        
        # Check for duplicate usernames
        if 'username' in df.columns and df['username'].duplicated().any():
            result['valid'] = False
            result['errors'].append("Duplicate usernames found")
        
        return result
    
    def validate_players_csv(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate players CSV format."""
        required_columns = {'name', 'base_price'}
        
        result = {'valid': True, 'errors': []}
        
        # Check required columns
        if not required_columns.issubset(set(df.columns)):
            missing = required_columns - set(df.columns)
            result['valid'] = False
            result['errors'].append(f"Missing required columns: {missing}")
        
        # Check for empty values in required columns
        for col in required_columns:
            if col in df.columns and df[col].isnull().any():
                result['valid'] = False
                result['errors'].append(f"Empty values found in column: {col}")
        
        # Check base_price is numeric
        if 'base_price' in df.columns:
            try:
                pd.to_numeric(df['base_price'])
            except ValueError:
                result['valid'] = False
                result['errors'].append("base_price must be numeric")
        
        # Check for duplicate player names
        if 'name' in df.columns and df['name'].duplicated().any():
            result['valid'] = False
            result['errors'].append("Duplicate player names found")
        
        return result
    
    def validate_teams_csv(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate teams CSV format."""
        required_columns = {'team_name'}
        
        result = {'valid': True, 'errors': []}
        
        # Check required columns
        if not required_columns.issubset(set(df.columns)):
            missing = required_columns - set(df.columns)
            result['valid'] = False
            result['errors'].append(f"Missing required columns: {missing}")
        
        # Check for empty values
        if 'team_name' in df.columns and df['team_name'].isnull().any():
            result['valid'] = False
            result['errors'].append("Empty team names found")
        
        # Check for duplicate team names
        if 'team_name' in df.columns and df['team_name'].duplicated().any():
            result['valid'] = False
            result['errors'].append("Duplicate team names found")
        
        return result
    
    def upload_users_csv(self, uploaded_file) -> bool:
        """Upload and process users CSV file."""
        try:
            df = pd.read_csv(uploaded_file)
            validation = self.validate_users_csv(df)
            
            if not validation['valid']:
                for error in validation['errors']:
                    st.error(f"Users CSV validation error: {error}")
                return False
            
            success = self.db_manager.bulk_insert_users(df)
            if success:
                st.success(f"Successfully uploaded {len(df)} users")
            else:
                st.error("Failed to upload users to database")
            
            return success
            
        except Exception as e:
            logger.error(f"Error uploading users CSV: {e}")
            st.error(f"Error processing users CSV: {e}")
            return False
    
    def upload_players_csv(self, uploaded_file) -> bool:
        """Upload and process players CSV file."""
        try:
            df = pd.read_csv(uploaded_file)
            
            # Normalize column names to match expected format
            column_mapping = {
                'Name': 'name',
                'name': 'name',
                'Base Price': 'base_price',
                'base_price': 'base_price',
                'BasePrice': 'base_price',
                'Base_Price': 'base_price'
            }
            
            # Rename columns if they exist
            for old_name, new_name in column_mapping.items():
                if old_name in df.columns:
                    df = df.rename(columns={old_name: new_name})
            
            validation = self.validate_players_csv(df)
            
            if not validation['valid']:
                for error in validation['errors']:
                    st.error(f"Players CSV validation error: {error}")
                return False
            
            success = self.db_manager.bulk_insert_players(df)
            if success:
                st.success(f"Successfully uploaded {len(df)} players")
            else:
                st.error("Failed to upload players to database")
            
            return success
            
        except Exception as e:
            logger.error(f"Error uploading players CSV: {e}")
            st.error(f"Error processing players CSV: {e}")
            return False
    
    def upload_teams_csv(self, uploaded_file) -> bool:
        """Upload and process teams CSV file."""
        try:
            df = pd.read_csv(uploaded_file)
            validation = self.validate_teams_csv(df)
            
            if not validation['valid']:
                for error in validation['errors']:
                    st.error(f"Teams CSV validation error: {error}")
                return False
            
            success = self.db_manager.bulk_insert_teams(df)
            if success:
                st.success(f"Successfully uploaded {len(df)} teams")
            else:
                st.error("Failed to upload teams to database")
            
            return success
            
        except Exception as e:
            logger.error(f"Error uploading teams CSV: {e}")
            st.error(f"Error processing teams CSV: {e}")
            return False
    
    def load_initial_data_from_csv(self) -> None:
        """Load initial data from CSV files if tables are empty."""
        try:
            # Load users if table is empty
            if self.db_manager.is_table_empty("users"):
                try:
                    users_df = pd.read_csv("data/users.csv")
                    self.db_manager.bulk_insert_users(users_df)
                    logger.info("Loaded initial users data")
                except FileNotFoundError:
                    logger.warning("No users.csv found in data directory")
            
            # Load teams if table is empty
            if self.db_manager.is_table_empty("teams"):
                try:
                    teams_df = pd.read_csv("data/teams.csv")
                    self.db_manager.bulk_insert_teams(teams_df)
                    logger.info("Loaded initial teams data")
                except FileNotFoundError:
                    logger.warning("No teams.csv found in data directory")
            
            # Load players if table is empty
            if self.db_manager.is_table_empty("players"):
                try:
                    players_df = pd.read_csv("data/players.csv")
                    self.db_manager.bulk_insert_players(players_df)
                    logger.info("Loaded initial players data")
                except FileNotFoundError:
                    logger.warning("No players.csv found in data directory")
                    
        except Exception as e:
            logger.error(f"Error loading initial data: {e}")
            st.error(f"Error loading initial data: {e}")

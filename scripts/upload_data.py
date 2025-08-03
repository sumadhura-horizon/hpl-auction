"""
CSV Data Upload Utility

This script allows you to upload CSV data to the auction database from the command line.
Useful for initial data setup and bulk data updates.
"""

import argparse
import pandas as pd
import sys
import os
from pathlib import Path

# Add the parent directory to Python path to import modules
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from src.core.database import DatabaseManager
from src.utils.file_manager import FileUploadManager


def upload_csv_data(file_path: str, data_type: str) -> bool:
    """Upload CSV data to database."""
    try:
        # Initialize managers
        db_manager = DatabaseManager()
        file_manager = FileUploadManager(db_manager)
        
        # Check if file exists
        if not Path(file_path).exists():
            print(f"Error: File '{file_path}' not found.")
            return False
        
        # Read CSV file
        df = pd.read_csv(file_path)
        print(f"Loaded {len(df)} records from {file_path}")
        
        # Upload based on data type
        if data_type == "users":
            validation = file_manager.validate_users_csv(df)
            if not validation['valid']:
                print("Validation errors:")
                for error in validation['errors']:
                    print(f"  - {error}")
                return False
            success = db_manager.bulk_insert_users(df)
        
        elif data_type == "players":
            validation = file_manager.validate_players_csv(df)
            if not validation['valid']:
                print("Validation errors:")
                for error in validation['errors']:
                    print(f"  - {error}")
                return False
            success = db_manager.bulk_insert_players(df)
        
        elif data_type == "teams":
            validation = file_manager.validate_teams_csv(df)
            if not validation['valid']:
                print("Validation errors:")
                for error in validation['errors']:
                    print(f"  - {error}")
                return False
            success = db_manager.bulk_insert_teams(df)
        
        else:
            print(f"Error: Unknown data type '{data_type}'. Use 'users', 'players', or 'teams'.")
            return False
        
        if success:
            print(f"✅ Successfully uploaded {data_type} data!")
        else:
            print(f"❌ Failed to upload {data_type} data.")
        
        return success
        
    except Exception as e:
        print(f"Error: {e}")
        return False


def reset_database():
    """Reset the database."""
    try:
        db_manager = DatabaseManager()
        db_manager.reset_database()
        print("✅ Database reset successfully!")
        return True
    except Exception as e:
        print(f"Error resetting database: {e}")
        return False


def load_initial_data():
    """Load initial data from CSV files in data directory."""
    try:
        db_manager = DatabaseManager()
        file_manager = FileUploadManager(db_manager)
        file_manager.load_initial_data_from_csv()
        print("✅ Initial data loaded successfully!")
        return True
    except Exception as e:
        print(f"Error loading initial data: {e}")
        return False


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="CSV Data Upload Utility for Auction System")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Upload command
    upload_parser = subparsers.add_parser('upload', help='Upload CSV data')
    upload_parser.add_argument('file_path', help='Path to CSV file')
    upload_parser.add_argument('data_type', choices=['users', 'players', 'teams'], 
                              help='Type of data to upload')
    
    # Reset command
    reset_parser = subparsers.add_parser('reset', help='Reset database')
    
    # Load initial data command
    init_parser = subparsers.add_parser('init', help='Load initial data from data/ directory')
    
    args = parser.parse_args()
    
    if args.command == 'upload':
        success = upload_csv_data(args.file_path, args.data_type)
        sys.exit(0 if success else 1)
    
    elif args.command == 'reset':
        success = reset_database()
        sys.exit(0 if success else 1)
    
    elif args.command == 'init':
        success = load_initial_data()
        sys.exit(0 if success else 1)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

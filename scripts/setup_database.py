#!/usr/bin/env python3
"""
Database setup script for PostgreSQL
Creates database and user for the auction system
"""
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging

# Add project root to path for imports
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)
from config.settings import DATABASE_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database_and_user():
    """Create PostgreSQL database and user."""
    try:
        # Try to connect as different users based on OS
        connection_attempts = [
            # macOS Homebrew default (current user, no password)
            {
                "host": DATABASE_CONFIG["host"],
                "port": DATABASE_CONFIG["port"],
                "database": "postgres",
                "user": os.getenv("USER", "postgres")
            },
            # Linux default (postgres user with password)
            {
                "host": DATABASE_CONFIG["host"],
                "port": DATABASE_CONFIG["port"],
                "database": "postgres",
                "user": "postgres",
                "password": os.getenv("POSTGRES_PASSWORD", "postgres")
            }
        ]
        
        conn = None
        for attempt in connection_attempts:
            try:
                logger.info(f"Trying to connect as user: {attempt['user']}")
                conn = psycopg2.connect(**attempt)
                logger.info("✅ PostgreSQL connection successful")
                break
            except Exception as e:
                logger.warning(f"Failed to connect with {attempt['user']}: {e}")
                continue
        
        if conn is None:
            raise Exception("Could not connect to PostgreSQL with any user")
            
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create user if not exists
        cursor.execute(f"""
            DO
            $do$
            BEGIN
               IF NOT EXISTS (
                  SELECT FROM pg_catalog.pg_roles
                  WHERE  rolname = '{DATABASE_CONFIG["user"]}') THEN
                  
                  CREATE ROLE {DATABASE_CONFIG["user"]} LOGIN PASSWORD '{DATABASE_CONFIG["password"]}';
               END IF;
            END
            $do$;
        """)
        logger.info(f"User {DATABASE_CONFIG['user']} created or already exists")
        
        # Create database if not exists
        cursor.execute(f"""
            SELECT 1 FROM pg_database WHERE datname = '{DATABASE_CONFIG["name"]}'
        """)
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f"CREATE DATABASE {DATABASE_CONFIG['name']} OWNER {DATABASE_CONFIG['user']}")
            logger.info(f"Database {DATABASE_CONFIG['name']} created")
        else:
            logger.info(f"Database {DATABASE_CONFIG['name']} already exists")
            
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        return False

def initialize_tables():
    """Initialize application tables."""
    try:
        # Import after database is created
        from src.core.database import DatabaseManager
        
        db_manager = DatabaseManager()
        db_manager.init_database()
        logger.info("Database tables initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing tables: {e}")
        return False

def main():
    """Main setup function."""
    logger.info("Starting database setup...")
    
    if not create_database_and_user():
        logger.error("Failed to create database and user")
        sys.exit(1)
    
    if not initialize_tables():
        logger.error("Failed to initialize tables")
        sys.exit(1)
    
    logger.info("Database setup completed successfully!")

if __name__ == "__main__":
    main()
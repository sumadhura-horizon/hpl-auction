"""
Configuration management for the auction system.
"""
import os
from typing import Optional


class Config:
    """Application configuration from environment variables."""
    
    # Database Configuration
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: str = os.getenv('DB_PORT', '5432')
    DB_NAME: str = os.getenv('DB_NAME', 'hpl_auction')
    DB_USER: str = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', 'postgres')
    
    # Application Configuration
    APP_PORT: int = int(os.getenv('APP_PORT', '8501'))
    APP_HOST: str = os.getenv('APP_HOST', 'localhost')
    
    # Auction Configuration
    TEAM_BUDGET: int = int(os.getenv('TEAM_BUDGET', '10000000'))  # 1 crore
    REGULAR_PLAYER_MIN_PRICE: int = int(os.getenv('REGULAR_PLAYER_MIN_PRICE', '200000'))  # 2 lakhs
    MARQUEE_PLAYER_MIN_PRICE: int = int(os.getenv('MARQUEE_PLAYER_MIN_PRICE', '1000000'))  # 10 lakhs
    CAPTAIN_PLAYER_PRICE: int = int(os.getenv('CAPTAIN_PLAYER_PRICE', '0'))  # Free
    AUCTION_PRICE_STEP: int = int(os.getenv('AUCTION_PRICE_STEP', '25000'))  # 25k steps
    DEFAULT_PLAYER_BASE_PRICE: int = int(os.getenv('DEFAULT_PLAYER_BASE_PRICE', '200000'))  # 2 lakhs
    PLAYER_BASE_PRICE_STEP: int = int(os.getenv('PLAYER_BASE_PRICE_STEP', '100000'))  # 1 lakh steps
    MAX_PLAYERS_PER_TEAM: int = int(os.getenv('MAX_PLAYERS_PER_TEAM', '9'))  # Including captain
    REGULAR_PLAYERS_NEEDED: int = int(os.getenv('REGULAR_PLAYERS_NEEDED', '8'))  # Excluding captain
    
    # Environment
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def get_database_params(cls) -> dict:
        """Get database connection parameters."""
        return {
            'host': cls.DB_HOST,
            'port': cls.DB_PORT,
            'database': cls.DB_NAME,
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD
        }


# Global config instance
config = Config()
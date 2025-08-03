"""
Configuration settings for the auction system.
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
SCRIPTS_DIR = BASE_DIR / "scripts"

# Database configuration
DATABASE_PATH = BASE_DIR / "auction.db"

# Application settings
APP_TITLE = "Badminton League Auction System"
APP_ICON = "🏸"
DEFAULT_TEAM_BUDGET = 10_000_000

# Streamlit configuration
STREAMLIT_CONFIG = {
    "page_title": APP_TITLE,
    "page_icon": APP_ICON,
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# File paths
LOGO_PATH = ASSETS_DIR / "hbl.png"

# CSV validation rules
CSV_VALIDATION = {
    "users": {
        "required_columns": {"username", "password", "role"},
        "valid_roles": {"admin", "auctioneer", "owner"}
    },
    "players": {
        "required_columns": {"name", "base_price"}
    },
    "teams": {
        "required_columns": {"team_name"}
    }
}

# User roles and permissions
USER_ROLES = {
    "admin": {
        "can_upload_data": True,
        "can_reset_db": True,
        "can_conduct_auction": True,
        "can_undo_auction": True,
        "can_view_all": True
    },
    "auctioneer": {
        "can_upload_data": False,
        "can_reset_db": False,
        "can_conduct_auction": True,
        "can_undo_auction": True,
        "can_view_all": True
    },
    "owner": {
        "can_upload_data": False,
        "can_reset_db": False,
        "can_conduct_auction": False,
        "can_undo_auction": False,
        "can_view_all": True
    }
}

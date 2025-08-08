"""
Data models for the auction system.
"""
from dataclasses import dataclass
from typing import Optional
from .config import config


@dataclass
class User:
    """User model for authentication."""
    id: Optional[int]
    username: str
    password: str
    role: str


@dataclass
class Player:
    """Player model for auction."""
    id: Optional[int]
    name: str
    base_price: int
    owner: Optional[str] = None
    auction_price: int = 0
    category: str = "regular"  # captain, marquee, regular
    photo_url: Optional[str] = None


@dataclass
class Team:
    """Team model."""
    id: Optional[int]
    team_name: str
    budget: int = config.TEAM_BUDGET  # 1 crore default budget
    spent: int = 0
    players_count: int = 0
    captain: Optional[str] = None

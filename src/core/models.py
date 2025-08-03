"""
Data models for the auction system.
"""
from dataclasses import dataclass
from typing import Optional


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


@dataclass
class Team:
    """Team model."""
    id: Optional[int]
    team_name: str

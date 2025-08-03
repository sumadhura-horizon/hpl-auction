"""
Test suite for the auction system.
"""
import pytest
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.database import DatabaseManager
from src.core.auth import AuthManager
from src.core.models import User, Player, Team


class TestDatabase:
    """Test database operations."""
    
    def setup_method(self):
        """Set up test database."""
        self.db = DatabaseManager(":memory:")  # Use in-memory database for tests
    
    def test_database_initialization(self):
        """Test database initialization."""
        # Database should be initialized without errors
        assert self.db is not None
    
    def test_user_authentication(self):
        """Test user authentication."""
        # Create a test user
        import pandas as pd
        users_df = pd.DataFrame([{
            'username': 'testuser',
            'password': 'testpass',
            'role': 'admin'
        }])
        
        self.db.bulk_insert_users(users_df)
        
        # Test authentication
        user = self.db.authenticate_user('testuser', 'testpass')
        assert user is not None
        assert user.username == 'testuser'
        assert user.role == 'admin'
        
        # Test failed authentication
        user = self.db.authenticate_user('testuser', 'wrongpass')
        assert user is None


class TestModels:
    """Test data models."""
    
    def test_user_model(self):
        """Test User model."""
        user = User(id=1, username="test", password="pass", role="admin")
        assert user.username == "test"
        assert user.role == "admin"
    
    def test_player_model(self):
        """Test Player model."""
        player = Player(id=1, name="Test Player", base_price=100000)
        assert player.name == "Test Player"
        assert player.base_price == 100000
        assert player.owner is None
        assert player.auction_price == 0
    
    def test_team_model(self):
        """Test Team model."""
        team = Team(id=1, team_name="Test Team")
        assert team.team_name == "Test Team"


if __name__ == "__main__":
    pytest.main([__file__])

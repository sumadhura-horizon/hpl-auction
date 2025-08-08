#!/usr/bin/env python3
"""
Simple test script to verify authentication is working.
"""

import sys
from pathlib import Path

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from src.core.database import DatabaseManager

def test_authentication():
    """Test authentication functionality."""
    print("🧪 Testing Authentication System")
    print("=" * 40)
    
    try:
        db = DatabaseManager()
        print("✅ Database connection established")
        
        # Test valid login
        print("\n🔐 Testing valid login...")
        user = db.authenticate_user('admin', '!hpl@Sumadhura')
        if user:
            print(f"✅ Admin login successful: {user.username} (role: {user.role})")
        else:
            print("❌ Admin login failed")
            
        # Test invalid login
        print("\n🔐 Testing invalid login...")
        user = db.authenticate_user('admin', 'wrongpassword')
        if user:
            print("❌ Invalid login should have failed")
        else:
            print("✅ Invalid login correctly rejected")
            
        # List all users
        print("\n👥 Users in database:")
        users_df = db.load_users_dataframe()
        for _, user in users_df.iterrows():
            print(f"  - {user['username']} ({user['role']})")
            
        print("\n🎉 Authentication test completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_authentication()

#!/usr/bin/env python3
"""
Quick test script to verify the PostgreSQL setup works
"""
import os
import sys
sys.path.insert(0, '.')

def test_imports():
    """Test if all imports work."""
    try:
        from config.settings import DATABASE_CONFIG, DATABASE_URL
        print("✅ Config imports successful")
        print(f"   Database: {DATABASE_CONFIG['name']}")
        print(f"   Host: {DATABASE_CONFIG['host']}")
        return True
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False

def test_database_connection():
    """Test database connection."""
    try:
        from src.core.database import DatabaseManager
        db = DatabaseManager()
        print("✅ Database manager initialized")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_environment():
    """Test environment setup."""
    if os.path.exists('.env'):
        print("✅ Environment file exists")
    else:
        print("⚠️  Environment file missing (will use defaults)")
    
    if os.path.exists('data/'):
        print("✅ Data directory exists")
    else:
        print("❌ Data directory missing")
        return False
    return True

def main():
    """Run all tests."""
    print("🧪 Testing HPL Auction System Setup")
    print("=" * 40)
    
    tests_passed = 0
    total_tests = 3
    
    if test_environment():
        tests_passed += 1
    
    if test_imports():
        tests_passed += 1
    
    if test_database_connection():
        tests_passed += 1
    
    print("=" * 40)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Setup looks good.")
        return 0
    else:
        print("❌ Some tests failed. Check the setup.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
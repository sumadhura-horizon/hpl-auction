#!/bin/bash

# Badminton League Auction System - Run Script
# This script starts the Streamlit application with proper configuration

echo "🏸 Starting Badminton League Auction System..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

# Initialize database if needed
if [ ! -f "auction.db" ]; then
    echo "📊 Initializing database..."
    python scripts/upload_data.py init
fi

# Start Streamlit application
echo "🚀 Starting Streamlit application..."
echo "📱 Application will be available at: http://localhost:8501"
echo ""
echo "Default login credentials:"
echo "  Admin: admin / !hpl@Sumadhura"
echo "  Auctioneer: auctioneer / Naresh@123"
echo "  Owner: owner1 / owner123"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

streamlit run app.py --server.headless true --server.port 8501

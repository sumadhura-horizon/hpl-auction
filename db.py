from pymongo import MongoClient
from pymongo.server_api import ServerApi

def get_db_connection():
    uri = "mongodb+srv://hpladmin:JBaOfvvuOGaNwD5F@hpl-auction.7xalghe.mongodb.net/?retryWrites=true&w=majority&appName=hpl-auction"
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client['hpl_auction']
    return db

def init_db():
    db = get_db_connection()
    
    # Create collections if they don't exist
    if 'users' not in db.list_collection_names():
        db.create_collection('users')
    if 'players' not in db.list_collection_names():
        db.create_collection('players')
    if 'teams' not in db.list_collection_names():
        db.create_collection('teams')

    print("Database initialized successfully.")
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
uri = os.getenv("MONGODB_URI")
client = MongoClient(uri)
db = client['hpl_auction']

def update_players_collection():
    players = db.players.find({})
    for player in players:
        if 'auction_status' not in player:
            db.players.update_one(
                {'_id': player['_id']},
                {'$set': {'auction_status': 'regular'}}
            )
    print("Players collection updated successfully.")

if __name__ == "__main__":
    update_players_collection()
    print("MongoDB update completed.")
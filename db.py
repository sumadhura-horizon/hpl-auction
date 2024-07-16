import sqlite3

def get_db_connection():
    conn = sqlite3.connect('cricket_auction.db')
    return conn

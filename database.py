import os
import logging
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

import certifi

# Singleton instance of MongoClient for connection pooling
_client = None

def get_db():
    global _client
    if _client is None:
        try:
            # Short timeout (5s) to prevent startup hang on bad connection, added certifi
            _client = MongoClient(
                MONGO_URI, 
                maxPoolSize=10, 
                serverSelectionTimeoutMS=5000, 
                tlsCAFile=certifi.where()
            ) 
            # Trigger a connection attempt
            _client.admin.command('ping')

            logging.info("Initialized shared MongoDB connection pool.")
        except (ServerSelectionTimeoutError, ConnectionFailure) as e:
            logging.error(f"MongoDB connection failed (Timeout/DNS): {e}")
            _client = None # Reset so we can try again later
            return None
        except Exception as e:
            logging.error(f"Unexpected error connecting to MongoDB: {e}")
            _client = None
            return None
    return _client.get_database() if _client else None

def init_db():
    """Initialize database indexes for performance."""
    try:
        db = get_db()
        if db is None:
            logging.warning("Database unreachable. Skipping index initialization.")
            return

        users = db["users"]
        settings = db["settings"]
        
        # Create a unique index on email for O(1) lookups and uniqueness enforcement
        logging.info("Ensuring indexes on collections...")
        users.create_index([("email", ASCENDING)], unique=True)
        
        # Performance indexes for analytics
        db["votes"].create_index([("user_id", ASCENDING)])
        db["votes"].create_index([("candidate_id", ASCENDING)])
        db["votes"].create_index([("timestamp", ASCENDING)])

        # Initialize global settings if they don't exist
        if settings.count_documents({}) == 0:
            logging.info("Initializing global voting settings...")
            settings.insert_one({
                "voting_active": False,
                "end_time": None
            })

        logging.info("Indexes and settings initialized.")
    except Exception as e:
        logging.error(f"Failed to initialize indexes: {e}")

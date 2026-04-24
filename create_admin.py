import os
import bcrypt
import logging
from database import get_db
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

def create_admin():
    try:
        db = get_db()
        users_collection = db["users"]

        # Admin Details
        name = "Vamsi Admin"
        email = "vamsiukkusuri0721@gmail.com"
        password = "vamsi0721" 

        # Check if admin exists (Optimized with field selection)
        if users_collection.find_one({"email": email}, {"_id": 1}):
            logging.info(f"Admin with email {email} already exists.")
            return

        # Hash password (Optimized: rounds=10)
        logging.info("Hashing admin password...")
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=10))

        # Create Admin Object
        admin_user = {
            "name": name,
            "email": email,
            "password": hashed_password,
            "is_admin": True,
            "has_voted": False
        }

        # Insert into DB
        users_collection.insert_one(admin_user)
        logging.info(f"Success: Admin user created successfully!")
        print("-" * 30)
        print(f"Email: {email}")
        print(f"Password: {password}")
        print("-" * 30)
        print("IMPORTANT: Change this password after first login.")

    except Exception as e:
        logging.error(f"Error during admin creation: {e}")

if __name__ == "__main__":
    create_admin()

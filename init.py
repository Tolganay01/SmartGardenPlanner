import os
import sys

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from config import Config

def initialize_database():
    """Initialize the database and create tables"""
    with app.app_context():
        # Create data directory if it doesn't exist
        data_dir = os.path.join(Config.BASE_DIR, 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # Create all tables
        db.create_all()
        print(f"Database created at: {os.path.join(data_dir, 'garden.db')}")
        print("Database initialized successfully!")

if __name__ == '__main__':
    initialize_database()
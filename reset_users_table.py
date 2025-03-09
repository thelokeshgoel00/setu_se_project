import sys
import os
import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base
from app.db_models import User

def reset_users_table():
    """
    Delete and recreate the users table in the SQLite database
    """
    print("Connecting to database...")
    
    # Create a session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Drop the users table if it exists
        print("Dropping users table...")
        session.execute(text("DROP TABLE IF EXISTS users"))
        session.commit()
        print("Users table dropped successfully.")
        
        # Recreate the users table
        print("Recreating users table...")
        Base.metadata.tables['users'].create(bind=engine)
        print("Users table recreated successfully.")
        
        print("Done! The users table has been reset.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    reset_users_table() 
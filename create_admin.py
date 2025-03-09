import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.db_models import Base, User, UserRole
from app.auth import get_password_hash
import argparse

def create_admin_user(username, email, password):
    """Create an admin user in the database"""
    # Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Check if username already exists
        db_user = db.query(User).filter(User.username == username).first()
        if db_user:
            print(f"User with username '{username}' already exists.")
            return False
        
        # Check if email already exists
        db_user = db.query(User).filter(User.email == email).first()
        if db_user:
            print(f"User with email '{email}' already exists.")
            return False
        
        # Create new admin user
        hashed_password = get_password_hash(password)
        db_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            role=UserRole.ADMIN
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        print(f"Admin user '{username}' created successfully.")
        return True
    
    except Exception as e:
        print(f"Error creating admin user: {e}")
        return False
    
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create an admin user")
    parser.add_argument("--username", required=True, help="Admin username")
    parser.add_argument("--email", required=True, help="Admin email")
    parser.add_argument("--password", required=True, help="Admin password")
    
    args = parser.parse_args()
    
    create_admin_user(args.username, args.email, args.password) 
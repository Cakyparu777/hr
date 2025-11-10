"""
Script to create an initial admin user.
Usage: python create_admin.py <email> <password> <name>
"""
import sys
import asyncio
from app.db.dynamodb import create_user, get_user_by_email
from app.core.security import get_password_hash
from dotenv import load_dotenv

load_dotenv()

async def create_admin_user(email: str, password: str, name: str):
    """Create an admin user."""
    # Check if user already exists
    existing_user = await get_user_by_email(email)
    if existing_user:
        print(f"User with email {email} already exists!")
        return
    
    user_data = {
        "name": name,
        "email": email,
        "role": "admin",
        "password_hash": get_password_hash(password)
    }
    
    user = await create_user(user_data)
    print(f"Admin user created successfully!")
    print(f"User ID: {user['user_id']}")
    print(f"Name: {user['name']}")
    print(f"Email: {user['email']}")
    print(f"Role: {user['role']}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python create_admin.py <email> <password> <name>")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    name = sys.argv[3]
    
    asyncio.run(create_admin_user(email, password, name))


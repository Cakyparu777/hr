"""
Create a default admin user if one doesn't exist.
This can be run on startup.
"""
import asyncio
import sys
from app.db.dynamodb import create_user, get_user_by_email
from app.core.security import get_password_hash

async def create_default_admin():
    """Create a default admin user if none exists."""
    default_email = "admin@example.com"
    default_password = "Admin123!"
    default_name = "Admin User"
    
    # Check if admin user already exists
    try:
        existing_user = await get_user_by_email(default_email)
        if existing_user:
            print(f"Admin user {default_email} already exists.")
            return
    except Exception as e:
        # If table doesn't exist or other error, we'll try to create anyway
        print(f"Warning: Could not check for existing admin user: {e}")
    
    # Create admin user
    try:
        user_data = {
            "name": default_name,
            "email": default_email,
            "role": "admin",
            "password_hash": get_password_hash(default_password),
            "must_change_password": False
        }
        
        user = await create_user(user_data)
        print(f"✓ Default admin user created!")
        print(f"  Email: {default_email}")
        print(f"  Password: {default_password}")
        print(f"  ⚠️  Please change the password after first login!")
    except Exception as e:
        print(f"Warning: Could not create default admin user: {e}")
        print("You can create one manually using: python create_admin.py <email> <password> <name>")

if __name__ == "__main__":
    asyncio.run(create_default_admin())


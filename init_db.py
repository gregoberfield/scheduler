#!/usr/bin/env python3
"""
Database initialization script
Creates all tables and optionally creates a test user
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.availability import AvailabilitySlot, AggregateSlotCount

def init_db():
    """Initialize the database"""
    app = create_app('development')
    
    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        print("✓ Tables created successfully!")
        
        # Check if any users exist
        user_count = User.query.count()
        print(f"Current user count: {user_count}")
        
        # Optionally create a test user
        if user_count == 0:
            create_test = input("\nNo users found. Create a test user? (y/n): ").lower()
            if create_test == 'y':
                char_name = input("Character name (default: Testchar): ").strip() or "Testchar"
                wow_class = input("Class (Warrior/Paladin/Hunter/Rogue/Priest/Shaman/Mage/Warlock/Druid, default: Warrior): ").strip() or "Warrior"
                password = input("Password (default: password): ").strip() or "password"
                
                user = User(
                    character_name=char_name,
                    wow_class=wow_class,
                    is_superuser=True,
                    is_admin=True
                )
                user.set_password(password)
                user.set_roles(['tank', 'dps'])
                
                db.session.add(user)
                db.session.commit()
                
                print(f"\n✓ Test user created!")
                print(f"  Character: {char_name}")
                print(f"  Class: {wow_class}")
                print(f"  Password: {password}")
                print(f"  Status: Superuser & Admin")
        
        print("\n✓ Database initialization complete!")
        print(f"Database location: {app.config['SQLALCHEMY_DATABASE_URI']}")

if __name__ == '__main__':
    init_db()

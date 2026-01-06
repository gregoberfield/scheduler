#!/usr/bin/env python3
"""
Database migration script to add group tables.
Run this in production to add the new group feature tables.
"""
import os
import sys
from app import create_app, db
from app.models.group import Group, GroupMembership, GroupInvite

def migrate_database():
    """Add group tables to existing database"""
    print("=== Group Feature Database Migration ===\n")
    
    app = create_app()
    
    with app.app_context():
        # Check if tables already exist
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        print("Existing tables:", ", ".join(existing_tables))
        print()
        
        # Check which group tables need to be created
        group_tables = {
            'groups': Group.__table__,
            'group_memberships': GroupMembership.__table__,
            'group_invites': GroupInvite.__table__
        }
        
        tables_to_create = []
        for table_name, table_obj in group_tables.items():
            if table_name in existing_tables:
                print(f"✓ {table_name} already exists")
            else:
                print(f"✗ {table_name} needs to be created")
                tables_to_create.append((table_name, table_obj))
        
        if not tables_to_create:
            print("\n✓ All group tables already exist. No migration needed.")
            return 0
        
        print(f"\n{len(tables_to_create)} table(s) will be created.")
        
        # Confirm before proceeding
        if os.environ.get('FLASK_ENV') == 'production':
            response = input("\nProceed with migration? (yes/no): ")
            if response.lower() != 'yes':
                print("Migration cancelled.")
                return 1
        
        print("\nCreating tables...")
        try:
            # Create only the missing tables
            for table_name, table_obj in tables_to_create:
                table_obj.create(db.engine)
                print(f"✓ Created {table_name}")
            
            print("\n✓ Migration completed successfully!")
            
            # Verify tables were created
            inspector = inspect(db.engine)
            new_tables = inspector.get_table_names()
            
            print("\nVerifying tables:")
            for table_name in group_tables.keys():
                if table_name in new_tables:
                    print(f"✓ {table_name} verified")
                else:
                    print(f"✗ {table_name} verification failed!")
                    return 1
            
            print("\n✓ All tables verified successfully!")
            return 0
            
        except Exception as e:
            print(f"\n✗ Migration failed: {str(e)}")
            return 1

if __name__ == '__main__':
    sys.exit(migrate_database())

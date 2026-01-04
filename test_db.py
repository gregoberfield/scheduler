#!/usr/bin/env python3
"""Test database connection and configuration"""
import os
import sys
from app import create_app, db
from sqlalchemy import text

def test_database_connection():
    """Test database connection and display configuration"""
    env = os.environ.get('FLASK_ENV', 'development')
    app = create_app(env)
    
    print(f"\n{'='*60}")
    print(f"Database Connection Test")
    print(f"{'='*60}\n")
    
    with app.app_context():
        try:
            # Test basic connection
            db.session.execute(text('SELECT 1'))
            print("✓ Database connection successful\n")
            
            # Display configuration
            print(f"Environment: {env}")
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            
            # Mask password in URI for security
            if '@' in db_uri:
                parts = db_uri.split('@')
                creds = parts[0].split('://')
                if len(creds) > 1 and ':' in creds[1]:
                    user = creds[1].split(':')[0]
                    masked_uri = f"{creds[0]}://{user}:***@{parts[1]}"
                else:
                    masked_uri = db_uri
            else:
                masked_uri = db_uri
            
            print(f"Database URI: {masked_uri}\n")
            
            # Check database type
            if db_uri.startswith('postgresql'):
                print("Database Type: PostgreSQL")
                result = db.session.execute(text('SELECT version()')).scalar()
                print(f"Version: {result.split(',')[0]}\n")
                
                # Display connection pool settings
                engine_opts = app.config.get('SQLALCHEMY_ENGINE_OPTIONS', {})
                print("Connection Pool Settings:")
                print(f"  Pool Size: {engine_opts.get('pool_size', 'default')}")
                print(f"  Max Overflow: {engine_opts.get('max_overflow', 'default')}")
                print(f"  Pool Recycle: {engine_opts.get('pool_recycle', 'default')}s")
                print(f"  Pool Pre-Ping: {engine_opts.get('pool_pre_ping', False)}")
                
                # Check current connections
                result = db.session.execute(text(
                    "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"
                )).scalar()
                print(f"\nCurrent Connections: {result}")
                
                # Check max connections
                max_conn = db.session.execute(text('SHOW max_connections')).scalar()
                print(f"Max Connections (PostgreSQL): {max_conn}")
                
            elif db_uri.startswith('sqlite'):
                print("Database Type: SQLite")
                result = db.session.execute(text('SELECT sqlite_version()')).scalar()
                print(f"Version: {result}")
                
                # Get database file size
                if 'sqlite:///' in db_uri:
                    db_path = db_uri.replace('sqlite:///', '')
                    if os.path.exists(db_path):
                        size = os.path.getsize(db_path)
                        print(f"Database Size: {size:,} bytes ({size/1024/1024:.2f} MB)")
                    else:
                        print(f"Database Path: {db_path} (not yet created)")
            else:
                print(f"Database Type: Unknown ({db_uri.split(':')[0]})")
            
            # Count records in tables
            print(f"\n{'='*60}")
            print("Table Statistics")
            print(f"{'='*60}\n")
            
            try:
                from app.models.user import User
                from app.models.availability import AvailabilitySlot, AggregateSlotCount
                
                user_count = User.query.count()
                slot_count = AvailabilitySlot.query.count()
                agg_count = AggregateSlotCount.query.count()
                
                print(f"Users: {user_count}")
                print(f"Availability Slots: {slot_count}")
                print(f"Aggregate Counts: {agg_count}")
                
                if user_count > 0:
                    print(f"\nSample user data:")
                    sample_user = User.query.first()
                    print(f"  - {sample_user.character_name} ({sample_user.wow_class})")
                
            except Exception as e:
                print(f"Could not query tables: {e}")
                print("Tables may not exist yet. Run database initialization.")
            
            print(f"\n{'='*60}")
            print("✓ All tests passed successfully")
            print(f"{'='*60}\n")
            
            return True
            
        except Exception as e:
            print(f"\n{'='*60}")
            print("✗ Database connection failed")
            print(f"{'='*60}\n")
            print(f"Error: {e}")
            print(f"\nTroubleshooting:")
            
            if 'could not connect to server' in str(e).lower():
                print("  - Check if PostgreSQL is running: sudo systemctl status postgresql")
                print("  - Check connection parameters in DATABASE_URL")
            elif 'password authentication failed' in str(e).lower():
                print("  - Verify database user credentials")
                print("  - Check DATABASE_URL in .env file")
            elif 'database' in str(e).lower() and 'does not exist' in str(e).lower():
                print("  - Create the database: createdb tbc_scheduler")
                print("  - Or run: sudo -u postgres createdb tbc_scheduler")
            else:
                print(f"  - Check DATABASE_URL configuration")
                print(f"  - Verify database server is accessible")
            
            print()
            return False

if __name__ == '__main__':
    success = test_database_connection()
    sys.exit(0 if success else 1)

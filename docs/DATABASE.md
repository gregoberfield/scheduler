# Database Configuration Guide

This guide covers database configuration for both development (SQLite) and production (PostgreSQL) environments.

## Table of Contents
- [Database Support](#database-support)
- [SQLite Configuration (Development)](#sqlite-configuration-development)
- [PostgreSQL Configuration (Production)](#postgresql-configuration-production)
- [Environment Variables](#environment-variables)
- [Connection Pool Settings](#connection-pool-settings)
- [Database Initialization](#database-initialization)
- [Migrations](#migrations)
- [Backup and Restore](#backup-and-restore)

## Database Support

The application supports both databases:

- **SQLite**: Default for development, file-based, zero configuration
- **PostgreSQL**: Recommended for production, better concurrency, connection pooling

The database is automatically selected based on the `DATABASE_URL` environment variable.

## SQLite Configuration (Development)

### Default Configuration

SQLite is used by default when no `DATABASE_URL` is set:

```python
# No configuration needed - uses default
# Database file: instance/tbc_scheduler.db
```

### Custom SQLite Path

Set in `.env`:

```bash
DATABASE_URL=sqlite:////absolute/path/to/database.db
```

### SQLite Advantages
- Zero configuration
- Perfect for development and testing
- Single file, easy to backup
- No separate database server needed

### SQLite Limitations
- Limited concurrent writes
- No built-in connection pooling
- Not recommended for production with multiple workers

## PostgreSQL Configuration (Production)

### Installation

#### Ubuntu/Debian
```bash
sudo apt install postgresql postgresql-contrib
```

#### macOS
```bash
brew install postgresql
brew services start postgresql
```

### Create Database and User

```bash
sudo -u postgres psql
```

```sql
-- Create database
CREATE DATABASE tbc_scheduler;

-- Create user with password
CREATE USER scheduler_user WITH ENCRYPTED PASSWORD 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE tbc_scheduler TO scheduler_user;

-- PostgreSQL 15+ requires additional permissions
\c tbc_scheduler
GRANT ALL ON SCHEMA public TO scheduler_user;

-- Exit
\q
```

### Connection String Format

PostgreSQL connection strings follow this format:

```
postgresql://username:password@host:port/database?options
```

#### Local PostgreSQL (Default Port)
```bash
DATABASE_URL=postgresql://scheduler_user:password@localhost/tbc_scheduler
```

#### Remote PostgreSQL
```bash
DATABASE_URL=postgresql://scheduler_user:password@db.example.com:5432/tbc_scheduler
```

#### With SSL Required
```bash
DATABASE_URL=postgresql://scheduler_user:password@db.example.com:5432/tbc_scheduler?sslmode=require
```

#### Unix Socket Connection
```bash
DATABASE_URL=postgresql://scheduler_user:password@/tbc_scheduler?host=/var/run/postgresql
```

### PostgreSQL Advantages
- Excellent concurrent access
- Connection pooling support
- Better performance under load
- ACID compliant
- Robust for production use

## Environment Variables

### Development (.env)

```bash
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=dev-secret-key

# Database - SQLite (default, can be omitted)
# DATABASE_URL=sqlite:///instance/tbc_scheduler.db

# Or use PostgreSQL in development
# DATABASE_URL=postgresql://scheduler_user:password@localhost/tbc_scheduler_dev
```

### Production (.env.production)

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=generate-strong-secret-key-here

# Database - PostgreSQL
DATABASE_URL=postgresql://scheduler_user:strong_password@localhost/tbc_scheduler

# Connection Pool Settings (PostgreSQL only)
DB_POOL_SIZE=10
DB_POOL_RECYCLE=3600
DB_MAX_OVERFLOW=20
DB_CONNECT_TIMEOUT=10

# Security
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
```

## Connection Pool Settings

These settings only apply to PostgreSQL (ignored by SQLite):

### DB_POOL_SIZE
Number of connections to maintain in the pool.

```bash
DB_POOL_SIZE=10  # Default
```

**Guidelines:**
- Development: 5-10
- Production (single worker): 10-15
- Production (4 workers): 5-10 per worker (total: 20-40)
- Calculate: (workers × pool_size) + max_overflow ≤ PostgreSQL max_connections

### DB_POOL_RECYCLE
Recycle connections after this many seconds.

```bash
DB_POOL_RECYCLE=3600  # Default: 1 hour
```

**Why:** Prevents stale connections and ensures fresh connections periodically.

### DB_MAX_OVERFLOW
Additional connections allowed beyond pool_size.

```bash
DB_MAX_OVERFLOW=20  # Default
```

**Why:** Handles traffic spikes without blocking requests.

### DB_CONNECT_TIMEOUT
Connection timeout in seconds.

```bash
DB_CONNECT_TIMEOUT=10  # Default
```

**Why:** Fail fast if database is unreachable.

### Pool Pre-Ping
Always enabled for PostgreSQL to verify connections before use.

**Why:** Detects and recycles broken connections automatically.

## Database Initialization

### Development (SQLite)

```bash
# Activate virtual environment
source venv/bin/activate

# Initialize database
python3 -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('Database initialized')"
```

### Production (PostgreSQL)

```bash
# Set environment
export FLASK_ENV=production

# Load environment file
source /opt/scheduler/app/.env.production

# Initialize database
/opt/scheduler/venv/bin/python3 -c "from app import create_app, db; app = create_app('production'); app.app_context().push(); db.create_all(); print('Database initialized')"
```

### Initialize Script

Create `init_db.py`:

```python
#!/usr/bin/env python3
"""Initialize the database"""
import os
from app import create_app, db

# Get environment
env = os.environ.get('FLASK_ENV', 'development')

# Create app
app = create_app(env)

with app.app_context():
    # Create all tables
    db.create_all()
    
    print(f"Database initialized for {env} environment")
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
```

Run:
```bash
python3 init_db.py
```

## Migrations

For schema changes after initial deployment, use Flask-Migrate:

### Install Flask-Migrate

```bash
pip install Flask-Migrate
```

Add to `requirements.txt`:
```
Flask-Migrate==4.0.5
```

### Setup Migrations

Update `app/__init__.py`:

```python
from flask_migrate import Migrate

migrate = Migrate()

def create_app(config_name=None):
    # ... existing code ...
    
    migrate.init_app(app, db)
    
    # ... rest of code ...
```

### Initialize Migrations

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### Future Schema Changes

```bash
# Make changes to models
# Then create migration
flask db migrate -m "Description of changes"

# Review migration file in migrations/versions/
# Apply migration
flask db upgrade
```

## Backup and Restore

### SQLite Backup

```bash
# Backup
cp instance/tbc_scheduler.db backups/tbc_scheduler_$(date +%Y%m%d).db

# Restore
cp backups/tbc_scheduler_20260104.db instance/tbc_scheduler.db
```

### PostgreSQL Backup

```bash
# Backup entire database
pg_dump -U scheduler_user -h localhost tbc_scheduler > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup with compression
pg_dump -U scheduler_user -h localhost tbc_scheduler | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Backup specific tables
pg_dump -U scheduler_user -h localhost -t users -t availability_slots tbc_scheduler > partial_backup.sql
```

### PostgreSQL Restore

```bash
# Restore from SQL dump
psql -U scheduler_user -h localhost tbc_scheduler < backup_20260104_120000.sql

# Restore from compressed dump
gunzip -c backup_20260104_120000.sql.gz | psql -U scheduler_user -h localhost tbc_scheduler

# Restore to new database
createdb -U postgres tbc_scheduler_restored
psql -U scheduler_user -h localhost tbc_scheduler_restored < backup_20260104_120000.sql
```

### Automated Backups

Create `/opt/scheduler/backup_db.sh`:

```bash
#!/bin/bash
# Automated PostgreSQL backup script

BACKUP_DIR="/opt/scheduler/backups"
DB_NAME="tbc_scheduler"
DB_USER="scheduler_user"
DATE=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS=14

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
pg_dump -U $DB_USER -h localhost $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Verify backup
if [ $? -eq 0 ]; then
    echo "Backup successful: db_backup_$DATE.sql.gz"
else
    echo "Backup failed!"
    exit 1
fi

# Remove old backups
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +$KEEP_DAYS -delete

# Optional: Upload to remote storage
# aws s3 cp $BACKUP_DIR/db_backup_$DATE.sql.gz s3://your-bucket/scheduler-backups/
```

Schedule with cron:
```bash
# Daily backup at 2 AM
0 2 * * * /opt/scheduler/backup_db.sh >> /opt/scheduler/logs/backup.log 2>&1
```

## Database Maintenance

### PostgreSQL Maintenance

#### Vacuum (Cleanup)
```sql
-- Vacuum specific tables
VACUUM ANALYZE availability_slots;
VACUUM ANALYZE aggregate_slot_counts;

-- Vacuum entire database
VACUUM ANALYZE;
```

#### Reindex
```sql
-- Reindex for better performance
REINDEX DATABASE tbc_scheduler;
```

#### Check Database Size
```sql
-- Database size
SELECT pg_size_pretty(pg_database_size('tbc_scheduler'));

-- Table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### SQLite Maintenance

```bash
# Vacuum database
sqlite3 instance/tbc_scheduler.db "VACUUM;"

# Check integrity
sqlite3 instance/tbc_scheduler.db "PRAGMA integrity_check;"

# Database size
ls -lh instance/tbc_scheduler.db
```

## Testing Database Configuration

### Test Connection Script

Create `test_db.py`:

```python
#!/usr/bin/env python3
"""Test database connection"""
import os
from app import create_app, db
from sqlalchemy import text

env = os.environ.get('FLASK_ENV', 'development')
app = create_app(env)

with app.app_context():
    try:
        # Test connection
        db.session.execute(text('SELECT 1'))
        
        print(f"✓ Database connection successful")
        print(f"  Environment: {env}")
        print(f"  Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        # Check if using PostgreSQL or SQLite
        if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgresql'):
            result = db.session.execute(text('SELECT version()')).scalar()
            print(f"  PostgreSQL Version: {result}")
            
            # Check pool settings
            print(f"  Pool Size: {app.config['SQLALCHEMY_ENGINE_OPTIONS']['pool_size']}")
            print(f"  Max Overflow: {app.config['SQLALCHEMY_ENGINE_OPTIONS']['max_overflow']}")
        else:
            print(f"  Using SQLite")
            
        # Count records
        from app.models.user import User
        from app.models.availability import AvailabilitySlot, AggregateSlotCount
        
        print(f"\nTable counts:")
        print(f"  Users: {User.query.count()}")
        print(f"  Availability Slots: {AvailabilitySlot.query.count()}")
        print(f"  Aggregate Counts: {AggregateSlotCount.query.count()}")
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        exit(1)
```

Run:
```bash
python3 test_db.py
```

## Troubleshooting

### PostgreSQL Connection Refused

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql

# Check if it's listening
sudo netstat -plunt | grep postgres
```

### Authentication Failed

```bash
# Verify user exists
sudo -u postgres psql -c "\du"

# Reset password
sudo -u postgres psql -c "ALTER USER scheduler_user WITH PASSWORD 'new_password';"
```

### Too Many Connections

```sql
-- Check current connections
SELECT count(*) FROM pg_stat_activity WHERE datname = 'tbc_scheduler';

-- Check max connections
SHOW max_connections;

-- Kill idle connections
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE datname = 'tbc_scheduler' 
  AND state = 'idle' 
  AND state_change < current_timestamp - interval '10 minutes';
```

Adjust pool settings in `.env.production`:
```bash
DB_POOL_SIZE=5  # Reduce pool size
DB_MAX_OVERFLOW=10  # Reduce overflow
```

### SQLite Database Locked

```bash
# Check for processes using the database
lsof instance/tbc_scheduler.db

# Kill processes if needed
# Then restart application
```

---

**Last Updated:** January 2026  
**Version:** 1.0

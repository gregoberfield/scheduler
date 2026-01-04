# Database Configuration - Summary of Changes

## What Changed

The application now supports both SQLite (development) and PostgreSQL (production) databases with proper configuration.

## Files Modified

### 1. `config.py`
- **Changed**: Database URI now uses absolute path for SQLite
- **Added**: PostgreSQL connection pool settings
- **Added**: Database-specific engine options

**Before:**
```python
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///scheduler.db'
```

**After:**
```python
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'tbc_scheduler.db')
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': int(os.environ.get('DB_POOL_SIZE', '10')),
    'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', '3600')),
    'pool_pre_ping': True,
    'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', '20')),
    'connect_args': {
        'connect_timeout': int(os.environ.get('DB_CONNECT_TIMEOUT', '10'))
    } if os.environ.get('DATABASE_URL', '').startswith('postgresql') else {}
}
```

### 2. `requirements.txt`
- **Added**: `psycopg2-binary==2.9.9` for PostgreSQL support

### 3. `.env`
- **Changed**: Commented out DATABASE_URL to use config.py default
- **Added**: Comments explaining PostgreSQL option

### 4. `.env.example`
- **Updated**: Shows both SQLite and PostgreSQL configuration examples
- **Added**: PostgreSQL connection pool environment variables

## New Files

### 1. `docs/DATABASE.md`
Comprehensive database configuration guide covering:
- SQLite vs PostgreSQL comparison
- Connection string formats
- Environment variables
- Connection pool settings
- Backup and restore procedures
- Maintenance tasks
- Troubleshooting

### 2. `test_db.py`
Database connection test script that:
- Tests database connectivity
- Displays configuration details
- Shows connection pool settings (PostgreSQL)
- Counts records in tables
- Provides troubleshooting hints

## How to Use

### Development (SQLite - Default)

Just run the application - no configuration needed:
```bash
python3 run.py
```

Database file: `instance/tbc_scheduler.db`

### Development (PostgreSQL - Optional)

1. Create PostgreSQL database:
```bash
sudo -u postgres psql
CREATE DATABASE tbc_scheduler_dev;
CREATE USER scheduler_user WITH PASSWORD 'devpassword';
GRANT ALL PRIVILEGES ON DATABASE tbc_scheduler_dev TO scheduler_user;
\q
```

2. Update `.env`:
```bash
DATABASE_URL=postgresql://scheduler_user:devpassword@localhost/tbc_scheduler_dev
```

3. Initialize database:
```bash
python3 -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

### Production (PostgreSQL)

1. Follow deployment guide in `docs/DEPLOYMENT.md`

2. Create `.env.production`:
```bash
FLASK_ENV=production
SECRET_KEY=generate-strong-key
DATABASE_URL=postgresql://scheduler_user:strong_password@localhost/tbc_scheduler
DB_POOL_SIZE=10
DB_POOL_RECYCLE=3600
DB_MAX_OVERFLOW=20
SESSION_COOKIE_SECURE=True
```

3. Initialize database and run:
```bash
export FLASK_ENV=production
python3 -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
gunicorn 'run:app'
```

## Testing Database Connection

Run the test script:
```bash
python3 test_db.py
```

Expected output:
```
============================================================
Database Connection Test
============================================================

✓ Database connection successful

Environment: development
Database URI: sqlite:////absolute/path/instance/tbc_scheduler.db

Database Type: SQLite
Version: 3.45.1
Database Size: 40,960 bytes (0.04 MB)

============================================================
Table Statistics
============================================================

Users: 3
Availability Slots: 182
Aggregate Counts: 98

Sample user data:
  - Tularemia (Warlock)

============================================================
✓ All tests passed successfully
============================================================
```

## PostgreSQL Connection Pool Settings

These environment variables control PostgreSQL connection pooling (ignored by SQLite):

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_POOL_SIZE` | 10 | Number of connections to maintain |
| `DB_POOL_RECYCLE` | 3600 | Recycle connections after N seconds |
| `DB_MAX_OVERFLOW` | 20 | Additional connections beyond pool_size |
| `DB_CONNECT_TIMEOUT` | 10 | Connection timeout in seconds |

**Important**: 
- Total connections = `DB_POOL_SIZE` + `DB_MAX_OVERFLOW`
- With 4 Gunicorn workers and pool_size=10, max_overflow=20:
  - Maximum connections = 4 × (10 + 20) = 120
- Ensure PostgreSQL `max_connections` > total connections needed

## Migration from Old Database

If you have data in `instance/scheduler.db` (old name), copy it:
```bash
cp instance/scheduler.db instance/tbc_scheduler.db
```

## Database File Names

- **Development**: `instance/tbc_scheduler.db` (SQLite)
- **Production**: PostgreSQL database named `tbc_scheduler`
- **Old name** (deprecated): `scheduler.db` or `instance/scheduler.db`

## Environment-Specific Configuration

The application automatically selects the correct database based on `DATABASE_URL`:

- **Not set**: Uses SQLite at `instance/tbc_scheduler.db`
- **Starts with `sqlite://`**: Uses SQLite at specified path
- **Starts with `postgresql://`**: Uses PostgreSQL with connection pooling

## Troubleshooting

### "Cannot access database file"
- Check file permissions
- Ensure `instance/` directory exists
- Run: `mkdir -p instance`

### "Connection refused" (PostgreSQL)
- Check if PostgreSQL is running: `sudo systemctl status postgresql`
- Verify connection string in `DATABASE_URL`
- Test connection: `python3 test_db.py`

### "Too many connections" (PostgreSQL)
- Reduce `DB_POOL_SIZE` and `DB_MAX_OVERFLOW`
- Check active connections: `SELECT count(*) FROM pg_stat_activity;`
- Increase PostgreSQL `max_connections` in `postgresql.conf`

## Additional Resources

- Full deployment guide: [docs/DEPLOYMENT.md](DEPLOYMENT.md)
- Database guide: [docs/DATABASE.md](DATABASE.md)
- PostgreSQL documentation: https://www.postgresql.org/docs/

---

**Summary**: The application now properly supports both SQLite (development) and PostgreSQL (production) with appropriate connection pooling, making it production-ready for deployment on Ubuntu VMs while maintaining easy development setup.

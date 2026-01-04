# Production Environment Variables Reference

Quick reference for production `.env.production` configuration.

## Minimal Production Configuration

```bash
# Flask Configuration
FLASK_ENV=production
FLASK_APP=run.py
SECRET_KEY=GENERATE_WITH_python3 -c 'import secrets; print(secrets.token_hex(32))'

# Database - PostgreSQL
DATABASE_URL=postgresql://scheduler_user:STRONG_PASSWORD@localhost/tbc_scheduler

# Security
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

## Full Production Configuration

```bash
# =============================================================================
# Flask Configuration
# =============================================================================
FLASK_ENV=production
FLASK_APP=run.py

# Generate strong secret key:
# python3 -c 'import secrets; print(secrets.token_hex(32))'
SECRET_KEY=your-generated-secret-key-here

# =============================================================================
# Database Configuration - PostgreSQL
# =============================================================================
DATABASE_URL=postgresql://scheduler_user:strong_password@localhost/tbc_scheduler

# Connection Pool Settings
# Total connections per worker = DB_POOL_SIZE + DB_MAX_OVERFLOW
# With 4 workers: max total = 4 × (10 + 20) = 120 connections
DB_POOL_SIZE=10
DB_POOL_RECYCLE=3600
DB_MAX_OVERFLOW=20
DB_CONNECT_TIMEOUT=10

# =============================================================================
# Security Configuration
# =============================================================================
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# =============================================================================
# Rate Limiting (Optional - requires Redis)
# =============================================================================
# Install Redis: sudo apt install redis-server
# RATELIMIT_STORAGE_URL=redis://localhost:6379

# =============================================================================
# Server Configuration (Optional)
# =============================================================================
# SERVER_NAME=your-domain.com
# PREFERRED_URL_SCHEME=https
```

## Environment Variable Descriptions

### Required Variables

| Variable | Example | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `production` | Sets production mode (disables debug) |
| `SECRET_KEY` | `6b1dc185...` | Cryptographic key for sessions (MUST be strong) |
| `DATABASE_URL` | `postgresql://user:pass@host/db` | PostgreSQL connection string |

### PostgreSQL Connection Pool

| Variable | Default | Description | Recommended |
|----------|---------|-------------|-------------|
| `DB_POOL_SIZE` | 10 | Connections per worker | 5-10 per worker |
| `DB_POOL_RECYCLE` | 3600 | Recycle after seconds | 3600 (1 hour) |
| `DB_MAX_OVERFLOW` | 20 | Extra connections | 10-20 per worker |
| `DB_CONNECT_TIMEOUT` | 10 | Timeout in seconds | 10-30 |

### Security Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `SESSION_COOKIE_SECURE` | False | Require HTTPS for cookies (MUST be True in production) |
| `SESSION_COOKIE_HTTPONLY` | True | Prevent JavaScript access to cookies |
| `SESSION_COOKIE_SAMESITE` | Lax | CSRF protection |

## Calculating Connection Pool Size

### Formula
```
Total Connections = (Number of Workers) × (DB_POOL_SIZE + DB_MAX_OVERFLOW)
```

### Examples

**4 Gunicorn workers, default settings:**
```
Total = 4 × (10 + 20) = 120 connections
```

**4 Gunicorn workers, conservative settings:**
```
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
Total = 4 × (5 + 10) = 60 connections
```

**Ensure PostgreSQL max_connections > Total Connections**
```sql
-- Check PostgreSQL max_connections
SHOW max_connections;

-- Typically 100-200, increase if needed in postgresql.conf
```

## Creating the .env.production File

### Method 1: Manual Creation

```bash
sudo nano /opt/scheduler/app/.env.production
```

Paste the configuration, then save.

### Method 2: Using Script

```bash
#!/bin/bash
# create_env_production.sh

# Generate secret key
SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(32))')

# Create .env.production
cat > /opt/scheduler/app/.env.production << EOF
# Flask Configuration
FLASK_ENV=production
FLASK_APP=run.py
SECRET_KEY=$SECRET

# Database - PostgreSQL
DATABASE_URL=postgresql://scheduler_user:CHANGE_PASSWORD@localhost/tbc_scheduler

# Connection Pool Settings
DB_POOL_SIZE=10
DB_POOL_RECYCLE=3600
DB_MAX_OVERFLOW=20
DB_CONNECT_TIMEOUT=10

# Security
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
EOF

echo "Created .env.production with generated SECRET_KEY"
echo "IMPORTANT: Edit file and change database password!"
```

Run:
```bash
chmod +x create_env_production.sh
./create_env_production.sh
```

### Method 3: Copy from Example

```bash
cp .env.example .env.production
nano .env.production
# Edit values
```

## Securing the .env.production File

```bash
# Set proper ownership
sudo chown scheduler:scheduler /opt/scheduler/app/.env.production

# Restrict permissions (owner read/write only)
sudo chmod 600 /opt/scheduler/app/.env.production

# Verify
ls -la /opt/scheduler/app/.env.production
# Should show: -rw------- 1 scheduler scheduler
```

## Testing Configuration

```bash
# Load environment
cd /opt/scheduler/app
source .env.production

# Test configuration
python3 -c "
from config import config
import os
conf = config['production']
print(f'Environment: {os.environ.get(\"FLASK_ENV\")}')
print(f'Database: {conf.SQLALCHEMY_DATABASE_URI.split(\"@\")[0].split(\":\")[0]}://...')
print(f'Pool Size: {conf.SQLALCHEMY_ENGINE_OPTIONS[\"pool_size\"]}')
print(f'Secure Cookies: {conf.SESSION_COOKIE_SECURE}')
"

# Test database connection
python3 test_db.py
```

## Environment Variable Loading Order

1. System environment variables
2. `.env.production` file (loaded by `python-dotenv`)
3. `config.py` defaults (if not set in above)

## Common Mistakes to Avoid

❌ **Don't:**
- Use weak SECRET_KEY
- Forget to set SESSION_COOKIE_SECURE=True
- Use SQLite in production with multiple workers
- Set DATABASE_URL with visible password in commands
- Commit .env.production to version control
- Leave default passwords

✅ **Do:**
- Generate strong SECRET_KEY (min 32 characters)
- Use PostgreSQL for production
- Calculate connection pool based on workers
- Restrict .env.production permissions (600)
- Use strong database passwords
- Test configuration before deployment

## Quick Deployment Checklist

- [ ] PostgreSQL installed and running
- [ ] Database and user created
- [ ] .env.production created with strong credentials
- [ ] File permissions set (600)
- [ ] SECRET_KEY generated (not default)
- [ ] DATABASE_URL uses PostgreSQL
- [ ] SESSION_COOKIE_SECURE=True
- [ ] Connection pool sized appropriately
- [ ] Configuration tested with test_db.py
- [ ] Database initialized (db.create_all())

## Additional Resources

- Deployment Guide: [docs/DEPLOYMENT.md](DEPLOYMENT.md)
- Database Guide: [docs/DATABASE.md](DATABASE.md)
- Changes Summary: [docs/DATABASE_CHANGES.md](DATABASE_CHANGES.md)

---

**Important**: Never commit `.env.production` to version control. Add it to `.gitignore`.

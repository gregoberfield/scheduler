# Production Deployment Guide

This guide covers deploying the TBC Launch Availability Scheduler on an Ubuntu VM without Docker.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Initial Server Setup](#initial-server-setup)
- [Installing Dependencies](#installing-dependencies)
- [Application Setup](#application-setup)
- [Database Configuration](#database-configuration)
- [Systemd Service Configuration](#systemd-service-configuration)
- [Nginx Configuration](#nginx-configuration)
- [SSL/TLS Setup](#ssltls-setup)
- [Deployment Process](#deployment-process)
- [Monitoring and Logs](#monitoring-and-logs)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Ubuntu 20.04 LTS or newer
- SSH access with sudo privileges
- GitHub repository access
- Domain name (optional, for SSL)
- At least 1GB RAM, 10GB disk space

## Initial Server Setup

### 1. Update System Packages

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Create Application User

```bash
sudo adduser --system --group --home /opt/scheduler scheduler
sudo usermod -aG www-data scheduler
```

### 3. Configure Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## Installing Dependencies

### 1. Install Python and Required Tools

```bash
sudo apt install -y python3.11 python3.11-venv python3-pip git nginx
```

### 2. Install PostgreSQL (Production Database)

```bash
sudo apt install -y postgresql postgresql-contrib
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

### 3. Install Supervisor (Process Manager)

```bash
sudo apt install -y supervisor
sudo systemctl enable supervisor
sudo systemctl start supervisor
```

## Application Setup

### 1. Clone Repository

```bash
sudo mkdir -p /opt/scheduler
sudo chown scheduler:scheduler /opt/scheduler
sudo -u scheduler git clone https://github.com/YOUR_USERNAME/scheduler.git /opt/scheduler/app
cd /opt/scheduler/app
```

### 2. Create Virtual Environment

```bash
sudo -u scheduler python3.11 -m venv /opt/scheduler/venv
```

### 3. Install Python Dependencies

```bash
sudo -u scheduler /opt/scheduler/venv/bin/pip install --upgrade pip
sudo -u scheduler /opt/scheduler/venv/bin/pip install -r /opt/scheduler/app/requirements.txt
sudo -u scheduler /opt/scheduler/venv/bin/pip install gunicorn psycopg2-binary
```

### 4. Create Required Directories

```bash
sudo -u scheduler mkdir -p /opt/scheduler/app/instance
sudo -u scheduler mkdir -p /opt/scheduler/logs
sudo -u scheduler mkdir -p /opt/scheduler/app/app/static/img/classes
```

### 5. Download Class Icons

```bash
cd /opt/scheduler/app
sudo -u scheduler bash create_icons.sh
```

## Database Configuration

### 1. Create PostgreSQL Database and User

```bash
sudo -u postgres psql
```

In PostgreSQL shell:

```sql
CREATE DATABASE tbc_scheduler;
CREATE USER scheduler_user WITH ENCRYPTED PASSWORD 'STRONG_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON DATABASE tbc_scheduler TO scheduler_user;

-- Connect to the database
\c tbc_scheduler

-- Grant schema permissions (required for PostgreSQL 15+)
GRANT ALL ON SCHEMA public TO scheduler_user;
GRANT CREATE ON SCHEMA public TO scheduler_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO scheduler_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO scheduler_user;

\q
```

### 2. Create Production Configuration

Create `/opt/scheduler/app/.env.production`:

```bash
sudo -u scheduler tee /opt/scheduler/app/.env.production > /dev/null << 'EOF'
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=GENERATE_STRONG_SECRET_KEY_HERE

# Database Configuration
DATABASE_URL=postgresql://scheduler_user:STRONG_PASSWORD_HERE@localhost/tbc_scheduler

# Server Configuration
SERVER_NAME=your-domain.com
PREFERRED_URL_SCHEME=https

# Rate Limiting (if using Redis)
# RATELIMIT_STORAGE_URL=redis://localhost:6379

# Session Configuration
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# Security Headers
SEND_FILE_MAX_AGE_DEFAULT=31536000
EOF
```

**Generate a strong secret key:**

```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

### 3. Initialize Database

```bash
cd /opt/scheduler/app
sudo -u scheduler /opt/scheduler/venv/bin/python3 -c "
from app import create_app, db
import os
os.environ['FLASK_ENV'] = 'production'
app = create_app()
with app.app_context():
    db.create_all()
    print('Database initialized successfully')
"
```

### 4. Create Initial Admin User

```bash
sudo -u scheduler /opt/scheduler/venv/bin/python3 create_admin.py
```

## Systemd Service Configuration

### 1. Create Gunicorn Service

Create `/etc/systemd/system/scheduler.service`:

```ini
[Unit]
Description=TBC Launch Scheduler - Gunicorn Service
After=network.target postgresql.service

[Service]
Type=notify
User=scheduler
Group=scheduler
WorkingDirectory=/opt/scheduler/app
Environment="PATH=/opt/scheduler/venv/bin"
Environment="FLASK_ENV=production"
EnvironmentFile=/opt/scheduler/app/.env.production

ExecStart=/opt/scheduler/venv/bin/gunicorn \
    --workers 4 \
    --worker-class sync \
    --bind unix:/opt/scheduler/scheduler.sock \
    --access-logfile /opt/scheduler/logs/access.log \
    --error-logfile /opt/scheduler/logs/error.log \
    --log-level info \
    --timeout 120 \
    'run:app'

ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable scheduler.service
sudo systemctl start scheduler.service
sudo systemctl status scheduler.service
```

## Nginx Configuration

### 1. Create Nginx Site Configuration

Create `/etc/nginx/sites-available/scheduler`:

```nginx
upstream scheduler_app {
    server unix:/opt/scheduler/scheduler.sock fail_timeout=0;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Redirect to HTTPS (after SSL is configured)
    # return 301 https://$server_name$request_uri;

    client_max_body_size 4M;
    client_body_buffer_size 128k;

    access_log /var/log/nginx/scheduler-access.log;
    error_log /var/log/nginx/scheduler-error.log;

    location /static {
        alias /opt/scheduler/app/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_buffering off;
        proxy_pass http://scheduler_app;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

### 2. Enable Site and Restart Nginx

```bash
sudo ln -s /etc/nginx/sites-available/scheduler /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## SSL/TLS Setup

### 1. Install Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 2. Obtain SSL Certificate

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### 3. Auto-Renewal

Certbot automatically sets up renewal. Test it:

```bash
sudo certbot renew --dry-run
```

### 4. Update Nginx Configuration for HTTPS

Certbot will automatically update your Nginx configuration. Verify the changes:

```bash
sudo cat /etc/nginx/sites-available/scheduler
```

The configuration should now include:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # ... rest of configuration
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

## Deployment Process

### Initial Deployment

Already covered in the sections above.

### Deploying Updates

When you need to deploy code updates from GitHub:

```bash
#!/bin/bash
# Save as /opt/scheduler/deploy.sh

set -e

echo "=== Starting Deployment ==="

# Navigate to app directory
cd /opt/scheduler/app

# Backup database (if using SQLite, for PostgreSQL use pg_dump)
echo "Creating database backup..."
sudo -u postgres pg_dump tbc_scheduler > /opt/scheduler/backups/db_backup_$(date +%Y%m%d_%H%M%S).sql

# Pull latest code
echo "Pulling latest code from GitHub..."
sudo -u scheduler git fetch origin
sudo -u scheduler git reset --hard origin/master

# Update dependencies
echo "Updating Python dependencies..."
sudo -u scheduler /opt/scheduler/venv/bin/pip install -r requirements.txt

# Run database migrations (if applicable)
echo "Running database migrations..."
# If you add migrations, run them here

# Rebuild aggregates (if needed)
echo "Rebuilding aggregate counts..."
sudo -u scheduler /opt/scheduler/venv/bin/python3 rebuild_aggregates.py

# Restart application
echo "Restarting application..."
sudo systemctl restart scheduler.service

# Wait for service to be ready
sleep 3

# Check service status
echo "Checking service status..."
sudo systemctl status scheduler.service --no-pager

echo "=== Deployment Complete ==="
```

Make the script executable:

```bash
sudo chmod +x /opt/scheduler/deploy.sh
```

### Rolling Back

If deployment fails, roll back to previous version:

```bash
cd /opt/scheduler/app
sudo -u scheduler git log --oneline -n 10  # Find commit hash
sudo -u scheduler git reset --hard COMMIT_HASH
sudo systemctl restart scheduler.service
```

## Monitoring and Logs

### Application Logs

```bash
# Gunicorn access logs
sudo tail -f /opt/scheduler/logs/access.log

# Gunicorn error logs
sudo tail -f /opt/scheduler/logs/error.log

# Systemd service logs
sudo journalctl -u scheduler.service -f

# Nginx access logs
sudo tail -f /var/log/nginx/scheduler-access.log

# Nginx error logs
sudo tail -f /var/log/nginx/scheduler-error.log
```

### Service Status

```bash
# Check scheduler service
sudo systemctl status scheduler.service

# Check nginx
sudo systemctl status nginx

# Check PostgreSQL
sudo systemctl status postgresql
```

### Database Access

```bash
# Connect to PostgreSQL
sudo -u postgres psql tbc_scheduler

# Common queries
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM availability_slots;
SELECT COUNT(*) FROM aggregate_slot_counts;
```

### Log Rotation

Create `/etc/logrotate.d/scheduler`:

```
/opt/scheduler/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 scheduler scheduler
    sharedscripts
    postrotate
        systemctl reload scheduler.service > /dev/null
    endscript
}
```

## Troubleshooting

### Service Won't Start

```bash
# Check service logs
sudo journalctl -u scheduler.service -n 50

# Check if socket file exists
ls -l /opt/scheduler/scheduler.sock

# Check file permissions
sudo ls -la /opt/scheduler/app/

# Verify virtual environment
sudo -u scheduler /opt/scheduler/venv/bin/python3 --version
```

### 502 Bad Gateway

```bash
# Check if Gunicorn is running
sudo systemctl status scheduler.service

# Check Nginx error logs
sudo tail -f /var/log/nginx/scheduler-error.log

# Verify socket permissions
sudo ls -l /opt/scheduler/scheduler.sock

# Test Gunicorn manually
sudo -u scheduler /opt/scheduler/venv/bin/gunicorn --bind 127.0.0.1:8000 'run:app'
```

### Database Connection Issues

```bash
# Verify PostgreSQL is running
sudo systemctl status postgresql

# Test database connection
sudo -u postgres psql -c "\l" | grep tbc_scheduler

# Check connection string in .env.production
sudo cat /opt/scheduler/app/.env.production | grep DATABASE_URL

# Test connection from Python
sudo -u scheduler /opt/scheduler/venv/bin/python3 -c "
import os
os.environ['DATABASE_URL'] = 'postgresql://scheduler_user:PASSWORD@localhost/tbc_scheduler'
from sqlalchemy import create_engine
engine = create_engine(os.environ['DATABASE_URL'])
conn = engine.connect()
print('Connection successful')
conn.close()
"
```

### High Memory Usage

```bash
# Check process memory usage
ps aux | grep gunicorn

# Reduce number of workers in systemd service
# Edit /etc/systemd/system/scheduler.service
# Change --workers 4 to --workers 2

sudo systemctl daemon-reload
sudo systemctl restart scheduler.service
```

### Aggregates Not Updating

```bash
# Manually rebuild aggregates
cd /opt/scheduler/app
sudo -u scheduler /opt/scheduler/venv/bin/python3 rebuild_aggregates.py

# Check for event listener errors in logs
sudo journalctl -u scheduler.service | grep -i aggregate
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R scheduler:scheduler /opt/scheduler/app
sudo chown -R scheduler:scheduler /opt/scheduler/logs

# Fix socket permissions
sudo chown scheduler:www-data /opt/scheduler/scheduler.sock
```

## Security Checklist

- [ ] Strong database password set
- [ ] Strong Flask SECRET_KEY generated
- [ ] SSL/TLS certificate installed
- [ ] Firewall configured (UFW)
- [ ] Only necessary ports open (80, 443, 22)
- [ ] SSH key authentication enabled
- [ ] Application running as non-root user
- [ ] Security headers configured in Nginx
- [ ] Database backups configured
- [ ] Log rotation configured
- [ ] `.env.production` file protected (600 permissions)
- [ ] Debug mode disabled (FLASK_ENV=production)
- [ ] Session cookies set to secure

## Performance Optimization

### 1. Enable Gzip Compression

Add to Nginx configuration:

```nginx
gzip on;
gzip_vary on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript;
```

### 2. Enable Redis for Rate Limiting (Optional)

```bash
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Update .env.production
echo "RATELIMIT_STORAGE_URL=redis://localhost:6379" | sudo tee -a /opt/scheduler/app/.env.production
```

### 3. Database Optimization

```sql
-- Add indexes for frequently queried columns
CREATE INDEX IF NOT EXISTS idx_availability_user_slot ON availability_slots(user_id, slot_index);
CREATE INDEX IF NOT EXISTS idx_availability_slot_state ON availability_slots(slot_index, state);
CREATE INDEX IF NOT EXISTS idx_aggregate_slot ON aggregate_slot_counts(slot_index);

-- Analyze tables for query optimization
ANALYZE availability_slots;
ANALYZE aggregate_slot_counts;
```

## Backup Strategy

### Automated Database Backups

Create `/opt/scheduler/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/scheduler/backups"
DATE=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS=14

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup PostgreSQL database
sudo -u postgres pg_dump tbc_scheduler | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Remove old backups
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +$KEEP_DAYS -delete

echo "Backup completed: db_backup_$DATE.sql.gz"
```

Add to crontab:

```bash
sudo crontab -e

# Add this line for daily 2 AM backups
0 2 * * * /opt/scheduler/backup.sh >> /opt/scheduler/logs/backup.log 2>&1
```

## Maintenance Tasks

### Weekly Tasks

- Review application logs for errors
- Check disk space usage
- Verify backups are running
- Review SSL certificate expiration

### Monthly Tasks

- Update system packages
- Review and optimize database
- Test disaster recovery process
- Review and update documentation

---

**Last Updated:** January 2026  
**Version:** 1.0

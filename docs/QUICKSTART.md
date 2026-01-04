# Quick Start Guide

## Option 1: Automated Setup (Recommended)

```bash
cd /home/greg/development/scheduler
./setup.sh
```

This will:
- Create virtual environment
- Install all dependencies
- Generate .env with random SECRET_KEY
- Create placeholder class icons
- Initialize database with optional test user

Then run:
```bash
source venv/bin/activate
python run.py
```

Open http://localhost:5000

## Option 2: Manual Setup

### 1. Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env and set a strong SECRET_KEY
```

### 3. Create Class Icons
```bash
python3 create_icons.py
```

### 4. Initialize Database
```bash
python3 init_db.py
```

### 5. Run Application
```bash
python run.py
```

## Option 3: Docker

```bash
# Create class icons first
python3 create_icons.py

# Build and run
docker-compose up -d

# Initialize database
docker-compose exec web python init_db.py

# View logs
docker-compose logs -f
```

## First Login

The first user to sign up becomes the superuser with admin privileges.

## Next Steps

1. Sign up with your character name and class
2. Go to "My Availability" to set your schedule
3. View "Guild Timeline" to see everyone's availability
4. Use "Heatmap" to find optimal raid times

## Troubleshooting

**Import errors?**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Database errors?**
```bash
rm scheduler.db  # Delete old database
python init_db.py  # Recreate
```

**Class icons missing?**
```bash
python3 create_icons.py
```

**Port 5000 already in use?**
Edit `run.py` and change the port number.

#!/bin/bash
# Complete setup script for WoW TBC Availability Planner

set -e  # Exit on error

echo "======================================"
echo "WoW TBC Availability Planner Setup"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "  ✓ Python $python_version"
echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "  ✓ Virtual environment created"
else
    echo "  Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "  ✓ Activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip > /dev/null
pip install -r requirements.txt
echo "  ✓ Dependencies installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    
    # Generate a random secret key
    secret_key=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    
    # Update .env with generated secret key
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/your-secret-key-change-this-in-production/$secret_key/" .env
    else
        # Linux
        sed -i "s/your-secret-key-change-this-in-production/$secret_key/" .env
    fi
    
    echo "  ✓ .env file created with random SECRET_KEY"
else
    echo "  .env file already exists"
fi
echo ""

# Create class icons
echo "Creating placeholder class icons..."
python3 create_icons.py
echo ""

# Initialize database
echo "Initializing database..."
python3 init_db.py
echo ""

echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "To start the application:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run the app: python run.py"
echo "  3. Open browser to: http://localhost:5000"
echo ""
echo "For Docker deployment:"
echo "  docker-compose up -d"
echo ""

#!/bin/bash
# Download WoW class icons from GitHub repository
# Source: https://github.com/orourkek/Wow-Icons

SCRIPT_DIR="$(dirname "$0")"
ICONS_DIR="$SCRIPT_DIR/app/static/img/classes"

# Create directory if it doesn't exist
mkdir -p "$ICONS_DIR"
cd "$ICONS_DIR"

echo "Downloading WoW class icons from GitHub..."

# GitHub raw content base URL
BASE_URL="https://raw.githubusercontent.com/orourkek/Wow-Icons/master/images/class"

# Class names as they appear in the repository
CLASSES="warrior paladin hunter rogue priest shaman mage warlock druid"

# Download small icons (18px) - for navigation and inline use
echo "Downloading 18px icons..."
for class in $CLASSES; do
    curl -sL "${BASE_URL}/18/${class}.gif" -o "${class}_small.gif"
    if [ $? -eq 0 ]; then
        echo "  ✓ Downloaded ${class}_small.gif"
    else
        echo "  ✗ Failed to download ${class}_small.gif"
    fi
done

# Download large icons (64px) - for profile and detailed views
echo ""
echo "Downloading 64px icons..."
for class in $CLASSES; do
    curl -sL "${BASE_URL}/64/${class}.png" -o "${class}.png"
    if [ $? -eq 0 ]; then
        echo "  ✓ Downloaded ${class}.png"
    else
        echo "  ✗ Failed to download ${class}.png"
    fi
done

echo ""
echo "✓ All class icons downloaded from GitHub!"
echo "Icons saved to: $ICONS_DIR"

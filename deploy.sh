#!/bin/bash
# Complete Deployment Script for Server Troubleshooting AI Tool

set -e  # Exit on any error

echo "🚀 Server Troubleshooting AI Tool - Complete Deployment"
echo "======================================================="

# Configuration
INSTALL_DIR="$HOME/server-troubleshooter"
SERVICE_NAME="troubleshooter-ollama"

# Create installation directory
echo "📁 Creating installation directory..."
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Copy all files to installation directory if running from different location
if [ "$(pwd)" != "$INSTALL_DIR" ]; then
    echo "📋 Copying files to installation directory..."
    cp -r "$(dirname "$0")"/* "$INSTALL_DIR/"
fi

# Make scripts executable
chmod +x install.sh
chmod +x test_setup.py
chmod +x server_troubleshooter.py

# Run the installation
echo "⚙️ Running installation script..."
./install.sh

# Test the setup
echo "🧪 Testing installation..."
python3 test_setup.py

echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo ""
echo "📍 Installation location: $INSTALL_DIR"
echo ""
echo "🚀 To start troubleshooting:"
echo "   cd $INSTALL_DIR"
echo "   ./run_troubleshooter.sh"
echo ""

# Final check
if [ -f "server_troubleshooter.py" ] && [ -f "run_troubleshooter.sh" ]; then
    echo "✅ All core files present and ready!"
else
    echo "❌ Some files are missing. Please check the installation."
    exit 1
fi

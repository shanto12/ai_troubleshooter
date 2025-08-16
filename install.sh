#!/bin/bash
# Server Troubleshooting AI Tool Installation Script

echo "🔧 Installing Server Troubleshooting AI Tool"
echo "=============================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  Please don't run this script as root"
    exit 1
fi

# Check OS compatibility
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ This tool is designed for Linux systems only"
    exit 1
fi

# Update package lists
echo "📦 Updating package lists..."
sudo apt update || { echo "Failed to update packages"; exit 1; }

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv curl || {
    echo "❌ Failed to install system dependencies"
    exit 1
}

# Install Ollama
echo "🤖 Installing Ollama (Local AI)..."
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.ai/install.sh | sh
    echo "✅ Ollama installed"
else
    echo "✅ Ollama already installed"
fi

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv troubleshooter_env
source troubleshooter_env/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install paramiko requests aiohttp

# Make the main script executable
chmod +x server_troubleshooter.py

# Create launcher script
cat > run_troubleshooter.sh << 'EOF'
#!/bin/bash
# Server Troubleshooter Launcher

cd "$(dirname "$0")"

# Check if Ollama is running
if ! pgrep -f "ollama serve" > /dev/null; then
    echo "🤖 Starting Ollama..."
    nohup ollama serve > ollama.log 2>&1 &
    sleep 3
fi

# Activate virtual environment and run
source troubleshooter_env/bin/activate
python3 server_troubleshooter.py "$@"
EOF

chmod +x run_troubleshooter.sh

# Create systemd service (optional)
cat > troubleshooter.service << 'EOF'
[Unit]
Description=Server Troubleshooting AI Tool - Ollama Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=/usr/local/bin/ollama serve
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "🎉 Installation Complete!"
echo "========================="
echo ""
echo "To start troubleshooting:"
echo "1. Run: ./run_troubleshooter.sh"
echo ""
echo "First run will download the AI model (this may take a few minutes)."
echo ""
echo "Optional: Enable Ollama as a system service:"
echo "  sudo cp troubleshooter.service /etc/systemd/system/"
echo "  sudo systemctl enable troubleshooter"
echo "  sudo systemctl start troubleshooter"
echo ""
echo "📁 Files created:"
echo "  - server_troubleshooter.py (main application)"
echo "  - run_troubleshooter.sh (launcher script)"
echo "  - troubleshooter_env/ (Python virtual environment)"
echo "  - troubleshooter.service (systemd service file)"
echo ""
echo "📖 For help: ./run_troubleshooter.sh --help"

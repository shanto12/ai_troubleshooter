# Server Troubleshooting AI Tool

A privacy-first server troubleshooting tool that combines local AI for data filtering with external AI for advanced analysis.

## Features

- 🔒 **Privacy-First**: Local AI filters sensitive data before sending to external APIs
- 🤖 **Dual AI System**: Local lightweight AI + powerful external AI (ChatGPT/Gemini)
- 🌐 **SSH Connectivity**: Connect to any server in your network
- 🛡️ **Read-Only by Default**: Only diagnostic commands by default, write operations require confirmation
- 📊 **Comprehensive Analysis**: Covers system, network, storage, memory, and service diagnostics
- 🔧 **Interactive Troubleshooting**: Step-by-step guided troubleshooting process

## Quick Start

1. **Install the tool:**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

2. **Run the troubleshooter:**
   ```bash
   ./run_troubleshooter.sh
   ```

3. **First-time setup:**
   - Choose AI provider (OpenAI or Gemini)
   - Enter your API key
   - Provide target server SSH credentials
   - Describe the issue you're troubleshooting

## System Requirements

- Linux operating system (Ubuntu/Debian/RHEL/CentOS)
- Python 3.8+ 
- Internet connection for AI APIs
- SSH access to target servers
- 2GB+ RAM (for local AI model)

## Supported External AI Providers

- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Google Gemini**: Gemini Pro

## How It Works

1. **Issue Description**: You describe the problem you're experiencing
2. **AI Planning**: External AI suggests diagnostic commands
3. **Command Execution**: Tool executes read-only diagnostic commands via SSH
4. **Data Filtering**: Local AI sanitizes output, removes sensitive data
5. **Analysis**: External AI analyzes filtered data and suggests solutions  
6. **Solution Execution**: With your permission, executes fix commands

## Privacy & Security

- **Local Data Filtering**: Sensitive information never leaves your network
- **SSH Security**: Uses standard SSH authentication (password/key-based)
- **Read-Only Default**: Write operations require explicit user confirmation
- **Audit Logging**: All actions logged to troubleshooter.log
- **No Data Storage**: No persistent storage of sensitive information

## Configuration

The tool supports configuration via:
- Interactive setup during first run
- Environment variables for automated deployments
- Configuration file for advanced users

## Troubleshooting

**Ollama not starting:**
```bash
# Check if Ollama is installed
ollama --version

# Start Ollama manually
ollama serve
```

**SSH connection issues:**
- Verify server IP and credentials
- Check firewall settings
- Ensure SSH service is running on target server

**API errors:**
- Verify API key is correct and has sufficient credits
- Check internet connectivity

## Contributing

This tool is designed for cybersecurity professionals and system administrators. Contributions welcome!

## License

MIT License - See LICENSE file for details

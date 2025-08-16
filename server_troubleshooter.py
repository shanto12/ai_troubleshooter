#!/usr/bin/env python3
"""
Server Troubleshooting AI Tool
A privacy-first server troubleshooting tool that uses local AI for data filtering
and external AI for advanced analysis.
"""

import os
import sys
import json
import re
import subprocess
import paramiko
import requests
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import asyncio
import aiohttp
import getpass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('troubleshooter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ServerConfig:
    """Configuration for server connection"""
    ip_address: str
    username: str
    password: str = None
    private_key_path: str = None
    port: int = 22

@dataclass
class AIConfig:
    """Configuration for AI services"""
    external_provider: str  # 'openai' or 'gemini'
    api_key: str
    local_model: str = "gemma:7b"
    ollama_url: str = "http://localhost:11434"

class DataSanitizer:
    """Sanitizes data to remove customer-specific information"""

    def __init__(self):
        self.sensitive_patterns = [
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b',  # IP addresses
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email addresses
            r'\b(?:password|pwd|passwd)\s*[:=]\s*\S+\b',  # Passwords
            r'\b(?:key|token|secret)\s*[:=]\s*\S+\b',  # Keys and tokens
            r'/home/[^/\s]+',  # Home directory paths
            r'/var/log/[^/\s]+/[^/\s]+',  # Specific log file paths
            r'\b[a-f0-9]{32,}\b',  # Hash values
            r'\b[A-Z0-9]{20,}\b',  # Long alphanumeric strings (likely IDs)
        ]

    def sanitize_output(self, text: str) -> str:
        """Remove sensitive information from command output"""
        sanitized = text

        # Replace IP addresses with generic ones
        sanitized = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', 'XXX.XXX.XXX.XXX', sanitized)

        # Replace email addresses
        sanitized = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'user@domain.com', sanitized)

        # Replace passwords and sensitive values
        sanitized = re.sub(r'(?:password|pwd|passwd|key|token|secret)\s*[:=]\s*\S+', 'REDACTED', sanitized, flags=re.IGNORECASE)

        # Replace home directory paths
        sanitized = re.sub(r'/home/[^/\s]+', '/home/user', sanitized)

        # Replace specific log paths
        sanitized = re.sub(r'/var/log/[^/\s]+/[^/\s]+', '/var/log/service/logfile', sanitized)

        # Replace hash values and long IDs
        sanitized = re.sub(r'\b[a-f0-9]{32,}\b', 'HASH_VALUE', sanitized)
        sanitized = re.sub(r'\b[A-Z0-9]{20,}\b', 'ID_VALUE', sanitized)

        return sanitized

    def extract_generic_info(self, command: str, output: str) -> Dict:
        """Extract generic information from command output"""
        sanitized_output = self.sanitize_output(output)

        return {
            'command_type': self._categorize_command(command),
            'sanitized_output': sanitized_output,
            'output_length': len(output),
            'contains_errors': 'error' in output.lower() or 'fail' in output.lower(),
            'exit_status': 'success' if not any(word in output.lower() for word in ['error', 'fail', 'not found', 'permission denied']) else 'error'
        }

    def _categorize_command(self, command: str) -> str:
        """Categorize the type of command being run"""
        cmd = command.lower().strip()

        if any(word in cmd for word in ['ps', 'top', 'htop', 'systemctl status']):
            return 'process_monitoring'
        elif any(word in cmd for word in ['df', 'du', 'lsblk', 'mount']):
            return 'storage_analysis'
        elif any(word in cmd for word in ['free', 'vmstat', 'iostat']):
            return 'memory_analysis'
        elif any(word in cmd for word in ['netstat', 'ss', 'ping', 'curl', 'wget']):
            return 'network_analysis'
        elif any(word in cmd for word in ['dmesg', 'journalctl', 'tail', 'grep']):
            return 'log_analysis'
        elif any(word in cmd for word in ['systemctl', 'service', 'chkconfig']):
            return 'service_management'
        else:
            return 'general_system'

class SSHManager:
    """Manages SSH connections to target servers"""

    def __init__(self, config: ServerConfig):
        self.config = config
        self.client = None

    def connect(self) -> bool:
        """Establish SSH connection"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            if self.config.private_key_path:
                key = paramiko.RSAKey.from_private_key_file(self.config.private_key_path)
                self.client.connect(
                    hostname=self.config.ip_address,
                    port=self.config.port,
                    username=self.config.username,
                    pkey=key,
                    timeout=30
                )
            else:
                self.client.connect(
                    hostname=self.config.ip_address,
                    port=self.config.port,
                    username=self.config.username,
                    password=self.config.password,
                    timeout=30
                )

            logger.info(f"Successfully connected to {self.config.ip_address}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to {self.config.ip_address}: {str(e)}")
            return False

    def execute_command(self, command: str) -> Tuple[str, str, int]:
        """Execute command on remote server"""
        if not self.client:
            raise Exception("No active SSH connection")

        try:
            logger.info(f"Executing command: {command}")
            stdin, stdout, stderr = self.client.exec_command(command, timeout=60)

            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            exit_status = stdout.channel.recv_exit_status()

            return output, error, exit_status

        except Exception as e:
            logger.error(f"Command execution failed: {str(e)}")
            return "", str(e), 1

    def disconnect(self):
        """Close SSH connection"""
        if self.client:
            self.client.close()
            logger.info("SSH connection closed")

class LocalAI:
    """Manages local AI using Ollama"""

    def __init__(self, config: AIConfig):
        self.config = config
        self.base_url = config.ollama_url

    def is_available(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def pull_model(self, model_name: str) -> bool:
        """Pull a model if not available"""
        try:
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                timeout=300
            )
            return response.status_code == 200
        except:
            return False

    def generate_response(self, prompt: str) -> str:
        """Generate response using local AI"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.config.local_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120
            )

            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                return "Local AI request failed"

        except Exception as e:
            logger.error(f"Local AI error: {str(e)}")
            return f"Local AI error: {str(e)}"

    def analyze_command_output(self, command: str, output: str, sanitized_data: Dict) -> str:
        """Analyze command output and generate insights for external AI"""
        prompt = f"""
You are a Linux system analysis assistant. Analyze the following command execution and provide a summary for external AI consultation.

Command Type: {sanitized_data['command_type']}
Command Executed: {command}
Output Status: {sanitized_data['exit_status']}
Output Length: {sanitized_data['output_length']} characters
Contains Errors: {sanitized_data['contains_errors']}

Based on this information, generate a concise analysis that can be sent to an external AI for troubleshooting recommendations. Focus on:
1. What type of system check was performed
2. Whether any issues were detected
3. What additional commands might be needed
4. General patterns or anomalies observed

Do not include any sensitive data - only provide generic technical analysis.
"""

        return self.generate_response(prompt)

class ExternalAI:
    """Manages external AI APIs (OpenAI/Gemini)"""

    def __init__(self, config: AIConfig):
        self.config = config

    async def get_troubleshooting_advice(self, analysis: str, issue_description: str) -> str:
        """Get troubleshooting advice from external AI"""
        if self.config.external_provider == 'openai':
            return await self._call_openai(analysis, issue_description)
        elif self.config.external_provider == 'gemini':
            return await self._call_gemini(analysis, issue_description)
        else:
            raise ValueError("Unsupported external AI provider")

    async def _call_openai(self, analysis: str, issue_description: str) -> str:
        """Call OpenAI API"""
        headers = {
            'Authorization': f'Bearer {self.config.api_key}',
            'Content-Type': 'application/json'
        }

        data = {
            'model': 'gpt-4',
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are an expert Linux system administrator. Provide specific troubleshooting commands and solutions based on the analysis provided.'
                },
                {
                    'role': 'user',
                    'content': f"""
Issue Description: {issue_description}

System Analysis: {analysis}

Please provide specific Linux commands to diagnose and resolve this issue. Format your response as:
1. DIAGNOSTIC_COMMANDS: List of read-only commands to gather more information
2. ANALYSIS: What these commands will reveal
3. POTENTIAL_SOLUTIONS: Suggested fix commands (mark any write operations clearly)
4. NEXT_STEPS: Additional recommendations
"""
                }
            ]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post('https://api.openai.com/v1/chat/completions', 
                                  headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['choices'][0]['message']['content']
                else:
                    return f"OpenAI API error: {response.status}"

    async def _call_gemini(self, analysis: str, issue_description: str) -> str:
        """Call Gemini API"""
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.config.api_key}'

        data = {
            'contents': [{
                'parts': [{
                    'text': f"""
You are an expert Linux system administrator. Provide specific troubleshooting commands and solutions.

Issue Description: {issue_description}

System Analysis: {analysis}

Please provide specific Linux commands to diagnose and resolve this issue. Format your response as:
1. DIAGNOSTIC_COMMANDS: List of read-only commands to gather more information
2. ANALYSIS: What these commands will reveal
3. POTENTIAL_SOLUTIONS: Suggested fix commands (mark any write operations clearly)
4. NEXT_STEPS: Additional recommendations
"""
                }]
            }]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['candidates'][0]['content']['parts'][0]['text']
                else:
                    return f"Gemini API error: {response.status}"

class TroubleshooterApp:
    """Main troubleshooting application"""

    def __init__(self):
        self.ssh_manager = None
        self.local_ai = None
        self.external_ai = None
        self.sanitizer = DataSanitizer()

    def setup_ai_config(self) -> AIConfig:
        """Setup AI configuration"""
        print("\n=== AI Configuration ===")
        provider = input("Choose external AI provider (openai/gemini): ").strip().lower()

        while provider not in ['openai', 'gemini']:
            print("Invalid provider. Please choose 'openai' or 'gemini'")
            provider = input("Choose external AI provider (openai/gemini): ").strip().lower()

        api_key = getpass.getpass(f"Enter {provider.upper()} API key: ").strip()

        local_model = input("Enter local model name (default: gemma:7b): ").strip()
        if not local_model:
            local_model = "gemma:7b"

        return AIConfig(
            external_provider=provider,
            api_key=api_key,
            local_model=local_model
        )

    def setup_server_config(self) -> ServerConfig:
        """Setup server configuration"""
        print("\n=== Server Configuration ===")
        ip_address = input("Enter target server IP address: ").strip()
        username = input("Enter SSH username: ").strip()

        auth_method = input("Authentication method (password/key): ").strip().lower()

        if auth_method == 'key':
            key_path = input("Enter private key path: ").strip()
            return ServerConfig(ip_address=ip_address, username=username, private_key_path=key_path)
        else:
            password = getpass.getpass("Enter SSH password: ")
            return ServerConfig(ip_address=ip_address, username=username, password=password)

    def initialize_local_ai(self, ai_config: AIConfig) -> bool:
        """Initialize local AI"""
        self.local_ai = LocalAI(ai_config)

        if not self.local_ai.is_available():
            print("Ollama is not running. Please install and start Ollama first.")
            print("Installation: curl -fsSL https://ollama.ai/install.sh | sh")
            print("Start: ollama serve")
            return False

        print(f"Checking local model: {ai_config.local_model}")
        if not self.local_ai.pull_model(ai_config.local_model):
            print(f"Failed to pull model {ai_config.local_model}")
            return False

        print("Local AI initialized successfully")
        return True

    async def run_troubleshooting_session(self, issue_description: str):
        """Run a troubleshooting session"""
        print(f"\n=== Troubleshooting Session Started ===")
        print(f"Issue: {issue_description}")

        # Get initial diagnostic commands from external AI
        initial_analysis = "Starting troubleshooting session for: " + issue_description
        advice = await self.external_ai.get_troubleshooting_advice(initial_analysis, issue_description)

        print("\n=== Initial AI Recommendations ===")
        print(advice)

        # Parse and execute diagnostic commands
        commands = self._extract_commands(advice, 'DIAGNOSTIC_COMMANDS')

        for i, command in enumerate(commands, 1):
            print(f"\n--- Executing Diagnostic Command {i}: {command} ---")

            # Execute command
            output, error, exit_status = self.ssh_manager.execute_command(command)

            if exit_status != 0 and error:
                print(f"Command failed with error: {error}")
                continue

            # Sanitize and analyze output
            sanitized_data = self.sanitizer.extract_generic_info(command, output)
            local_analysis = self.local_ai.analyze_command_output(command, output, sanitized_data)

            print(f"Local AI Analysis: {local_analysis}")

            # Get external AI recommendations based on analysis
            detailed_advice = await self.external_ai.get_troubleshooting_advice(local_analysis, issue_description)
            print(f"External AI Advice:\n{detailed_advice}")

            # Check for solution commands
            solution_commands = self._extract_commands(detailed_advice, 'POTENTIAL_SOLUTIONS')

            if solution_commands:
                print("\n=== Potential Solutions Found ===")
                for j, sol_cmd in enumerate(solution_commands, 1):
                    print(f"{j}. {sol_cmd}")

                if input("\nExecute solution commands? (y/n): ").strip().lower() == 'y':
                    await self._execute_solution_commands(solution_commands)

        print("\n=== Troubleshooting Session Complete ===")

    def _extract_commands(self, text: str, section: str) -> List[str]:
        """Extract commands from AI response"""
        commands = []
        lines = text.split('\n')
        in_section = False

        for line in lines:
            if section in line:
                in_section = True
                continue
            elif line.strip().startswith(('1.', '2.', '3.', '4.', 'ANALYSIS:', 'POTENTIAL_SOLUTIONS:', 'NEXT_STEPS:')):
                if not line.strip().startswith(('1.', '2.', '3.', '4.')):
                    in_section = False
                continue

            if in_section and line.strip():
                # Extract command from line
                command = line.strip()
                # Remove numbering and clean up
                command = re.sub(r'^\d+\.\s*', '', command)
                command = re.sub(r'^[-*]\s*', '', command)
                if command and not command.startswith('#'):
                    commands.append(command)

        return commands

    async def _execute_solution_commands(self, commands: List[str]):
        """Execute solution commands with user confirmation"""
        for i, command in enumerate(commands, 1):
            print(f"\n--- Solution Command {i}: {command} ---")

            # Check if it's a write operation
            write_operations = ['rm', 'mv', 'cp', 'chmod', 'chown', 'systemctl restart', 'systemctl stop', 'kill', 'pkill']
            is_write_op = any(op in command.lower() for op in write_operations)

            if is_write_op:
                print("⚠️  WARNING: This is a write/modification operation!")
                if input(f"Execute '{command}'? (y/n): ").strip().lower() != 'y':
                    print("Skipped.")
                    continue

            output, error, exit_status = self.ssh_manager.execute_command(command)

            if exit_status == 0:
                print(f"✅ Success: {output}")
            else:
                print(f"❌ Error: {error}")

    async def run(self):
        """Main application entry point"""
        print("🔧 Server Troubleshooting AI Tool")
        print("==================================")

        try:
            # Setup configuration
            ai_config = self.setup_ai_config()
            server_config = self.setup_server_config()

            # Initialize components
            if not self.initialize_local_ai(ai_config):
                return

            self.external_ai = ExternalAI(ai_config)
            self.ssh_manager = SSHManager(server_config)

            # Connect to server
            if not self.ssh_manager.connect():
                print("Failed to connect to target server")
                return

            # Get issue description
            issue_description = input("\nDescribe the issue you want to troubleshoot: ").strip()

            # Run troubleshooting session
            await self.run_troubleshooting_session(issue_description)

        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user")
        except Exception as e:
            logger.error(f"Application error: {str(e)}")
            print(f"An error occurred: {str(e)}")
        finally:
            if self.ssh_manager:
                self.ssh_manager.disconnect()

def main():
    """Application entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == '--install-deps':
        install_dependencies()
        return

    app = TroubleshooterApp()
    asyncio.run(app.run())

def install_dependencies():
    """Install required dependencies"""
    dependencies = [
        'paramiko',
        'requests',
        'aiohttp'
    ]

    for dep in dependencies:
        print(f"Installing {dep}...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', dep])

    print("All dependencies installed!")

if __name__ == "__main__":
    main()

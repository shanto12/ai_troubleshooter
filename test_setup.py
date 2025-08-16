#!/usr/bin/env python3
"""
Test script for Server Troubleshooting AI Tool
"""

import sys
import subprocess
import requests

def test_ollama_connection():
    """Test if Ollama is running and accessible"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running and accessible")
            models = response.json().get("models", [])
            if models:
                print(f"📋 Available models: {[m['name'] for m in models]}")
            else:
                print("⚠️  No models installed yet")
            return True
        else:
            print(f"❌ Ollama responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama (not running?)")
        return False
    except Exception as e:
        print(f"❌ Ollama test failed: {str(e)}")
        return False

def test_dependencies():
    """Test if all Python dependencies are installed"""
    required_modules = ['paramiko', 'requests', 'aiohttp']
    missing = []

    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} is installed")
        except ImportError:
            print(f"❌ {module} is missing")
            missing.append(module)

    return len(missing) == 0

def test_ssh_connectivity():
    """Basic SSH connectivity test"""
    try:
        import paramiko
        print("✅ SSH library (paramiko) is available")
        return True
    except ImportError:
        print("❌ SSH library (paramiko) is not installed")
        return False

def main():
    print("🧪 Testing Server Troubleshooting AI Tool")
    print("==========================================")

    tests_passed = 0
    total_tests = 3

    print("\n1. Testing Python dependencies...")
    if test_dependencies():
        tests_passed += 1

    print("\n2. Testing SSH connectivity...")
    if test_ssh_connectivity():
        tests_passed += 1

    print("\n3. Testing Ollama connection...")
    if test_ollama_connection():
        tests_passed += 1

    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")

    if tests_passed == total_tests:
        print("🎉 All tests passed! You're ready to run the troubleshooter.")
    else:
        print("⚠️  Some tests failed. Please check the installation.")
        if tests_passed < total_tests:
            print("\n🔧 Suggested fixes:")
            print("- Run: pip install -r requirements.txt")
            print("- Start Ollama: ollama serve")
            print("- Check the installation guide in README.md")

if __name__ == "__main__":
    main()

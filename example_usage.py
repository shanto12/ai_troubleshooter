#!/usr/bin/env python3
"""
Example usage of the Server Troubleshooting AI Tool
This demonstrates how the tool would be used programmatically
"""

import asyncio

async def example_troubleshooting_session():
    """Example of how the tool works"""

    print("🎯 Example Troubleshooting Session")
    print("==================================")

    print("\n1. 🤖 AI analyzes your issue description:")
    issue = "Server is running slowly and users are complaining about timeouts"
    print(f"   Issue: {issue}")

    print("\n2. 🔍 AI suggests diagnostic commands:")
    suggested_commands = [
        "uptime",
        "free -h", 
        "df -h",
        "ps aux --sort=-%cpu | head -20",
        "netstat -tuln",
        "journalctl -xe --no-pager -n 20"
    ]

    for i, cmd in enumerate(suggested_commands, 1):
        print(f"   {i}. {cmd}")

    print("\n3. 🔧 Tool executes commands via SSH:")
    print("   ✅ uptime -> Load average: 8.5, 9.2, 7.8")
    print("   ✅ free -h -> Memory: 15G used / 16G total (94%)")
    print("   ✅ df -h -> Disk usage: 85% on /var/log")
    print("   ⚠️  ps aux -> Multiple Java processes consuming CPU")

    print("\n4. 🤖 Local AI filters sensitive data:")
    print("   • IP addresses → XXX.XXX.XXX.XXX")
    print("   • User paths → /home/user")
    print("   • Process IDs → Generic analysis")

    print("\n5. 🧠 External AI analyzes filtered data:")
    print("   ANALYSIS: High memory usage (94%) and disk space (85%) detected.")
    print("   Multiple Java processes indicate possible memory leak.")

    print("\n6. ⚡ Tool suggests solutions:")
    solutions = [
        "journalctl -u java-app --no-pager -n 100",
        "sudo systemctl restart java-app  [WRITE OPERATION]",
        "sudo find /var/log -name '*.log' -mtime +7 -delete  [WRITE OPERATION]"
    ]

    for i, solution in enumerate(solutions, 1):
        write_op = "WRITE OPERATION" in solution
        status = "⚠️ " if write_op else "✅"
        print(f"   {status} {i}. {solution}")

    print("\n7. 🛡️ Safety confirmation for write operations:")
    print("   → User confirms: 'Yes, restart the Java service'")
    print("   → Tool executes: sudo systemctl restart java-app")
    print("   → Result: ✅ Service restarted successfully")

    print("\n8. 📊 Final verification:")
    print("   → Memory usage: 45% (improved!)")  
    print("   → Load average: 2.1 (normal)")
    print("   → Java service: Active (running)")

    print("\n🎉 Issue resolved! Server performance restored.")

if __name__ == "__main__":
    asyncio.run(example_troubleshooting_session())

#!/usr/bin/env python3
"""
Example usage of analyze_traffic_log.py
"""

import subprocess
import sys
import os

# Example 1: Basic analysis with plots
log_file = "../intraffic.log"
if os.path.exists(log_file):
    print("Running traffic log analysis...")
    subprocess.run([sys.executable, "analyze_traffic_log.py", log_file])
else:
    print(f"Log file not found: {log_file}")
    print("\nUsage examples:")
    print("  python analyze_traffic_log.py intraffic.log")
    print("  python analyze_traffic_log.py intraffic.log -o ./output_dir")
    print("  python analyze_traffic_log.py intraffic.log --no-plots")
    print("  python analyze_traffic_log.py intraffic.log --summary")


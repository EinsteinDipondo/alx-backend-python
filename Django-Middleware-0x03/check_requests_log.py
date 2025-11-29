#!/usr/bin/env python
"""
Script to check if requests.log file exists and is not empty
"""
import os
import sys

def check_requests_log():
    print("🔍 Checking requests.log file...")
    
    log_file = 'requests.log'
    
    # Check if file exists
    if not os.path.exists(log_file):
        print(f"❌ {log_file} does not exist!")
        print("   Current directory:", os.getcwd())
        print("   Expected file path:", os.path.abspath(log_file))
        
        # Show files in current directory
        print("\n📁 Files in current directory:")
        for file in os.listdir('.'):
            if file.endswith('.log') or file == 'requests.log':
                print(f"   - {file}")
        
        return False
    
    print(f"✅ {log_file} exists")
    
    # Check file size
    file_size = os.path.getsize(log_file)
    print(f"📊 File size: {file_size} bytes")
    
    if file_size == 0:
        print("❌ requests.log exists but is EMPTY")
        print("   No log entries have been recorded yet")
        return False
    else:
        print("✅ requests.log is NOT empty")
        
        # Show first few lines of the log file
        print("\n📄 First 5 lines of requests.log:")
        print("-" * 50)
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()[:5]  # Read first 5 lines
                for i, line in enumerate(lines, 1):
                    print(f"{i}: {line.strip()}")
        except Exception as e:
            print(f"Error reading log file: {e}")
        print("-" * 50)
        
        return True

if __name__ == '__main__':
    success = check_requests_log()
    sys.exit(0 if success else 1)
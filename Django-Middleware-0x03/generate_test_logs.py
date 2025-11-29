#!/usr/bin/env python
"""
Script to generate test log entries by making requests to the server
"""
import os
import django
import requests
import time
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messaging_app.settings')
django.setup()

def generate_test_requests():
    print("🚀 Generating test requests to create log entries...")
    
    base_url = "http://localhost:8000"
    
    # Test endpoints that should trigger logging
    test_endpoints = [
        "/api/chats/test/",
        "/admin/",
        "/api/token/",
        "/api/chats/conversations/",
    ]
    
    for endpoint in test_endpoints:
        try:
            print(f"📤 Making request to: {endpoint}")
            # Using requests library to make HTTP calls
            response = requests.get(f"{base_url}{endpoint}", timeout=2)
            print(f"   Response: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Cannot connect to server. Is the server running?")
        except requests.exceptions.Timeout:
            print(f"   ⏰ Request timeout")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(0.5)  # Small delay between requests

def check_server_running():
    """Check if Django development server is running"""
    try:
        response = requests.get("http://localhost:8000/", timeout=1)
        return True
    except:
        return False

if __name__ == '__main__':
    print("🔧 Testing requests.log generation...")
    
    # First check current state
    from check_requests_log import check_requests_log
    current_state = check_requests_log()
    
    if not current_state:
        print("\n🔄 Attempting to generate log entries...")
        
        if check_server_running():
            print("✅ Server is running, generating test requests...")
            generate_test_requests()
            
            # Wait a moment for logs to be written
            time.sleep(1)
            
            # Check again
            print("\n🔍 Re-checking requests.log after test requests...")
            final_state = check_requests_log()
            
            if final_state:
                print("\n🎉 Success! requests.log now exists and has content!")
            else:
                print("\n❌ Still no log entries. The middleware might not be working properly.")
        else:
            print("\n❌ Django server is not running!")
            print("   Please start the server with: python manage.py runserver")
            print("   Then run this script again.")
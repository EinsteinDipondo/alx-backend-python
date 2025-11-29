#!/usr/bin/env python
"""
Verification script to check if middleware is properly set up
"""
import os
import sys

def verify_complete_setup():
    print("🔍 Verifying complete middleware setup...")
    
    # Check if we're in the right directory
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    
    # Check if manage.py exists
    if not os.path.exists('manage.py'):
        print("❌ manage.py not found in current directory")
        return False
    print("✅ manage.py exists")
    
    # Check if chats/middleware.py exists
    middleware_path = 'messaging_app/chats/middleware.py'
    if not os.path.exists(middleware_path):
        print(f"❌ {middleware_path} does not exist!")
        return False
    print(f"✅ {middleware_path} exists")
    
    # Check if middleware classes are defined
    with open(middleware_path, 'r') as f:
        content = f.read()
        
        required_elements = [
            ('class RequestLoggingMiddleware', 'RequestLoggingMiddleware class'),
            ('class RestrictAccessByTimeMiddleware', 'RestrictAccessByTimeMiddleware class'),
            ('def __init__', '__init__ method'),
            ('def __call__', '__call__ method'),
            ('HttpResponseForbidden', 'HttpResponseForbidden import'),
        ]
        
        for element, description in required_elements:
            if element in content:
                print(f"✅ {description} found")
            else:
                print(f"❌ {description} NOT found")
                return False
    
    # Check if settings.py has middleware configured
    settings_path = 'messaging_app/settings.py'
    if not os.path.exists(settings_path):
        print(f"❌ {settings_path} does not exist!")
        return False
        
    with open(settings_path, 'r') as f:
        settings_content = f.read()
        
        middleware_checks = [
            ('chats.middleware.RestrictAccessByTimeMiddleware', 'RestrictAccessByTimeMiddleware in settings'),
            ('chats.middleware.RequestLoggingMiddleware', 'RequestLoggingMiddleware in settings'),
        ]
        
        for middleware, description in middleware_checks:
            if middleware in settings_content:
                print(f"✅ {description}")
            else:
                print(f"❌ {description}")
                return False
    
    # Check directory structure
    print("\n📁 Project structure:")
    expected_dirs = [
        'messaging_app/chats/',
        'messaging_app/messaging_app/',
    ]
    
    for dir_path in expected_dirs:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path} exists")
            # List some key files
            if dir_path == 'messaging_app/chats/':
                chat_files = os.listdir(dir_path)
                print(f"   Files in chats/: {[f for f in chat_files if f.endswith('.py')]}")
        else:
            print(f"❌ {dir_path} does not exist")
    
    print("\n🎉 All checks passed! The middleware is properly set up.")
    return True

if __name__ == '__main__':
    success = verify_complete_setup()
    sys.exit(0 if success else 1)
#!/usr/bin/env python
"""
Verification script to check if middleware is properly configured
"""
import os
import sys

def check_middleware_configuration():
    print("🔍 Checking middleware configuration...")
    
    # Check if settings.py exists
    settings_path = 'messaging_app/settings.py'
    if not os.path.exists(settings_path):
        print("❌ ERROR: settings.py does not exist!")
        print("   Current directory:", os.getcwd())
        print("   Looking for:", os.path.abspath(settings_path))
        return False
    
    print("✅ settings.py exists")
    
    # Check if middleware is configured in settings.py
    with open(settings_path, 'r') as f:
        content = f.read()
        
        # Check for RestrictAccessByTimeMiddleware
        if 'chats.middleware.RestrictAccessByTimeMiddleware' in content:
            print("✅ RestrictAccessByTimeMiddleware is configured in settings.py")
        else:
            print("❌ RestrictAccessByTimeMiddleware is NOT configured in settings.py")
            return False
            
        # Check for RequestLoggingMiddleware
        if 'chats.middleware.RequestLoggingMiddleware' in content:
            print("✅ RequestLoggingMiddleware is configured in settings.py")
        else:
            print("❌ RequestLoggingMiddleware is NOT configured in settings.py")
            return False
    
    # Check if middleware.py exists
    middleware_path = 'messaging_app/chats/middleware.py'
    if not os.path.exists(middleware_path):
        print("❌ ERROR: middleware.py does not exist!")
        return False
    
    print("✅ middleware.py exists")
    
    # Check if middleware classes are defined
    with open(middleware_path, 'r') as f:
        content = f.read()
        
        if 'class RestrictAccessByTimeMiddleware' in content:
            print("✅ RestrictAccessByTimeMiddleware class is defined")
        else:
            print("❌ RestrictAccessByTimeMiddleware class is NOT defined")
            return False
            
        if 'class RequestLoggingMiddleware' in content:
            print("✅ RequestLoggingMiddleware class is defined")
        else:
            print("❌ RequestLoggingMiddleware class is NOT defined")
            return False
            
        if '__init__' in content and '__call__' in content:
            print("✅ Both __init__ and __call__ methods are present")
        else:
            print("❌ Missing __init__ or __call__ methods")
            return False
    
    print("\n🎉 All checks passed! Middleware is properly configured.")
    return True

if __name__ == '__main__':
    success = check_middleware_configuration()
    sys.exit(0 if success else 1)
#!/usr/bin/env python
"""
Test script to verify middleware functionality
"""
import os
import django
from datetime import datetime, time
from django.test import RequestFactory

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messaging_app.settings')
django.setup()

from chats.middleware import RestrictAccessByTimeMiddleware, RequestLoggingMiddleware

def test_time_restriction_middleware():
    print("🧪 Testing RestrictAccessByTimeMiddleware...")
    
    factory = RequestFactory()
    
    def mock_get_response(request):
        from django.http import HttpResponse
        return HttpResponse("OK")
    
    middleware = RestrictAccessByTimeMiddleware(mock_get_response)
    
    # Test different times
    test_cases = [
        (time(20, 59), False, "8:59 PM - Should be allowed"),
        (time(21, 0), True, "9:00 PM - Should be restricted"),
        (time(23, 59), True, "11:59 PM - Should be restricted"),
        (time(0, 0), True, "12:00 AM - Should be restricted"),
        (time(5, 59), True, "5:59 AM - Should be restricted"),
        (time(6, 0), False, "6:00 AM - Should be allowed"),
    ]
    
    print("\n📋 Time Restriction Test Results:")
    print("-" * 50)
    
    for test_time, should_restrict, description in test_cases:
        # Create chat request
        request = factory.get('/api/chats/conversations/')
        
        # Mock the time checking
        original_method = middleware._is_restricted_time
        middleware._is_restricted_time = lambda ct: original_method(test_time)
        
        response = middleware(request)
        is_restricted = response.status_code == 403
        
        status = "✅ PASS" if is_restricted == should_restrict else "❌ FAIL"
        print(f"{status} {description}")
        
        # Restore original method
        middleware._is_restricted_time = original_method

def test_logging_middleware():
    print("\n🧪 Testing RequestLoggingMiddleware...")
    
    factory = RequestFactory()
    
    def mock_get_response(request):
        from django.http import HttpResponse
        return HttpResponse("OK")
    
    middleware = RequestLoggingMiddleware(mock_get_response)
    
    # Test with anonymous user
    request = factory.get('/api/chats/test/')
    request.user = type('User', (), {'is_authenticated': False, 'username': 'testuser'})()
    
    response = middleware(request)
    
    print("✅ RequestLoggingMiddleware processed request without errors")
    print("📝 Check requests.log file for logged entries")

if __name__ == '__main__':
    test_time_restriction_middleware()
    test_logging_middleware()
    print("\n🎯 Middleware testing complete!")
# Django-Middleware-0x03/messaging_app/chats/middleware.py
import logging
from datetime import datetime, time, timedelta
from django.http import HttpResponseForbidden, JsonResponse
from django.core.cache import cache
import re

class RequestLoggingMiddleware:
    """
    Middleware to log each user's requests including timestamp, user, and request path.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Set up logger specifically for requests
        self.logger = logging.getLogger('request_logger')
        
        # Ensure the logger has a file handler
        if not self.logger.handlers:
            # Create file handler
            handler = logging.FileHandler('requests.log')
            # Create formatter with the exact required format
            formatter = logging.Formatter('%(asctime)s - User: %(user)s - Path: %(path)s')
            handler.setFormatter(formatter)
            # Add handler to logger
            self.logger.addHandler(handler)
            # Set level to INFO
            self.logger.setLevel(logging.INFO)
            # Prevent propagation to avoid duplicate logs
            self.logger.propagate = False

    def __call__(self, request):
        # Get the user information
        user = "Anonymous"
        if hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user.username
        
        # Log the request information using extra context for the formatter
        self.logger.info('', extra={'user': user, 'path': request.path})
        
        # Process the request and get response
        response = self.get_response(request)
        
        return response


class RestrictAccessByTimeMiddleware:
    """
    Middleware that restricts access to the messaging app during certain hours.
    Denies access by returning 403 Forbidden if accessed outside 9PM and 6AM.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Define restricted time period: 9:00 PM to 6:00 AM (21:00 to 06:00)
        self.restricted_start = time(21, 0)  # 9:00 PM
        self.restricted_end = time(6, 0)     # 6:00 AM

    def __call__(self, request):
        # Get current server time
        current_time = datetime.now().time()
        
        # Check if the request is for chat endpoints
        is_chat_endpoint = (
            request.path.startswith('/api/chats/') or 
            request.path.startswith('/chats/')
        )
        
        # If it's a chat endpoint and current time is within restricted hours
        if is_chat_endpoint and self._is_restricted_time(current_time):
            return HttpResponseForbidden(
                "Access to chat services is restricted between 9:00 PM and 6:00 AM. "
                "Please try again during allowed hours."
            )
        
        # Process the request if not restricted
        response = self.get_response(request)
        return response

    def _is_restricted_time(self, current_time):
        """
        Check if current time is within restricted hours (9:00 PM to 6:00 AM)
        
        There are two cases to handle:
        1. Same day: 21:00 to 23:59
        2. Overnight: 00:00 to 06:00
        """
        if self.restricted_start <= self.restricted_end:
            # Normal case: start < end (not applicable for our 9PM-6AM scenario)
            return self.restricted_start <= current_time <= self.restricted_end
        else:
            # Overnight case: start > end (9PM to 6AM crosses midnight)
            return current_time >= self.restricted_start or current_time <= self.restricted_end


class OffensiveLanguageMiddleware:
    """
    Middleware that detects and blocks offensive language in chat messages.
    Also implements rate limiting: 5 messages per minute per IP address.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Rate limiting configuration
        self.rate_limit = 5  # 5 messages
        self.rate_window = 60  # 1 minute in seconds
        
        # Common offensive words list (can be expanded)
        self.offensive_words = [
            'badword1', 'badword2', 'offensive', 'hate', 'attack',
            # Add more offensive words as needed
            'curse', 'swear', 'abuse', 'insult'
        ]
        
        # Compile regex patterns for offensive words
        self.offensive_patterns = [
            re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
            for word in self.offensive_words
        ]

    def __call__(self, request):
        # Get client IP address
        ip_address = self._get_client_ip(request)
        
        # Check if this is a message creation request
        is_message_post = (
            request.method == 'POST' and 
            ('/api/chats/messages/' in request.path or '/chats/messages/' in request.path)
        )
        
        if is_message_post:
            # Check rate limiting first
            rate_limit_check = self._check_rate_limit(ip_address)
            if not rate_limit_check['allowed']:
                return JsonResponse({
                    'error': f'Rate limit exceeded. Please wait {rate_limit_check["wait_time"]} seconds.',
                    'limit': self.rate_limit,
                    'window': self.rate_window,
                    'remaining_time': rate_limit_check['wait_time']
                }, status=429)
            
            # Check for offensive language in the message content
            offensive_check = self._check_offensive_language(request)
            if offensive_check['has_offensive']:
                return JsonResponse({
                    'error': 'Message contains offensive language and cannot be sent.',
                    'offensive_words': offensive_check['offensive_words']
                }, status=400)
        
        # Process the request if not blocked
        response = self.get_response(request)
        return response

    def _get_client_ip(self, request):
        """
        Get the client's IP address from the request
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _check_rate_limit(self, ip_address):
        """
        Check if the IP address has exceeded the rate limit
        Returns 5 messages per minute
        """
        cache_key = f'rate_limit_{ip_address}'
        
        # Get current count and timestamp from cache
        current_data = cache.get(cache_key, {'count': 0, 'first_request': datetime.now()})
        
        current_time = datetime.now()
        time_diff = (current_time - current_data['first_request']).total_seconds()
        
        if time_diff > self.rate_window:
            # Reset counter if time window has passed
            current_data = {'count': 1, 'first_request': current_time}
            cache.set(cache_key, current_data, self.rate_window)
            return {'allowed': True, 'wait_time': 0}
        else:
            # Check if within limit
            if current_data['count'] >= self.rate_limit:
                wait_time = self.rate_window - int(time_diff)
                return {'allowed': False, 'wait_time': wait_time}
            else:
                # Increment counter
                current_data['count'] += 1
                cache.set(cache_key, current_data, self.rate_window)
                return {'allowed': True, 'wait_time': 0}

    def _check_offensive_language(self, request):
        """
        Check the request content for offensive language
        """
        offensive_words_found = []
        
        try:
            # Try to get message content from request body
            if hasattr(request, 'data'):
                # For DRF requests
                content = request.data.get('content', '')
            else:
                # For regular Django requests
                content = request.POST.get('content', '')
            
            # Check for offensive words
            for pattern in self.offensive_patterns:
                if pattern.search(content):
                    offensive_words_found.append(pattern.pattern.replace(r'\b', '').replace(r'\B', ''))
            
        except Exception as e:
            # If we can't check the content, allow the request
            # In production, you might want to log this error
            pass
        
        return {
            'has_offensive': len(offensive_words_found) > 0,
            'offensive_words': offensive_words_found
        }
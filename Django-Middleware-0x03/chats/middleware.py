# Django-Middleware-0x03/messaging_app/chats/middleware.py
import logging
from datetime import datetime, time
from django.http import HttpResponseForbidden

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
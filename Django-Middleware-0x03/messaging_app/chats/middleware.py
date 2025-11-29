# Django-Middleware-0x03/messaging_app/chats/middleware.py
import logging
from datetime import datetime

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
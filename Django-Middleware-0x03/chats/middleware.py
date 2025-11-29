# Django-Middleware-0x03/messaging_app/chats/middleware.py
import logging
from datetime import datetime

class RequestLoggingMiddleware:
    """
    Middleware to log each user's requests including timestamp, user, and request path.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Set up logger
        self.logger = logging.getLogger('request_logger')
        
        # Create file handler if it doesn't exist
        if not self.logger.handlers:
            handler = logging.FileHandler('requests.log')
            formatter = logging.Formatter('%(asctime)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def __call__(self, request):
        # Get the user information
        user = "Anonymous"
        if hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user.username
        
        # Log the request information
        log_message = f"User: {user} - Path: {request.path} - Method: {request.method}"
        self.logger.info(log_message)
        
        # Process the request and get response
        response = self.get_response(request)
        
        return response
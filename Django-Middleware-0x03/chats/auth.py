# messaging_app/chats/auth.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication class with additional logging or validation if needed.
    """
    
    def authenticate(self, request):
        try:
            # Get the header
            header = self.get_header(request)
            if header is None:
                return None

            # Get the raw token
            raw_token = self.get_raw_token(header)
            if raw_token is None:
                return None

            # Validate the token
            validated_token = self.get_validated_token(raw_token)
            
            # Get the user from the validated token
            user = self.get_user(validated_token)
            
            return (user, validated_token)
            
        except AuthenticationFailed as e:
            # Re-raise the exception
            raise e
        except Exception as e:
            # Handle any other exceptions
            raise AuthenticationFailed('Invalid token') from e
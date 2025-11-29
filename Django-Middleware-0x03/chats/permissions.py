# chats/permissions.py
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

class IsParticipantOfConversation(permissions.BasePermission):
    """
    Custom permission to only allow participants in a conversation to:
    - Send, view, update and delete messages in that conversation
    """
    
    def has_permission(self, request, view):
        # Allow only authenticated users to access the API
        if not request.user or not request.user.is_authenticated:
            return False
        
        return True

    def has_object_permission(self, request, view, obj):
        """
        Check if the user is a participant in the conversation for:
        - GET, PUT, PATCH, DELETE methods
        """
        # For Conversation objects
        if hasattr(obj, 'participants'):
            is_participant = request.user in obj.participants.all()
            if not is_participant:
                raise PermissionDenied("You are not a participant in this conversation")
            return True
        
        # For Message objects - check if user is participant in the conversation
        if hasattr(obj, 'conversation'):
            is_participant = request.user in obj.conversation.participants.all()
            if not is_participant:
                raise PermissionDenied("You are not a participant in this conversation")
            
            # For PUT, PATCH, DELETE - check if user is the message sender
            if request.method in ['PUT', 'PATCH', 'DELETE']:
                if obj.sender != request.user:
                    raise PermissionDenied("You can only modify your own messages")
            
            return True
        
        return False

class IsAuthenticated(permissions.BasePermission):
    """
    Custom IsAuthenticated permission for consistency
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
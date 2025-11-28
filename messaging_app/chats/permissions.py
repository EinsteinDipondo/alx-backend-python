# chats/permissions.py
from rest_framework import permissions

class IsParticipantOfConversation(permissions.BasePermission):
    """
    Custom permission to only allow participants in a conversation to:
    - Send, view, update and delete messages in that conversation
    """
    
    def has_permission(self, request, view):
        # Allow only authenticated users to access the API
        if not request.user or not request.user.is_authenticated:
            return False
        
        # For creating messages, check if user is participant in the conversation
        if view.action == 'create':
            # This will be handled in the serializer or view
            return True
        
        return True

    def has_object_permission(self, request, view, obj):
        """
        Check if the user is a participant in the conversation
        """
        # For Conversation objects
        if hasattr(obj, 'participants'):
            return request.user in obj.participants.all()
        
        # For Message objects - check if user is participant in the conversation
        if hasattr(obj, 'conversation'):
            return request.user in obj.conversation.participants.all()
        
        # For other objects, default to safe methods only
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return False

class IsMessageOwner(permissions.BasePermission):
    """
    Custom permission to only allow message sender to update or delete their own messages
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any participant (handled by IsParticipantOfConversation)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions (update, delete) are only allowed to the message sender
        return obj.sender == request.user

class IsAuthenticated(permissions.BasePermission):
    """
    Custom IsAuthenticated permission for consistency
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
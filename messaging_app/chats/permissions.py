# messaging_app/chats/permissions.py
from rest_framework import permissions

class IsConversationParticipant(permissions.BasePermission):
    """
    Custom permission to only allow participants of a conversation to access it.
    """
    def has_object_permission(self, request, view, obj):
        # Check if the user is a participant in the conversation
        return request.user in obj.participants.all()

class IsMessageOwnerOrConversationParticipant(permissions.BasePermission):
    """
    Custom permission to only allow:
    - The message sender to access their own messages
    - Participants of the conversation to access messages in that conversation
    """
    def has_object_permission(self, request, view, obj):
        # User is the sender of the message
        if obj.sender == request.user:
            return True
        
        # User is a participant in the conversation that contains the message
        return request.user in obj.conversation.participants.all()

class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to access it.
    """
    def has_object_permission(self, request, view, obj):
        # For user profile or similar objects
        return obj.user == request.user

class CanAccessConversation(permissions.BasePermission):
    """
    Custom permission for conversation list view to only show user's conversations.
    This is used in get_queryset method of views.
    """
    def has_permission(self, request, view):
        # All authenticated users can access conversation lists
        # The filtering happens in the view's get_queryset method
        return request.user.is_authenticated
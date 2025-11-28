# chats/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer, ConversationCreateSerializer
from .permissions import IsParticipantOfConversation, IsMessageOwner, IsAuthenticated

class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing conversations.
    Users can only see conversations they are participants in.
    """
    permission_classes = [IsAuthenticated, IsParticipantOfConversation]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ConversationCreateSerializer
        return ConversationSerializer

    def get_queryset(self):
        """
        Return only conversations where the current user is a participant
        """
        return Conversation.objects.filter(participants=self.request.user)

    def perform_create(self, serializer):
        """
        Automatically add the current user as a participant when creating a conversation
        """
        conversation = serializer.save()
        conversation.participants.add(self.request.user)
        
        # Add other participants if provided
        participants = self.request.data.get('participants', [])
        for participant_id in participants:
            if participant_id != self.request.user.id:
                conversation.participants.add(participant_id)

    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """
        Custom action to add a participant to a conversation
        """
        conversation = self.get_object()
        participant_id = request.data.get('participant_id')
        
        if participant_id:
            conversation.participants.add(participant_id)
            return Response({'status': 'participant added'})
        return Response({'error': 'participant_id required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def remove_participant(self, request, pk=None):
        """
        Custom action to remove a participant from a conversation
        """
        conversation = self.get_object()
        participant_id = request.data.get('participant_id')
        
        if participant_id:
            # Don't allow removing yourself if you're the only participant
            if participant_id == request.user.id and conversation.participants.count() == 1:
                return Response(
                    {'error': 'Cannot remove yourself as the only participant'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            conversation.participants.remove(participant_id)
            return Response({'status': 'participant removed'})
        return Response({'error': 'participant_id required'}, status=status.HTTP_400_BAD_REQUEST)

class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing messages.
    Users can only access messages from conversations they are participants in.
    Users can only update/delete their own messages.
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, IsParticipantOfConversation, IsMessageOwner]

    def get_queryset(self):
        """
        Return only messages from conversations where the current user is a participant
        """
        user_conversations = Conversation.objects.filter(participants=self.request.user)
        return Message.objects.filter(conversation__in=user_conversations)

    def perform_create(self, serializer):
        """
        Set the sender as the current user when creating a message
        Also verify that the user is a participant in the conversation
        """
        conversation = serializer.validated_data['conversation']
        
        # Check if user is a participant in the conversation
        if self.request.user not in conversation.participants.all():
            raise PermissionDenied("You are not a participant in this conversation")
        
        serializer.save(sender=self.request.user)

    def get_permissions(self):
        """
        You can add custom permission logic based on action if needed
        """
        return super().get_permissions()
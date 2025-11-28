# chats/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer, ConversationCreateSerializer
from .permissions import IsParticipantOfConversation, IsAuthenticated

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

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """
        Custom action to get messages for a specific conversation
        Check if user is participant using conversation_id
        """
        conversation = self.get_object()
        
        # This will automatically check permissions via IsParticipantOfConversation
        messages = conversation.messages.all().order_by('timestamp')
        page = self.paginate_queryset(messages)
        
        if page is not None:
            serializer = MessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

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
                    status=status.HTTP_403_FORBIDDEN
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
    permission_classes = [IsAuthenticated, IsParticipantOfConversation]

    def get_queryset(self):
        """
        Return only messages from conversations where the current user is a participant
        """
        user_conversations = Conversation.objects.filter(participants=self.request.user)
        return Message.objects.filter(conversation__in=user_conversations)

    def list(self, request, *args, **kwargs):
        """
        Override list to allow filtering by conversation_id
        """
        conversation_id = request.query_params.get('conversation_id')
        
        if conversation_id:
            # Check if user is participant in this specific conversation
            try:
                conversation = Conversation.objects.get(id=conversation_id)
                if request.user not in conversation.participants.all():
                    return Response(
                        {'error': 'You are not a participant in this conversation'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
                queryset = Message.objects.filter(conversation_id=conversation_id)
            except Conversation.DoesNotExist:
                return Response(
                    {'error': 'Conversation not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            queryset = self.get_queryset()
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Create a new message with conversation_id validation
        """
        conversation_id = request.data.get('conversation')
        
        if not conversation_id:
            return Response(
                {'error': 'conversation_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if conversation exists and user is participant
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            if request.user not in conversation.participants.all():
                return Response(
                    {'error': 'You are not a participant in this conversation'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """
        Set the sender as the current user when creating a message
        Conversation validation is already done in create() method
        """
        serializer.save(sender=self.request.user)

    def update(self, request, *args, **kwargs):
        """
        Override update to check if user owns the message
        """
        message = self.get_object()
        
        # Check if user is the sender of the message (for PUT, PATCH)
        if message.sender != request.user:
            return Response(
                {'error': 'You can only update your own messages'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Override destroy to check if user owns the message
        """
        message = self.get_object()
        
        # Check if user is the sender of the message (for DELETE)
        if message.sender != request.user:
            return Response(
                {'error': 'You can only delete your own messages'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """
        Custom action to mark a message as read
        Only participants can mark messages as read
        """
        message = self.get_object()
        
        # Check if user is participant in the conversation
        if request.user not in message.conversation.participants.all():
            return Response(
                {'error': 'You are not a participant in this conversation'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        message.is_read = True
        message.save()
        
        return Response({'status': 'message marked as read'})
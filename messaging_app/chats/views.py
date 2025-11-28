# chats/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer, ConversationCreateSerializer
from .permissions import IsParticipantOfConversation, IsAuthenticated
from .filters import MessageFilter, ConversationFilter
from .pagination import MessagePagination, ConversationPagination

class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing conversations.
    Users can only see conversations they are participants in.
    """
    permission_classes = [IsAuthenticated, IsParticipantOfConversation]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ConversationFilter
    pagination_class = ConversationPagination
    search_fields = ['participants__username', 'participants__email']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ConversationCreateSerializer
        return ConversationSerializer

    def get_queryset(self):
        """
        Return only conversations where the current user is a participant
        """
        return Conversation.objects.filter(participants=self.request.user).distinct()

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
        Custom action to get messages for a specific conversation with pagination and filtering
        """
        conversation = self.get_object()
        
        # Get filtered and paginated messages
        messages = Message.objects.filter(conversation=conversation)
        
        # Apply filtering
        message_filter = MessageFilter(request.GET, queryset=messages)
        filtered_messages = message_filter.qs
        
        # Apply ordering (newest first by default)
        ordering = request.GET.get('ordering', '-timestamp')
        if ordering:
            filtered_messages = filtered_messages.order_by(ordering)
        
        # Paginate
        page = self.paginate_queryset(filtered_messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = MessageSerializer(filtered_messages, many=True)
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
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = MessageFilter
    pagination_class = MessagePagination
    search_fields = ['content', 'sender__username']
    ordering_fields = ['timestamp', 'sender__username']
    ordering = ['-timestamp']  # Newest messages first by default

    def get_queryset(self):
        """
        Return only messages from conversations where the current user is a participant
        """
        user_conversations = Conversation.objects.filter(participants=self.request.user)
        return Message.objects.filter(conversation__in=user_conversations).select_related('sender', 'conversation')

    def list(self, request, *args, **kwargs):
        """
        Override list to apply custom filtering and ensure user can only see their conversations
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Additional security: ensure user can only filter by conversations they participate in
        conversation_id = request.query_params.get('conversation')
        if conversation_id:
            try:
                conversation = Conversation.objects.get(id=conversation_id)
                if request.user not in conversation.participants.all():
                    return Response(
                        {'error': 'You are not a participant in this conversation'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Conversation.DoesNotExist:
                pass
        
        # Apply the same check for participant filter
        participant_id = request.query_params.get('participant')
        if participant_id:
            # Ensure the filtered conversations still only include user's conversations
            queryset = queryset.filter(conversation__participants=self.request.user)
        
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
        """
        serializer.save(sender=self.request.user)

    def update(self, request, *args, **kwargs):
        """
        Override update to check if user owns the message
        """
        message = self.get_object()
        
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
        """
        message = self.get_object()
        
        if request.user not in message.conversation.participants.all():
            return Response(
                {'error': 'You are not a participant in this conversation'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        message.is_read = True
        message.save()
        
        return Response({'status': 'message marked as read'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """
        Custom action to get count of unread messages
        """
        unread_count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': unread_count})
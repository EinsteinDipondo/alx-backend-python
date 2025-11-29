# chats/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer, ConversationCreateSerializer
from .permissions import IsParticipantOfConversation, IsAuthenticated
from .filters import MessageFilter, ConversationFilter

class MessagePagination(PageNumberPagination):
    """
    Custom pagination for messages - 20 messages per page
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
            },
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'results': data
        })

class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing conversations.
    Users can only see conversations they are participants in.
    """
    permission_classes = [IsAuthenticated, IsParticipantOfConversation]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ConversationFilter
    pagination_class = PageNumberPagination  # Use PageNumberPagination
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
        
        # Apply filtering using MessageFilter
        message_filter = MessageFilter(request.GET, queryset=messages)
        filtered_messages = message_filter.qs
        
        # Apply ordering (newest first by default)
        ordering = request.GET.get('ordering', '-timestamp')
        if ordering:
            filtered_messages = filtered_messages.order_by(ordering)
        
        # Paginate using PageNumberPagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(filtered_messages, request)
        
        if page is not None:
            serializer = MessageSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = MessageSerializer(filtered_messages, many=True)
        return Response(serializer.data)

class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing messages.
    Users can only access messages from conversations they are participants in.
    Users can only update/delete their own messages.
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, IsParticipantOfConversation]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = MessageFilter  # Use the MessageFilter class
    pagination_class = MessagePagination  # Custom pagination with 20 per page
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
        
        # Apply the same check for user filter
        user_id = request.query_params.get('user')
        if user_id:
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

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Custom search action with filtering
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Example of using multiple filters together
        # This demonstrates filtering conversations with specific users AND messages within time range
        user_id = request.query_params.get('user')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if user_id and start_date and end_date:
            # This demonstrates the exact requirement: 
            # "retrieve conversations with specific users or messages within a time range"
            queryset = queryset.filter(
                Q(conversation__participants=user_id) |
                Q(timestamp__range=[start_date, end_date])
            )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
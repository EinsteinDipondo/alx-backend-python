from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import User, Conversation, Message, ConversationParticipant
from .serializers import (
    UserSerializer,
    ConversationSerializer,
    ConversationDetailSerializer,
    MessageSerializer,
    MessageWithConversationSerializer,
    ConversationMessageSerializer
)


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing, creating, and managing conversations
    """
    queryset = Conversation.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Return appropriate serializer class based on action
        """
        if self.action == 'retrieve':
            return ConversationDetailSerializer
        elif self.action == 'messages':
            return ConversationMessageSerializer
        return ConversationSerializer

    def get_queryset(self):
        """
        Return conversations where the current user is a participant
        """
        user = self.request.user
        return Conversation.objects.filter(participants=user).prefetch_related(
            'participants', 'messages', 'messages__sender'
        ).order_by('-created_at')

    def perform_create(self, serializer):
        """
        Create a new conversation and ensure the creator is included as a participant
        """
        conversation = serializer.save()
        
        # Automatically add the current user as a participant if not already included
        if self.request.user not in conversation.participants.all():
            ConversationParticipant.objects.create(
                conversation=conversation,
                user=self.request.user
            )

    def create(self, request, *args, **kwargs):
        """
        Create a new conversation with participants
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Ensure the current user is included in participants
        participant_ids = request.data.get('participant_ids', [])
        current_user_id = str(request.user.user_id)
        
        if current_user_id not in [str(pid) for pid in participant_ids]:
            participant_ids.append(current_user_id)
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """
        Custom action to get all messages in a conversation
        """
        conversation = self.get_object()
        messages = conversation.messages.all().order_by('sent_at')
        page = self.paginate_queryset(messages)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """
        Custom action to add a participant to a conversation
        """
        conversation = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {"error": "user_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if conversation.participants.filter(user_id=user_id).exists():
            return Response(
                {"error": "User is already a participant"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ConversationParticipant.objects.create(
            conversation=conversation,
            user=user
        )
        
        return Response(
            {"message": "Participant added successfully"}, 
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'])
    def participants(self, request, pk=None):
        """
        Custom action to get all participants in a conversation
        """
        conversation = self.get_object()
        participants = conversation.participants.all()
        serializer = UserSerializer(participants, many=True)
        return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing, creating, and managing messages
    """
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """
        Return appropriate serializer class based on action
        """
        if self.action == 'list':
            return MessageWithConversationSerializer
        return MessageSerializer

    def get_queryset(self):
        """
        Return messages that the current user can access
        (messages in conversations where user is a participant)
        """
        user = self.request.user
        user_conversations = Conversation.objects.filter(participants=user)
        return Message.objects.filter(
            conversation__in=user_conversations
        ).select_related('sender', 'conversation').order_by('-sent_at')

    def perform_create(self, serializer):
        """
        Automatically set the sender to the current user
        """
        serializer.save(sender=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Create a new message in a conversation
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check if user has access to the conversation
        conversation_id = request.data.get('conversation')
        try:
            conversation = Conversation.objects.get(conversation_id=conversation_id)
            if not conversation.participants.filter(user_id=request.user.user_id).exists():
                return Response(
                    {"error": "You are not a participant in this conversation"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except Conversation.DoesNotExist:
            return Response(
                {"error": "Conversation not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )

    @action(detail=False, methods=['get'])
    def my_messages(self, request):
        """
        Custom action to get current user's messages
        """
        user = request.user
        messages = Message.objects.filter(sender=user).select_related(
            'conversation'
        ).order_by('-sent_at')
        
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageWithConversationSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = MessageWithConversationSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Custom action to search messages by content
        """
        query = request.query_params.get('q', '')
        if not query:
            return Response(
                {"error": "Search query parameter 'q' is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        user_conversations = Conversation.objects.filter(participants=user)
        
        messages = Message.objects.filter(
            conversation__in=user_conversations,
            message_body__icontains=query
        ).select_related('sender', 'conversation').order_by('-sent_at')
        
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageWithConversationSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = MessageWithConversationSerializer(messages, many=True)
        return Response(serializer.data)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing user instances
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Users can only see other users they share conversations with
        """
        user = self.request.user
        user_conversations = Conversation.objects.filter(participants=user)
        
        # Get all users who share conversations with the current user
        shared_users = User.objects.filter(
            conversations__in=user_conversations
        ).exclude(user_id=user.user_id).distinct()
        
        return shared_users

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Custom action to get current user's profile
        """
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)
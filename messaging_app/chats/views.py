# chats/views.py
from rest_framework import viewsets, permissions
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from .permissions import IsConversationParticipant, IsMessageOwnerOrConversationParticipant, CanAccessConversation

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated, CanAccessConversation]

    def get_queryset(self):
        # Users can only see conversations they are participants in
        return Conversation.objects.filter(participants=self.request.user)

    def get_permissions(self):
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAuthenticated, IsConversationParticipant]
        return super().get_permissions()

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsMessageOwnerOrConversationParticipant]

    def get_queryset(self):
        # Users can only see messages from conversations they participate in
        user_conversations = Conversation.objects.filter(participants=self.request.user)
        return Message.objects.filter(conversation__in=user_conversations)

    def perform_create(self, serializer):
        # Set the sender as the current user when creating a message
        serializer.save(sender=self.request.user)
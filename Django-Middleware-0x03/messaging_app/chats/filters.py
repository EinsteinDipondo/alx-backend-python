# chats/filters.py
import django_filters
from django_filters import rest_framework as filters
from .models import Message, Conversation
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta

class MessageFilter(filters.FilterSet):
    """
    Filter for messages to retrieve:
    - Conversations with specific users (via conversation participants)
    - Messages within a time range
    """
    
    # Filter by conversation ID
    conversation = filters.ModelChoiceFilter(
        field_name='conversation',
        queryset=Conversation.objects.all(),
        label='Conversation ID'
    )
    
    # Filter by specific user (participant in the conversation)
    user = filters.ModelChoiceFilter(
        method='filter_by_user',
        queryset=User.objects.all(),
        label='User (participant in conversation)'
    )
    
    # Filter by sender
    sender = filters.ModelChoiceFilter(
        field_name='sender',
        queryset=User.objects.all(),
        label='Sender'
    )
    
    # Time range filtering
    start_date = filters.DateTimeFilter(
        field_name='timestamp', 
        lookup_expr='gte',
        label='Start Date (YYYY-MM-DD HH:MM:SS)'
    )
    
    end_date = filters.DateTimeFilter(
        field_name='timestamp', 
        lookup_expr='lte',
        label='End Date (YYYY-MM-DD HH:MM:SS)'
    )
    
    # Date range (date only, without time)
    start_date_date = filters.DateFilter(
        field_name='timestamp', 
        lookup_expr='gte',
        label='Start Date (YYYY-MM-DD)'
    )
    
    end_date_date = filters.DateFilter(
        field_name='timestamp', 
        lookup_expr='lte',
        label='End Date (YYYY-MM-DD)'
    )
    
    # Last N days filtering
    last_days = filters.NumberFilter(
        method='filter_last_days',
        label='Last N Days'
    )
    
    # Today's messages
    today = filters.BooleanFilter(
        method='filter_today',
        label="Today's Messages"
    )
    
    # Unread messages
    unread = filters.BooleanFilter(
        field_name='is_read',
        lookup_expr='exact',
        exclude=True,
        label='Unread Messages'
    )

    class Meta:
        model = Message
        fields = [
            'conversation', 
            'sender', 
            'user',
            'is_read'
        ]

    def filter_by_user(self, queryset, name, value):
        """
        Filter messages by conversations that include a specific user
        """
        if value:
            # Get conversations that include the specified user
            conversations_with_user = Conversation.objects.filter(participants=value)
            return queryset.filter(conversation__in=conversations_with_user)
        return queryset

    def filter_last_days(self, queryset, name, value):
        """
        Filter messages from the last N days
        """
        if value:
            start_date = timezone.now() - timedelta(days=value)
            return queryset.filter(timestamp__gte=start_date)
        return queryset

    def filter_today(self, queryset, name, value):
        """
        Filter today's messages
        """
        if value:
            today = timezone.now().date()
            return queryset.filter(timestamp__date=today)
        return queryset

class ConversationFilter(filters.FilterSet):
    """
    Filter for conversations with specific users
    """
    # Filter by participant user
    participant = filters.ModelChoiceFilter(
        field_name='participants',
        queryset=User.objects.all(),
        label='Participant User'
    )
    
    # Filter by multiple participants (exact match)
    with_users = filters.ModelMultipleChoiceFilter(
        field_name='participants',
        queryset=User.objects.all(),
        label='With Users (exact match)'
    )
    
    # Filter by conversation created after date
    created_after = filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Created After'
    )
    
    # Filter by conversation updated after date
    updated_after = filters.DateTimeFilter(
        field_name='updated_at',
        lookup_expr='gte',
        label='Updated After'
    )

    class Meta:
        model = Conversation
        fields = ['participant']

    def filter_has_unread(self, queryset, name, value):
        """
        Filter conversations that have unread messages
        """
        if value:
            return queryset.filter(messages__is_read=False).distinct()
        return queryset
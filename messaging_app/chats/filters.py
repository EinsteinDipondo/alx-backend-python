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
    - Messages with specific users (via conversation participants)
    - Messages within a time range
    - Messages from specific conversations
    """
    conversation = filters.ModelChoiceFilter(
        field_name='conversation',
        queryset=Conversation.objects.all(),
        label='Conversation'
    )
    
    participant = filters.ModelChoiceFilter(
        field_name='conversation__participants',
        queryset=User.objects.all(),
        label='Participant User'
    )
    
    sender = filters.ModelChoiceFilter(
        field_name='sender',
        queryset=User.objects.all(),
        label='Sender'
    )
    
    # Date range filtering
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
            'participant',
            'is_read'
        ]

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
    Filter for conversations
    """
    participant = filters.ModelChoiceFilter(
        field_name='participants',
        queryset=User.objects.all(),
        label='Participant'
    )
    
    has_unread = filters.BooleanFilter(
        method='filter_has_unread',
        label='Has Unread Messages'
    )
    
    created_after = filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Created After'
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
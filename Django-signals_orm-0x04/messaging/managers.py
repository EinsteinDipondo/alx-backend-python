from django.db import models
from django.db.models import Q, Count, Case, When, IntegerField
from django.utils import timezone
from datetime import timedelta

class UnreadMessagesManager(models.Manager):
    """
    Custom manager for unread messages with optimized queries
    """
    
    def get_queryset(self):
        """Default queryset for this manager"""
        return super().get_queryset()
    
    def unread_for_user(self, user):
        """
        Get all unread messages for a specific user
        Uses .only() to fetch only necessary fields for optimization
        """
        return self.get_queryset().filter(
            receiver=user,
            is_read=False
        ).select_related('sender').only(
            'id', 'sender__username', 'sender__id', 'content', 
            'timestamp', 'parent_message_id', 'is_thread_starter'
        ).order_by('-timestamp')
    
    def unread_count_for_user(self, user):
        """
        Get count of unread messages for a user
        More efficient than len(queryset) for counting
        """
        return self.unread_for_user(user).count()
    
    def unread_thread_starters_for_user(self, user):
        """
        Get unread thread starter messages for a user
        """
        return self.unread_for_user(user).filter(
            is_thread_starter=True
        ).only(
            'id', 'sender__username', 'content', 'timestamp'
        )
    
    def unread_replies_for_user(self, user):
        """
        Get unread reply messages for a user
        """
        return self.unread_for_user(user).filter(
            is_thread_starter=False
        ).select_related('parent_message').only(
            'id', 'sender__username', 'content', 'timestamp',
            'parent_message__id', 'parent_message__content'
        )
    
    def mark_as_read(self, user, message_ids=None):
        """
        Mark messages as read for a user
        If message_ids is provided, only mark those specific messages
        """
        queryset = self.unread_for_user(user)
        if message_ids:
            queryset = queryset.filter(id__in=message_ids)
        
        return queryset.update(is_read=True)
    
    def unread_by_conversation(self, user):
        """
        Get unread messages grouped by conversation/thread
        """
        return self.unread_for_user(user).values(
            'parent_message_id'
        ).annotate(
            unread_count=Count('id'),
            oldest_unread=models.Min('timestamp')
        ).order_by('-oldest_unread')

class MessageManager(models.Manager):
    """
    Default manager with additional custom methods
    """
    
    def create_message(self, sender, receiver, content, parent_message=None):
        """
        Custom method to create a message with proper threading
        """
        message = self.model(
            sender=sender,
            receiver=receiver,
            content=content,
            parent_message=parent_message
        )
        message.save()
        return message
    
    def get_user_inbox(self, user):
        """
        Get all messages for a user (both sent and received)
        with optimized queries
        """
        return self.filter(
            Q(sender=user) | Q(receiver=user)
        ).select_related('sender', 'receiver').prefetch_related(
            'replies'
        ).only(
            'id', 'sender__username', 'receiver__username', 'content',
            'timestamp', 'is_read', 'is_thread_starter', 'parent_message_id'
        ).order_by('-timestamp')
    
    def get_conversation_between(self, user1, user2):
        """
        Get conversation between two users
        """
        return self.filter(
            (Q(sender=user1) & Q(receiver=user2)) |
            (Q(sender=user2) & Q(receiver=user1))
        ).select_related('sender', 'receiver').only(
            'id', 'sender__username', 'receiver__username', 'content',
            'timestamp', 'is_read', 'is_thread_starter'
        ).order_by('timestamp')

class UnreadMessageCountManager(models.Manager):
    """
    Specialized manager for unread message counts and statistics
    """
    
    def get_user_unread_stats(self, user):
        """
        Get comprehensive unread message statistics for a user
        """
        from django.db.models import Count
        
        # Base queryset for unread messages
        base_qs = Message.unread.unread_for_user(user)
        
        # Today's unread messages
        today = timezone.now().date()
        today_unread = base_qs.filter(
            timestamp__date=today
        ).count()
        
        # Unread messages from last 7 days
        week_ago = timezone.now() - timedelta(days=7)
        week_unread = base_qs.filter(
            timestamp__gte=week_ago
        ).count()
        
        # Unread thread starters vs replies
        thread_starters_unread = base_qs.filter(
            is_thread_starter=True
        ).count()
        
        replies_unread = base_qs.filter(
            is_thread_starter=False
        ).count()
        
        # Unread by sender
        unread_by_sender = base_qs.values(
            'sender__username'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        return {
            'total_unread': base_qs.count(),
            'today_unread': today_unread,
            'week_unread': week_unread,
            'thread_starters_unread': thread_starters_unread,
            'replies_unread': replies_unread,
            'unread_by_sender': list(unread_by_sender),
        }
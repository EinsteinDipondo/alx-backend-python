from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q, Count, Case, When, IntegerField, Manager
from django.urls import reverse
from django.db import connection

class UnreadMessagesManager(Manager):
    """
    Custom manager for unread messages with optimized queries
    """
    
    def get_queryset(self):
        """Default queryset for this manager"""
        return super().get_queryset()
    
    def for_user(self, user):
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
        )
    
    def unread_count_for_user(self, user):
        """
        Get count of unread messages for a user
        More efficient than len(queryset) for counting
        """
        return self.for_user(user).count()
    
    def unread_thread_starters_for_user(self, user):
        """
        Get unread thread starter messages for a user
        """
        return self.for_user(user).filter(
            is_thread_starter=True
        ).only(
            'id', 'sender__username', 'content', 'timestamp'
        )
    
    def unread_replies_for_user(self, user):
        """
        Get unread reply messages for a user
        """
        return self.for_user(user).filter(
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
        queryset = self.for_user(user)
        if message_ids:
            queryset = queryset.filter(id__in=message_ids)
        
        return queryset.update(is_read=True)
    
    def unread_by_conversation(self, user):
        """
        Get unread messages grouped by conversation/thread
        """
        from django.db.models import Min
        return self.for_user(user).values(
            'parent_message_id'
        ).annotate(
            unread_count=Count('id'),
            oldest_unread=Min('timestamp')
        ).order_by('-oldest_unread')

class MessageManager(Manager):
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

class Message(models.Model):
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_messages'
    )
    receiver = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='received_messages'
    )
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Read status field - replacing the previous is_read BooleanField
    is_read = models.BooleanField(
        default=False,
        help_text="Whether the receiver has read this message"
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the message was read by the receiver"
    )
    
    edited = models.BooleanField(default=False)
    last_edited = models.DateTimeField(null=True, blank=True)
    edit_count = models.PositiveIntegerField(default=0)
    
    # Threading fields
    parent_message = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='replies',
        null=True,
        blank=True,
        help_text="The message this is replying to"
    )
    is_thread_starter = models.BooleanField(
        default=False,
        help_text="Whether this message started a conversation thread"
    )
    thread_depth = models.PositiveIntegerField(
        default=0,
        help_text="Depth in the thread hierarchy (0 for root messages)"
    )
    
    # Managers
    objects = MessageManager()  # Default manager
    unread = UnreadMessagesManager()  # Custom manager for unread messages
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['receiver', 'is_read', 'timestamp']),
            models.Index(fields=['parent_message', 'timestamp']),
            models.Index(fields=['sender', 'receiver', 'timestamp']),
            models.Index(fields=['is_thread_starter', 'timestamp']),
        ]
    
    def __str__(self):
        if self.parent_message:
            return f"Reply from {self.sender} to {self.receiver} (Thread: {self.parent_message.id})"
        return f"Message from {self.sender} to {self.receiver}"
    
    def save(self, *args, **kwargs):
        # Handle threading logic
        if self.parent_message:
            self.is_thread_starter = False
            self.thread_depth = self.parent_message.thread_depth + 1
        else:
            self.is_thread_starter = True
            self.thread_depth = 0
        
        # Handle edit tracking
        if self.pk:
            try:
                original = Message.objects.get(pk=self.pk)
                if original.content != self.content:
                    self.edited = True
                    self.last_edited = timezone.now()
                    self.edit_count += 1
            except Message.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
    
    def mark_as_read(self, commit=True):
        """
        Mark this message as read
        """
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            if commit:
                self.save(update_fields=['is_read', 'read_at'])
    
    @property
    def is_unread(self):
        """Convenience property to check if message is unread"""
        return not self.is_read
    
    @property
    def thread_root(self):
        """Get the root message of the thread using recursive approach"""
        current = self
        while current.parent_message:
            current = current.parent_message
        return current
    
    @property
    def reply_count(self):
        """Get total number of replies in this thread"""
        return self.get_all_replies().count()
    
    def get_all_replies(self):
        """Get all replies recursively using Django ORM"""
        return Message.objects.filter(
            Q(parent_message=self) |
            Q(parent_message__parent_message=self) |
            Q(parent_message__parent_message__parent_message=self) |
            Q(parent_message__parent_message__parent_message__parent_message=self)
        )
    
    @classmethod
    def get_thread_tree(cls, root_message_id):
        """
        Build a complete thread tree using recursive CTE with raw SQL
        This provides true recursive querying for unlimited depth
        """
        with connection.cursor() as cursor:
            cursor.execute("""
                WITH RECURSIVE thread_tree AS (
                    -- Base case: the root message
                    SELECT 
                        id,
                        sender_id,
                        receiver_id,
                        content,
                        timestamp,
                        is_read,
                        edited,
                        parent_message_id,
                        thread_depth,
                        0 as level,
                        CAST(id AS TEXT) as path
                    FROM messaging_message 
                    WHERE id = %s
                    
                    UNION ALL
                    
                    -- Recursive case: all replies
                    SELECT 
                        m.id,
                        m.sender_id,
                        m.receiver_id,
                        m.content,
                        m.timestamp,
                        m.is_read,
                        m.edited,
                        m.parent_message_id,
                        m.thread_depth,
                        tt.level + 1 as level,
                        tt.path || '->' || m.id as path
                    FROM messaging_message m
                    INNER JOIN thread_tree tt ON m.parent_message_id = tt.id
                )
                SELECT * FROM thread_tree
                ORDER BY path;
            """, [root_message_id])
            
            columns = [col[0] for col in cursor.description]
            return [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]
    
    @classmethod
    def get_thread_messages_optimized(cls, thread_root_id, max_depth=10):
        """
        Get all messages in a thread using optimized ORM queries
        This simulates recursive behavior with multiple prefetches
        """
        # Build a complex filter to get messages up to max_depth levels deep
        depth_filters = Q(id=thread_root_id)
        current_filter = Q(parent_message_id=thread_root_id)
        
        for depth in range(2, max_depth + 1):
            parent_field = 'parent_message__' * (depth - 1) + 'parent_message_id'
            depth_filters |= Q(**{parent_field: thread_root_id})
        
        return cls.objects.filter(depth_filters).select_related(
            'sender', 'receiver'
        ).prefetch_related(
            'replies__sender',
            'replies__receiver',
            'replies__replies__sender',
            'replies__replies__receiver',
            'replies__replies__replies__sender',
            'replies__replies__replies__receiver'
        ).only(
            'id', 'sender__username', 'receiver__username', 'content',
            'timestamp', 'is_read', 'thread_depth', 'parent_message_id',
            'is_thread_starter', 'edited'
        ).order_by('thread_depth', 'timestamp')
    
    def build_thread_hierarchy(self, messages=None):
        """
        Build a hierarchical thread structure from a flat queryset
        This is an efficient way to handle threading in Python
        """
        if messages is None:
            messages = Message.objects.filter(
                Q(id=self.thread_root.id) | 
                Q(parent_message__thread_root=self.thread_root)
            ).select_related('sender', 'receiver', 'parent_message').only(
                'id', 'sender__username', 'receiver__username', 'content',
                'timestamp', 'is_read', 'thread_depth', 'parent_message_id'
            ).order_by('thread_depth', 'timestamp')
        
        message_dict = {}
        root_message = None
        
        # Build dictionary for quick lookup
        for message in messages:
            message_dict[message.id] = {
                'message': message,
                'replies': []
            }
            if message.parent_message is None:
                root_message = message_dict[message.id]
        
        # Build hierarchy
        for message in messages:
            if message.parent_message and message.parent_message.id in message_dict:
                parent_data = message_dict[message.parent_message.id]
                parent_data['replies'].append(message_dict[message.id])
        
        return root_message

class UnreadMessageCountManager(Manager):
    """
    Specialized manager for unread message counts and statistics
    """
    
    def get_user_unread_stats(self, user):
        """
        Get comprehensive unread message statistics for a user
        """
        from django.db.models import Count, Q
        from django.utils import timezone
        from datetime import timedelta
        
        # Base queryset for unread messages
        base_qs = Message.unread.for_user(user)
        
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

# Add the specialized manager to Message class
Message.unread_stats = UnreadMessageCountManager()

class MessageHistory(models.Model):
    message = models.ForeignKey(
        Message, 
        on_delete=models.CASCADE, 
        related_name='history'
    )
    old_content = models.TextField()
    edited_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='message_edits'
    )
    edited_at = models.DateTimeField(default=timezone.now)
    edit_reason = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        ordering = ['-edited_at']
        verbose_name = 'Message History'
        verbose_name_plural = 'Message Histories'
    
    def __str__(self):
        return f"History for Message {self.message.id} edited by {self.edited_by}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('message', 'New Message'),
        ('system', 'System Notification'),
        ('edit', 'Message Edited'),
        ('reply', 'Thread Reply'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    message = models.ForeignKey(
        Message, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        null=True,
        blank=True
    )
    notification_type = models.CharField(
        max_length=20, 
        choices=NOTIFICATION_TYPES, 
        default='message'
    )
    title = models.CharField(max_length=255)
    message_content = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.user}: {self.title}"

class ConversationManager(models.Manager):
    """Custom manager for conversation-related queries"""
    
    def get_user_conversations_optimized(self, user):
        """Get conversations with optimized queries using select_related and prefetch_related"""
        from django.db.models import Prefetch, Count
        
        # Get thread starters and prefetch limited replies
        thread_starters = Message.objects.filter(
            is_thread_starter=True
        ).filter(
            Q(sender=user) | Q(receiver=user)
        ).select_related('sender', 'receiver').annotate(
            total_replies=Count('replies'),
            unread_replies=Count(
                Case(
                    When(replies__is_read=False, replies__receiver=user, then=1),
                    output_field=IntegerField(),
                )
            )
        ).prefetch_related(
            Prefetch(
                'replies',
                queryset=Message.objects.select_related('sender', 'receiver').only(
                    'id', 'sender__username', 'content', 'timestamp', 'is_read'
                ).order_by('-timestamp')[:5]
            )
        ).only(
            'id', 'sender__username', 'receiver__username', 'content',
            'timestamp', 'is_read', 'is_thread_starter'
        ).order_by('-timestamp')
        
        return thread_starters

class Conversation(models.Model):
    """Model to represent conversation metadata (optional enhancement)"""
    participants = models.ManyToManyField(User, related_name='conversations')
    latest_message = models.ForeignKey(
        Message,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversation_latest'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    unread_count = models.PositiveIntegerField(default=0)
    
    objects = ConversationManager()
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        participants_names = ", ".join([user.username for user in self.participants.all()[:2]])
        return f"Conversation: {participants_names}"
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q, Count, Case, When, IntegerField
from django.urls import reverse
from django.db import connection

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
    is_read = models.BooleanField(default=False)
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
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
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
    
    def get_absolute_url(self):
        return reverse('messaging:message_thread', kwargs={'message_id': self.thread_root.id})
    
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
        # This uses a recursive common table expression (CTE) via raw SQL
        # for true recursive querying, but we'll implement an ORM alternative
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
            ).select_related('sender', 'receiver', 'parent_message').order_by('thread_depth', 'timestamp')
        
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

# ... (keep MessageHistory, Notification, Conversation models from previous implementation)
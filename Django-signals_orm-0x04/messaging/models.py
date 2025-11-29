from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q, Count, Case, When, IntegerField
from django.urls import reverse

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
            original = Message.objects.get(pk=self.pk)
            if original.content != self.content:
                self.edited = True
                self.last_edited = timezone.now()
                self.edit_count += 1
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('messaging:message_thread', kwargs={'message_id': self.thread_root.id})
    
    @property
    def thread_root(self):
        """Get the root message of the thread"""
        if self.parent_message:
            return self.parent_message.thread_root
        return self
    
    @property
    def reply_count(self):
        """Get total number of replies in this thread"""
        return self.replies.count()
    
    @property
    def direct_reply_count(self):
        """Get number of direct replies to this message"""
        return self.replies.filter(thread_depth=self.thread_depth + 1).count()
    
    def get_thread_participants(self):
        """Get all users who participated in this thread"""
        from django.db.models import Q
        thread_root = self.thread_root
        participants = User.objects.filter(
            Q(sent_messages__parent_message=thread_root) |
            Q(sent_messages=thread_root) |
            Q(received_messages__parent_message=thread_root) |
            Q(received_messages=thread_root)
        ).distinct()
        return participants
    
    @classmethod
    def get_user_conversations(cls, user):
        """Get all conversation threads for a user"""
        # Get all thread starters where user is sender or receiver
        return cls.objects.filter(
            is_thread_starter=True
        ).filter(
            Q(sender=user) | Q(receiver=user)
        ).select_related('sender', 'receiver').prefetch_related('replies').order_by('-timestamp')
    
    @classmethod
    def get_thread_messages(cls, thread_root_id):
        """Get all messages in a thread with optimal querying"""
        return cls.objects.filter(
            Q(id=thread_root_id) | Q(parent_message_id=thread_root_id) | 
            Q(parent_message__parent_message_id=thread_root_id)
        ).select_related(
            'sender', 'receiver', 'parent_message'
        ).prefetch_related(
            'replies__sender',
            'replies__receiver',
            'replies__replies__sender',
            'replies__replies__receiver'
        ).order_by('thread_depth', 'timestamp')

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
            recent_reply_count=Count(
                Case(
                    When(replies__timestamp__gte=timezone.now() - timezone.timedelta(days=7), then=1),
                    output_field=IntegerField(),
                )
            )
        ).prefetch_related(
            Prefetch(
                'replies',
                queryset=Message.objects.select_related('sender', 'receiver').order_by('-timestamp')[:5]
            )
        ).order_by('-timestamp')
        
        return thread_starters
    
    def get_full_thread_optimized(self, thread_root_id):
        """Get full thread with all replies using optimized queries"""
        return Message.objects.filter(
            Q(id=thread_root_id) | 
            Q(parent_message_id=thread_root_id) |
            Q(parent_message__parent_message_id=thread_root_id) |
            Q(parent_message__parent_message__parent_message_id=thread_root_id)
        ).select_related(
            'sender', 'receiver', 'parent_message',
            'parent_message__sender', 'parent_message__receiver'
        ).prefetch_related(
            'replies__sender',
            'replies__receiver',
            'replies__replies__sender',
            'replies__replies__receiver'
        ).order_by('thread_depth', 'timestamp')
    
    def get_conversation_between_users(self, user1, user2):
        """Get all conversation threads between two users"""
        return Message.objects.filter(
            is_thread_starter=True
        ).filter(
            (Q(sender=user1) & Q(receiver=user2)) |
            (Q(sender=user2) & Q(receiver=user1))
        ).select_related('sender', 'receiver').prefetch_related(
            'replies__sender',
            'replies__receiver'
        ).order_by('-timestamp')

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
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Message, Notification, MessageHistory

@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    """
    Signal to create a notification when a new message is created
    """
    if created:
        # Create notification for the receiver
        Notification.objects.create(
            user=instance.receiver,
            message=instance,
            notification_type='message',
            title=f"New message from {instance.sender.username}",
            message_content=f"You have received a new message: {instance.content[:100]}..."
        )

@receiver(pre_save, sender=Message)
def log_message_edit(sender, instance, **kwargs):
    """
    Signal to log message edits before saving the updated message
    """
    if instance.pk:  # Only for existing messages (updates)
        try:
            original = Message.objects.get(pk=instance.pk)
            
            # Check if content has changed
            if original.content != instance.content:
                # Create message history record
                MessageHistory.objects.create(
                    message=instance,
                    old_content=original.content,
                    edited_by=instance.sender,  # Assuming sender is editing
                    edit_reason=f"Message edited (edit #{instance.edit_count + 1})"
                )
                
                # Create notification for edit (optional)
                Notification.objects.create(
                    user=instance.receiver,
                    message=instance,
                    notification_type='edit',
                    title=f"Message edited by {instance.sender.username}",
                    message_content=f"Message was edited. Previous content: {original.content[:100]}..."
                )
                
        except Message.DoesNotExist:
            # Message doesn't exist yet (shouldn't happen for updates)
            pass

# Optional: Signal for when a user is created
@receiver(post_save, sender=User)
def send_welcome_notification(sender, instance, created, **kwargs):
    """
    Example signal for sending welcome notification to new users
    """
    if created:
        Notification.objects.create(
            user=instance,
            notification_type='system',
            title="Welcome to our platform!",
            message_content="Thank you for joining us. We're excited to have you here!"
        )
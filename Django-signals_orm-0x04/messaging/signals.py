from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db import transaction
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

@receiver(post_delete, sender=User)
def cleanup_user_data(sender, instance, **kwargs):
    """
    Signal to clean up all user-related data after a user is deleted
    This handles additional cleanup beyond CASCADE deletes and ensures
    all related data is properly removed.
    """
    user_id = instance.id
    username = instance.username
    
    print(f"Cleaning up data for deleted user: {username} (ID: {user_id})")
    
    # Use transaction to ensure data consistency
    with transaction.atomic():
        # Clean up messages where user was sender or receiver
        # Even with CASCADE, we explicitly delete to ensure cleanup
        sent_messages = Message.objects.filter(sender_id=user_id)
        received_messages = Message.objects.filter(receiver_id=user_id)
        
        sent_count = sent_messages.count()
        received_count = received_messages.count()
        
        # Delete messages where user was sender or receiver
        sent_messages.delete()
        received_messages.delete()
        
        print(f"Deleted {sent_count} sent messages and {received_count} received messages")
        
        # Clean up notifications for the user
        user_notifications = Notification.objects.filter(user_id=user_id)
        notification_count = user_notifications.count()
        user_notifications.delete()
        print(f"Deleted {notification_count} user notifications")
        
        # Clean up message history where user was the editor
        user_edit_history = MessageHistory.objects.filter(edited_by_id=user_id)
        edit_history_count = user_edit_history.count()
        user_edit_history.delete()
        print(f"Deleted {edit_history_count} message edit history records")
        
        # Additional cleanup: Notifications related to messages that involved this user
        # This handles cases where notifications might reference messages that are being deleted
        related_notifications = Notification.objects.filter(
            message__sender_id=user_id
        ) | Notification.objects.filter(
            message__receiver_id=user_id
        )
        
        related_notification_count = related_notifications.count()
        related_notifications.delete()
        print(f"Deleted {related_notification_count} related notifications")
    
    # Log the cleanup completion
    print(f"Completed cleanup for deleted user: {username}")

# Optional: Pre-delete signal to log what will be deleted
@receiver(post_delete, sender=User)
def log_user_deletion_stats(sender, instance, **kwargs):
    """
    Additional signal to log statistics about what was deleted
    This runs after the main cleanup signal
    """
    # This is just for logging purposes - the actual deletion happens in cleanup_user_data
    print(f"User {instance.username} deletion processing completed")

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
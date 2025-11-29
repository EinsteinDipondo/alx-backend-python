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
    This provides an additional layer of cleanup beyond CASCADE deletes
    """
    user_id = instance.id
    username = instance.username
    
    print(f"Cleaning up data for deleted user: {username} (ID: {user_id})")
    
    # Additional cleanup for any orphaned records or complex relationships
    # Even with CASCADE, we might want to do additional logging or cleanup
    
    # Clean up any notifications where this user was involved
    # This handles cases where CASCADE might not cover everything
    try:
        # Delete notifications for messages where this user was sender or receiver
        notifications_to_delete = Notification.objects.filter(
            message__sender=instance
        ) | Notification.objects.filter(
            message__receiver=instance
        )
        
        notification_count = notifications_to_delete.count()
        notifications_to_delete.delete()
        print(f"Deleted {notification_count} related notifications")
        
    except Exception as e:
        print(f"Error cleaning up notifications for user {username}: {e}")
    
    # Clean up message history where this user was the editor
    try:
        edit_history_count = MessageHistory.objects.filter(edited_by=instance).count()
        MessageHistory.objects.filter(edited_by=instance).delete()
        print(f"Deleted {edit_history_count} message edit history records")
        
    except Exception as e:
        print(f"Error cleaning up message history for user {username}: {e}")
    
    # Log the cleanup completion
    print(f"Completed cleanup for deleted user: {username}")

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

# Additional signal for pre_delete to log what will be deleted
@receiver(pre_save, sender=User)
def log_user_deletion_attempt(sender, instance, **kwargs):
    """
    Log when a user is about to be deleted (for audit purposes)
    """
    if instance.pk is not None:
        try:
            original_user = User.objects.get(pk=instance.pk)
            # User exists and is being modified
            pass
        except User.DoesNotExist:
            # User is being created, not deleted
            pass
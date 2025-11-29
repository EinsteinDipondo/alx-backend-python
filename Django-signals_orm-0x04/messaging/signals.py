from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Message, Notification

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
        
        # Optional: You can also send other types of notifications here
        # For example, email notifications, push notifications, etc.
        print(f"Notification created for {instance.receiver.username}")

# Optional: Signal for when a user is created (example of other signal usage)
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
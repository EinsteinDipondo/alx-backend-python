from django.test import TestCase
from django.contrib.auth.models import User
from .models import Message, Notification

class MessageSignalTests(TestCase):
    
    def setUp(self):
        # Create test users
        self.sender = User.objects.create_user(
            username='sender', 
            email='sender@example.com', 
            password='testpass123'
        )
        self.receiver = User.objects.create_user(
            username='receiver', 
            email='receiver@example.com', 
            password='testpass123'
        )
    
    def test_notification_created_on_new_message(self):
        """Test that a notification is automatically created when a new message is saved"""
        # Count initial notifications
        initial_notification_count = Notification.objects.count()
        
        # Create a new message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Hello, this is a test message!"
        )
        
        # Check that a notification was created
        final_notification_count = Notification.objects.count()
        self.assertEqual(final_notification_count, initial_notification_count + 1)
        
        # Verify notification details
        notification = Notification.objects.first()
        self.assertEqual(notification.user, self.receiver)
        self.assertEqual(notification.message, message)
        self.assertEqual(notification.notification_type, 'message')
        self.assertIn(self.sender.username, notification.title)
        self.assertIn("Hello", notification.message_content)
    
    def test_no_notification_on_message_update(self):
        """Test that notifications are not created when existing messages are updated"""
        # Create a message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Initial message"
        )
        
        # Count notifications after creation
        notification_count_after_creation = Notification.objects.count()
        
        # Update the message
        message.content = "Updated message"
        message.save()
        
        # Check that no new notification was created
        notification_count_after_update = Notification.objects.count()
        self.assertEqual(notification_count_after_update, notification_count_after_creation)
    
    def test_notification_content_truncation(self):
        """Test that long message content is properly truncated in notifications"""
        long_content = "A" * 200  # Create a very long message
        
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content=long_content
        )
        
        notification = Notification.objects.get(message=message)
        
        # Check that content is truncated
        self.assertTrue(len(notification.message_content) < len(long_content))
        self.assertTrue(notification.message_content.endswith("..."))

class NotificationModelTests(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='testpass123'
        )
    
    def test_notification_creation(self):
        """Test basic notification creation"""
        notification = Notification.objects.create(
            user=self.user,
            title="Test Notification",
            message_content="This is a test notification",
            notification_type='system'
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, "Test Notification")
        self.assertEqual(notification.notification_type, 'system')
        self.assertFalse(notification.is_read)
    
    def test_notification_str_representation(self):
        """Test the string representation of Notification model"""
        notification = Notification.objects.create(
            user=self.user,
            title="Test Notification",
            message_content="Test content"
        )
        
        expected_str = f"Notification for {self.user}: Test Notification"
        self.assertEqual(str(notification), expected_str)

class MessageModelTests(TestCase):
    
    def setUp(self):
        self.sender = User.objects.create_user(
            username='sender', 
            password='testpass123'
        )
        self.receiver = User.objects.create_user(
            username='receiver', 
            password='testpass123'
        )
    
    def test_message_creation(self):
        """Test basic message creation"""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Test message content"
        )
        
        self.assertEqual(message.sender, self.sender)
        self.assertEqual(message.receiver, self.receiver)
        self.assertEqual(message.content, "Test message content")
        self.assertFalse(message.is_read)
    
    def test_message_str_representation(self):
        """Test the string representation of Message model"""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Test content"
        )
        
        expected_str = f"Message from {self.sender} to {self.receiver}"
        self.assertEqual(str(message), expected_str)
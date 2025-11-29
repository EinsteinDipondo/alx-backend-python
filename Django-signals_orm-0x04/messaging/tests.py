from django.test import TestCase
from django.contrib.auth.models import User
from .models import Message, Notification, MessageHistory

class MessageEditSignalTests(TestCase):
    
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
        
        # Create initial message
        self.message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Initial message content"
        )
    
    def test_message_history_created_on_edit(self):
        """Test that message history is created when a message is edited"""
        # Count initial history records
        initial_history_count = MessageHistory.objects.count()
        
        # Update the message content
        self.message.content = "Updated message content"
        self.message.save()
        
        # Check that a history record was created
        final_history_count = MessageHistory.objects.count()
        self.assertEqual(final_history_count, initial_history_count + 1)
        
        # Verify history record details
        history = MessageHistory.objects.first()
        self.assertEqual(history.message, self.message)
        self.assertEqual(history.old_content, "Initial message content")
        self.assertEqual(history.edited_by, self.sender)
    
    def test_message_edit_fields_updated(self):
        """Test that edit-related fields are updated when message is edited"""
        # Initial state
        self.assertFalse(self.message.edited)
        self.assertIsNone(self.message.last_edited)
        self.assertEqual(self.message.edit_count, 0)
        
        # Edit the message
        self.message.content = "Edited content"
        self.message.save()
        
        # Refresh from database
        self.message.refresh_from_db()
        
        # Check that edit fields are updated
        self.assertTrue(self.message.edited)
        self.assertIsNotNone(self.message.last_edited)
        self.assertEqual(self.message.edit_count, 1)
    
    def test_multiple_edits_create_multiple_history_records(self):
        """Test that multiple edits create multiple history records"""
        initial_history_count = MessageHistory.objects.count()
        
        # First edit
        self.message.content = "First edit"
        self.message.save()
        
        # Second edit
        self.message.content = "Second edit"
        self.message.save()
        
        # Third edit
        self.message.content = "Third edit"
        self.message.save()
        
        final_history_count = MessageHistory.objects.count()
        self.assertEqual(final_history_count, initial_history_count + 3)
        
        # Verify edit count on message
        self.message.refresh_from_db()
        self.assertEqual(self.message.edit_count, 3)
        
        # Verify history records contain correct old content
        history_records = MessageHistory.objects.all().order_by('edited_at')
        self.assertEqual(history_records[0].old_content, "Initial message content")
        self.assertEqual(history_records[1].old_content, "First edit")
        self.assertEqual(history_records[2].old_content, "Second edit")
    
    def test_no_history_on_non_content_changes(self):
        """Test that history is not created when non-content fields change"""
        initial_history_count = MessageHistory.objects.count()
        
        # Change non-content field
        self.message.is_read = True
        self.message.save()
        
        final_history_count = MessageHistory.objects.count()
        self.assertEqual(final_history_count, initial_history_count)
    
    def test_edit_notification_created(self):
        """Test that a notification is created when a message is edited"""
        initial_notification_count = Notification.objects.filter(
            notification_type='edit'
        ).count()
        
        # Edit the message
        self.message.content = "Edited content"
        self.message.save()
        
        final_notification_count = Notification.objects.filter(
            notification_type='edit'
        ).count()
        
        self.assertEqual(final_notification_count, initial_notification_count + 1)
        
        # Verify edit notification details
        notification = Notification.objects.filter(notification_type='edit').first()
        self.assertEqual(notification.user, self.receiver)
        self.assertEqual(notification.message, self.message)
        self.assertIn("edited", notification.title.lower())

class MessageHistoryModelTests(TestCase):
    
    def setUp(self):
        self.sender = User.objects.create_user(
            username='sender', 
            password='testpass123'
        )
        self.receiver = User.objects.create_user(
            username='receiver', 
            password='testpass123'
        )
        self.message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Test message"
        )
    
    def test_message_history_creation(self):
        """Test basic message history creation"""
        history = MessageHistory.objects.create(
            message=self.message,
            old_content="Previous content",
            edited_by=self.sender,
            edit_reason="Test edit"
        )
        
        self.assertEqual(history.message, self.message)
        self.assertEqual(history.old_content, "Previous content")
        self.assertEqual(history.edited_by, self.sender)
        self.assertEqual(history.edit_reason, "Test edit")
    
    def test_message_history_str_representation(self):
        """Test the string representation of MessageHistory model"""
        history = MessageHistory.objects.create(
            message=self.message,
            old_content="Previous content",
            edited_by=self.sender
        )
        
        expected_str = f"History for Message {self.message.id} edited by {self.sender}"
        self.assertEqual(str(history), expected_str)

# ... (keep the existing NotificationModelTests and MessageModelTests from previous implementation)
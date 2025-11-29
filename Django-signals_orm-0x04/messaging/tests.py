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
# Add this to your messaging/tests.py

class UserDeletionSignalTests(TestCase):
    """
    Tests specifically for the post_delete signal cleanup functionality
    """
    
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            username='user1', 
            email='user1@example.com', 
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2', 
            email='user2@example.com', 
            password='testpass123'
        )
        
        # Create comprehensive test data
        self.message1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Message from user1 to user2"
        )
        
        self.message2 = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content="Message from user2 to user1"
        )
        
        # Create notifications
        self.notification1 = Notification.objects.create(
            user=self.user1,
            message=self.message2,
            title="Notification for user1",
            message_content="Test content"
        )
        
        self.notification2 = Notification.objects.create(
            user=self.user2,
            message=self.message1,
            title="Notification for user2", 
            message_content="Test content"
        )
        
        # Create message history
        self.message1.content = "Edited content"
        self.message1.save()  # This creates a MessageHistory record
        
        # Store initial counts
        self.initial_message_count = Message.objects.count()
        self.initial_notification_count = Notification.objects.count()
        self.initial_history_count = MessageHistory.objects.count()
    
    def test_post_delete_signal_cleans_up_sent_messages(self):
        """Test that post_delete signal deletes messages where user was sender"""
        sent_messages_count = Message.objects.filter(sender=self.user1).count()
        self.assertEqual(sent_messages_count, 1)  # message1
        
        # Delete user1 - this should trigger the post_delete signal
        self.user1.delete()
        
        # Verify sent messages are deleted
        self.assertFalse(Message.objects.filter(sender_id=self.user1.id).exists())
    
    def test_post_delete_signal_cleans_up_received_messages(self):
        """Test that post_delete signal deletes messages where user was receiver"""
        received_messages_count = Message.objects.filter(receiver=self.user1).count()
        self.assertEqual(received_messages_count, 1)  # message2
        
        # Delete user1
        self.user1.delete()
        
        # Verify received messages are deleted
        self.assertFalse(Message.objects.filter(receiver_id=self.user1.id).exists())
    
    def test_post_delete_signal_cleans_up_user_notifications(self):
        """Test that post_delete signal deletes user's notifications"""
        user_notifications_count = Notification.objects.filter(user=self.user1).count()
        self.assertEqual(user_notifications_count, 1)  # notification1
        
        # Delete user1
        self.user1.delete()
        
        # Verify user notifications are deleted
        self.assertFalse(Notification.objects.filter(user_id=self.user1.id).exists())
    
    def test_post_delete_signal_cleans_up_message_edit_history(self):
        """Test that post_delete signal deletes message edit history"""
        edit_history_count = MessageHistory.objects.filter(edited_by=self.user1).count()
        self.assertEqual(edit_history_count, 1)  # from message1 edit
        
        # Delete user1
        self.user1.delete()
        
        # Verify edit history is deleted
        self.assertFalse(MessageHistory.objects.filter(edited_by_id=self.user1.id).exists())
    
    def test_post_delete_signal_cleans_up_related_notifications(self):
        """Test that post_delete signal cleans up notifications related to user's messages"""
        # Count notifications related to user1's messages
        related_notifications_count = Notification.objects.filter(
            message__sender=self.user1
        ).count()
        self.assertEqual(related_notifications_count, 1)  # notification2 for message1
        
        # Delete user1
        self.user1.delete()
        
        # Verify related notifications are deleted
        self.assertFalse(Notification.objects.filter(message__sender_id=self.user1.id).exists())
    
    def test_complete_user_data_cleanup(self):
        """Test comprehensive cleanup of all user-related data"""
        # Store user ID before deletion
        user1_id = self.user1.id
        
        # Verify data exists before deletion
        self.assertTrue(Message.objects.filter(sender_id=user1_id).exists())
        self.assertTrue(Message.objects.filter(receiver_id=user1_id).exists())
        self.assertTrue(Notification.objects.filter(user_id=user1_id).exists())
        self.assertTrue(MessageHistory.objects.filter(edited_by_id=user1_id).exists())
        self.assertTrue(Notification.objects.filter(message__sender_id=user1_id).exists())
        
        # Delete user1 - this triggers the post_delete signal
        self.user1.delete()
        
        # Verify ALL user-related data is cleaned up
        self.assertFalse(Message.objects.filter(sender_id=user1_id).exists())
        self.assertFalse(Message.objects.filter(receiver_id=user1_id).exists())
        self.assertFalse(Notification.objects.filter(user_id=user1_id).exists())
        self.assertFalse(MessageHistory.objects.filter(edited_by_id=user1_id).exists())
        self.assertFalse(Notification.objects.filter(message__sender_id=user1_id).exists())
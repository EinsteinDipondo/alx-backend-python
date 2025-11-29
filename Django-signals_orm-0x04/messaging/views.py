from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView
from .models import Message, Notification, MessageHistory

@login_required
def delete_account_confirmation(request):
    """View to show account deletion confirmation page"""
    # Get statistics for user confirmation
    sent_messages_count = Message.objects.filter(sender=request.user).count()
    received_messages_count = Message.objects.filter(receiver=request.user).count()
    notifications_count = Notification.objects.filter(user=request.user).count()
    
    context = {
        'sent_messages_count': sent_messages_count,
        'received_messages_count': received_messages_count,
        'notifications_count': notifications_count,
    }
    
    return render(request, 'messaging/delete_account_confirmation.html', context)

@login_required
@transaction.atomic
def delete_user_account(request):
    """View to handle user account deletion"""
    if request.method == 'POST':
        # Verify user's password for security
        password = request.POST.get('password')
        if not request.user.check_password(password):
            django_messages.error(request, 'Incorrect password. Account deletion cancelled.')
            return redirect('delete_account_confirmation')
        
        # Store user info for confirmation message
        username = request.user.username
        email = request.user.email
        
        # Delete the user account
        # This will trigger the post_delete signal for cleanup
        request.user.delete()
        
        # Logout the user
        logout(request)
        
        # Success message
        django_messages.success(
            request, 
            f'Account {username} ({email}) has been permanently deleted along with all associated data.'
        )
        
        return redirect('home')
    
    # If not POST, redirect to confirmation page
    return redirect('delete_account_confirmation')

@login_required
def user_data_summary(request):
    """View to show user what data will be deleted"""
    user = request.user
    
    # Get user's data statistics
    user_data = {
        'sent_messages': Message.objects.filter(sender=user),
        'received_messages': Message.objects.filter(receiver=user),
        'notifications': Notification.objects.filter(user=user),
        'message_edits': MessageHistory.objects.filter(edited_by=user),
    }
    
    context = {
        'sent_messages_count': user_data['sent_messages'].count(),
        'received_messages_count': user_data['received_messages'].count(),
        'notifications_count': user_data['notifications'].count(),
        'message_edits_count': user_data['message_edits'].count(),
        'recent_sent_messages': user_data['sent_messages'].order_by('-timestamp')[:5],
        'recent_received_messages': user_data['received_messages'].order_by('-timestamp')[:5],
    }
    
    return render(request, 'messaging/user_data_summary.html', context)

class AccountDeletionView(View):
    """Class-based view for account deletion process"""
    
    @method_decorator(login_required)
    def get(self, request):
        """Show account deletion options"""
        return render(request, 'messaging/account_deletion.html')
    
    @method_decorator(login_required)
    def post(self, request):
        """Handle account deletion request"""
        action = request.POST.get('action')
        
        if action == 'view_data':
            return redirect('user_data_summary')
        elif action == 'delete_account':
            return redirect('delete_account_confirmation')
        else:
            django_messages.error(request, 'Invalid action.')
            return redirect('account_deletion')

@login_required
def bulk_delete_messages(request):
    """Optional: View to allow users to delete their messages before account deletion"""
    if request.method == 'POST':
        message_type = request.POST.get('message_type')
        
        with transaction.atomic():
            if message_type == 'sent':
                deleted_count, _ = Message.objects.filter(sender=request.user).delete()
                django_messages.success(request, f'Deleted {deleted_count} sent messages.')
            elif message_type == 'received':
                deleted_count, _ = Message.objects.filter(receiver=request.user).delete()
                django_messages.success(request, f'Deleted {deleted_count} received messages.')
            elif message_type == 'all':
                deleted_count, _ = Message.objects.filter(
                    sender=request.user
                ).delete()
                received_count, _ = Message.objects.filter(
                    receiver=request.user
                ).delete()
                django_messages.success(
                    request, 
                    f'Deleted all messages (sent: {deleted_count}, received: {received_count}).'
                )
            else:
                django_messages.error(request, 'Invalid message type.')
        
        return redirect('user_data_summary')
    
    return redirect('user_data_summary')
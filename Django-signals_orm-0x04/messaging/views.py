from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, DetailView
from django.db.models import Q, Count, Prefetch
from django.http import JsonResponse
from .models import Message, Notification, MessageHistory, Conversation

@login_required
def unread_messages(request):
    """View to display only unread messages using the custom manager"""
    # Using the custom unread manager with optimized queries
    unread_messages = Message.unread.for_user(request.user)
    
    # Get unread statistics
    unread_stats = Message.unread_stats.get_user_unread_stats(request.user)
    
    context = {
        'unread_messages': unread_messages,
        'unread_stats': unread_stats,
        'total_unread': unread_stats['total_unread'],
        'active_tab': 'unread',
    }
    return render(request, 'messaging/unread_messages.html', context)

@login_required
def unread_thread_starters(request):
    """View to display unread thread starter messages"""
    unread_threads = Message.unread.unread_thread_starters_for_user(request.user)
    
    context = {
        'unread_threads': unread_threads,
        'total_unread': Message.unread.unread_count_for_user(request.user),
        'active_tab': 'unread_threads',
    }
    return render(request, 'messaging/unread_threads.html', context)

@login_required
def unread_replies(request):
    """View to display unread reply messages"""
    unread_replies = Message.unread.unread_replies_for_user(request.user)
    
    context = {
        'unread_replies': unread_replies,
        'total_unread': Message.unread.unread_count_for_user(request.user),
        'active_tab': 'unread_replies',
    }
    return render(request, 'messaging/unread_replies.html', context)

@login_required
def mark_all_as_read(request):
    """View to mark all unread messages as read"""
    if request.method == 'POST':
        updated_count = Message.unread.mark_as_read(request.user)
        django_messages.success(request, f"Marked {updated_count} messages as read.")
        return redirect('messaging:unread_messages')
    
    return redirect('messaging:unread_messages')

@login_required
def mark_thread_as_read(request, thread_root_id):
    """View to mark all unread messages in a thread as read"""
    thread_root = get_object_or_404(Message, id=thread_root_id)
    
    if request.user not in [thread_root.sender, thread_root.receiver]:
        django_messages.error(request, "You cannot modify this thread.")
        return redirect('messaging:unread_messages')
    
    if request.method == 'POST':
        # Get all message IDs in the thread
        thread_messages = Message.get_thread_messages_optimized(thread_root_id)
        message_ids = [msg.id for msg in thread_messages if not msg.is_read and msg.receiver == request.user]
        
        # Mark them as read using the custom manager
        updated_count = Message.unread.mark_as_read(request.user, message_ids)
        django_messages.success(request, f"Marked {updated_count} messages in thread as read.")
    
    return redirect('messaging:message_thread', message_id=thread_root_id)

@login_required
def unread_message_stats(request):
    """API endpoint to get unread message statistics"""
    stats = Message.unread_stats.get_user_unread_stats(request.user)
    return JsonResponse(stats)

class UnreadMessagesView(ListView):
    """Class-based view for unread messages using custom manager"""
    model = Message
    template_name = 'messaging/unread_messages_cbv.html'
    context_object_name = 'unread_messages'
    paginate_by = 20
    
    def get_queryset(self):
        """Use the custom unread manager"""
        return Message.unread.for_user(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_unread'] = Message.unread.unread_count_for_user(self.request.user)
        context['active_tab'] = 'unread'
        context['unread_stats'] = Message.unread_stats.get_user_unread_stats(self.request.user)
        return context

@login_required
def message_thread(request, message_id):
    """View to display a full message thread - updated to use custom manager"""
    thread_root = get_object_or_404(Message, id=message_id)
    
    # Check if user can view this thread
    if request.user not in [thread_root.sender, thread_root.receiver]:
        django_messages.error(request, "You cannot view this conversation.")
        return redirect('messaging:conversation_list')
    
    # Use recursive CTE for true recursive querying
    thread_tree = Message.get_thread_tree(thread_root.id)
    
    # Convert to Message objects for template using optimized query
    message_ids = [item['id'] for item in thread_tree]
    messages = Message.objects.filter(id__in=message_ids).select_related(
        'sender', 'receiver', 'parent_message'
    ).only(
        'id', 'sender__username', 'receiver__username', 'content',
        'timestamp', 'is_read', 'thread_depth', 'parent_message_id',
        'edited', 'is_thread_starter'
    ).order_by('thread_depth', 'timestamp')
    
    # Mark unread messages as read when viewing thread
    unread_messages = Message.unread.for_user(request.user).filter(id__in=message_ids)
    unread_messages.update(is_read=True, read_at=timezone.now())
    
    # Build hierarchy for template
    thread_hierarchy = thread_root.build_thread_hierarchy(messages)
    
    context = {
        'thread_root': thread_root,
        'thread_tree': thread_tree,
        'thread_hierarchy': thread_hierarchy,
        'messages': messages,
        'participants': thread_root.get_thread_participants(),
    }
    return render(request, 'messaging/message_thread.html', context)

# ... (keep other existing views from previous implementations)
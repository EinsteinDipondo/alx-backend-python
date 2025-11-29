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
def reply_to_message(request, message_id):
    """View to handle replying to a message"""
    parent_message = get_object_or_404(Message, id=message_id)
    
    # Check if user can reply to this message
    if request.user not in [parent_message.sender, parent_message.receiver]:
        django_messages.error(request, "You cannot reply to this message.")
        return redirect('messaging:message_list')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create the reply
            reply = Message.objects.create(
                sender=request.user,
                receiver=parent_message.sender if request.user == parent_message.receiver else parent_message.receiver,
                content=content,
                parent_message=parent_message
            )
            
            # Create notification for the reply
            Notification.objects.create(
                user=reply.receiver,
                message=reply,
                notification_type='reply',
                title=f"New reply from {reply.sender.username}",
                message_content=f"{reply.sender.username} replied to your message: {reply.content[:100]}..."
            )
            
            django_messages.success(request, "Reply sent successfully!")
            return redirect('messaging:message_thread', message_id=parent_message.thread_root.id)
    
    context = {
        'parent_message': parent_message,
    }
    return render(request, 'messaging/reply_to_message.html', context)

@login_required
def message_thread(request, message_id):
    """View to display a full message thread"""
    thread_root = get_object_or_404(Message, id=message_id)
    
    # Check if user can view this thread
    if request.user not in [thread_root.sender, thread_root.receiver]:
        django_messages.error(request, "You cannot view this conversation.")
        return redirect('messaging:message_list')
    
    # Get all messages in the thread with optimized queries
    thread_messages = Message.get_thread_messages(thread_root.id)
    
    # Mark messages as read when viewing thread
    unread_messages = thread_messages.filter(receiver=request.user, is_read=False)
    unread_messages.update(is_read=True)
    
    context = {
        'thread_root': thread_root,
        'thread_messages': thread_messages,
        'participants': thread_root.get_thread_participants(),
    }
    return render(request, 'messaging/message_thread.html', context)

class ConversationListView(ListView):
    """Class-based view to display user's conversations"""
    model = Message
    template_name = 'messaging/conversation_list.html'
    context_object_name = 'conversations'
    paginate_by = 20
    
    def get_queryset(self):
        # Use optimized query to get user's conversations
        return Message.get_user_conversations(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'conversations'
        return context

class ThreadDetailView(DetailView):
    """Class-based view for thread detail with optimized queries"""
    model = Message
    template_name = 'messaging/thread_detail.html'
    context_object_name = 'thread_root'
    
    def get_queryset(self):
        # Optimize queries for thread detail
        return Message.objects.select_related(
            'sender', 'receiver'
        ).prefetch_related(
            Prefetch(
                'replies',
                queryset=Message.objects.select_related('sender', 'receiver').prefetch_related(
                    Prefetch(
                        'replies',
                        queryset=Message.objects.select_related('sender', 'receiver')
                    )
                )
            )
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thread_root = self.object
        
        # Get all messages in thread with optimized query
        thread_messages = Message.get_thread_messages(thread_root.id)
        context['thread_messages'] = thread_messages
        context['participants'] = thread_root.get_thread_participants()
        
        return context

@login_required
def api_thread_messages(request, thread_root_id):
    """API endpoint to get thread messages (for AJAX loading)"""
    thread_root = get_object_or_404(Message, id=thread_root_id)
    
    if request.user not in [thread_root.sender, thread_root.receiver]:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Get thread messages with optimized queries
    thread_messages = Message.get_thread_messages(thread_root.id)
    
    # Format data for JSON response
    messages_data = []
    for msg in thread_messages:
        messages_data.append({
            'id': msg.id,
            'sender': msg.sender.username,
            'receiver': msg.receiver.username,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat(),
            'thread_depth': msg.thread_depth,
            'parent_id': msg.parent_message.id if msg.parent_message else None,
            'is_read': msg.is_read,
            'edited': msg.edited,
        })
    
    return JsonResponse({
        'thread_root': thread_root.id,
        'messages': messages_data
    })

# ... (keep existing account deletion views from previous implementation)
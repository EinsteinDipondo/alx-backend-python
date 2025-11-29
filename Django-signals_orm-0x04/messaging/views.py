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
    """View to display a full message thread using recursive query"""
    thread_root = get_object_or_404(Message, id=message_id)
    
    # Check if user can view this thread
    if request.user not in [thread_root.sender, thread_root.receiver]:
        django_messages.error(request, "You cannot view this conversation.")
        return redirect('messaging:conversation_list')
    
    # Method 1: Use recursive CTE for true recursive querying
    thread_tree = Message.get_thread_tree(thread_root.id)
    
    # Convert to Message objects for template
    message_ids = [item['id'] for item in thread_tree]
    messages = Message.objects.filter(id__in=message_ids).select_related(
        'sender', 'receiver', 'parent_message'
    ).order_by('thread_depth', 'timestamp')
    
    # Build hierarchy for template
    thread_hierarchy = thread_root.build_thread_hierarchy(messages)
    
    # Mark messages as read when viewing thread
    unread_messages = messages.filter(receiver=request.user, is_read=False)
    unread_messages.update(is_read=True)
    
    context = {
        'thread_root': thread_root,
        'thread_tree': thread_tree,
        'thread_hierarchy': thread_hierarchy,
        'messages': messages,
        'participants': thread_root.get_thread_participants(),
    }
    return render(request, 'messaging/message_thread.html', context)

@login_required
def message_thread_optimized(request, message_id):
    """Alternative view using optimized ORM queries (non-recursive but efficient)"""
    thread_root = get_object_or_404(Message, id=message_id)
    
    # Check if user can view this thread
    if request.user not in [thread_root.sender, thread_root.receiver]:
        django_messages.error(request, "You cannot view this conversation.")
        return redirect('messaging:conversation_list')
    
    # Use optimized ORM query (good for threads up to 10 levels deep)
    messages = Message.get_thread_messages_optimized(thread_root.id)
    
    # Build hierarchy
    thread_hierarchy = thread_root.build_thread_hierarchy(messages)
    
    # Mark messages as read
    unread_messages = messages.filter(receiver=request.user, is_read=False)
    unread_messages.update(is_read=True)
    
    context = {
        'thread_root': thread_root,
        'messages': messages,
        'thread_hierarchy': thread_hierarchy,
        'participants': thread_root.get_thread_participants(),
    }
    return render(request, 'messaging/message_thread_optimized.html', context)

class ConversationListView(ListView):
    """Class-based view to display user's conversations"""
    model = Message
    template_name = 'messaging/conversation_list.html'
    context_object_name = 'conversations'
    paginate_by = 20
    
    def get_queryset(self):
        # Get all thread starters where user is sender or receiver
        return Message.objects.filter(
            is_thread_starter=True
        ).filter(
            Q(sender=self.request.user) | Q(receiver=self.request.user)
        ).select_related('sender', 'receiver').prefetch_related('replies').annotate(
            reply_count=Count('replies')
        ).order_by('-timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'conversations'
        return context

@login_required
def api_thread_tree(request, thread_root_id):
    """API endpoint to get thread tree using recursive query"""
    thread_root = get_object_or_404(Message, id=thread_root_id)
    
    if request.user not in [thread_root.sender, thread_root.receiver]:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Use recursive CTE to get complete thread tree
    thread_tree = Message.get_thread_tree(thread_root.id)
    
    # Get full message objects for the tree
    message_ids = [item['id'] for item in thread_tree]
    messages = Message.objects.filter(id__in=message_ids).select_related(
        'sender', 'receiver', 'parent_message'
    ).in_bulk()
    
    # Build hierarchical response
    def build_tree(node_id):
        node_data = thread_tree[[i for i, item in enumerate(thread_tree) if item['id'] == node_id][0]]
        message_obj = messages.get(node_id)
        
        children = [item for item in thread_tree if item.get('parent_message_id') == node_id]
        
        return {
            'id': node_id,
            'sender': message_obj.sender.username if message_obj else 'Unknown',
            'receiver': message_obj.receiver.username if message_obj else 'Unknown',
            'content': message_obj.content if message_obj else '',
            'timestamp': message_obj.timestamp.isoformat() if message_obj else '',
            'thread_depth': node_data['thread_depth'],
            'is_read': message_obj.is_read if message_obj else True,
            'edited': message_obj.edited if message_obj else False,
            'replies': [build_tree(child['id']) for child in children]
        }
    
    # Find root (message with no parent)
    root_nodes = [item for item in thread_tree if item.get('parent_message_id') is None]
    if root_nodes:
        tree_data = build_tree(root_nodes[0]['id'])
    else:
        tree_data = {}
    
    return JsonResponse({
        'thread_root': thread_root.id,
        'tree': tree_data
    })

@login_required
def recursive_thread_view(request, message_id):
    """View that demonstrates recursive template rendering"""
    thread_root = get_object_or_404(Message, id=message_id)
    
    # Check if user can view this thread
    if request.user not in [thread_root.sender, thread_root.receiver]:
        django_messages.error(request, "You cannot view this conversation.")
        return redirect('messaging:conversation_list')
    
    # Get flat list of messages in thread
    messages = Message.get_thread_messages_optimized(thread_root.id)
    
    # Build a dictionary for efficient parent-child lookups
    message_dict = {}
    for message in messages:
        message_dict[message.id] = message
    
    # Build parent-child relationships
    thread_structure = []
    for message in messages:
        if message.parent_message is None:
            thread_structure.append(message)
        else:
            # This will be handled in template recursively
            pass
    
    context = {
        'thread_root': thread_root,
        'messages': messages,
        'message_dict': message_dict,
        'thread_structure': thread_structure,
        'participants': thread_root.get_thread_participants(),
    }
    return render(request, 'messaging/recursive_thread.html', context)

# ... (keep existing account deletion views from previous implementation)
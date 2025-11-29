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
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django.core.cache import cache
from .models import Message, Notification, MessageHistory, Conversation

# Cache the conversation list view for 60 seconds
@login_required
@cache_page(60 * 1)  # 60 seconds cache
@vary_on_cookie  # Vary cache based on user cookie (different cache per user)
def conversation_list(request):
    """View to display user's conversations with caching"""
    print(f"Cache MISS - Loading conversations for user: {request.user.username}")
    
    conversations = Conversation.objects.get_user_conversations_optimized(request.user)
    
    # Get unread counts for each conversation
    for conversation in conversations:
        conversation.unread_count = Message.unread.unread_for_user(request.user).filter(
            parent_message=conversation
        ).count()
    
    context = {
        'conversations': conversations,
        'total_unread': Message.unread.unread_count_for_user(request.user),
        'active_tab': 'conversations',
        'cache_timestamp': timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return render(request, 'messaging/conversation_list.html', context)

# Cache the message thread view for 60 seconds
@login_required
@cache_page(60 * 1)  # 60 seconds cache
@vary_on_cookie  # Vary cache based on user cookie
def message_thread(request, message_id):
    """View to display a full message thread with caching"""
    print(f"Cache MISS - Loading thread {message_id} for user: {request.user.username}")
    
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
    
    # Build hierarchy for template
    thread_hierarchy = thread_root.build_thread_hierarchy(messages)
    
    context = {
        'thread_root': thread_root,
        'thread_tree': thread_tree,
        'thread_hierarchy': thread_hierarchy,
        'messages': messages,
        'participants': thread_root.get_thread_participants(),
        'cache_timestamp': timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return render(request, 'messaging/message_thread.html', context)

# Cache the unread messages view for 60 seconds
@login_required
@cache_page(60 * 1)  # 60 seconds cache
@vary_on_cookie  # Vary cache based on user cookie
def unread_messages(request):
    """View to display only unread messages using the custom manager with caching"""
    print(f"Cache MISS - Loading unread messages for user: {request.user.username}")
    
    # Using the custom unread manager with optimized queries
    unread_messages = Message.unread.unread_for_user(request.user)
    
    # Get unread statistics
    unread_stats = Message.unread_stats.get_user_unread_stats(request.user)
    
    context = {
        'unread_messages': unread_messages,
        'unread_stats': unread_stats,
        'total_unread': unread_stats['total_unread'],
        'active_tab': 'unread',
        'cache_timestamp': timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return render(request, 'messaging/unread_messages.html', context)

# Class-based view with caching using method_decorator
@method_decorator(cache_page(60 * 1), name='dispatch')
@method_decorator(vary_on_cookie, name='dispatch')
class CachedConversationListView(ListView):
    """Class-based view to display user's conversations with caching"""
    model = Message
    template_name = 'messaging/conversation_list_cached.html'
    context_object_name = 'conversations'
    paginate_by = 20
    
    def get_queryset(self):
        print(f"Cache MISS - Loading conversations for user: {self.request.user.username}")
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
        context['cache_timestamp'] = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        return context

# Manual cache implementation for more control
@login_required
def user_inbox(request):
    """View to display user's inbox with manual caching"""
    cache_key = f"user_inbox_{request.user.id}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        print(f"Cache HIT - Loading inbox from cache for user: {request.user.username}")
        context = cached_data
        context['cache_source'] = 'cache'
    else:
        print(f"Cache MISS - Loading inbox from database for user: {request.user.username}")
        # Get all messages for the user
        all_messages = Message.objects.get_user_inbox(request.user)
        
        # Get unread messages separately for highlighting
        unread_messages = Message.unread.unread_for_user(request.user)
        unread_message_ids = set(unread_messages.values_list('id', flat=True))
        
        context = {
            'all_messages': all_messages,
            'unread_message_ids': unread_message_ids,
            'unread_count': Message.unread.unread_count_for_user(request.user),
            'active_tab': 'inbox',
            'cache_timestamp': timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            'cache_source': 'database',
        }
        
        # Cache for 60 seconds
        cache.set(cache_key, context, 60)
    
    return render(request, 'messaging/user_inbox.html', context)

# API view with caching
@login_required
@cache_page(60 * 1)
@vary_on_cookie
def api_thread_tree(request, thread_root_id):
    """API endpoint to get thread tree using recursive query with caching"""
    print(f"Cache MISS - API thread tree for thread {thread_root_id}, user: {request.user.username}")
    
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
    
    response_data = {
        'thread_root': thread_root.id,
        'tree': tree_data,
        'cache_timestamp': timezone.now().isoformat(),
    }
    
    return JsonResponse(response_data)

# Utility view to clear cache
@login_required
def clear_cache(request):
    """View to clear cache for the current user"""
    if request.method == 'POST':
        # Clear specific cache keys for this user
        cache_keys_to_clear = [
            f"user_inbox_{request.user.id}",
        ]
        
        for key in cache_keys_to_clear:
            cache.delete(key)
        
        django_messages.success(request, "Your cache has been cleared.")
        return redirect('messaging:user_inbox')
    
    return render(request, 'messaging/clear_cache.html')

# Non-cached view for comparison
@login_required
def conversation_list_uncached(request):
    """Uncached version of conversation list for comparison"""
    print(f"UNCACHED - Loading conversations for user: {request.user.username}")
    
    conversations = Conversation.objects.get_user_conversations_optimized(request.user)
    
    # Get unread counts for each conversation
    for conversation in conversations:
        conversation.unread_count = Message.unread.unread_for_user(request.user).filter(
            parent_message=conversation
        ).count()
    
    context = {
        'conversations': conversations,
        'total_unread': Message.unread.unread_count_for_user(request.user),
        'active_tab': 'conversations',
        'cache_timestamp': timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        'cache_status': 'uncached',
    }
    return render(request, 'messaging/conversation_list.html', context)

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

# ... (keep other existing views from previous implementations)
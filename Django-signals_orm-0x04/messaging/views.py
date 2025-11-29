from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Message, MessageHistory

@login_required
def message_detail(request, message_id):
    """View to display message details and edit history"""
    message = get_object_or_404(Message, id=message_id)
    
    # Check if user has permission to view this message
    if request.user not in [message.sender, message.receiver]:
        return render(request, 'errors/403.html', status=403)
    
    # Get edit history
    edit_history = message.history.all().order_by('-edited_at')
    
    context = {
        'message': message,
        'edit_history': edit_history,
    }
    
    return render(request, 'messaging/message_detail.html', context)

@login_required
def message_edit_history(request, message_id):
    """View to display only the edit history of a message"""
    message = get_object_or_404(Message, id=message_id)
    
    # Check if user has permission to view this message's history
    if request.user not in [message.sender, message.receiver]:
        return render(request, 'errors/403.html', status=403)
    
    edit_history = message.history.all().order_by('-edited_at')
    
    context = {
        'message': message,
        'edit_history': edit_history,
    }
    
    return render(request, 'messaging/message_edit_history.html', context)
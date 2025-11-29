from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Unread messages URLs
    path('unread/', views.unread_messages, name='unread_messages'),
    path('unread/cbv/', views.UnreadMessagesView.as_view(), name='unread_messages_cbv'),
    path('unread/threads/', views.unread_thread_starters, name='unread_threads'),
    path('unread/replies/', views.unread_replies, name='unread_replies'),
    path('unread/mark-all-read/', views.mark_all_as_read, name='mark_all_read'),
    path('thread/<int:thread_root_id>/mark-read/', views.mark_thread_as_read, name='mark_thread_read'),
    path('api/unread/stats/', views.unread_message_stats, name='unread_stats'),
    
    # Threading URLs
    path('conversations/', views.ConversationListView.as_view(), name='conversation_list'),
    path('thread/<int:message_id>/', views.message_thread, name='message_thread'),
    path('thread/<int:message_id>/optimized/', views.message_thread_optimized, name='message_thread_optimized'),
    path('thread/<int:message_id>/recursive/', views.recursive_thread_view, name='recursive_thread'),
    path('message/<int:message_id>/reply/', views.reply_to_message, name='reply_to_message'),
    path('api/thread/<int:thread_root_id>/tree/', views.api_thread_tree, name='api_thread_tree'),
    
    # Account deletion URLs
    path('account/delete/', views.AccountDeletionView.as_view(), name='account_deletion'),
    path('account/delete/confirmation/', views.delete_account_confirmation, name='delete_account_confirmation'),
    path('account/delete/confirm/', views.delete_user_account, name='delete_user_account'),
    path('account/data/', views.user_data_summary, name='user_data_summary'),
    path('account/delete/messages/', views.bulk_delete_messages, name='bulk_delete_messages'),
]
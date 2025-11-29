from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Threading URLs
    path('conversations/', views.ConversationListView.as_view(), name='conversation_list'),
    path('thread/<int:message_id>/', views.message_thread, name='message_thread'),
    path('thread/<int:pk>/detail/', views.ThreadDetailView.as_view(), name='thread_detail'),
    path('message/<int:message_id>/reply/', views.reply_to_message, name='reply_to_message'),
    path('api/thread/<int:thread_root_id>/messages/', views.api_thread_messages, name='api_thread_messages'),
    
    # Account deletion URLs (from previous implementation)
    path('account/delete/', views.AccountDeletionView.as_view(), name='account_deletion'),
    path('account/delete/confirmation/', views.delete_account_confirmation, name='delete_account_confirmation'),
    path('account/delete/confirm/', views.delete_user_account, name='delete_user_account'),
    path('account/data/', views.user_data_summary, name='user_data_summary'),
    path('account/delete/messages/', views.bulk_delete_messages, name='bulk_delete_messages'),
]
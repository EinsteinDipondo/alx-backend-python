from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Account deletion URLs
    path('account/delete/', views.AccountDeletionView.as_view(), name='account_deletion'),
    path('account/delete/confirmation/', views.delete_account_confirmation, name='delete_account_confirmation'),
    path('account/delete/confirm/', views.delete_user_account, name='delete_user_account'),
    path('account/data/', views.user_data_summary, name='user_data_summary'),
    path('account/delete/messages/', views.bulk_delete_messages, name='bulk_delete_messages'),
    
    # Existing messaging URLs (if any)
    # path('messages/', views.message_list, name='message_list'),
    # path('messages/<int:message_id>/', views.message_detail, name='message_detail'),
]
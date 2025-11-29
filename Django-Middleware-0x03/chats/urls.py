from django.urls import path
from . import views

urlpatterns = [
    # Existing endpoints
    path('conversations/', views.conversation_list, name='conversation-list'),
    path('messages/', views.message_list, name='message-list'),
    path('test/', views.test_view, name='test-view'),
    
    # Role-based endpoints for testing middleware
    path('admin/', views.admin_dashboard, name='admin-dashboard'),
    path('moderator/', views.moderator_panel, name='moderator-panel'),
    path('users/', views.user_management, name='user-management'),
    path('reports/', views.report_management, name='report-management'),
    path('messages/bulk_delete/', views.bulk_delete_messages, name='bulk-delete-messages'),
]
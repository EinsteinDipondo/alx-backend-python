from django.urls import path
from . import views

urlpatterns = [
    path('conversations/', views.conversation_list, name='conversation-list'),
    path('messages/', views.message_list, name='message-list'),
    path('test/', views.test_view, name='test-view'),
]
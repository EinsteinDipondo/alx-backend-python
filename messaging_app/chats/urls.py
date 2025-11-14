from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'conversations', views.ConversationViewSet, basename='conversation')
router.register(r'messages', views.MessageViewSet, basename='message')
router.register(r'users', views.UserViewSet, basename='user')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]

# NestedDefaultRouter would be used like this if we had drf-nested-routers installed:
# from rest_framework_nested import routers
# router = routers.DefaultRouter()
# router.register(r'conversations', views.ConversationViewSet, basename='conversation')
# conversations_router = routers.NestedDefaultRouter(router, r'conversations', lookup='conversation')
# conversations_router.register(r'messages', views.MessageViewSet, basename='conversation-messages')
from django.contrib import admin
from .models import Message, Notification

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'timestamp', 'is_read']
    list_filter = ['timestamp', 'is_read']
    search_fields = ['sender__username', 'receiver__username', 'content']
    readonly_fields = ['timestamp']
    
    fieldsets = (
        ('Message Information', {
            'fields': ('sender', 'receiver', 'content', 'timestamp', 'is_read')
        }),
    )

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message_content']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Notification Information', {
            'fields': ('user', 'message', 'notification_type', 'title', 'message_content')
        }),
        ('Status', {
            'fields': ('is_read', 'created_at')
        }),
    )
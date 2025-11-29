from django.contrib import admin
from django.utils.html import format_html
from .models import Message, Notification, MessageHistory

class MessageHistoryInline(admin.TabularInline):
    model = MessageHistory
    extra = 0
    readonly_fields = ['edited_by', 'edited_at', 'old_content', 'edit_reason']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        'sender', 
        'receiver', 
        'content_preview', 
        'timestamp', 
        'is_read', 
        'edited',
        'edit_count',
        'last_edited'
    ]
    list_filter = ['timestamp', 'is_read', 'edited', 'last_edited']
    search_fields = ['sender__username', 'receiver__username', 'content']
    readonly_fields = ['timestamp', 'last_edited', 'edit_count']
    inlines = [MessageHistoryInline]
    
    fieldsets = (
        ('Message Information', {
            'fields': ('sender', 'receiver', 'content', 'timestamp', 'is_read')
        }),
        ('Edit Information', {
            'fields': ('edited', 'last_edited', 'edit_count'),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

@admin.register(MessageHistory)
class MessageHistoryAdmin(admin.ModelAdmin):
    list_display = ['message', 'edited_by', 'edited_at', 'old_content_preview', 'edit_reason']
    list_filter = ['edited_at', 'edited_by']
    search_fields = ['message__content', 'old_content', 'edited_by__username']
    readonly_fields = ['message', 'old_content', 'edited_by', 'edited_at']
    
    def old_content_preview(self, obj):
        return obj.old_content[:50] + "..." if len(obj.old_content) > 50 else obj.old_content
    old_content_preview.short_description = 'Old Content'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

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
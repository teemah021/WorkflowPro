"""
Admin configuration for AuditLog model.
"""
from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for audit logs (read-only)"""
    
    list_display = [
        'timestamp',
        'actor',
        'action',
        'content_type',
        'object_id',
        'ip_address'
    ]
    
    list_filter = ['action', 'timestamp', 'content_type']
    search_fields = ['actor__username', 'object_id', 'ip_address']
    
    readonly_fields = [
        'id',
        'actor',
        'action',
        'content_type',
        'object_id',
        'metadata',
        'ip_address',
        'user_agent',
        'timestamp'
    ]
    
    fieldsets = (
        ('Action Details', {
            'fields': ('id', 'actor', 'action', 'timestamp')
        }),
        ('Target Object', {
            'fields': ('content_type', 'object_id')
        }),
        ('Request Information', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent manual creation"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent editing"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion"""
        return False

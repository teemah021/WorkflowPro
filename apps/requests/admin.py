"""
Admin configuration for Request model.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Request


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    """Admin interface for Request model"""
    
    list_display = [
        'title',
        'status_badge',
        'creator',
        'assigned_to',
        'reviewed_by',
        'created_at',
        'is_deleted'
    ]
    
    list_filter = ['status', 'is_deleted', 'created_at', 'reviewed_at']
    search_fields = ['title', 'description', 'creator__username']
    
    readonly_fields = [
        'id',
        'creator',
        'reviewed_by',
        'reviewed_at',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'title', 'description', 'status')
        }),
        ('Assignment', {
            'fields': ('creator', 'assigned_to', 'reviewed_by', 'reviewed_at')
        }),
        ('Rejection Details', {
            'fields': ('rejection_reason',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('is_deleted', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Display colored status badge"""
        colors = {
            'draft': '#6c757d',
            'submitted': '#007bff',
            'approved': '#28a745',
            'rejected': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def has_delete_permission(self, request, obj=None):
        """Prevent hard delete from admin"""
        return False

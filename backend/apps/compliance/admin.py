"""Admin configuration for compliance app."""

from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'actor', 'action', 'resource_type', 'resource_id']
    list_filter = ['action', 'resource_type']
    search_fields = ['actor__email', 'resource_id']
    readonly_fields = [
        'actor', 'actor_ip', 'action', 'resource_type',
        'resource_id', 'changes', 'metadata', 'timestamp',
    ]
    ordering = ['-timestamp']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

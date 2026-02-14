"""Admin configuration for communications app."""

from django.contrib import admin

from .models import EmailLog, EmailTemplate, Notification


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    """Admin for email templates."""

    list_display = ['name', 'category', 'department', 'is_active', 'version', 'created_at']
    list_filter = ['category', 'is_active', 'department']
    search_fields = ['name', 'subject', 'body_text']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'category', 'department', 'is_active', 'version'),
        }),
        ('Email Content', {
            'fields': ('subject', 'body_html', 'body_text'),
        }),
        ('Variables', {
            'fields': ('variables',),
            'description': 'Available merge fields for this template (JSON format)',
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
        }),
    )


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    """Admin for email logs."""

    list_display = [
        'recipient',
        'subject',
        'status',
        'sent_at',
        'opened_at',
        'template',
        'application',
        'created_at',
    ]
    list_filter = ['status', 'sent_at', 'created_at']
    search_fields = ['recipient', 'sender', 'subject', 'message_id']
    readonly_fields = ['created_at', 'updated_at', 'sent_at', 'opened_at']
    autocomplete_fields = ['template', 'application']

    fieldsets = (
        ('Email Info', {
            'fields': ('sender', 'recipient', 'subject'),
        }),
        ('Content', {
            'fields': ('body_html', 'body_text'),
        }),
        ('Status', {
            'fields': ('status', 'sent_at', 'opened_at'),
        }),
        ('Related Objects', {
            'fields': ('template', 'application'),
        }),
        ('Delivery Info', {
            'fields': ('message_id', 'error_message', 'metadata'),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin for notifications."""

    list_display = [
        'recipient',
        'type',
        'title',
        'is_read',
        'read_at',
        'created_at',
    ]
    list_filter = ['type', 'is_read', 'created_at']
    search_fields = ['title', 'body', 'recipient__email', 'recipient__first_name', 'recipient__last_name']
    readonly_fields = ['created_at', 'updated_at', 'read_at']
    autocomplete_fields = ['recipient']

    fieldsets = (
        ('Basic Info', {
            'fields': ('recipient', 'type', 'title', 'body'),
        }),
        ('Link', {
            'fields': ('link',),
        }),
        ('Read Status', {
            'fields': ('is_read', 'read_at'),
        }),
        ('Additional Data', {
            'fields': ('metadata',),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

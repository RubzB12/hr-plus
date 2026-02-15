"""Django admin for integrations app."""

import json

from django.contrib import admin
from django.utils.html import format_html

from .models import Integration, JobBoardPosting, WebhookDelivery, WebhookEndpoint


@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    """Admin for Integration model."""

    list_display = [
        'name',
        'provider_badge',
        'category_badge',
        'is_active',
        'sync_status_badge',
        'last_sync',
        'failure_count',
        'created_at',
    ]
    list_filter = ['provider', 'category', 'is_active', 'sync_status', 'created_at']
    search_fields = ['name', 'provider']
    readonly_fields = [
        'id',
        'config_display',
        'last_sync',
        'sync_status',
        'error_log',
        'failure_count',
        'is_oauth_configured',
        'needs_token_refresh',
        'is_circuit_broken',
        'created_at',
        'updated_at',
    ]
    fieldsets = (
        (
            None,
            {
                'fields': (
                    'id',
                    'provider',
                    'category',
                    'name',
                    'is_active',
                )
            },
        ),
        (
            'Configuration',
            {
                'fields': ('config', 'config_display', 'metadata'),
                'description': 'Configuration is encrypted in database. Config display shows keys only.',
            },
        ),
        (
            'OAuth',
            {
                'fields': (
                    'oauth_token',
                    'oauth_refresh_token',
                    'oauth_expires_at',
                    'is_oauth_configured',
                    'needs_token_refresh',
                ),
                'classes': ('collapse',),
            },
        ),
        (
            'Sync Status',
            {
                'fields': (
                    'last_sync',
                    'sync_status',
                    'error_log',
                    'failure_count',
                    'is_circuit_broken',
                )
            },
        ),
        ('Metadata', {'fields': ('created_at', 'updated_at')}),
    )

    def provider_badge(self, obj):
        """Display provider with icon/badge."""
        colors = {
            'indeed': '#2164f3',
            'linkedin': '#0077b5',
            'glassdoor': '#0caa41',
            'bamboo_hr': '#73c41d',
            'workday': '#eb7125',
            'adp': '#d4111e',
        }
        color = colors.get(obj.provider, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_provider_display(),
        )

    provider_badge.short_description = 'Provider'

    def category_badge(self, obj):
        """Display category with badge."""
        colors = {
            'job_board': 'blue',
            'hris': 'green',
            'ats': 'purple',
            'custom': 'gray',
        }
        color = colors.get(obj.category, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_category_display(),
        )

    category_badge.short_description = 'Category'

    def sync_status_badge(self, obj):
        """Display sync status with color badge."""
        colors = {
            'idle': 'gray',
            'syncing': 'blue',
            'success': 'green',
            'error': 'red',
        }
        color = colors.get(obj.sync_status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_sync_status_display(),
        )

    sync_status_badge.short_description = 'Status'

    def config_display(self, obj):
        """Display config keys only (not sensitive values)."""
        try:
            config = json.loads(obj.config) if obj.config else {}
            keys = list(config.keys())
            return format_html(
                '<div style="background: #f5f5f5; padding: 10px; border-radius: 3px;">'
                '<strong>Config keys:</strong> {}'
                '</div>',
                ', '.join(keys) if keys else 'No config',
            )
        except (json.JSONDecodeError, TypeError):
            return 'Invalid config'

    config_display.short_description = 'Configuration (keys only)'


class WebhookDeliveryInline(admin.TabularInline):
    """Inline for webhook deliveries."""

    model = WebhookDelivery
    extra = 0
    max_num = 10
    readonly_fields = [
        'event_type',
        'delivered_at',
        'response_status',
        'attempts',
        'created_at',
    ]
    fields = ['event_type', 'delivered_at', 'response_status', 'attempts', 'created_at']
    ordering = ['-created_at']

    def has_add_permission(self, request, obj=None):
        """Disable adding deliveries manually."""
        return False


@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(admin.ModelAdmin):
    """Admin for WebhookEndpoint model."""

    list_display = [
        'url_display',
        'integration_display',
        'event_count',
        'is_active',
        'failure_count',
        'last_success',
        'last_failure',
    ]
    list_filter = ['is_active', 'integration', 'created_at']
    search_fields = ['url']
    readonly_fields = [
        'id',
        'failure_count',
        'last_success',
        'last_failure',
        'should_disable',
        'created_at',
        'updated_at',
    ]
    fieldsets = (
        (
            None,
            {
                'fields': (
                    'id',
                    'integration',
                    'url',
                    'events',
                    'is_active',
                    'headers',
                )
            },
        ),
        (
            'Security',
            {
                'fields': ('secret',),
                'description': 'Secret is encrypted in database. Used for HMAC signing.',
            },
        ),
        (
            'Delivery Status',
            {
                'fields': (
                    'failure_count',
                    'should_disable',
                    'last_success',
                    'last_failure',
                )
            },
        ),
        ('Metadata', {'fields': ('created_at', 'updated_at')}),
    )
    inlines = [WebhookDeliveryInline]

    def url_display(self, obj):
        """Display URL truncated."""
        url = obj.url
        if len(url) > 50:
            return url[:47] + '...'
        return url

    url_display.short_description = 'URL'

    def integration_display(self, obj):
        """Display integration name."""
        if obj.integration:
            return obj.integration.name
        return '-'

    integration_display.short_description = 'Integration'

    def event_count(self, obj):
        """Display number of subscribed events."""
        return len(obj.events) if obj.events else 0

    event_count.short_description = 'Events'


@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    """Admin for WebhookDelivery model (read-only)."""

    list_display = [
        'event_type',
        'endpoint_url_display',
        'status_badge',
        'response_status',
        'attempts',
        'created_at',
    ]
    list_filter = ['event_type', 'delivered_at', 'response_status', 'created_at']
    search_fields = ['endpoint__url', 'event_type']
    readonly_fields = [
        'id',
        'endpoint',
        'event_type',
        'payload_display',
        'response_status',
        'response_body',
        'delivered_at',
        'is_delivered',
        'is_success',
        'attempts',
        'error_message',
        'created_at',
        'updated_at',
    ]
    fieldsets = (
        (
            None,
            {'fields': ('id', 'endpoint', 'event_type', 'payload_display', 'attempts')},
        ),
        (
            'Response',
            {
                'fields': (
                    'response_status',
                    'response_body',
                    'delivered_at',
                    'is_delivered',
                    'is_success',
                    'error_message',
                )
            },
        ),
        ('Metadata', {'fields': ('created_at', 'updated_at')}),
    )

    def has_add_permission(self, request):
        """Disable adding deliveries manually."""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable editing deliveries."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion for cleanup."""
        return True

    def endpoint_url_display(self, obj):
        """Display endpoint URL truncated."""
        url = obj.endpoint.url
        if len(url) > 40:
            return url[:37] + '...'
        return url

    endpoint_url_display.short_description = 'Endpoint'

    def status_badge(self, obj):
        """Display delivery status with color badge."""
        if obj.is_success:
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 10px; border-radius: 3px;">Success</span>'
            )
        elif obj.delivered_at:
            return format_html(
                '<span style="background-color: orange; color: white; padding: 3px 10px; border-radius: 3px;">Delivered ({})</span>',
                obj.response_status,
            )
        else:
            return format_html(
                '<span style="background-color: red; color: white; padding: 3px 10px; border-radius: 3px;">Failed</span>'
            )

    status_badge.short_description = 'Status'

    def payload_display(self, obj):
        """Display payload in formatted JSON."""
        try:
            payload_json = json.dumps(obj.payload, indent=2)
            return format_html('<pre>{}</pre>', payload_json)
        except (TypeError, ValueError):
            return obj.payload

    payload_display.short_description = 'Payload'


@admin.register(JobBoardPosting)
class JobBoardPostingAdmin(admin.ModelAdmin):
    """Admin for JobBoardPosting model."""

    list_display = [
        'requisition_title_display',
        'integration_display',
        'status_badge',
        'external_id_display',
        'posted_at',
        'last_synced',
        'view_url',
    ]
    list_filter = ['status', 'integration', 'posted_at']
    search_fields = ['requisition__title', 'external_id']
    readonly_fields = [
        'id',
        'external_id',
        'posted_at',
        'last_synced',
        'status',
        'url',
        'metadata_display',
        'is_active',
        'created_at',
        'updated_at',
    ]
    fieldsets = (
        (
            None,
            {
                'fields': (
                    'id',
                    'requisition',
                    'integration',
                    'status',
                    'is_active',
                )
            },
        ),
        (
            'External Board',
            {
                'fields': (
                    'external_id',
                    'url',
                    'posted_at',
                    'last_synced',
                    'metadata_display',
                )
            },
        ),
        ('Metadata', {'fields': ('created_at', 'updated_at')}),
    )

    def has_add_permission(self, request):
        """Disable manual creation (use API)."""
        return False

    def requisition_title_display(self, obj):
        """Display requisition title."""
        return obj.requisition.title

    requisition_title_display.short_description = 'Job'
    requisition_title_display.admin_order_field = 'requisition__title'

    def integration_display(self, obj):
        """Display integration provider."""
        return obj.integration.get_provider_display()

    integration_display.short_description = 'Board'

    def external_id_display(self, obj):
        """Display external ID truncated."""
        if not obj.external_id:
            return '-'
        external_id = obj.external_id
        if len(external_id) > 30:
            return external_id[:27] + '...'
        return external_id

    external_id_display.short_description = 'External ID'

    def status_badge(self, obj):
        """Display status with color badge."""
        colors = {
            'draft': 'gray',
            'posted': 'green',
            'closed': 'red',
            'error': 'orange',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = 'Status'

    def view_url(self, obj):
        """Display link to external posting."""
        if obj.url:
            return format_html(
                '<a href="{}" target="_blank" rel="noopener noreferrer">View Posting →</a>',
                obj.url,
            )
        return '-'

    view_url.short_description = 'External URL'

    def metadata_display(self, obj):
        """Display metadata in formatted JSON."""
        try:
            metadata_json = json.dumps(obj.metadata, indent=2)
            return format_html('<pre>{}</pre>', metadata_json)
        except (TypeError, ValueError):
            return obj.metadata

    metadata_display.short_description = 'Metadata'

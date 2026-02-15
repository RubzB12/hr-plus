"""Serializers for integrations app."""

import json

from rest_framework import serializers

from .models import Integration, JobBoardPosting, WebhookDelivery, WebhookEndpoint


class IntegrationSerializer(serializers.ModelSerializer):
    """Serializer for Integration model with sensitive field masking."""

    provider_display = serializers.CharField(source='get_provider_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    sync_status_display = serializers.CharField(source='get_sync_status_display', read_only=True)

    # Sensitive fields - write only
    config = serializers.JSONField(write_only=True, required=True)
    oauth_token = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    oauth_refresh_token = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)

    # Masked config for read responses
    config_keys = serializers.SerializerMethodField()
    has_oauth = serializers.BooleanField(source='is_oauth_configured', read_only=True)
    needs_token_refresh = serializers.BooleanField(read_only=True)
    is_circuit_broken = serializers.BooleanField(read_only=True)

    class Meta:
        model = Integration
        fields = [
            'id',
            'provider',
            'provider_display',
            'category',
            'category_display',
            'name',
            'is_active',
            'config',  # Write only
            'config_keys',  # Read only - only shows keys, not values
            'oauth_token',  # Write only
            'oauth_refresh_token',  # Write only
            'oauth_expires_at',
            'has_oauth',
            'needs_token_refresh',
            'last_sync',
            'sync_status',
            'sync_status_display',
            'error_log',
            'failure_count',
            'is_circuit_broken',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'last_sync',
            'sync_status',
            'error_log',
            'failure_count',
            'created_at',
            'updated_at',
        ]

    def get_config_keys(self, obj):
        """Return only config keys, not sensitive values."""
        try:
            config = json.loads(obj.config) if obj.config else {}
            return list(config.keys())
        except (json.JSONDecodeError, TypeError):
            return []

    def validate_config(self, value):
        """Validate config is a valid dict."""
        if not isinstance(value, dict):
            raise serializers.ValidationError('Config must be a dictionary')
        return value


class IntegrationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating integrations with provider-specific validation."""

    config = serializers.JSONField(required=True)

    class Meta:
        model = Integration
        fields = [
            'provider',
            'category',
            'name',
            'is_active',
            'config',
            'oauth_token',
            'oauth_refresh_token',
            'oauth_expires_at',
            'metadata',
        ]

    def validate(self, data):
        """Validate config structure based on provider."""
        provider = data.get('provider')
        config = data.get('config', {})

        if not isinstance(config, dict):
            raise serializers.ValidationError({'config': 'Config must be a dictionary'})

        # Provider-specific validation
        if provider == 'indeed':
            required = ['employer_id', 'api_key']
            for field in required:
                if field not in config:
                    raise serializers.ValidationError(
                        {'config': f'Indeed integration requires "{field}" in config'}
                    )

        elif provider == 'linkedin':
            # LinkedIn uses OAuth, config may have client_id/secret
            if not data.get('oauth_token'):
                raise serializers.ValidationError(
                    {'oauth_token': 'LinkedIn integration requires OAuth token'}
                )

        elif provider == 'bamboo_hr':
            required = ['subdomain', 'api_key']
            for field in required:
                if field not in config:
                    raise serializers.ValidationError(
                        {'config': f'BambooHR integration requires "{field}" in config'}
                    )

        elif provider == 'workday':
            required = ['tenant_url', 'username', 'password']
            for field in required:
                if field not in config:
                    raise serializers.ValidationError(
                        {'config': f'Workday integration requires "{field}" in config'}
                    )

        elif provider == 'adp':
            required = ['client_id', 'client_secret', 'api_url']
            for field in required:
                if field not in config:
                    raise serializers.ValidationError(
                        {'config': f'ADP integration requires "{field}" in config'}
                    )

        return data


class WebhookEndpointSerializer(serializers.ModelSerializer):
    """Serializer for webhook endpoints."""

    # Secret is write-only
    secret = serializers.CharField(write_only=True, required=False, allow_null=True)
    has_secret = serializers.SerializerMethodField()
    should_disable = serializers.BooleanField(read_only=True)

    integration_name = serializers.CharField(
        source='integration.name', read_only=True, allow_null=True
    )

    class Meta:
        model = WebhookEndpoint
        fields = [
            'id',
            'integration',
            'integration_name',
            'url',
            'secret',  # Write only
            'has_secret',
            'events',
            'is_active',
            'failure_count',
            'should_disable',
            'last_success',
            'last_failure',
            'headers',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'failure_count',
            'last_success',
            'last_failure',
            'created_at',
            'updated_at',
        ]

    def get_has_secret(self, obj):
        """Indicate if secret is configured without exposing it."""
        return bool(obj.secret)

    def validate_events(self, value):
        """Validate event types."""
        if not isinstance(value, list):
            raise serializers.ValidationError('Events must be a list')

        valid_events = [
            'application.created',
            'application.stage_changed',
            'application.rejected',
            'application.hired',
            'offer.created',
            'offer.sent',
            'offer.accepted',
            'offer.declined',
            'requisition.opened',
            'requisition.filled',
            'requisition.cancelled',
        ]

        for event in value:
            if event not in valid_events:
                raise serializers.ValidationError(f'Invalid event type: {event}')

        return value

    def validate_url(self, value):
        """Validate webhook URL."""
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError('URL must start with http:// or https://')
        return value

    def validate_headers(self, value):
        """Validate headers is a dict."""
        if value and not isinstance(value, dict):
            raise serializers.ValidationError('Headers must be a dictionary')
        return value or {}


class WebhookDeliverySerializer(serializers.ModelSerializer):
    """Read-only serializer for webhook delivery logs."""

    endpoint_url = serializers.CharField(source='endpoint.url', read_only=True)
    is_delivered = serializers.BooleanField(read_only=True)
    is_success = serializers.BooleanField(read_only=True)

    class Meta:
        model = WebhookDelivery
        fields = [
            'id',
            'endpoint',
            'endpoint_url',
            'event_type',
            'payload',
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
        read_only_fields = '__all__'  # Delivery logs are read-only


class JobBoardPostingSerializer(serializers.ModelSerializer):
    """Serializer for job board postings."""

    requisition_title = serializers.CharField(source='requisition.title', read_only=True)
    integration_name = serializers.CharField(source='integration.name', read_only=True)
    integration_provider = serializers.CharField(
        source='integration.get_provider_display', read_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = JobBoardPosting
        fields = [
            'id',
            'requisition',
            'requisition_title',
            'integration',
            'integration_name',
            'integration_provider',
            'external_id',
            'posted_at',
            'last_synced',
            'status',
            'status_display',
            'is_active',
            'url',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'external_id',
            'posted_at',
            'last_synced',
            'status',
            'url',
            'metadata',
            'created_at',
            'updated_at',
        ]


class TestConnectionSerializer(serializers.Serializer):
    """Input serializer for testing integration connection."""

    integration_id = serializers.UUIDField(required=True)

    def validate_integration_id(self, value):
        """Validate integration exists."""
        if not Integration.objects.filter(id=value).exists():
            raise serializers.ValidationError('Integration not found')
        return value


class JobBoardPostingCreateSerializer(serializers.Serializer):
    """Input serializer for posting job to board."""

    requisition_id = serializers.UUIDField(required=True)
    integration_id = serializers.UUIDField(required=True)

    def validate_integration_id(self, value):
        """Validate integration exists and is a job board."""
        try:
            integration = Integration.objects.get(id=value)
            if integration.category != 'job_board':
                raise serializers.ValidationError('Integration must be a job board')
            if not integration.is_active:
                raise serializers.ValidationError('Integration is not active')
        except Integration.DoesNotExist:
            raise serializers.ValidationError('Integration not found')
        return value

    def validate_requisition_id(self, value):
        """Validate requisition exists."""
        from apps.jobs.models import Requisition

        if not Requisition.objects.filter(id=value).exists():
            raise serializers.ValidationError('Requisition not found')
        return value

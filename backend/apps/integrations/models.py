"""Models for external integrations and webhooks."""

from django.db import models
from encrypted_fields import EncryptedCharField, EncryptedTextField

from apps.core.models import BaseModel


class Integration(BaseModel):
    """External service integration configuration."""

    PROVIDER_CHOICES = [
        ('indeed', 'Indeed'),
        ('linkedin', 'LinkedIn'),
        ('glassdoor', 'Glassdoor'),
        ('bamboo_hr', 'BambooHR'),
        ('workday', 'Workday'),
        ('adp', 'ADP'),
        ('custom', 'Custom Integration'),
    ]

    CATEGORY_CHOICES = [
        ('job_board', 'Job Board'),
        ('hris', 'HRIS'),
        ('ats', 'Applicant Tracking System'),
        ('custom', 'Custom'),
    ]

    SYNC_STATUS_CHOICES = [
        ('idle', 'Idle'),
        ('syncing', 'Syncing'),
        ('success', 'Success'),
        ('error', 'Error'),
    ]

    provider = models.CharField(
        max_length=50,
        choices=PROVIDER_CHOICES,
        help_text='Integration provider',
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        help_text='Integration category',
    )
    name = models.CharField(
        max_length=200,
        help_text='User-friendly integration name',
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text='Enable or disable integration',
    )
    config = EncryptedTextField(
        help_text='Encrypted JSON configuration (API keys, endpoints, settings)',
    )
    oauth_token = EncryptedTextField(
        null=True,
        blank=True,
        help_text='OAuth access token (encrypted)',
    )
    oauth_refresh_token = EncryptedTextField(
        null=True,
        blank=True,
        help_text='OAuth refresh token (encrypted)',
    )
    oauth_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='OAuth token expiration timestamp',
    )
    last_sync = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last successful sync timestamp',
    )
    sync_status = models.CharField(
        max_length=20,
        choices=SYNC_STATUS_CHOICES,
        default='idle',
        db_index=True,
        help_text='Current sync status',
    )
    error_log = models.TextField(
        blank=True,
        help_text='Last error message',
    )
    failure_count = models.IntegerField(
        default=0,
        help_text='Consecutive failure count for circuit breaker',
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Provider-specific metadata',
    )

    class Meta:
        unique_together = [('provider', 'name')]
        indexes = [
            models.Index(fields=['is_active', 'sync_status']),
            models.Index(fields=['category']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_provider_display()} - {self.name}'

    @property
    def is_oauth_configured(self):
        """Check if OAuth tokens are configured."""
        return bool(self.oauth_token)

    @property
    def needs_token_refresh(self):
        """Check if OAuth token needs refresh."""
        if not self.oauth_expires_at:
            return False
        from django.utils import timezone
        from datetime import timedelta

        # Refresh if token expires within 10 minutes
        return timezone.now() + timedelta(minutes=10) >= self.oauth_expires_at

    @property
    def is_circuit_broken(self):
        """Check if circuit breaker should block requests."""
        return self.failure_count >= 10


class WebhookEndpoint(BaseModel):
    """Webhook subscription endpoint for external consumers."""

    integration = models.ForeignKey(
        Integration,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='webhook_endpoints',
        help_text='Associated integration (optional)',
    )
    url = models.URLField(
        max_length=500,
        help_text='Webhook endpoint URL to POST events to',
    )
    secret = EncryptedCharField(
        max_length=255,
        help_text='HMAC signing secret (encrypted)',
    )
    events = models.JSONField(
        default=list,
        help_text='List of event types to send to this endpoint',
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text='Enable or disable webhook delivery',
    )
    failure_count = models.IntegerField(
        default=0,
        db_index=True,
        help_text='Consecutive delivery failure count',
    )
    last_success = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last successful delivery timestamp',
    )
    last_failure = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last failed delivery timestamp',
    )
    headers = models.JSONField(
        default=dict,
        blank=True,
        help_text='Custom HTTP headers to include in requests',
    )

    class Meta:
        indexes = [
            models.Index(fields=['is_active', 'failure_count']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'Webhook: {self.url}'

    @property
    def should_disable(self):
        """Check if endpoint should be auto-disabled due to failures."""
        return self.failure_count >= 10


class WebhookDelivery(BaseModel):
    """Log of webhook delivery attempts."""

    endpoint = models.ForeignKey(
        WebhookEndpoint,
        on_delete=models.CASCADE,
        related_name='deliveries',
        help_text='Target webhook endpoint',
    )
    event_type = models.CharField(
        max_length=100,
        db_index=True,
        help_text='Event type (e.g., application.created)',
    )
    payload = models.JSONField(
        help_text='Full event payload sent to webhook',
    )
    response_status = models.IntegerField(
        null=True,
        blank=True,
        help_text='HTTP response status code',
    )
    response_body = models.TextField(
        blank=True,
        help_text='Response body from webhook endpoint',
    )
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Successful delivery timestamp',
    )
    attempts = models.IntegerField(
        default=1,
        help_text='Number of delivery attempts',
    )
    error_message = models.TextField(
        blank=True,
        help_text='Error message if delivery failed',
    )

    class Meta:
        indexes = [
            models.Index(fields=['event_type', '-created_at']),
            models.Index(fields=['endpoint', '-created_at']),
            models.Index(fields=['delivered_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        status = 'Delivered' if self.delivered_at else 'Failed'
        return f'{self.event_type} → {self.endpoint.url} ({status})'

    @property
    def is_delivered(self):
        """Check if webhook was successfully delivered."""
        return self.delivered_at is not None

    @property
    def is_success(self):
        """Check if delivery was successful based on status code."""
        if self.response_status is None:
            return False
        return 200 <= self.response_status < 300


class JobBoardPosting(BaseModel):
    """Track job postings on external job boards."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('closed', 'Closed'),
        ('error', 'Error'),
    ]

    requisition = models.ForeignKey(
        'jobs.Requisition',
        on_delete=models.CASCADE,
        related_name='board_postings',
        help_text='Job requisition posted to board',
    )
    integration = models.ForeignKey(
        Integration,
        on_delete=models.CASCADE,
        related_name='job_postings',
        help_text='Job board integration used',
    )
    external_id = models.CharField(
        max_length=255,
        help_text='Job ID from external job board',
    )
    posted_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Initial posting timestamp',
    )
    last_synced = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last sync with job board',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True,
        help_text='Posting status',
    )
    url = models.URLField(
        max_length=500,
        blank=True,
        help_text='Public job posting URL on the board',
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Board-specific posting data',
    )

    class Meta:
        unique_together = [('requisition', 'integration')]
        indexes = [
            models.Index(fields=['status', '-posted_at']),
            models.Index(fields=['integration', 'external_id']),
        ]
        ordering = ['-posted_at']

    def __str__(self):
        board = self.integration.get_provider_display()
        return f'{self.requisition.title} on {board} ({self.get_status_display()})'

    @property
    def is_active(self):
        """Check if posting is currently active on the board."""
        return self.status == 'posted'

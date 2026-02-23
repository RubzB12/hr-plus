"""Models for communications app."""

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class EmailTemplate(BaseModel):
    """Reusable email template with merge field support."""

    CATEGORY_CHOICES = [
        ('application', 'Application'),
        ('interview', 'Interview'),
        ('offer', 'Offer'),
        ('rejection', 'Rejection'),
        ('onboarding', 'Onboarding'),
        ('general', 'General'),
    ]

    name = models.CharField(max_length=200, unique=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    subject = models.CharField(max_length=500)
    body_html = models.TextField()
    body_text = models.TextField()
    variables = models.JSONField(
        default=dict,
        help_text=(
            'Available merge fields for this template '
            '(e.g., {"candidate_name": "string", "job_title": "string"})'
        ),
    )
    department = models.ForeignKey(
        'accounts.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_templates',
        help_text='If set, template is department-specific',
    )
    is_active = models.BooleanField(default=True)
    version = models.IntegerField(default=1)

    class Meta:
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category', 'is_active']),
        ]

    def __str__(self):
        return f'{self.name} (v{self.version})'


class EmailLog(BaseModel):
    """Log of all emails sent from the system."""

    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('bounced', 'Bounced'),
        ('failed', 'Failed'),
    ]

    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_logs',
    )
    application = models.ForeignKey(
        'applications.Application',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emails',
        help_text='If email is related to an application',
    )
    sender = models.EmailField()
    recipient = models.EmailField()
    subject = models.CharField(max_length=500)
    body_html = models.TextField(blank=True)
    body_text = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='queued',
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    message_id = models.CharField(
        max_length=500,
        blank=True,
        help_text='External email provider message ID',
    )
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(
        default=dict,
        help_text='Additional metadata (merge fields used, provider response, etc.)',
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['application', '-created_at']),
        ]

    def __str__(self):
        return f'{self.subject} to {self.recipient} ({self.status})'


class Notification(BaseModel):
    """In-app notification for internal users."""

    TYPE_CHOICES = [
        ('application', 'Application Update'),
        ('interview', 'Interview'),
        ('scorecard', 'Scorecard Reminder'),
        ('approval', 'Approval Request'),
        ('mention', 'Mention'),
        ('system', 'System'),
        ('stage_change', 'Application Stage Change'),
        ('application_received', 'Application Received'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    body = models.TextField()
    link = models.CharField(
        max_length=500,
        blank=True,
        help_text='Internal app link (e.g., /applications/123)',
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(
        default=dict,
        help_text='Additional context (application_id, interview_id, etc.)',
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', '-created_at']),
            models.Index(fields=['recipient', '-created_at']),
        ]

    def __str__(self):
        return f'{self.title} for {self.recipient.get_full_name()}'


class MessageThread(BaseModel):
    """Conversation thread between users (internal and/or candidates)."""

    subject = models.CharField(max_length=200, blank=True)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='message_threads',
    )
    application = models.ForeignKey(
        'applications.Application',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='message_threads',
        help_text='If thread is related to a specific application',
    )
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['-updated_at']),
            models.Index(fields=['application', '-updated_at']),
        ]

    def __str__(self):
        participant_count = self.participants.count()
        return f'Thread: {self.subject or "No subject"} ({participant_count} participants)'


class Message(BaseModel):
    """Individual message within a thread."""

    thread = models.ForeignKey(
        MessageThread,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
    )
    body = models.TextField()
    attachments = models.JSONField(
        default=list,
        blank=True,
        help_text='List of attachment URLs/metadata',
    )
    read_by = models.JSONField(
        default=dict,
        blank=True,
        help_text='Dict of user_id: timestamp when message was read',
    )
    is_system_message = models.BooleanField(
        default=False,
        help_text='System-generated message (e.g., "John moved application to Interview")',
    )

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['thread', 'created_at']),
            models.Index(fields=['sender', '-created_at']),
        ]

    def __str__(self):
        return f'Message from {self.sender.get_full_name()} in {self.thread}'

    def mark_as_read(self, user):
        """Mark message as read by a user."""
        from django.utils import timezone

        if str(user.id) not in self.read_by:
            self.read_by[str(user.id)] = timezone.now().isoformat()
            self.save(update_fields=['read_by'])

    def is_read_by(self, user) -> bool:
        """Check if user has read this message."""
        return str(user.id) in self.read_by

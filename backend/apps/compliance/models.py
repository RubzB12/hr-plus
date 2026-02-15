"""Compliance and audit models for HR-Plus."""

from django.conf import settings
from django.db import models
from encrypted_fields import EncryptedCharField, EncryptedTextField

from apps.core.models import BaseModel


class AuditLog(models.Model):
    """
    Immutable audit log for tracking all system actions.
    Append-only — records should never be updated or deleted.
    """

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    actor_ip = models.GenericIPAddressField(null=True, blank=True)
    action = models.CharField(max_length=50)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=255)
    changes = models.JSONField(
        null=True,
        blank=True,
        help_text='Before/after snapshot for update operations.',
    )
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'compliance_audit_log'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['actor', '-timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
        permissions = [
            ('export_auditlog', 'Can export audit logs'),
        ]

    def __str__(self):
        actor_str = self.actor.email if self.actor else 'anonymous'
        return f'{actor_str} {self.action} {self.resource_type}/{self.resource_id}'


class EEOData(BaseModel):
    """
    Equal Employment Opportunity self-identification data.

    CRITICAL: This data MUST be stored separately and NEVER shown to hiring team.
    Only accessible for compliance reporting (aggregated, anonymized).
    All sensitive fields are encrypted at rest.
    """

    candidate = models.OneToOneField(
        'accounts.CandidateProfile',
        on_delete=models.CASCADE,
        related_name='eeo_data',
    )

    # Encrypted fields
    gender = EncryptedCharField(
        max_length=100,
        null=True,
        blank=True,
        help_text='Self-identified gender (optional)',
    )
    race_ethnicity = EncryptedCharField(
        max_length=200,
        null=True,
        blank=True,
        help_text='Self-identified race/ethnicity (optional)',
    )
    veteran_status = EncryptedCharField(
        max_length=100,
        null=True,
        blank=True,
        help_text='Protected veteran status (optional)',
    )
    disability_status = EncryptedCharField(
        max_length=100,
        null=True,
        blank=True,
        help_text='Disability status (optional)',
    )

    consent_given = models.BooleanField(
        default=True,
        help_text='Candidate consented to provide this data',
    )
    collected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'compliance_eeo_data'
        verbose_name = 'EEO Data'
        verbose_name_plural = 'EEO Data'
        permissions = [
            ('view_eeo_reports', 'Can view aggregated EEO reports'),
            ('export_eeo_data', 'Can export EEO compliance reports'),
        ]

    def __str__(self):
        return f'EEO data for {self.candidate.user.email}'


class ConsentRecord(BaseModel):
    """
    Record of user consents for data processing (GDPR compliance).
    """

    CONSENT_TYPES = [
        ('data_processing', 'Data Processing'),
        ('marketing', 'Marketing Communications'),
        ('data_sharing', 'Data Sharing with Partners'),
        ('eeo_collection', 'EEO Data Collection'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='consent_records',
    )
    consent_type = models.CharField(
        max_length=50,
        choices=CONSENT_TYPES,
    )
    given_at = models.DateTimeField(auto_now_add=True)
    withdrawn_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address when consent was given',
    )
    user_agent = models.TextField(blank=True, help_text='Browser user agent')

    class Meta:
        db_table = 'compliance_consent_record'
        ordering = ['-given_at']
        indexes = [
            models.Index(fields=['user', 'consent_type']),
            models.Index(fields=['-given_at']),
        ]

    def __str__(self):
        status = 'withdrawn' if self.withdrawn_at else 'active'
        return f'{self.user.email} - {self.get_consent_type_display()} ({status})'

    @property
    def is_active(self):
        """Check if consent is currently active."""
        return self.withdrawn_at is None


class AnonymizationRecord(BaseModel):
    """
    Record of candidate data anonymization (GDPR Right to Erasure).
    Preserves audit trail while removing PII.
    """

    candidate_id = models.UUIDField(
        help_text='Original candidate UUID (preserved for audit trail)',
    )
    candidate_email_hash = models.CharField(
        max_length=64,
        help_text='SHA-256 hash of email for duplicate detection',
    )
    anonymized_at = models.DateTimeField(auto_now_add=True)
    anonymized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='anonymizations_performed',
    )
    reason = models.CharField(
        max_length=200,
        help_text='Reason for anonymization (user request, retention policy, etc.)',
    )
    applications_count = models.IntegerField(
        default=0,
        help_text='Number of applications at time of anonymization',
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional anonymization context',
    )

    class Meta:
        db_table = 'compliance_anonymization_record'
        ordering = ['-anonymized_at']
        indexes = [
            models.Index(fields=['-anonymized_at']),
            models.Index(fields=['candidate_id']),
        ]

    def __str__(self):
        return f'Anonymization of {self.candidate_id} on {self.anonymized_at.date()}'


class DataRetentionPolicy(BaseModel):
    """
    Data retention policies for automatic data purging (GDPR compliance).
    """

    DATA_TYPES = [
        ('candidate_application', 'Candidate Applications'),
        ('candidate_profile', 'Candidate Profiles'),
        ('assessment_results', 'Assessment Results'),
        ('interview_notes', 'Interview Notes'),
        ('communication_logs', 'Communication Logs'),
        ('audit_logs', 'Audit Logs'),
    ]

    data_type = models.CharField(
        max_length=50,
        choices=DATA_TYPES,
        unique=True,
    )
    retention_days = models.PositiveIntegerField(
        help_text='Number of days to retain data after creation/last update',
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this policy is currently enforced',
    )
    grace_period_days = models.PositiveIntegerField(
        default=30,
        help_text='Grace period before data is actually deleted',
    )
    description = models.TextField(
        blank=True,
        help_text='Description of this retention policy',
    )
    last_executed = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last time this policy was executed',
    )

    class Meta:
        db_table = 'compliance_data_retention_policy'
        verbose_name = 'Data Retention Policy'
        verbose_name_plural = 'Data Retention Policies'
        ordering = ['data_type']

    def __str__(self):
        return f'{self.get_data_type_display()} - {self.retention_days} days'

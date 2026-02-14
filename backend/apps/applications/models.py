"""Application and event models for HR-Plus."""


from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class Application(BaseModel):
    """A candidate's application to a specific requisition."""

    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('screening', 'Screening'),
        ('interview', 'Interview'),
        ('assessment', 'Assessment'),
        ('offer', 'Offer'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]

    SOURCE_CHOICES = [
        ('direct', 'Direct'),
        ('career_site', 'Career Site'),
        ('linkedin', 'LinkedIn'),
        ('indeed', 'Indeed'),
        ('referral', 'Referral'),
        ('agency', 'Agency'),
        ('other', 'Other'),
    ]

    application_id = models.CharField(
        max_length=20,
        unique=True,
        help_text='Auto-generated, e.g. APP-2026-00001',
    )
    candidate = models.ForeignKey(
        'accounts.CandidateProfile',
        on_delete=models.CASCADE,
        related_name='applications',
    )
    requisition = models.ForeignKey(
        'jobs.Requisition',
        on_delete=models.CASCADE,
        related_name='applications',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='applied',
        db_index=True,
    )
    current_stage = models.ForeignKey(
        'jobs.PipelineStage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applications',
    )
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='career_site',
    )
    referrer = models.ForeignKey(
        'accounts.InternalUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referred_applications',
    )
    resume_snapshot = models.JSONField(
        null=True,
        blank=True,
        help_text='Snapshot of resume data at time of application.',
    )
    cover_letter = models.TextField(blank=True)
    screening_responses = models.JSONField(
        default=dict,
        blank=True,
        help_text='Answers to requisition screening questions.',
    )
    is_starred = models.BooleanField(default=False)
    rejection_reason = models.CharField(max_length=200, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    hired_at = models.DateTimeField(null=True, blank=True)
    withdrawn_at = models.DateTimeField(null=True, blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'applications_application'
        ordering = ['-applied_at']
        constraints = [
            models.UniqueConstraint(
                fields=['candidate', 'requisition'],
                name='unique_candidate_requisition',
            ),
        ]
        indexes = [
            models.Index(fields=['requisition', 'status']),
            models.Index(fields=['candidate', '-applied_at']),
        ]

    def __str__(self):
        return f'{self.application_id}: {self.candidate} → {self.requisition}'


class ApplicationEvent(BaseModel):
    """Immutable audit trail for application lifecycle events."""

    EVENT_TYPE_CHOICES = [
        ('application.created', 'Application Created'),
        ('application.stage_changed', 'Stage Changed'),
        ('application.status_changed', 'Status Changed'),
        ('application.withdrawn', 'Withdrawn'),
        ('application.rejected', 'Rejected'),
        ('application.hired', 'Hired'),
        ('note.added', 'Note Added'),
        ('email.sent', 'Email Sent'),
    ]

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='events',
    )
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    from_stage = models.ForeignKey(
        'jobs.PipelineStage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    to_stage = models.ForeignKey(
        'jobs.PipelineStage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'applications_event'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['application', '-created_at']),
        ]

    def __str__(self):
        return f'{self.application.application_id}: {self.event_type}'


class Tag(BaseModel):
    """Reusable tag for categorising applications."""

    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(
        max_length=7,
        default='#6366f1',
        help_text='Hex colour code.',
    )

    class Meta:
        db_table = 'applications_tag'
        ordering = ['name']

    def __str__(self):
        return self.name


class ApplicationTag(BaseModel):
    """Through model for application-tag relationship."""

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='application_tags',
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='application_tags',
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )

    class Meta:
        db_table = 'applications_application_tag'
        unique_together = [['application', 'tag']]

    def __str__(self):
        return f'{self.application.application_id} — {self.tag.name}'


class RejectionReason(BaseModel):
    """Pre-defined rejection reasons for consistency and analytics."""

    label = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'applications_rejection_reason'
        ordering = ['label']

    def __str__(self):
        return self.label


class CandidateNote(BaseModel):
    """Internal note attached to an application."""

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='notes',
    )
    author = models.ForeignKey(
        'accounts.InternalUser',
        on_delete=models.PROTECT,
        related_name='candidate_notes',
    )
    body = models.TextField()
    is_private = models.BooleanField(
        default=False,
        help_text='Private notes are visible only to the author.',
    )

    class Meta:
        db_table = 'applications_candidate_note'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['application', '-created_at']),
        ]

    def __str__(self):
        return f'Note on {self.application.application_id} by {self.author}'

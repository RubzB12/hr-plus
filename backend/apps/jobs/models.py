"""Job requisition and pipeline models for HR-Plus."""

from django.db import models
from django.utils.text import slugify

from apps.core.models import BaseModel


class Requisition(BaseModel):
    """Job requisition — the core hiring unit."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('open', 'Open'),
        ('on_hold', 'On Hold'),
        ('filled', 'Filled'),
        ('cancelled', 'Cancelled'),
    ]

    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', 'Full-time'),
        ('part_time', 'Part-time'),
        ('contract', 'Contract'),
        ('temporary', 'Temporary'),
        ('internship', 'Internship'),
    ]

    REMOTE_POLICY_CHOICES = [
        ('onsite', 'On-site'),
        ('hybrid', 'Hybrid'),
        ('remote', 'Remote'),
    ]

    requisition_id = models.CharField(
        max_length=20,
        unique=True,
        help_text='Auto-generated ID, e.g. REQ-2026-001',
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    department = models.ForeignKey(
        'accounts.Department',
        on_delete=models.PROTECT,
        related_name='requisitions',
    )
    team = models.ForeignKey(
        'accounts.Team',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requisitions',
    )
    hiring_manager = models.ForeignKey(
        'accounts.InternalUser',
        on_delete=models.PROTECT,
        related_name='managed_requisitions',
    )
    recruiter = models.ForeignKey(
        'accounts.InternalUser',
        on_delete=models.PROTECT,
        related_name='owned_requisitions',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True,
    )
    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES,
        default='full_time',
    )
    level = models.ForeignKey(
        'accounts.JobLevel',
        on_delete=models.PROTECT,
        related_name='requisitions',
    )
    location = models.ForeignKey(
        'accounts.Location',
        on_delete=models.PROTECT,
        related_name='requisitions',
    )
    remote_policy = models.CharField(
        max_length=10,
        choices=REMOTE_POLICY_CHOICES,
        default='onsite',
    )
    salary_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    salary_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    salary_currency = models.CharField(max_length=3, default='ZAR')
    description = models.TextField(help_text='Rich text job description.')
    requirements_required = models.JSONField(
        default=list,
        blank=True,
        help_text='List of required qualifications.',
    )
    requirements_preferred = models.JSONField(
        default=list,
        blank=True,
        help_text='List of preferred qualifications.',
    )
    screening_questions = models.JSONField(
        default=list,
        blank=True,
        help_text='Custom screening questions for applicants.',
    )
    headcount = models.PositiveIntegerField(default=1)
    filled_count = models.PositiveIntegerField(default=0)
    target_start_date = models.DateField(null=True, blank=True)
    target_fill_date = models.DateField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        'accounts.InternalUser',
        on_delete=models.PROTECT,
        related_name='created_requisitions',
    )
    version = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'jobs_requisition'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['department', 'status']),
            models.Index(fields=['recruiter', 'status']),
        ]

    def __str__(self):
        return f'{self.requisition_id}: {self.title}'

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            self.slug = f'{base_slug}-{str(self.id)[:8]}'
        super().save(*args, **kwargs)

    @property
    def is_published(self):
        return self.status == 'open' and self.published_at is not None


class PipelineStage(BaseModel):
    """Pipeline stage within a requisition's hiring process."""

    STAGE_TYPE_CHOICES = [
        ('application', 'Application'),
        ('screening', 'Screening'),
        ('phone_screen', 'Phone Screen'),
        ('interview', 'Interview'),
        ('assessment', 'Assessment'),
        ('offer', 'Offer'),
        ('hired', 'Hired'),
        ('custom', 'Custom'),
    ]

    requisition = models.ForeignKey(
        Requisition,
        on_delete=models.CASCADE,
        related_name='stages',
    )
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField()
    stage_type = models.CharField(
        max_length=20,
        choices=STAGE_TYPE_CHOICES,
        default='custom',
    )
    auto_actions = models.JSONField(
        default=list,
        blank=True,
        help_text='Actions triggered when a candidate enters this stage.',
    )

    class Meta:
        db_table = 'jobs_pipeline_stage'
        ordering = ['requisition', 'order']
        unique_together = [['requisition', 'order']]

    def __str__(self):
        return f'{self.requisition.requisition_id} — {self.name}'


class RequisitionApproval(BaseModel):
    """An approval step in the requisition approval chain."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('skipped', 'Skipped'),
    ]

    requisition = models.ForeignKey(
        Requisition,
        on_delete=models.CASCADE,
        related_name='approvals',
    )
    approver = models.ForeignKey(
        'accounts.InternalUser',
        on_delete=models.PROTECT,
        related_name='approval_requests',
    )
    order = models.PositiveIntegerField(
        help_text='Order in the approval chain (0 = first).',
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True)

    class Meta:
        db_table = 'jobs_requisition_approval'
        ordering = ['requisition', 'order']
        unique_together = [['requisition', 'order']]

    def __str__(self):
        return (
            f'{self.requisition.requisition_id} — '
            f'{self.approver} ({self.status})'
        )

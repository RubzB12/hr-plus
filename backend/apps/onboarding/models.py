"""Onboarding models for HR-Plus."""

from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class OnboardingTemplate(BaseModel):
    """
    Template for onboarding plans.

    Defines standard tasks and documents required for a department or role.
    """

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    department = models.ForeignKey(
        'accounts.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='onboarding_templates',
    )
    job_level = models.ForeignKey(
        'accounts.JobLevel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='onboarding_templates',
    )
    is_active = models.BooleanField(default=True)
    tasks = models.JSONField(
        default=list,
        help_text='List of task templates with title, description, category, days_offset',
    )
    required_documents = models.JSONField(
        default=list, help_text='List of required document types'
    )
    forms = models.JSONField(default=list, help_text='List of required form types')

    class Meta:
        db_table = 'onboarding_template'
        ordering = ['name']

    def __str__(self):
        return self.name


class OnboardingPlan(BaseModel):
    """
    Onboarding plan for a new hire.

    Created when an offer is accepted, tracks all pre-boarding and day-1 activities.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending Start'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    application = models.OneToOneField(
        'applications.Application',
        on_delete=models.CASCADE,
        related_name='onboarding_plan',
    )
    offer = models.OneToOneField(
        'offers.Offer', on_delete=models.CASCADE, related_name='onboarding_plan'
    )
    template = models.ForeignKey(
        OnboardingTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='plans',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateField(help_text='First day of work')
    buddy = models.ForeignKey(
        'accounts.InternalUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='onboarding_buddy_for',
        help_text='Buddy/mentor assigned to new hire',
    )
    hr_contact = models.ForeignKey(
        'accounts.InternalUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='onboarding_hr_contact_for',
        help_text='HR contact for onboarding questions',
    )
    access_token = models.CharField(
        max_length=64,
        unique=True,
        help_text='Token for candidate to access onboarding portal',
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'onboarding_plan'
        ordering = ['-created_at']

    def __str__(self):
        candidate_name = self.application.candidate.user.get_full_name()
        return f'Onboarding: {candidate_name} - {self.start_date}'

    @property
    def progress_percentage(self) -> int:
        """Calculate onboarding completion percentage."""
        total_tasks = self.tasks.count()
        if total_tasks == 0:
            return 0
        completed_tasks = self.tasks.filter(status='completed').count()
        return round((completed_tasks / total_tasks) * 100)

    @property
    def is_overdue(self) -> bool:
        """Check if onboarding has overdue tasks."""
        from django.utils import timezone

        return self.tasks.filter(
            due_date__lt=timezone.now().date(), status__in=['pending', 'in_progress']
        ).exists()


class OnboardingTask(BaseModel):
    """
    Individual task in an onboarding plan.

    Can be assigned to candidate, buddy, HR, or manager.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
    ]

    CATEGORY_CHOICES = [
        ('admin', 'Administrative'),
        ('equipment', 'Equipment Setup'),
        ('access', 'System Access'),
        ('training', 'Training'),
        ('meeting', 'Meetings'),
        ('document', 'Documentation'),
        ('other', 'Other'),
    ]

    plan = models.ForeignKey(
        OnboardingPlan, on_delete=models.CASCADE, related_name='tasks'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='onboarding_tasks',
        help_text='User responsible for completing this task',
    )
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='onboarding_tasks_completed',
    )
    order = models.IntegerField(default=0, help_text='Display order')
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'onboarding_task'
        ordering = ['order', 'due_date']

    def __str__(self):
        return f'{self.title} ({self.get_status_display()})'


class OnboardingDocument(BaseModel):
    """
    Document uploaded or generated during onboarding.

    Can be uploaded by candidate (I-9, tax forms) or by HR (offer letter, handbook).
    """

    DOCUMENT_TYPE_CHOICES = [
        ('i9', 'I-9 Form'),
        ('w4', 'W-4 Tax Form'),
        ('direct_deposit', 'Direct Deposit Form'),
        ('emergency_contact', 'Emergency Contact Form'),
        ('signed_offer', 'Signed Offer Letter'),
        ('nda', 'Non-Disclosure Agreement'),
        ('handbook_acknowledgment', 'Handbook Acknowledgment'),
        ('equipment_agreement', 'Equipment Agreement'),
        ('photo_id', 'Photo ID'),
        ('work_authorization', 'Work Authorization'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Upload'),
        ('uploaded', 'Uploaded'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    plan = models.ForeignKey(
        OnboardingPlan, on_delete=models.CASCADE, related_name='documents'
    )
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES)
    file = models.FileField(upload_to='onboarding/%Y/%m/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='onboarding_documents_uploaded',
    )
    uploaded_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='onboarding_documents_reviewed',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'onboarding_document'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'{self.get_document_type_display()} - {self.get_status_display()}'


class OnboardingForm(BaseModel):
    """
    Form submitted during onboarding.

    Collects structured data like equipment preferences, dietary restrictions,
    emergency contacts, etc.
    """

    FORM_TYPE_CHOICES = [
        ('equipment_preferences', 'Equipment Preferences'),
        ('workspace_preferences', 'Workspace Preferences'),
        ('emergency_contact', 'Emergency Contact Information'),
        ('dietary_restrictions', 'Dietary Restrictions'),
        ('accessibility_needs', 'Accessibility Needs'),
        ('parking', 'Parking Request'),
        ('benefits_enrollment', 'Benefits Enrollment'),
        ('other', 'Other'),
    ]

    plan = models.ForeignKey(
        OnboardingPlan, on_delete=models.CASCADE, related_name='forms'
    )
    form_type = models.CharField(max_length=50, choices=FORM_TYPE_CHOICES)
    data = models.JSONField(
        default=dict, help_text='Form responses as key-value pairs'
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='onboarding_forms_submitted',
    )

    class Meta:
        db_table = 'onboarding_form'
        ordering = ['-submitted_at']
        unique_together = [['plan', 'form_type']]

    def __str__(self):
        return f'{self.get_form_type_display()}'

    @property
    def is_submitted(self) -> bool:
        """Check if form has been submitted."""
        return self.submitted_at is not None

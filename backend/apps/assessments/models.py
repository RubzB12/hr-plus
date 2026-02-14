"""Models for assessments app."""

from django.db import models

from apps.core.models import BaseModel


class AssessmentTemplate(BaseModel):
    """Template for assessments that can be assigned to candidates."""

    ASSESSMENT_TYPE_CHOICES = [
        ('technical', 'Technical Skills'),
        ('coding', 'Coding Challenge'),
        ('behavioral', 'Behavioral'),
        ('cognitive', 'Cognitive Ability'),
        ('personality', 'Personality'),
        ('culture_fit', 'Culture Fit'),
        ('custom', 'Custom'),
    ]

    name = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=ASSESSMENT_TYPE_CHOICES)
    description = models.TextField(blank=True)
    instructions = models.TextField(
        help_text='Instructions shown to candidate when taking assessment'
    )
    duration = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Duration in minutes (null if no time limit)',
    )
    passing_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Minimum score to pass (e.g., 70.00)',
    )
    scoring_rubric = models.JSONField(
        default=dict,
        blank=True,
        help_text='JSON structure defining how to score the assessment',
    )
    questions = models.JSONField(
        default=list,
        blank=True,
        help_text='Assessment questions and answer options (for built-in assessments)',
    )
    external_url = models.URLField(
        blank=True,
        help_text='URL for external assessment platform (e.g., HackerRank, Codility)',
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'assessments_template'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.get_type_display()})'


class Assessment(BaseModel):
    """An assessment assigned to a candidate."""

    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
        ('waived', 'Waived'),
    ]

    application = models.ForeignKey(
        'applications.Application',
        on_delete=models.CASCADE,
        related_name='assessments',
    )
    template = models.ForeignKey(
        AssessmentTemplate,
        on_delete=models.PROTECT,
        related_name='instances',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='assigned',
        db_index=True,
    )
    assigned_by = models.ForeignKey(
        'accounts.InternalUser',
        on_delete=models.PROTECT,
        related_name='assessments_assigned',
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Deadline for completion',
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When candidate started the assessment',
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When assessment was submitted',
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Final score (e.g., 85.50)',
    )
    responses = models.JSONField(
        default=dict,
        blank=True,
        help_text='Candidate responses to assessment questions',
    )
    evaluator_notes = models.TextField(
        blank=True,
        help_text='Notes from evaluator who scored the assessment',
    )
    evaluated_by = models.ForeignKey(
        'accounts.InternalUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assessments_evaluated',
    )
    evaluated_at = models.DateTimeField(null=True, blank=True)

    # Token for candidate access (UUID-based)
    access_token = models.CharField(
        max_length=100,
        unique=True,
        help_text='Unique token for candidate to access assessment',
    )

    class Meta:
        db_table = 'assessments_assessment'
        ordering = ['-assigned_at']
        indexes = [
            models.Index(fields=['application', 'status']),
            models.Index(fields=['access_token']),
        ]

    def __str__(self):
        candidate_name = self.application.candidate.user.get_full_name()
        return f'{self.template.name} - {candidate_name} ({self.status})'

    @property
    def is_passed(self):
        """Check if assessment passed based on passing score."""
        if self.score is None or self.template.passing_score is None:
            return None
        return self.score >= self.template.passing_score

    @property
    def is_overdue(self):
        """Check if assessment is past due date."""
        if not self.due_date or self.status == 'completed':
            return False
        from django.utils import timezone

        return timezone.now() > self.due_date


class ReferenceCheckRequest(BaseModel):
    """Request sent to a reference contact to provide feedback on candidate."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]

    RELATIONSHIP_CHOICES = [
        ('manager', 'Manager/Supervisor'),
        ('colleague', 'Colleague/Peer'),
        ('direct_report', 'Direct Report'),
        ('client', 'Client/Customer'),
        ('other', 'Other'),
    ]

    application = models.ForeignKey(
        'applications.Application',
        on_delete=models.CASCADE,
        related_name='reference_checks',
    )
    reference_name = models.CharField(max_length=200)
    reference_email = models.EmailField()
    reference_phone = models.CharField(max_length=50, blank=True)
    reference_company = models.CharField(max_length=200, blank=True)
    reference_title = models.CharField(max_length=200, blank=True)
    relationship = models.CharField(
        max_length=20,
        choices=RELATIONSHIP_CHOICES,
        default='manager',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
    )
    requested_by = models.ForeignKey(
        'accounts.InternalUser',
        on_delete=models.PROTECT,
        related_name='reference_checks_requested',
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When email was sent to reference',
    )
    due_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Deadline for reference to respond',
    )
    questionnaire = models.JSONField(
        default=list,
        help_text='Questions to ask the reference',
    )
    notes = models.TextField(
        blank=True,
        help_text='Internal notes about this reference',
    )

    # Token for reference access (UUID-based)
    access_token = models.CharField(
        max_length=100,
        unique=True,
        help_text='Unique token for reference to access form',
    )

    class Meta:
        db_table = 'assessments_reference_request'
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['application', 'status']),
            models.Index(fields=['access_token']),
        ]

    def __str__(self):
        candidate_name = self.application.candidate.user.get_full_name()
        return f'Reference: {self.reference_name} for {candidate_name}'


class ReferenceCheckResponse(BaseModel):
    """Response from a reference contact."""

    RECOMMENDATION_CHOICES = [
        ('highly_recommend', 'Highly Recommend'),
        ('recommend', 'Recommend'),
        ('recommend_with_reservations', 'Recommend with Reservations'),
        ('do_not_recommend', 'Do Not Recommend'),
        ('no_opinion', 'No Opinion'),
    ]

    request = models.OneToOneField(
        ReferenceCheckRequest,
        on_delete=models.CASCADE,
        related_name='response',
    )
    responses = models.JSONField(
        default=dict,
        help_text='Answers to questionnaire questions',
    )
    overall_recommendation = models.CharField(
        max_length=30,
        choices=RECOMMENDATION_CHOICES,
        null=True,
        blank=True,
    )
    would_rehire = models.BooleanField(
        null=True,
        blank=True,
        help_text='Would you hire this person again? (if former manager)',
    )
    additional_comments = models.TextField(
        blank=True,
        help_text='Additional feedback from reference',
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reference_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of reference submitter',
    )

    class Meta:
        db_table = 'assessments_reference_response'
        ordering = ['-submitted_at']

    def __str__(self):
        return f'Response from {self.request.reference_name}'

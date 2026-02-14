"""Models for interviews app."""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import BaseModel


class ScorecardTemplate(BaseModel):
    """Template defining scorecard criteria for interviews."""

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    department = models.ForeignKey(
        'accounts.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scorecard_templates',
    )
    rating_scale_min = models.IntegerField(default=1)
    rating_scale_max = models.IntegerField(default=5)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ScorecardCriterion(BaseModel):
    """Evaluation criterion for scorecards."""

    CATEGORY_CHOICES = [
        ('technical', 'Technical Skills'),
        ('communication', 'Communication'),
        ('problem_solving', 'Problem Solving'),
        ('culture_fit', 'Culture Fit'),
        ('leadership', 'Leadership'),
        ('other', 'Other'),
    ]

    template = models.ForeignKey(
        ScorecardTemplate,
        on_delete=models.CASCADE,
        related_name='criteria',
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    order = models.IntegerField(default=0)
    weight = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=1.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )

    class Meta:
        ordering = ['template', 'order']
        unique_together = [['template', 'order']]

    def __str__(self):
        return f'{self.template.name} - {self.name}'


class Interview(BaseModel):
    """Scheduled interview session."""

    TYPE_CHOICES = [
        ('phone_screen', 'Phone Screen'),
        ('video', 'Video Interview'),
        ('onsite', 'On-site Interview'),
        ('panel', 'Panel Interview'),
        ('technical', 'Technical Interview'),
        ('behavioral', 'Behavioral Interview'),
        ('case_study', 'Case Study'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
        ('no_show', 'No Show'),
    ]

    application = models.ForeignKey(
        'applications.Application',
        on_delete=models.CASCADE,
        related_name='interviews',
    )
    interview_plan_stage = models.ForeignKey(
        'jobs.PipelineStage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interviews',
    )
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
    )
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    timezone = models.CharField(max_length=100, default='UTC')
    location = models.CharField(max_length=500, blank=True)
    video_link = models.URLField(blank=True)
    prep_notes_interviewer = models.TextField(blank=True)
    prep_notes_candidate = models.TextField(blank=True)
    scorecard_template = models.ForeignKey(
        ScorecardTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interviews',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_interviews',
    )
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['scheduled_start']
        indexes = [
            models.Index(fields=['application', 'status']),
            models.Index(fields=['scheduled_start']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.application.application_id} - {self.get_type_display()} - {self.scheduled_start}'


class InterviewParticipant(BaseModel):
    """Interviewer assigned to an interview."""

    ROLE_CHOICES = [
        ('lead', 'Lead Interviewer'),
        ('shadow', 'Shadow Interviewer'),
        ('observer', 'Observer'),
    ]

    RSVP_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('tentative', 'Tentative'),
    ]

    interview = models.ForeignKey(
        Interview,
        on_delete=models.CASCADE,
        related_name='participants',
    )
    interviewer = models.ForeignKey(
        'accounts.InternalUser',
        on_delete=models.CASCADE,
        related_name='interview_participations',
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='lead')
    rsvp_status = models.CharField(
        max_length=20,
        choices=RSVP_CHOICES,
        default='pending',
    )
    rsvp_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [['interview', 'interviewer']]

    def __str__(self):
        return f'{self.interviewer.user.get_full_name()} - {self.interview}'


class Scorecard(BaseModel):
    """Interviewer's evaluation of a candidate."""

    RECOMMENDATION_CHOICES = [
        ('strong_hire', 'Strong Hire'),
        ('hire', 'Hire'),
        ('no_hire', 'No Hire'),
        ('strong_no_hire', 'Strong No Hire'),
    ]

    interview = models.ForeignKey(
        Interview,
        on_delete=models.CASCADE,
        related_name='scorecards',
    )
    interviewer = models.ForeignKey(
        'accounts.InternalUser',
        on_delete=models.PROTECT,
        related_name='scorecards',
    )
    overall_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
    )
    recommendation = models.CharField(
        max_length=20,
        choices=RECOMMENDATION_CHOICES,
        null=True,
        blank=True,
    )
    strengths = models.TextField(blank=True)
    concerns = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    is_draft = models.BooleanField(default=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [['interview', 'interviewer']]
        indexes = [
            models.Index(fields=['interview', 'is_draft']),
            models.Index(fields=['interviewer', 'is_draft']),
        ]

    def __str__(self):
        return f'Scorecard - {self.interview} - {self.interviewer.user.get_full_name()}'


class ScorecardCriterionRating(BaseModel):
    """Individual criterion rating within a scorecard."""

    scorecard = models.ForeignKey(
        Scorecard,
        on_delete=models.CASCADE,
        related_name='criterion_ratings',
    )
    criterion = models.ForeignKey(
        ScorecardCriterion,
        on_delete=models.CASCADE,
        related_name='ratings',
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    comment = models.TextField(blank=True)

    class Meta:
        unique_together = [['scorecard', 'criterion']]

    def __str__(self):
        return f'{self.scorecard} - {self.criterion.name}: {self.rating}'


class Debrief(BaseModel):
    """Post-interview debrief meeting and decision."""

    DECISION_CHOICES = [
        ('advance', 'Advance to Next Stage'),
        ('reject', 'Reject'),
        ('hold', 'Hold'),
        ('pending', 'Pending More Feedback'),
    ]

    application = models.ForeignKey(
        'applications.Application',
        on_delete=models.CASCADE,
        related_name='debriefs',
    )
    scheduled_at = models.DateTimeField()
    decision = models.CharField(
        max_length=20,
        choices=DECISION_CHOICES,
        null=True,
        blank=True,
    )
    notes = models.TextField(blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='debrief_decisions',
    )
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-scheduled_at']
        indexes = [
            models.Index(fields=['application', 'scheduled_at']),
        ]

    def __str__(self):
        return f'Debrief - {self.application.application_id} - {self.scheduled_at}'

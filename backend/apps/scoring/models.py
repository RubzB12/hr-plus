"""Candidate score model for HR-Plus scoring engine."""

from django.db import models

from apps.core.models import BaseModel


class CandidateScore(BaseModel):
    """Aggregated score for a single Application."""

    application = models.OneToOneField(
        'applications.Application',
        on_delete=models.CASCADE,
        related_name='candidate_score',
    )

    # Sub-scores (nullable until that stage has data)
    profile_score = models.IntegerField(null=True, blank=True)
    interview_score = models.IntegerField(null=True, blank=True)
    assessment_score = models.IntegerField(null=True, blank=True)
    final_score = models.IntegerField(null=True, blank=True)

    # Detailed breakdowns
    profile_breakdown = models.JSONField(default=dict, blank=True)
    interview_breakdown = models.JSONField(default=dict, blank=True)
    assessment_breakdown = models.JSONField(default=dict, blank=True)

    # Required-criteria gate
    meets_required_criteria = models.BooleanField(default=True)

    # Metadata
    scored_at = models.DateTimeField(auto_now=True)
    scoring_version = models.CharField(max_length=10, default='1.0')

    class Meta:
        db_table = 'scoring_candidate_score'
        indexes = [
            models.Index(fields=['application']),
            models.Index(fields=['final_score']),
        ]

    def __str__(self):
        return f'Score for {self.application.application_id}: {self.final_score}'

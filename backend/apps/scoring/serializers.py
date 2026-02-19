"""Serializers for the scoring app."""

from rest_framework import serializers

from .models import CandidateScore


class CandidateScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateScore
        fields = [
            'id',
            'profile_score',
            'interview_score',
            'assessment_score',
            'final_score',
            'profile_breakdown',
            'interview_breakdown',
            'assessment_breakdown',
            'meets_required_criteria',
            'scored_at',
            'scoring_version',
        ]
        read_only_fields = fields


class RequisitionCriteriaSerializer(serializers.Serializer):
    """Input/output serializer for RequisitionCriteria."""

    id = serializers.UUIDField(read_only=True)
    criterion_type = serializers.ChoiceField(
        choices=['skill', 'experience_years', 'education', 'job_title'],
    )
    value = serializers.CharField(max_length=200, allow_blank=True, default='')
    weight = serializers.IntegerField(min_value=1, max_value=100, default=10)
    is_required = serializers.BooleanField(default=False)
    min_proficiency = serializers.ChoiceField(
        choices=['', 'beginner', 'intermediate', 'advanced', 'expert'],
        default='',
        required=False,
        allow_blank=True,
    )
    min_years = serializers.IntegerField(
        min_value=0, allow_null=True, required=False, default=None,
    )
    order = serializers.IntegerField(min_value=0, default=0)
    created_at = serializers.DateTimeField(read_only=True)

"""Serializers for interviews app."""

from rest_framework import serializers

from apps.accounts.serializers import InternalUserListSerializer

from .models import (
    Debrief,
    Interview,
    InterviewParticipant,
    Scorecard,
    ScorecardCriterion,
    ScorecardCriterionRating,
    ScorecardTemplate,
)


class ScorecardTemplateSerializer(serializers.ModelSerializer):
    """Serializer for scorecard templates."""

    class Meta:
        model = ScorecardTemplate
        fields = [
            'id',
            'name',
            'description',
            'rating_scale_min',
            'rating_scale_max',
            'is_active',
        ]


class ScorecardCriterionSerializer(serializers.ModelSerializer):
    """Serializer for scorecard criteria."""

    class Meta:
        model = ScorecardCriterion
        fields = [
            'id',
            'name',
            'description',
            'category',
            'order',
            'weight',
        ]


class InterviewParticipantSerializer(serializers.ModelSerializer):
    """Serializer for interview participants."""

    interviewer = InternalUserListSerializer(read_only=True)

    class Meta:
        model = InterviewParticipant
        fields = [
            'id',
            'interviewer',
            'role',
            'rsvp_status',
            'rsvp_at',
        ]


class InterviewListSerializer(serializers.ModelSerializer):
    """Serializer for interview list view."""

    candidate_name = serializers.CharField(
        source='application.candidate.user.get_full_name',
        read_only=True,
    )
    requisition_title = serializers.CharField(
        source='application.requisition.title',
        read_only=True,
    )
    stage_name = serializers.CharField(
        source='interview_plan_stage.name',
        read_only=True,
        allow_null=True,
    )
    participants = InterviewParticipantSerializer(many=True, read_only=True)

    class Meta:
        model = Interview
        fields = [
            'id',
            'application',
            'candidate_name',
            'requisition_title',
            'type',
            'status',
            'scheduled_start',
            'scheduled_end',
            'timezone',
            'location',
            'video_link',
            'stage_name',
            'participants',
            'created_at',
        ]


class InterviewDetailSerializer(serializers.ModelSerializer):
    """Serializer for interview detail view."""

    candidate_name = serializers.CharField(
        source='application.candidate.user.get_full_name',
        read_only=True,
    )
    candidate_email = serializers.CharField(
        source='application.candidate.user.email',
        read_only=True,
    )
    requisition_title = serializers.CharField(
        source='application.requisition.title',
        read_only=True,
    )
    application_id_display = serializers.CharField(
        source='application.application_id',
        read_only=True,
    )
    stage_name = serializers.CharField(
        source='interview_plan_stage.name',
        read_only=True,
        allow_null=True,
    )
    participants = InterviewParticipantSerializer(many=True, read_only=True)

    class Meta:
        model = Interview
        fields = [
            'id',
            'application',
            'application_id_display',
            'candidate_name',
            'candidate_email',
            'requisition_title',
            'type',
            'status',
            'scheduled_start',
            'scheduled_end',
            'timezone',
            'location',
            'video_link',
            'prep_notes_interviewer',
            'prep_notes_candidate',
            'stage_name',
            'scorecard_template',
            'participants',
            'cancelled_at',
            'cancellation_reason',
            'created_at',
            'updated_at',
        ]


class ScheduleInterviewSerializer(serializers.Serializer):
    """Serializer for scheduling an interview."""

    application_id = serializers.UUIDField()
    type = serializers.ChoiceField(choices=Interview.TYPE_CHOICES)
    scheduled_start = serializers.DateTimeField()
    scheduled_end = serializers.DateTimeField()
    timezone = serializers.CharField(default='UTC')
    location = serializers.CharField(required=False, allow_blank=True)
    video_link = serializers.URLField(required=False, allow_blank=True)
    prep_notes_interviewer = serializers.CharField(required=False, allow_blank=True)
    prep_notes_candidate = serializers.CharField(required=False, allow_blank=True)
    interview_plan_stage_id = serializers.UUIDField(required=False, allow_null=True)
    scorecard_template_id = serializers.UUIDField(required=False, allow_null=True)
    interviewer_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
    )


class CancelInterviewSerializer(serializers.Serializer):
    """Serializer for cancelling an interview."""

    reason = serializers.CharField(required=False, allow_blank=True)


class RescheduleInterviewSerializer(serializers.Serializer):
    """Serializer for rescheduling an interview."""

    scheduled_start = serializers.DateTimeField()
    scheduled_end = serializers.DateTimeField()


class ScorecardCriterionRatingSerializer(serializers.ModelSerializer):
    """Serializer for criterion ratings."""

    criterion_name = serializers.CharField(source='criterion.name', read_only=True)
    category = serializers.CharField(source='criterion.category', read_only=True)

    class Meta:
        model = ScorecardCriterionRating
        fields = [
            'id',
            'criterion',
            'criterion_name',
            'category',
            'rating',
            'comment',
        ]


class ScorecardSerializer(serializers.ModelSerializer):
    """Serializer for scorecards."""

    interviewer_name = serializers.CharField(
        source='interviewer.user.get_full_name',
        read_only=True,
    )
    criterion_ratings = ScorecardCriterionRatingSerializer(many=True, read_only=True)

    class Meta:
        model = Scorecard
        fields = [
            'id',
            'interview',
            'interviewer',
            'interviewer_name',
            'overall_rating',
            'recommendation',
            'strengths',
            'concerns',
            'notes',
            'criterion_ratings',
            'is_draft',
            'submitted_at',
            'created_at',
            'updated_at',
        ]


class CreateScorecardSerializer(serializers.Serializer):
    """Serializer for creating/updating a scorecard."""

    overall_rating = serializers.IntegerField(
        min_value=1,
        max_value=5,
        required=False,
        allow_null=True,
    )
    recommendation = serializers.ChoiceField(
        choices=Scorecard.RECOMMENDATION_CHOICES,
        required=False,
        allow_null=True,
    )
    strengths = serializers.CharField(required=False, allow_blank=True)
    concerns = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    criterion_ratings = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True,
    )
    is_draft = serializers.BooleanField(default=True)


class DebriefSerializer(serializers.ModelSerializer):
    """Serializer for debriefs."""

    decided_by_name = serializers.CharField(
        source='decided_by.get_full_name',
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Debrief
        fields = [
            'id',
            'application',
            'scheduled_at',
            'decision',
            'notes',
            'decided_by',
            'decided_by_name',
            'decided_at',
            'created_at',
            'updated_at',
        ]


class CreateDebriefSerializer(serializers.Serializer):
    """Serializer for creating a debrief."""

    application_id = serializers.UUIDField()
    scheduled_at = serializers.DateTimeField()
    notes = serializers.CharField(required=False, allow_blank=True)


class RecordDecisionSerializer(serializers.Serializer):
    """Serializer for recording a debrief decision."""

    decision = serializers.ChoiceField(choices=Debrief.DECISION_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True)


class CandidateInterviewSerializer(serializers.ModelSerializer):
    """Serializer for candidate-facing interview view."""

    requisition_title = serializers.CharField(
        source='application.requisition.title',
        read_only=True,
    )
    interviewers = serializers.SerializerMethodField()

    class Meta:
        model = Interview
        fields = [
            'id',
            'requisition_title',
            'type',
            'status',
            'scheduled_start',
            'scheduled_end',
            'timezone',
            'location',
            'video_link',
            'prep_notes_candidate',
            'interviewers',
        ]

    def get_interviewers(self, obj):
        """Return list of interviewer names (anonymized for privacy)."""
        return [
            {
                'name': p.interviewer.user.get_full_name(),
                'role': p.role,
            }
            for p in obj.participants.all()
        ]

"""Serializers for assessments app."""

from rest_framework import serializers

from apps.accounts.serializers import InternalUserSerializer
from apps.applications.serializers import InternalApplicationListSerializer

from .models import (
    Assessment,
    AssessmentTemplate,
    ReferenceCheckRequest,
    ReferenceCheckResponse,
)


class AssessmentTemplateSerializer(serializers.ModelSerializer):
    """Serializer for AssessmentTemplate."""

    class Meta:
        model = AssessmentTemplate
        fields = [
            'id',
            'name',
            'type',
            'description',
            'instructions',
            'duration',
            'passing_score',
            'scoring_rubric',
            'questions',
            'external_url',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AssessmentTemplateListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing templates."""

    class Meta:
        model = AssessmentTemplate
        fields = [
            'id',
            'name',
            'type',
            'description',
            'duration',
            'passing_score',
            'is_active',
            'created_at',
        ]


class AssessmentSerializer(serializers.ModelSerializer):
    """Serializer for Assessment."""

    application_details = InternalApplicationListSerializer(
        source='application', read_only=True
    )
    template_details = AssessmentTemplateListSerializer(
        source='template', read_only=True
    )
    assigned_by_details = InternalUserSerializer(source='assigned_by', read_only=True)
    evaluated_by_details = InternalUserSerializer(
        source='evaluated_by', read_only=True
    )
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Assessment
        fields = [
            'id',
            'application',
            'application_details',
            'template',
            'template_details',
            'status',
            'assigned_by',
            'assigned_by_details',
            'due_date',
            'access_token',
            'started_at',
            'completed_at',
            'responses',
            'score',
            'evaluated_by',
            'evaluated_by_details',
            'evaluated_at',
            'evaluator_notes',
            'is_overdue',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'access_token',
            'started_at',
            'completed_at',
            'score',
            'evaluated_by',
            'evaluated_at',
            'is_overdue',
            'created_at',
            'updated_at',
            'application_details',
            'template_details',
            'assigned_by_details',
            'evaluated_by_details',
        ]


class AssessmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing assessments."""

    candidate_name = serializers.CharField(
        source='application.candidate.user.get_full_name', read_only=True
    )
    template_name = serializers.CharField(source='template.name', read_only=True)
    template_type = serializers.CharField(source='template.type', read_only=True)
    requisition_title = serializers.CharField(
        source='application.requisition.title', read_only=True
    )
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Assessment
        fields = [
            'id',
            'candidate_name',
            'requisition_title',
            'template_name',
            'template_type',
            'status',
            'due_date',
            'score',
            'is_overdue',
            'created_at',
        ]


class AssessmentCreateSerializer(serializers.Serializer):
    """Serializer for creating/assigning assessments."""

    application = serializers.UUIDField()
    template = serializers.PrimaryKeyRelatedField(
        queryset=AssessmentTemplate.objects.filter(is_active=True)
    )
    due_days = serializers.IntegerField(default=7, min_value=1, max_value=90)
    due_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_application(self, value):
        """Validate application exists."""
        from apps.applications.models import Application

        try:
            return Application.objects.get(pk=value)
        except Application.DoesNotExist:
            raise serializers.ValidationError('Application not found') from None


class AssessmentSubmitSerializer(serializers.Serializer):
    """Serializer for candidate assessment submission."""

    responses = serializers.JSONField()

    def validate_responses(self, value):
        """Validate responses structure."""
        if not isinstance(value, dict):
            raise serializers.ValidationError('Responses must be a dictionary')
        return value


class AssessmentScoreSerializer(serializers.Serializer):
    """Serializer for scoring an assessment."""

    score = serializers.FloatField(min_value=0, max_value=100)
    notes = serializers.CharField(required=False, allow_blank=True)


class ReferenceCheckRequestSerializer(serializers.ModelSerializer):
    """Serializer for ReferenceCheckRequest."""

    application_details = InternalApplicationListSerializer(
        source='application', read_only=True
    )
    requested_by_details = InternalUserSerializer(
        source='requested_by', read_only=True
    )
    response = serializers.SerializerMethodField()

    class Meta:
        model = ReferenceCheckRequest
        fields = [
            'id',
            'application',
            'application_details',
            'reference_name',
            'reference_email',
            'reference_phone',
            'reference_company',
            'reference_title',
            'relationship',
            'requested_by',
            'requested_by_details',
            'status',
            'questionnaire',
            'notes',
            'due_date',
            'sent_at',
            'access_token',
            'response',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'access_token',
            'sent_at',
            'created_at',
            'updated_at',
            'application_details',
            'requested_by_details',
            'response',
        ]

    def get_response(self, obj):
        """Get response if exists."""
        try:
            return ReferenceCheckResponseSerializer(obj.response).data
        except ReferenceCheckResponse.DoesNotExist:
            return None


class ReferenceCheckRequestListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing reference requests."""

    candidate_name = serializers.CharField(
        source='application.candidate.user.get_full_name', read_only=True
    )
    requisition_title = serializers.CharField(
        source='application.requisition.title', read_only=True
    )

    class Meta:
        model = ReferenceCheckRequest
        fields = [
            'id',
            'candidate_name',
            'requisition_title',
            'reference_name',
            'reference_email',
            'relationship',
            'status',
            'due_date',
            'sent_at',
            'created_at',
        ]


class ReferenceCheckRequestCreateSerializer(serializers.Serializer):
    """Serializer for creating reference check requests."""

    application = serializers.UUIDField()
    reference_name = serializers.CharField(max_length=200)
    reference_email = serializers.EmailField()
    reference_phone = serializers.CharField(max_length=50, required=False, allow_blank=True)
    reference_company = serializers.CharField(
        max_length=200, required=False, allow_blank=True
    )
    reference_title = serializers.CharField(
        max_length=200, required=False, allow_blank=True
    )
    relationship = serializers.CharField(max_length=50, default='manager')
    questionnaire = serializers.JSONField(required=False, allow_null=True)
    due_days = serializers.IntegerField(default=14, min_value=1, max_value=90)
    due_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_application(self, value):
        """Validate application exists."""
        from apps.applications.models import Application

        try:
            return Application.objects.get(pk=value)
        except Application.DoesNotExist:
            raise serializers.ValidationError('Application not found') from None

    def validate_questionnaire(self, value):
        """Validate questionnaire structure."""
        if value is not None and not isinstance(value, list):
            raise serializers.ValidationError('Questionnaire must be a list')
        return value


class ReferenceCheckResponseSerializer(serializers.ModelSerializer):
    """Serializer for ReferenceCheckResponse."""

    request_details = ReferenceCheckRequestSerializer(source='request', read_only=True)

    class Meta:
        model = ReferenceCheckResponse
        fields = [
            'id',
            'request',
            'request_details',
            'responses',
            'overall_recommendation',
            'would_rehire',
            'additional_comments',
            'reference_ip',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'request_details']


class ReferenceCheckResponseSubmitSerializer(serializers.Serializer):
    """Serializer for reference submitting their response."""

    responses = serializers.JSONField()
    overall_recommendation = serializers.ChoiceField(
        choices=[
            ('highly_recommend', 'Highly Recommend'),
            ('recommend', 'Recommend'),
            ('recommend_with_reservations', 'Recommend with Reservations'),
            ('do_not_recommend', 'Do Not Recommend'),
        ],
        required=False,
        allow_null=True,
    )
    would_rehire = serializers.BooleanField(required=False, allow_null=True)
    additional_comments = serializers.CharField(
        required=False, allow_blank=True, max_length=5000
    )

    def validate_responses(self, value):
        """Validate responses structure."""
        if not isinstance(value, dict):
            raise serializers.ValidationError('Responses must be a dictionary')
        return value

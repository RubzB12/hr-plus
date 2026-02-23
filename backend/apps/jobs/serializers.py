"""Serializers for jobs app."""

from rest_framework import serializers

from apps.accounts.serializers import (
    DepartmentSerializer,
    InternalUserSerializer,
    JobLevelSerializer,
    LocationSerializer,
    TeamSerializer,
)

from .models import PipelineStage, Requisition, RequisitionApproval

# --- Public serializers (career site) ---

class PublicJobListSerializer(serializers.ModelSerializer):
    """Minimal fields for job listing cards."""

    department = serializers.CharField(source='department.name')
    location_name = serializers.CharField(source='location.name')
    location_city = serializers.CharField(source='location.city')
    location_country = serializers.CharField(source='location.country')
    level = serializers.CharField(source='level.name')

    class Meta:
        model = Requisition
        fields = [
            'id', 'title', 'slug', 'department',
            'location_name', 'location_city', 'location_country',
            'employment_type', 'remote_policy',
            'salary_min', 'salary_max', 'salary_currency',
            'level', 'published_at', 'application_deadline',
        ]


class PublicJobDetailSerializer(serializers.ModelSerializer):
    """Full job detail for the job page."""

    department = serializers.CharField(source='department.name')
    team = serializers.CharField(source='team.name', default=None)
    location_name = serializers.CharField(source='location.name')
    location_city = serializers.CharField(source='location.city')
    location_country = serializers.CharField(source='location.country')
    level = serializers.CharField(source='level.name')

    class Meta:
        model = Requisition
        fields = [
            'id', 'title', 'slug', 'department', 'team',
            'location_name', 'location_city', 'location_country',
            'employment_type', 'remote_policy',
            'salary_min', 'salary_max', 'salary_currency',
            'level', 'description',
            'requirements_required', 'requirements_preferred',
            'screening_questions', 'published_at', 'application_deadline',
        ]


class JobCategorySerializer(serializers.Serializer):
    department__id = serializers.UUIDField()
    department__name = serializers.CharField()
    job_count = serializers.IntegerField()


# --- Internal serializers (dashboard) ---

class PipelineStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PipelineStage
        fields = ['id', 'name', 'order', 'stage_type', 'auto_actions']
        read_only_fields = ['id']


class RequisitionListSerializer(serializers.ModelSerializer):
    """Summary view for requisition list."""

    department = DepartmentSerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    hiring_manager = InternalUserSerializer(read_only=True)
    recruiter = InternalUserSerializer(read_only=True)

    class Meta:
        model = Requisition
        fields = [
            'id', 'requisition_id', 'title', 'slug', 'status',
            'department', 'location', 'hiring_manager', 'recruiter',
            'employment_type', 'remote_policy', 'headcount',
            'filled_count', 'opened_at', 'target_fill_date',
            'created_at',
        ]


class RequisitionApprovalSerializer(serializers.ModelSerializer):
    approver = InternalUserSerializer(read_only=True)

    class Meta:
        model = RequisitionApproval
        fields = [
            'id', 'approver', 'order', 'status',
            'decided_at', 'comments',
        ]


class RequisitionDetailSerializer(serializers.ModelSerializer):
    """Full detail view for a single requisition."""

    department = DepartmentSerializer(read_only=True)
    team = TeamSerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    level = JobLevelSerializer(read_only=True)
    hiring_manager = InternalUserSerializer(read_only=True)
    recruiter = InternalUserSerializer(read_only=True)
    stages = PipelineStageSerializer(many=True, read_only=True)
    approvals = RequisitionApprovalSerializer(many=True, read_only=True)

    class Meta:
        model = Requisition
        fields = [
            'id', 'requisition_id', 'title', 'slug', 'status',
            'department', 'team', 'location', 'level',
            'hiring_manager', 'recruiter',
            'employment_type', 'remote_policy',
            'salary_min', 'salary_max', 'salary_currency',
            'description', 'requirements_required',
            'requirements_preferred', 'screening_questions',
            'headcount', 'filled_count',
            'target_start_date', 'target_fill_date',
            'opened_at', 'closed_at', 'published_at',
            'version', 'stages', 'approvals',
            'created_at', 'updated_at',
        ]


class SubmitForApprovalSerializer(serializers.Serializer):
    """Input for submitting a requisition for approval."""
    approver_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
    )


class ApprovalActionSerializer(serializers.Serializer):
    """Input for approving or rejecting a requisition."""
    comments = serializers.CharField(
        max_length=2000, required=False, allow_blank=True, default='',
    )


class PendingApprovalSerializer(serializers.ModelSerializer):
    """Pending approval for the approvals list."""
    requisition = RequisitionListSerializer(read_only=True)

    class Meta:
        model = RequisitionApproval
        fields = [
            'id', 'requisition', 'order', 'status', 'created_at',
        ]


class RequisitionCreateSerializer(serializers.ModelSerializer):
    """Write serializer for creating/updating a requisition."""

    class Meta:
        model = Requisition
        fields = [
            'title', 'department', 'team', 'hiring_manager', 'recruiter',
            'employment_type', 'level', 'location', 'remote_policy',
            'salary_min', 'salary_max', 'salary_currency',
            'description', 'requirements_required',
            'requirements_preferred', 'screening_questions',
            'headcount', 'target_start_date', 'target_fill_date',
        ]

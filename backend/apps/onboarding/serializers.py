"""Onboarding serializers."""

from rest_framework import serializers

from .models import (
    OnboardingDocument,
    OnboardingForm,
    OnboardingPlan,
    OnboardingTask,
    OnboardingTemplate,
)


class OnboardingTaskSerializer(serializers.ModelSerializer):
    """Serializer for onboarding tasks."""

    assigned_to_name = serializers.CharField(
        source='assigned_to.get_full_name', read_only=True, allow_null=True
    )
    completed_by_name = serializers.CharField(
        source='completed_by.get_full_name', read_only=True, allow_null=True
    )
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = OnboardingTask
        fields = [
            'id',
            'plan',
            'title',
            'description',
            'category',
            'category_display',
            'assigned_to',
            'assigned_to_name',
            'due_date',
            'status',
            'status_display',
            'completed_at',
            'completed_by',
            'completed_by_name',
            'order',
            'notes',
            'is_overdue',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'plan',
            'completed_at',
            'completed_by',
            'created_at',
            'updated_at',
        ]

    def get_is_overdue(self, obj):
        from django.utils import timezone

        if obj.status in ['completed', 'skipped']:
            return False
        if not obj.due_date:
            return False
        return obj.due_date < timezone.now().date()


class OnboardingDocumentSerializer(serializers.ModelSerializer):
    """Serializer for onboarding documents."""

    document_type_display = serializers.CharField(
        source='get_document_type_display', read_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    uploaded_by_name = serializers.CharField(
        source='uploaded_by.get_full_name', read_only=True, allow_null=True
    )

    class Meta:
        model = OnboardingDocument
        fields = [
            'id',
            'plan',
            'document_type',
            'document_type_display',
            'file',
            'status',
            'status_display',
            'uploaded_by',
            'uploaded_by_name',
            'uploaded_at',
            'reviewed_by',
            'reviewed_at',
            'rejection_reason',
            'notes',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'plan',
            'uploaded_by',
            'uploaded_at',
            'reviewed_by',
            'reviewed_at',
            'created_at',
        ]


class OnboardingFormSerializer(serializers.ModelSerializer):
    """Serializer for onboarding forms."""

    form_type_display = serializers.CharField(source='get_form_type_display', read_only=True)
    is_submitted = serializers.BooleanField(read_only=True)

    class Meta:
        model = OnboardingForm
        fields = [
            'id',
            'plan',
            'form_type',
            'form_type_display',
            'data',
            'submitted_at',
            'submitted_by',
            'is_submitted',
            'created_at',
        ]
        read_only_fields = ['id', 'plan', 'submitted_at', 'submitted_by', 'created_at']


class OnboardingPlanSerializer(serializers.ModelSerializer):
    """Serializer for onboarding plans."""

    candidate_name = serializers.CharField(
        source='application.candidate.user.get_full_name', read_only=True
    )
    candidate_email = serializers.EmailField(
        source='application.candidate.user.email', read_only=True
    )
    requisition_title = serializers.CharField(
        source='application.requisition.title', read_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    progress_percentage = serializers.IntegerField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    buddy_name = serializers.CharField(
        source='buddy.user.get_full_name', read_only=True, allow_null=True
    )
    hr_contact_name = serializers.CharField(
        source='hr_contact.user.get_full_name', read_only=True, allow_null=True
    )

    class Meta:
        model = OnboardingPlan
        fields = [
            'id',
            'application',
            'offer',
            'template',
            'status',
            'status_display',
            'start_date',
            'buddy',
            'buddy_name',
            'hr_contact',
            'hr_contact_name',
            'completed_at',
            'notes',
            'progress_percentage',
            'is_overdue',
            'candidate_name',
            'candidate_email',
            'requisition_title',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'application',
            'offer',
            'completed_at',
            'progress_percentage',
            'is_overdue',
            'created_at',
            'updated_at',
        ]


class OnboardingPlanDetailSerializer(OnboardingPlanSerializer):
    """Detailed serializer with nested tasks, documents, and forms."""

    tasks = OnboardingTaskSerializer(many=True, read_only=True)
    documents = OnboardingDocumentSerializer(many=True, read_only=True)
    forms = OnboardingFormSerializer(many=True, read_only=True)

    class Meta(OnboardingPlanSerializer.Meta):
        fields = OnboardingPlanSerializer.Meta.fields + ['tasks', 'documents', 'forms']


class OnboardingTemplateSerializer(serializers.ModelSerializer):
    """Serializer for onboarding templates."""

    department_name = serializers.CharField(
        source='department.name', read_only=True, allow_null=True
    )
    job_level_name = serializers.CharField(
        source='job_level.name', read_only=True, allow_null=True
    )

    class Meta:
        model = OnboardingTemplate
        fields = [
            'id',
            'name',
            'description',
            'department',
            'department_name',
            'job_level',
            'job_level_name',
            'is_active',
            'tasks',
            'required_documents',
            'forms',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# Request serializers


class TaskCompleteSerializer(serializers.Serializer):
    """Serializer for marking task as complete."""

    notes = serializers.CharField(required=False, allow_blank=True)


class DocumentUploadSerializer(serializers.Serializer):
    """Serializer for document upload."""

    document_type = serializers.ChoiceField(choices=OnboardingDocument.DOCUMENT_TYPE_CHOICES)
    file = serializers.FileField()


class FormSubmitSerializer(serializers.Serializer):
    """Serializer for form submission."""

    form_type = serializers.ChoiceField(choices=OnboardingForm.FORM_TYPE_CHOICES)
    data = serializers.JSONField()


class AssignBuddySerializer(serializers.Serializer):
    """Serializer for assigning buddy."""

    buddy_id = serializers.UUIDField()


class UpdateStartDateSerializer(serializers.Serializer):
    """Serializer for updating start date."""

    start_date = serializers.DateField()

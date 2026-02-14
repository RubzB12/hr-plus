"""Django admin configuration for assessments app."""

from django.contrib import admin

from .models import (
    Assessment,
    AssessmentTemplate,
    ReferenceCheckRequest,
    ReferenceCheckResponse,
)


@admin.register(AssessmentTemplate)
class AssessmentTemplateAdmin(admin.ModelAdmin):
    """Admin for AssessmentTemplate model."""

    list_display = [
        'name',
        'type',
        'duration',
        'passing_score',
        'is_active',
        'created_at',
    ]
    list_filter = ['type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        (
            'Basic Information',
            {
                'fields': (
                    'id',
                    'name',
                    'type',
                    'description',
                    'instructions',
                    'is_active',
                )
            },
        ),
        (
            'Configuration',
            {
                'fields': (
                    'duration',
                    'passing_score',
                    'questions',
                    'scoring_rubric',
                    'external_url',
                )
            },
        ),
        ('Metadata', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    """Admin for Assessment model."""

    list_display = [
        'id',
        'get_candidate_name',
        'template',
        'status',
        'score',
        'due_date',
        'assigned_by',
        'created_at',
    ]
    list_filter = ['status', 'template__type', 'created_at', 'due_date']
    search_fields = [
        'application__candidate__user__first_name',
        'application__candidate__user__last_name',
        'application__candidate__user__email',
        'template__name',
    ]
    readonly_fields = [
        'id',
        'access_token',
        'started_at',
        'completed_at',
        'evaluated_at',
        'created_at',
        'updated_at',
    ]
    fieldsets = (
        (
            'Basic Information',
            {'fields': ('id', 'application', 'template', 'status', 'access_token')},
        ),
        (
            'Assignment',
            {'fields': ('assigned_by', 'due_date')},
        ),
        (
            'Completion',
            {
                'fields': (
                    'started_at',
                    'completed_at',
                    'responses',
                )
            },
        ),
        (
            'Evaluation',
            {'fields': ('score', 'evaluated_by', 'evaluated_at', 'evaluator_notes')},
        ),
        ('Metadata', {'fields': ('created_at', 'updated_at')}),
    )

    def get_candidate_name(self, obj):
        """Get candidate name."""
        return obj.application.candidate.user.get_full_name()

    get_candidate_name.short_description = 'Candidate'
    get_candidate_name.admin_order_field = 'application__candidate__user__last_name'


@admin.register(ReferenceCheckRequest)
class ReferenceCheckRequestAdmin(admin.ModelAdmin):
    """Admin for ReferenceCheckRequest model."""

    list_display = [
        'id',
        'get_candidate_name',
        'reference_name',
        'reference_email',
        'relationship',
        'status',
        'due_date',
        'sent_at',
        'created_at',
    ]
    list_filter = ['status', 'relationship', 'created_at', 'sent_at']
    search_fields = [
        'application__candidate__user__first_name',
        'application__candidate__user__last_name',
        'reference_name',
        'reference_email',
    ]
    readonly_fields = ['id', 'access_token', 'sent_at', 'created_at', 'updated_at']
    fieldsets = (
        (
            'Basic Information',
            {'fields': ('id', 'application', 'status', 'access_token')},
        ),
        (
            'Reference Details',
            {
                'fields': (
                    'reference_name',
                    'reference_email',
                    'reference_phone',
                    'reference_company',
                    'reference_title',
                    'relationship',
                )
            },
        ),
        (
            'Request Details',
            {'fields': ('requested_by', 'questionnaire', 'notes', 'due_date', 'sent_at')},
        ),
        ('Metadata', {'fields': ('created_at', 'updated_at')}),
    )

    def get_candidate_name(self, obj):
        """Get candidate name."""
        return obj.application.candidate.user.get_full_name()

    get_candidate_name.short_description = 'Candidate'
    get_candidate_name.admin_order_field = 'application__candidate__user__last_name'


@admin.register(ReferenceCheckResponse)
class ReferenceCheckResponseAdmin(admin.ModelAdmin):
    """Admin for ReferenceCheckResponse model."""

    list_display = [
        'id',
        'get_candidate_name',
        'get_reference_name',
        'overall_recommendation',
        'would_rehire',
        'created_at',
    ]
    list_filter = ['overall_recommendation', 'would_rehire', 'created_at']
    search_fields = [
        'request__application__candidate__user__first_name',
        'request__application__candidate__user__last_name',
        'request__reference_name',
    ]
    readonly_fields = ['id', 'reference_ip', 'created_at']
    fieldsets = (
        (
            'Basic Information',
            {'fields': ('id', 'request')},
        ),
        (
            'Response',
            {
                'fields': (
                    'responses',
                    'overall_recommendation',
                    'would_rehire',
                    'additional_comments',
                )
            },
        ),
        ('Metadata', {'fields': ('reference_ip', 'created_at')}),
    )

    def get_candidate_name(self, obj):
        """Get candidate name."""
        return obj.request.application.candidate.user.get_full_name()

    get_candidate_name.short_description = 'Candidate'

    def get_reference_name(self, obj):
        """Get reference name."""
        return obj.request.reference_name

    get_reference_name.short_description = 'Reference'

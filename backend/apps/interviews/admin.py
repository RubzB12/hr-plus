"""Admin configuration for interviews app."""

from django.contrib import admin

from .models import (
    Debrief,
    Interview,
    InterviewParticipant,
    Scorecard,
    ScorecardCriterion,
    ScorecardCriterionRating,
    ScorecardTemplate,
)


class ScorecardCriterionInline(admin.TabularInline):
    """Inline for scorecard criteria."""

    model = ScorecardCriterion
    extra = 1
    fields = ['name', 'description', 'category', 'order', 'weight']


@admin.register(ScorecardTemplate)
class ScorecardTemplateAdmin(admin.ModelAdmin):
    """Admin for scorecard templates."""

    list_display = ['name', 'department', 'rating_scale_min', 'rating_scale_max', 'is_active', 'created_at']
    list_filter = ['is_active', 'department']
    search_fields = ['name', 'description']
    inlines = [ScorecardCriterionInline]


class InterviewParticipantInline(admin.TabularInline):
    """Inline for interview participants."""

    model = InterviewParticipant
    extra = 1
    fields = ['interviewer', 'role', 'rsvp_status', 'rsvp_at']
    autocomplete_fields = ['interviewer']


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    """Admin for interviews."""

    list_display = [
        'application',
        'type',
        'status',
        'scheduled_start',
        'scheduled_end',
        'created_by',
        'created_at',
    ]
    list_filter = ['type', 'status', 'scheduled_start']
    search_fields = [
        'application__application_id',
        'application__candidate__user__email',
        'application__candidate__user__first_name',
        'application__candidate__user__last_name',
    ]
    autocomplete_fields = ['application', 'scorecard_template', 'created_by']
    inlines = [InterviewParticipantInline]
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Info', {
            'fields': ('application', 'type', 'status', 'interview_plan_stage'),
        }),
        ('Schedule', {
            'fields': ('scheduled_start', 'scheduled_end', 'timezone'),
        }),
        ('Location', {
            'fields': ('location', 'video_link'),
        }),
        ('Preparation', {
            'fields': ('prep_notes_interviewer', 'prep_notes_candidate', 'scorecard_template'),
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
        }),
        ('Cancellation', {
            'fields': ('cancelled_at', 'cancellation_reason'),
            'classes': ('collapse',),
        }),
    )


class ScorecardCriterionRatingInline(admin.TabularInline):
    """Inline for scorecard criterion ratings."""

    model = ScorecardCriterionRating
    extra = 0
    fields = ['criterion', 'rating', 'comment']


@admin.register(Scorecard)
class ScorecardAdmin(admin.ModelAdmin):
    """Admin for scorecards."""

    list_display = [
        'interview',
        'interviewer',
        'overall_rating',
        'recommendation',
        'is_draft',
        'submitted_at',
        'created_at',
    ]
    list_filter = ['is_draft', 'recommendation', 'overall_rating']
    search_fields = [
        'interview__application__application_id',
        'interviewer__user__email',
        'interviewer__user__first_name',
        'interviewer__user__last_name',
    ]
    autocomplete_fields = ['interview', 'interviewer']
    readonly_fields = ['submitted_at', 'created_at', 'updated_at']
    inlines = [ScorecardCriterionRatingInline]

    fieldsets = (
        ('Basic Info', {
            'fields': ('interview', 'interviewer', 'is_draft', 'submitted_at'),
        }),
        ('Evaluation', {
            'fields': ('overall_rating', 'recommendation'),
        }),
        ('Feedback', {
            'fields': ('strengths', 'concerns', 'notes'),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
        }),
    )


@admin.register(Debrief)
class DebriefAdmin(admin.ModelAdmin):
    """Admin for debriefs."""

    list_display = [
        'application',
        'scheduled_at',
        'decision',
        'decided_by',
        'decided_at',
        'created_at',
    ]
    list_filter = ['decision', 'scheduled_at']
    search_fields = [
        'application__application_id',
        'application__candidate__user__email',
        'notes',
    ]
    autocomplete_fields = ['application', 'decided_by']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Info', {
            'fields': ('application', 'scheduled_at'),
        }),
        ('Decision', {
            'fields': ('decision', 'decided_by', 'decided_at', 'notes'),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

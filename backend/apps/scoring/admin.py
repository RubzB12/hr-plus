from django.contrib import admin

from .models import CandidateScore


@admin.register(CandidateScore)
class CandidateScoreAdmin(admin.ModelAdmin):
    list_display = [
        'application',
        'final_score',
        'profile_score',
        'interview_score',
        'assessment_score',
        'meets_required_criteria',
        'scoring_version',
        'scored_at',
    ]
    readonly_fields = [
        'application',
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
    list_filter = ['meets_required_criteria', 'scoring_version']
    search_fields = ['application__application_id']

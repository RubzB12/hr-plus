"""Admin configuration for offers app."""

from django.contrib import admin

from .models import Offer, OfferApproval, OfferNegotiationLog


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    """Admin for Offer model."""

    list_display = [
        'offer_id',
        'application',
        'title',
        'status',
        'version',
        'start_date',
        'expiration_date',
        'sent_at',
        'created_at',
    ]
    list_filter = ['status', 'salary_currency', 'salary_frequency', 'created_at']
    search_fields = [
        'offer_id',
        'title',
        'application__candidate__user__email',
        'application__candidate__user__first_name',
        'application__candidate__user__last_name',
    ]
    readonly_fields = [
        'offer_id',
        'version',
        'sent_at',
        'viewed_at',
        'responded_at',
        'created_at',
        'updated_at',
    ]
    raw_id_fields = ['application', 'level', 'department', 'reporting_to']
    fieldsets = (
        (
            'Basic Information',
            {
                'fields': (
                    'offer_id',
                    'application',
                    'version',
                    'status',
                )
            },
        ),
        (
            'Position Details',
            {
                'fields': (
                    'title',
                    'level',
                    'department',
                    'reporting_to',
                )
            },
        ),
        (
            'Compensation',
            {
                'fields': (
                    'base_salary',
                    'salary_currency',
                    'salary_frequency',
                    'bonus',
                    'equity',
                    'sign_on_bonus',
                    'relocation',
                )
            },
        ),
        (
            'Dates',
            {
                'fields': (
                    'start_date',
                    'expiration_date',
                )
            },
        ),
        (
            'Documents & Notes',
            {
                'fields': (
                    'offer_letter_pdf',
                    'notes',
                )
            },
        ),
        (
            'Tracking',
            {
                'fields': (
                    'sent_at',
                    'viewed_at',
                    'responded_at',
                    'decline_reason',
                    'esignature_envelope_id',
                )
            },
        ),
        (
            'Metadata',
            {
                'fields': (
                    'created_by',
                    'created_at',
                    'updated_at',
                )
            },
        ),
    )


@admin.register(OfferApproval)
class OfferApprovalAdmin(admin.ModelAdmin):
    """Admin for OfferApproval model."""

    list_display = [
        'offer',
        'approver',
        'order',
        'status',
        'decided_at',
        'created_at',
    ]
    list_filter = ['status', 'decided_at', 'created_at']
    search_fields = [
        'offer__offer_id',
        'approver__user__email',
        'approver__user__first_name',
        'approver__user__last_name',
        'comments',
    ]
    readonly_fields = ['decided_at', 'created_at', 'updated_at']
    raw_id_fields = ['offer', 'approver']
    ordering = ['offer', 'order']


@admin.register(OfferNegotiationLog)
class OfferNegotiationLogAdmin(admin.ModelAdmin):
    """Admin for OfferNegotiationLog model."""

    list_display = [
        'offer',
        'logged_by',
        'outcome',
        'created_at',
    ]
    list_filter = ['outcome', 'created_at']
    search_fields = [
        'offer__offer_id',
        'logged_by__user__email',
        'candidate_request',
        'internal_response',
    ]
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['offer', 'logged_by']
    ordering = ['-created_at']

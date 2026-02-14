"""Admin configuration for applications app."""

from django.contrib import admin

from .models import Application, ApplicationEvent, CandidateNote, RejectionReason, Tag


class ApplicationEventInline(admin.TabularInline):
    model = ApplicationEvent
    extra = 0
    readonly_fields = [
        'event_type', 'actor', 'from_stage', 'to_stage',
        'metadata', 'created_at',
    ]


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'application_id', 'candidate', 'requisition',
        'status', 'current_stage', 'source', 'applied_at',
    ]
    list_filter = ['status', 'source']
    search_fields = [
        'application_id',
        'candidate__user__email',
        'candidate__user__first_name',
    ]
    raw_id_fields = ['candidate', 'requisition', 'current_stage', 'referrer']
    readonly_fields = ['application_id']
    inlines = [ApplicationEventInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color']
    search_fields = ['name']


@admin.register(RejectionReason)
class RejectionReasonAdmin(admin.ModelAdmin):
    list_display = ['label', 'is_active']
    list_filter = ['is_active']


@admin.register(CandidateNote)
class CandidateNoteAdmin(admin.ModelAdmin):
    list_display = ['application', 'author', 'is_private', 'created_at']
    list_filter = ['is_private']
    raw_id_fields = ['application', 'author']

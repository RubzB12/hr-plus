"""Admin configuration for jobs app."""

from django.contrib import admin

from .models import PipelineStage, Requisition, RequisitionApproval


class PipelineStageInline(admin.TabularInline):
    model = PipelineStage
    extra = 0
    ordering = ['order']


class RequisitionApprovalInline(admin.TabularInline):
    model = RequisitionApproval
    extra = 0
    ordering = ['order']
    readonly_fields = ['decided_at']


@admin.register(Requisition)
class RequisitionAdmin(admin.ModelAdmin):
    list_display = [
        'requisition_id', 'title', 'status', 'department',
        'recruiter', 'headcount', 'filled_count', 'created_at',
    ]
    list_filter = ['status', 'employment_type', 'remote_policy', 'department']
    search_fields = ['requisition_id', 'title']
    raw_id_fields = [
        'hiring_manager', 'recruiter', 'created_by',
        'department', 'team', 'location', 'level',
    ]
    inlines = [PipelineStageInline, RequisitionApprovalInline]
    readonly_fields = ['requisition_id', 'slug', 'version']


@admin.register(RequisitionApproval)
class RequisitionApprovalAdmin(admin.ModelAdmin):
    list_display = ['requisition', 'approver', 'order', 'status', 'decided_at']
    list_filter = ['status']
    raw_id_fields = ['requisition', 'approver']
    readonly_fields = ['decided_at']

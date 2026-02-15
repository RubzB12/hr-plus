"""Django admin for onboarding app."""

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    OnboardingDocument,
    OnboardingForm,
    OnboardingPlan,
    OnboardingTask,
    OnboardingTemplate,
)


@admin.register(OnboardingTemplate)
class OnboardingTemplateAdmin(admin.ModelAdmin):
    """Admin for OnboardingTemplate model."""

    list_display = [
        'name',
        'department',
        'job_level',
        'is_active',
        'task_count',
        'created_at',
    ]
    list_filter = ['is_active', 'department', 'job_level', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        (
            None,
            {
                'fields': (
                    'id',
                    'name',
                    'description',
                    'department',
                    'job_level',
                    'is_active',
                )
            },
        ),
        ('Configuration', {'fields': ('tasks', 'required_documents', 'forms')}),
        ('Metadata', {'fields': ('created_at', 'updated_at')}),
    )

    def task_count(self, obj):
        """Display number of tasks in template."""
        return len(obj.tasks) if obj.tasks else 0

    task_count.short_description = 'Tasks'


class OnboardingTaskInline(admin.TabularInline):
    """Inline admin for OnboardingTask."""

    model = OnboardingTask
    extra = 0
    readonly_fields = ['completed_at', 'completed_by']
    fields = [
        'title',
        'category',
        'assigned_to',
        'due_date',
        'status',
        'completed_at',
        'order',
    ]
    ordering = ['order', 'due_date']


class OnboardingDocumentInline(admin.TabularInline):
    """Inline admin for OnboardingDocument."""

    model = OnboardingDocument
    extra = 0
    readonly_fields = ['uploaded_at', 'uploaded_by', 'reviewed_at', 'reviewed_by']
    fields = ['document_type', 'status', 'uploaded_by', 'uploaded_at', 'reviewed_by']


class OnboardingFormInline(admin.TabularInline):
    """Inline admin for OnboardingForm."""

    model = OnboardingForm
    extra = 0
    readonly_fields = ['submitted_at', 'submitted_by']
    fields = ['form_type', 'submitted_at', 'submitted_by']


@admin.register(OnboardingPlan)
class OnboardingPlanAdmin(admin.ModelAdmin):
    """Admin for OnboardingPlan model."""

    list_display = [
        'candidate_name',
        'job_title',
        'start_date',
        'status_badge',
        'progress_display',
        'buddy',
        'hr_contact',
        'created_at',
    ]
    list_filter = ['status', 'start_date', 'created_at']
    search_fields = [
        'application__candidate__user__first_name',
        'application__candidate__user__last_name',
        'application__candidate__user__email',
        'application__requisition__title',
    ]
    readonly_fields = [
        'id',
        'access_token',
        'completed_at',
        'progress_percentage',
        'is_overdue',
        'created_at',
        'updated_at',
    ]
    fieldsets = (
        (
            None,
            {
                'fields': (
                    'id',
                    'application',
                    'offer',
                    'template',
                    'status',
                    'start_date',
                )
            },
        ),
        ('Team', {'fields': ('buddy', 'hr_contact')}),
        (
            'Portal Access',
            {
                'fields': ('access_token',),
                'description': 'Share this token with the candidate to access their onboarding portal',
            },
        ),
        (
            'Progress',
            {'fields': ('progress_percentage', 'is_overdue', 'completed_at', 'notes')},
        ),
        ('Metadata', {'fields': ('created_at', 'updated_at')}),
    )
    inlines = [OnboardingTaskInline, OnboardingDocumentInline, OnboardingFormInline]

    def candidate_name(self, obj):
        """Display candidate name."""
        return obj.application.candidate.user.get_full_name()

    candidate_name.short_description = 'Candidate'
    candidate_name.admin_order_field = 'application__candidate__user__last_name'

    def job_title(self, obj):
        """Display job title."""
        return obj.application.requisition.title

    job_title.short_description = 'Position'
    job_title.admin_order_field = 'application__requisition__title'

    def status_badge(self, obj):
        """Display status with color badge."""
        colors = {
            'pending': 'gray',
            'in_progress': 'blue',
            'completed': 'green',
            'cancelled': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = 'Status'

    def progress_display(self, obj):
        """Display progress percentage."""
        percentage = obj.progress_percentage
        color = 'green' if percentage == 100 else 'orange' if percentage >= 50 else 'red'
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; color: white; text-align: center; border-radius: 3px; padding: 2px;">{:}%</div>'
            '</div>',
            percentage,
            color,
            percentage,
        )

    progress_display.short_description = 'Progress'


@admin.register(OnboardingTask)
class OnboardingTaskAdmin(admin.ModelAdmin):
    """Admin for OnboardingTask model."""

    list_display = [
        'title',
        'plan_candidate',
        'category',
        'assigned_to',
        'due_date',
        'status_badge',
        'overdue_badge',
    ]
    list_filter = ['status', 'category', 'due_date', 'created_at']
    search_fields = [
        'title',
        'description',
        'plan__application__candidate__user__first_name',
        'plan__application__candidate__user__last_name',
    ]
    readonly_fields = ['id', 'completed_at', 'completed_by', 'created_at', 'updated_at']
    fieldsets = (
        (
            None,
            {
                'fields': (
                    'id',
                    'plan',
                    'title',
                    'description',
                    'category',
                    'assigned_to',
                    'due_date',
                    'status',
                    'order',
                )
            },
        ),
        ('Completion', {'fields': ('completed_at', 'completed_by', 'notes')}),
        ('Metadata', {'fields': ('created_at', 'updated_at')}),
    )

    def plan_candidate(self, obj):
        """Display candidate name from plan."""
        return obj.plan.application.candidate.user.get_full_name()

    plan_candidate.short_description = 'Candidate'

    def status_badge(self, obj):
        """Display status with color badge."""
        colors = {
            'pending': 'gray',
            'in_progress': 'blue',
            'completed': 'green',
            'skipped': 'orange',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = 'Status'

    def overdue_badge(self, obj):
        """Display overdue badge if task is overdue."""
        from django.utils import timezone

        if obj.status in ['completed', 'skipped']:
            return '-'
        if obj.due_date and obj.due_date < timezone.now().date():
            return format_html(
                '<span style="background-color: red; color: white; padding: 3px 10px; border-radius: 3px;">OVERDUE</span>'
            )
        return '-'

    overdue_badge.short_description = 'Overdue?'


@admin.register(OnboardingDocument)
class OnboardingDocumentAdmin(admin.ModelAdmin):
    """Admin for OnboardingDocument model."""

    list_display = [
        'document_type_display',
        'plan_candidate',
        'status_badge',
        'uploaded_at',
        'uploaded_by',
        'reviewed_by',
    ]
    list_filter = ['status', 'document_type', 'uploaded_at', 'reviewed_at']
    search_fields = [
        'plan__application__candidate__user__first_name',
        'plan__application__candidate__user__last_name',
    ]
    readonly_fields = [
        'id',
        'uploaded_at',
        'uploaded_by',
        'reviewed_at',
        'reviewed_by',
        'created_at',
    ]
    fieldsets = (
        (
            None,
            {'fields': ('id', 'plan', 'document_type', 'file', 'status')},
        ),
        ('Upload Info', {'fields': ('uploaded_by', 'uploaded_at')}),
        (
            'Review Info',
            {'fields': ('reviewed_by', 'reviewed_at', 'rejection_reason', 'notes')},
        ),
        ('Metadata', {'fields': ('created_at',)}),
    )

    def document_type_display(self, obj):
        """Display document type."""
        return obj.get_document_type_display()

    document_type_display.short_description = 'Document Type'

    def plan_candidate(self, obj):
        """Display candidate name from plan."""
        return obj.plan.application.candidate.user.get_full_name()

    plan_candidate.short_description = 'Candidate'

    def status_badge(self, obj):
        """Display status with color badge."""
        colors = {
            'pending': 'gray',
            'uploaded': 'blue',
            'reviewed': 'orange',
            'approved': 'green',
            'rejected': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = 'Status'


@admin.register(OnboardingForm)
class OnboardingFormAdmin(admin.ModelAdmin):
    """Admin for OnboardingForm model."""

    list_display = [
        'form_type_display',
        'plan_candidate',
        'is_submitted',
        'submitted_at',
        'submitted_by',
    ]
    list_filter = ['form_type', 'submitted_at']
    search_fields = [
        'plan__application__candidate__user__first_name',
        'plan__application__candidate__user__last_name',
    ]
    readonly_fields = ['id', 'submitted_at', 'submitted_by', 'created_at']
    fieldsets = (
        (None, {'fields': ('id', 'plan', 'form_type', 'data')}),
        ('Submission', {'fields': ('submitted_by', 'submitted_at')}),
        ('Metadata', {'fields': ('created_at',)}),
    )

    def form_type_display(self, obj):
        """Display form type."""
        return obj.get_form_type_display()

    form_type_display.short_description = 'Form Type'

    def plan_candidate(self, obj):
        """Display candidate name from plan."""
        return obj.plan.application.candidate.user.get_full_name()

    plan_candidate.short_description = 'Candidate'

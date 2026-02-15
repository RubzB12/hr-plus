"""Onboarding services for HR-Plus."""

import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from rest_framework.exceptions import NotFound

from apps.accounts.models import InternalUser
from apps.applications.models import Application
from apps.core.exceptions import BusinessValidationError
from apps.offers.models import Offer

from .models import (
    OnboardingDocument,
    OnboardingForm,
    OnboardingPlan,
    OnboardingTask,
    OnboardingTemplate,
)


class OnboardingService:
    """Service for managing onboarding plans and tasks."""

    @staticmethod
    @transaction.atomic
    def create_plan_from_offer(offer: Offer, *, start_date, template=None) -> OnboardingPlan:
        """
        Create onboarding plan when offer is accepted.

        Auto-selects template based on department/level if not provided.
        Generates access token for candidate portal.
        """
        if offer.status != 'accepted':
            raise BusinessValidationError('Onboarding can only be created for accepted offers')

        # Check if plan already exists
        if hasattr(offer, 'onboarding_plan'):
            return offer.onboarding_plan

        # Auto-select template if not provided
        if not template:
            template = OnboardingService._select_template(offer.application)

        # Generate secure access token
        access_token = secrets.token_urlsafe(32)

        # Create plan
        plan = OnboardingPlan.objects.create(
            application=offer.application,
            offer=offer,
            template=template,
            start_date=start_date,
            access_token=access_token,
            status='pending',
        )

        # Create tasks from template
        if template and template.tasks:
            OnboardingService._create_tasks_from_template(plan, template)

        # Create required documents from template
        if template and template.required_documents:
            OnboardingService._create_documents_from_template(plan, template)

        # Create forms from template
        if template and template.forms:
            OnboardingService._create_forms_from_template(plan, template)

        # Send welcome email
        from apps.communications.services import EmailService

        EmailService.send_onboarding_welcome(plan)

        return plan

    @staticmethod
    def _select_template(application: Application) -> OnboardingTemplate | None:
        """Auto-select best matching template for application."""
        requisition = application.requisition

        # Try exact match: department + job level
        template = OnboardingTemplate.objects.filter(
            is_active=True, department=requisition.department, job_level=requisition.level
        ).first()

        if template:
            return template

        # Try department only
        template = OnboardingTemplate.objects.filter(
            is_active=True, department=requisition.department, job_level__isnull=True
        ).first()

        if template:
            return template

        # Try job level only
        template = OnboardingTemplate.objects.filter(
            is_active=True, department__isnull=True, job_level=requisition.level
        ).first()

        if template:
            return template

        # Use default template (no department or level specified)
        return OnboardingTemplate.objects.filter(
            is_active=True, department__isnull=True, job_level__isnull=True
        ).first()

    @staticmethod
    def _create_tasks_from_template(plan: OnboardingPlan, template: OnboardingTemplate):
        """Create tasks from template configuration."""
        for idx, task_data in enumerate(template.tasks):
            # Calculate due date based on days_offset from start date
            days_offset = task_data.get('days_offset', 0)
            due_date = plan.start_date + timedelta(days=days_offset)

            # Determine who should be assigned
            assigned_to = None
            if task_data.get('assigned_to') == 'candidate':
                assigned_to = plan.application.candidate.user
            elif task_data.get('assigned_to') == 'buddy' and plan.buddy:
                assigned_to = plan.buddy.user
            elif task_data.get('assigned_to') == 'hr' and plan.hr_contact:
                assigned_to = plan.hr_contact.user

            OnboardingTask.objects.create(
                plan=plan,
                title=task_data.get('title', ''),
                description=task_data.get('description', ''),
                category=task_data.get('category', 'other'),
                assigned_to=assigned_to,
                due_date=due_date,
                order=idx,
            )

    @staticmethod
    def _create_documents_from_template(plan: OnboardingPlan, template: OnboardingTemplate):
        """Create document placeholders from template."""
        for doc_type in template.required_documents:
            OnboardingDocument.objects.create(
                plan=plan, document_type=doc_type, status='pending'
            )

    @staticmethod
    def _create_forms_from_template(plan: OnboardingPlan, template: OnboardingTemplate):
        """Create form placeholders from template."""
        for form_type in template.forms:
            OnboardingForm.objects.create(plan=plan, form_type=form_type)

    @staticmethod
    @transaction.atomic
    def complete_task(task: OnboardingTask, *, completed_by) -> OnboardingTask:
        """Mark task as completed and update plan progress."""
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.completed_by = completed_by
        task.save(update_fields=['status', 'completed_at', 'completed_by', 'updated_at'])

        # Check if all tasks are complete
        plan = task.plan
        if not plan.tasks.exclude(status='completed').exists():
            OnboardingService.complete_plan(plan)

        return task

    @staticmethod
    @transaction.atomic
    def complete_plan(plan: OnboardingPlan) -> OnboardingPlan:
        """Mark onboarding plan as completed."""
        plan.status = 'completed'
        plan.completed_at = timezone.now()
        plan.save(update_fields=['status', 'completed_at', 'updated_at'])

        # Send completion notification
        from apps.communications.services import EmailService

        EmailService.send_onboarding_completed(plan)

        return plan

    @staticmethod
    @transaction.atomic
    def upload_document(
        plan: OnboardingPlan, *, document_type: str, file, uploaded_by
    ) -> OnboardingDocument:
        """Upload a required document."""
        # Get or create document record
        document, created = OnboardingDocument.objects.get_or_create(
            plan=plan,
            document_type=document_type,
            defaults={'status': 'pending'},
        )

        document.file = file
        document.status = 'uploaded'
        document.uploaded_at = timezone.now()
        document.uploaded_by = uploaded_by
        document.save()

        # Notify HR of upload
        from apps.communications.services import NotificationService

        if plan.hr_contact:
            NotificationService.create_notification(
                recipient=plan.hr_contact.user,
                notification_type='onboarding_document_uploaded',
                title='New Onboarding Document Uploaded',
                body=f'{plan.application.candidate.user.get_full_name()} uploaded {document.get_document_type_display()}',
                link=f'/onboarding/plans/{plan.id}/documents',
                metadata={'document_id': str(document.id), 'document_type': document.document_type},
            )

        return document

    @staticmethod
    @transaction.atomic
    def submit_form(
        plan: OnboardingPlan, *, form_type: str, data: dict, submitted_by
    ) -> OnboardingForm:
        """Submit onboarding form data."""
        try:
            form = OnboardingForm.objects.get(plan=plan, form_type=form_type)
        except OnboardingForm.DoesNotExist:
            # Create form if it doesn't exist
            form = OnboardingForm.objects.create(plan=plan, form_type=form_type)

        form.data = data
        form.submitted_at = timezone.now()
        form.submitted_by = submitted_by
        form.save()

        return form

    @staticmethod
    def assign_buddy(plan: OnboardingPlan, *, buddy: InternalUser) -> OnboardingPlan:
        """Assign a buddy/mentor to help with onboarding."""
        plan.buddy = buddy
        plan.save(update_fields=['buddy', 'updated_at'])

        # Notify buddy
        from apps.communications.services import NotificationService

        NotificationService.create_notification(
            recipient=buddy.user,
            notification_type='onboarding_buddy_assigned',
            title='You\'ve Been Assigned as an Onboarding Buddy',
            body=f'You are now the onboarding buddy for {plan.application.candidate.user.get_full_name()}',
            link=f'/onboarding/plans/{plan.id}',
            metadata={'plan_id': str(plan.id)},
        )

        return plan

    @staticmethod
    def assign_hr_contact(plan: OnboardingPlan, *, hr_contact: InternalUser) -> OnboardingPlan:
        """Assign HR contact for onboarding questions."""
        plan.hr_contact = hr_contact
        plan.save(update_fields=['hr_contact', 'updated_at'])

        return plan

    @staticmethod
    @transaction.atomic
    def update_start_date(plan: OnboardingPlan, *, new_start_date) -> OnboardingPlan:
        """
        Update start date and recalculate all task due dates.
        """
        old_start_date = plan.start_date
        date_diff = (new_start_date - old_start_date).days

        plan.start_date = new_start_date
        plan.save(update_fields=['start_date', 'updated_at'])

        # Adjust task due dates
        for task in plan.tasks.all():
            if task.due_date:
                task.due_date = task.due_date + timedelta(days=date_diff)
                task.save(update_fields=['due_date', 'updated_at'])

        return plan

    @staticmethod
    def get_plan_by_token(access_token: str) -> OnboardingPlan:
        """Get onboarding plan by access token (for candidate portal)."""
        try:
            return OnboardingPlan.objects.select_related(
                'application__candidate__user',
                'application__requisition',
                'offer',
                'template',
                'buddy__user',
                'hr_contact__user',
            ).prefetch_related('tasks', 'documents', 'forms').get(access_token=access_token)
        except OnboardingPlan.DoesNotExist:
            raise NotFound('Invalid onboarding access token')

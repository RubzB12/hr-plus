"""Tests for onboarding services."""

import secrets
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from apps.accounts.tests.factories import InternalUserFactory
from apps.core.exceptions import BusinessValidationError
from apps.offers.tests.factories import OfferFactory
from apps.onboarding.models import OnboardingDocument, OnboardingForm, OnboardingPlan, OnboardingTask
from apps.onboarding.services import OnboardingService

from .factories import (
    OnboardingPlanFactory,
    OnboardingTaskFactory,
    OnboardingTemplateFactory,
)


@pytest.mark.django_db
class TestCreatePlanFromOffer:
    """Tests for OnboardingService.create_plan_from_offer."""

    @patch('apps.communications.services.EmailService.send_onboarding_welcome')
    def test_create_plan_success(self, mock_email):
        """Test successful plan creation from accepted offer."""
        offer = OfferFactory(status='accepted')
        start_date = timezone.now().date() + timedelta(days=14)
        template = OnboardingTemplateFactory()

        plan = OnboardingService.create_plan_from_offer(
            offer, start_date=start_date, template=template
        )

        assert plan.id is not None
        assert plan.application == offer.application
        assert plan.offer == offer
        assert plan.template == template
        assert plan.start_date == start_date
        assert plan.status == 'pending'
        assert len(plan.access_token) > 0

        # Verify email was sent
        mock_email.assert_called_once_with(plan)

    def test_create_plan_rejected_offer(self):
        """Test that plan cannot be created for non-accepted offer."""
        offer = OfferFactory(status='pending')
        start_date = timezone.now().date() + timedelta(days=14)

        with pytest.raises(BusinessValidationError, match='only be created for accepted offers'):
            OnboardingService.create_plan_from_offer(offer, start_date=start_date)

    @patch('apps.communications.services.EmailService.send_onboarding_welcome')
    def test_create_plan_duplicate(self, mock_email):
        """Test that duplicate plans are not created."""
        offer = OfferFactory(status='accepted')
        start_date = timezone.now().date() + timedelta(days=14)

        # Create first plan
        plan1 = OnboardingService.create_plan_from_offer(offer, start_date=start_date)

        # Attempting to create second plan should return existing plan
        plan2 = OnboardingService.create_plan_from_offer(offer, start_date=start_date)

        assert plan1.id == plan2.id
        # Email should only be sent once
        assert mock_email.call_count == 1

    @patch('apps.communications.services.EmailService.send_onboarding_welcome')
    def test_create_plan_auto_selects_template(self, mock_email):
        """Test that template is auto-selected if not provided."""
        offer = OfferFactory(status='accepted')
        start_date = timezone.now().date() + timedelta(days=14)

        # Create template matching offer's department and job level
        template = OnboardingTemplateFactory(
            department=offer.application.requisition.department,
            job_level=offer.application.requisition.level,
        )

        plan = OnboardingService.create_plan_from_offer(offer, start_date=start_date)

        assert plan.template == template

    @patch('apps.communications.services.EmailService.send_onboarding_welcome')
    def test_create_plan_creates_tasks_from_template(self, mock_email):
        """Test that tasks are created from template."""
        offer = OfferFactory(status='accepted')
        start_date = timezone.now().date() + timedelta(days=14)
        template = OnboardingTemplateFactory(
            tasks=[
                {
                    'title': 'Task 1',
                    'description': 'First task',
                    'category': 'admin',
                    'days_offset': 0,
                    'assigned_to': 'candidate',
                },
                {
                    'title': 'Task 2',
                    'description': 'Second task',
                    'category': 'equipment',
                    'days_offset': 1,
                    'assigned_to': 'hr',
                },
            ]
        )

        plan = OnboardingService.create_plan_from_offer(
            offer, start_date=start_date, template=template
        )

        tasks = plan.tasks.all()
        assert tasks.count() == 2
        assert tasks[0].title == 'Task 1'
        assert tasks[0].due_date == start_date
        assert tasks[1].title == 'Task 2'
        assert tasks[1].due_date == start_date + timedelta(days=1)

    @patch('apps.communications.services.EmailService.send_onboarding_welcome')
    def test_create_plan_creates_documents_from_template(self, mock_email):
        """Test that document placeholders are created from template."""
        offer = OfferFactory(status='accepted')
        start_date = timezone.now().date() + timedelta(days=14)
        template = OnboardingTemplateFactory(required_documents=['i9', 'w4', 'direct_deposit'])

        plan = OnboardingService.create_plan_from_offer(
            offer, start_date=start_date, template=template
        )

        documents = plan.documents.all()
        assert documents.count() == 3
        assert documents.filter(document_type='i9').exists()
        assert documents.filter(document_type='w4').exists()
        assert documents.filter(document_type='direct_deposit').exists()

    @patch('apps.communications.services.EmailService.send_onboarding_welcome')
    def test_create_plan_creates_forms_from_template(self, mock_email):
        """Test that form placeholders are created from template."""
        offer = OfferFactory(status='accepted')
        start_date = timezone.now().date() + timedelta(days=14)
        template = OnboardingTemplateFactory(
            forms=['equipment_preferences', 'emergency_contact']
        )

        plan = OnboardingService.create_plan_from_offer(
            offer, start_date=start_date, template=template
        )

        forms = plan.forms.all()
        assert forms.count() == 2
        assert forms.filter(form_type='equipment_preferences').exists()
        assert forms.filter(form_type='emergency_contact').exists()


@pytest.mark.django_db
class TestCompleteTask:
    """Tests for OnboardingService.complete_task."""

    def test_complete_task_success(self):
        """Test marking task as completed."""
        task = OnboardingTaskFactory(status='pending')
        user = task.plan.application.candidate.user

        completed_task = OnboardingService.complete_task(task, completed_by=user)

        assert completed_task.status == 'completed'
        assert completed_task.completed_at is not None
        assert completed_task.completed_by == user

    @patch('apps.communications.services.EmailService.send_onboarding_completed')
    def test_complete_task_auto_completes_plan(self, mock_email):
        """Test that plan is auto-completed when all tasks are done."""
        plan = OnboardingPlanFactory()
        task1 = OnboardingTaskFactory(plan=plan, status='completed')
        task2 = OnboardingTaskFactory(plan=plan, status='pending')
        user = plan.application.candidate.user

        # Complete the last pending task
        OnboardingService.complete_task(task2, completed_by=user)

        # Plan should be auto-completed
        plan.refresh_from_db()
        assert plan.status == 'completed'
        assert plan.completed_at is not None

        # Completion email should be sent
        mock_email.assert_called_once_with(plan)


@pytest.mark.django_db
class TestCompletePlan:
    """Tests for OnboardingService.complete_plan."""

    @patch('apps.communications.services.EmailService.send_onboarding_completed')
    def test_complete_plan(self, mock_email):
        """Test marking plan as completed."""
        plan = OnboardingPlanFactory(status='in_progress')

        completed_plan = OnboardingService.complete_plan(plan)

        assert completed_plan.status == 'completed'
        assert completed_plan.completed_at is not None

        # Email should be sent
        mock_email.assert_called_once_with(plan)


@pytest.mark.django_db
class TestUploadDocument:
    """Tests for OnboardingService.upload_document."""

    @patch('apps.communications.services.NotificationService.create_notification')
    def test_upload_document_new(self, mock_notification):
        """Test uploading a new document."""
        plan = OnboardingPlanFactory()
        mock_file = SimpleUploadedFile('i9_form.pdf', b'file_content', content_type='application/pdf')
        user = plan.application.candidate.user

        document = OnboardingService.upload_document(
            plan, document_type='i9', file=mock_file, uploaded_by=user
        )

        assert document.plan == plan
        assert document.document_type == 'i9'
        assert document.status == 'uploaded'
        assert document.uploaded_by == user
        assert document.uploaded_at is not None

        # Notification should be sent to HR contact
        if plan.hr_contact:
            mock_notification.assert_called_once()

    @patch('apps.communications.services.NotificationService.create_notification')
    def test_upload_document_replace(self, mock_notification):
        """Test replacing an existing document."""
        plan = OnboardingPlanFactory()
        existing_doc = OnboardingDocument.objects.create(
            plan=plan, document_type='i9', status='pending'
        )
        mock_file = SimpleUploadedFile('i9_form_v2.pdf', b'file_content_v2', content_type='application/pdf')
        user = plan.application.candidate.user

        document = OnboardingService.upload_document(
            plan, document_type='i9', file=mock_file, uploaded_by=user
        )

        # Should be same document, just updated
        assert document.id == existing_doc.id
        assert document.status == 'uploaded'
        assert document.uploaded_by == user


@pytest.mark.django_db
class TestSubmitForm:
    """Tests for OnboardingService.submit_form."""

    def test_submit_form_existing(self):
        """Test submitting data for existing form."""
        plan = OnboardingPlanFactory()
        existing_form = OnboardingForm.objects.create(
            plan=plan, form_type='equipment_preferences', data={}
        )
        user = plan.application.candidate.user
        form_data = {'laptop': 'MacBook Pro', 'monitor': '27 inch'}

        form = OnboardingService.submit_form(
            plan, form_type='equipment_preferences', data=form_data, submitted_by=user
        )

        assert form.id == existing_form.id
        assert form.data == form_data
        assert form.submitted_by == user
        assert form.submitted_at is not None

    def test_submit_form_creates_if_not_exists(self):
        """Test that form is created if it doesn't exist."""
        plan = OnboardingPlanFactory()
        user = plan.application.candidate.user
        form_data = {'laptop': 'MacBook Pro'}

        form = OnboardingService.submit_form(
            plan, form_type='equipment_preferences', data=form_data, submitted_by=user
        )

        assert form.plan == plan
        assert form.form_type == 'equipment_preferences'
        assert form.data == form_data
        assert form.submitted_by == user


@pytest.mark.django_db
class TestAssignBuddy:
    """Tests for OnboardingService.assign_buddy."""

    @patch('apps.communications.services.NotificationService.create_notification')
    def test_assign_buddy(self, mock_notification):
        """Test assigning a buddy to onboarding plan."""
        plan = OnboardingPlanFactory(buddy=None)
        buddy = InternalUserFactory()

        updated_plan = OnboardingService.assign_buddy(plan, buddy=buddy)

        assert updated_plan.buddy == buddy

        # Notification should be sent to buddy
        mock_notification.assert_called_once()


@pytest.mark.django_db
class TestUpdateStartDate:
    """Tests for OnboardingService.update_start_date."""

    def test_update_start_date(self):
        """Test updating start date and recalculating task due dates."""
        old_start_date = timezone.now().date() + timedelta(days=14)
        plan = OnboardingPlanFactory(start_date=old_start_date)

        # Create tasks with due dates relative to old start date
        task1 = OnboardingTaskFactory(plan=plan, due_date=old_start_date)
        task2 = OnboardingTaskFactory(plan=plan, due_date=old_start_date + timedelta(days=7))

        # Update start date to 7 days earlier
        new_start_date = old_start_date - timedelta(days=7)
        updated_plan = OnboardingService.update_start_date(plan, new_start_date=new_start_date)

        assert updated_plan.start_date == new_start_date

        # Task due dates should be adjusted
        task1.refresh_from_db()
        task2.refresh_from_db()
        assert task1.due_date == new_start_date
        assert task2.due_date == new_start_date + timedelta(days=7)


@pytest.mark.django_db
class TestGetPlanByToken:
    """Tests for OnboardingService.get_plan_by_token."""

    def test_get_plan_by_token_success(self):
        """Test retrieving plan by access token."""
        plan = OnboardingPlanFactory()

        retrieved_plan = OnboardingService.get_plan_by_token(plan.access_token)

        assert retrieved_plan.id == plan.id

    def test_get_plan_by_token_invalid(self):
        """Test that invalid token raises error."""
        from rest_framework.exceptions import NotFound

        with pytest.raises(NotFound, match='Invalid onboarding access token'):
            OnboardingService.get_plan_by_token('invalid-token')

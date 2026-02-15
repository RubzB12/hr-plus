"""Tests for onboarding views."""

from datetime import timedelta
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.tests.factories import InternalUserFactory
from apps.onboarding.models import OnboardingDocument, OnboardingForm, OnboardingTask

from .factories import (
    OnboardingDocumentFactory,
    OnboardingFormFactory,
    OnboardingPlanFactory,
    OnboardingTaskFactory,
    OnboardingTemplateFactory,
)


@pytest.fixture
def api_client():
    """Fixture for API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client):
    """Fixture for authenticated API client."""
    user = InternalUserFactory()
    api_client.force_authenticate(user=user.user)
    return api_client


@pytest.mark.django_db
class TestOnboardingPortalView:
    """Tests for candidate portal - OnboardingPortalView."""

    def test_get_plan_by_token_success(self, api_client):
        """Test retrieving onboarding plan by access token."""
        plan = OnboardingPlanFactory()

        url = reverse('onboarding-portal', kwargs={'token': plan.access_token})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(plan.id)
        assert 'tasks' in response.data
        assert 'documents' in response.data
        assert 'forms' in response.data

    def test_get_plan_invalid_token(self, api_client):
        """Test that invalid token returns 404."""
        url = reverse('onboarding-portal', kwargs={'token': 'invalid-token'})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unauthenticated_access_allowed(self, api_client):
        """Test that candidate portal allows unauthenticated access."""
        plan = OnboardingPlanFactory()

        # No authentication required
        url = reverse('onboarding-portal', kwargs={'token': plan.access_token})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestOnboardingPortalTasksView:
    """Tests for candidate portal - OnboardingPortalTasksView."""

    def test_get_tasks(self, api_client):
        """Test retrieving tasks for a plan."""
        plan = OnboardingPlanFactory()
        OnboardingTaskFactory.create_batch(3, plan=plan)

        url = reverse('onboarding-portal-tasks', kwargs={'token': plan.access_token})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3

    def test_get_tasks_invalid_token(self, api_client):
        """Test that invalid token returns 404."""
        url = reverse('onboarding-portal-tasks', kwargs={'token': 'invalid-token'})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestOnboardingPortalTaskCompleteView:
    """Tests for candidate portal - OnboardingPortalTaskCompleteView."""

    @patch('apps.onboarding.services.OnboardingService.complete_task')
    def test_complete_task_success(self, mock_complete, api_client):
        """Test marking task as complete."""
        plan = OnboardingPlanFactory()
        task = OnboardingTaskFactory(plan=plan, status='pending')
        mock_complete.return_value = task

        url = reverse(
            'onboarding-portal-task-complete',
            kwargs={'token': plan.access_token, 'task_id': task.id},
        )
        response = api_client.post(url, {'notes': 'Completed successfully'})

        assert response.status_code == status.HTTP_200_OK
        mock_complete.assert_called_once()

    def test_complete_task_invalid_token(self, api_client):
        """Test that invalid token returns 404."""
        task = OnboardingTaskFactory()

        url = reverse(
            'onboarding-portal-task-complete',
            kwargs={'token': 'invalid-token', 'task_id': task.id},
        )
        response = api_client.post(url, {})

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_complete_task_not_in_plan(self, api_client):
        """Test completing task that doesn't belong to plan."""
        plan = OnboardingPlanFactory()
        other_task = OnboardingTaskFactory()  # Different plan

        url = reverse(
            'onboarding-portal-task-complete',
            kwargs={'token': plan.access_token, 'task_id': other_task.id},
        )
        response = api_client.post(url, {})

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestOnboardingPortalDocumentUploadView:
    """Tests for candidate portal - OnboardingPortalDocumentUploadView."""

    @patch('apps.onboarding.services.OnboardingService.upload_document')
    def test_upload_document_success(self, mock_upload, api_client):
        """Test uploading a document."""
        plan = OnboardingPlanFactory()
        document = OnboardingDocumentFactory(plan=plan)
        mock_upload.return_value = document

        # Create mock file
        mock_file = SimpleUploadedFile('test.pdf', b'file_content', content_type='application/pdf')

        url = reverse('onboarding-portal-document-upload', kwargs={'token': plan.access_token})
        response = api_client.post(
            url, {'document_type': 'i9', 'file': mock_file}, format='multipart'
        )

        assert response.status_code == status.HTTP_201_CREATED
        mock_upload.assert_called_once()

    def test_upload_document_missing_file(self, api_client):
        """Test that missing file returns validation error."""
        plan = OnboardingPlanFactory()

        url = reverse('onboarding-portal-document-upload', kwargs={'token': plan.access_token})
        response = api_client.post(url, {'document_type': 'i9'})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_upload_document_invalid_token(self, api_client):
        """Test that invalid token returns 404."""
        mock_file = SimpleUploadedFile('test.pdf', b'file_content', content_type='application/pdf')

        url = reverse('onboarding-portal-document-upload', kwargs={'token': 'invalid-token'})
        response = api_client.post(
            url, {'document_type': 'i9', 'file': mock_file}, format='multipart'
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestOnboardingPortalFormSubmitView:
    """Tests for candidate portal - OnboardingPortalFormSubmitView."""

    @patch('apps.onboarding.services.OnboardingService.submit_form')
    def test_submit_form_success(self, mock_submit, api_client):
        """Test submitting a form."""
        plan = OnboardingPlanFactory()
        form = OnboardingFormFactory(plan=plan)
        mock_submit.return_value = form

        url = reverse('onboarding-portal-form-submit', kwargs={'token': plan.access_token})
        response = api_client.post(
            url,
            {'form_type': 'equipment_preferences', 'data': {'laptop': 'MacBook Pro'}},
            format='json',
        )

        assert response.status_code == status.HTTP_201_CREATED
        mock_submit.assert_called_once()

    def test_submit_form_invalid_data(self, api_client):
        """Test that invalid data returns validation error."""
        plan = OnboardingPlanFactory()

        url = reverse('onboarding-portal-form-submit', kwargs={'token': plan.access_token})
        response = api_client.post(url, {'form_type': 'equipment_preferences'}, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestOnboardingPlanViewSet:
    """Tests for internal management - OnboardingPlanViewSet."""

    def test_list_plans_requires_auth(self, api_client):
        """Test that listing plans requires authentication."""
        url = reverse('onboardingplan-list')
        response = api_client.get(url)

        # Returns 403 because IsInternalUser requires both authentication and internal user status
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_list_plans(self, authenticated_client):
        """Test listing onboarding plans."""
        OnboardingPlanFactory.create_batch(3)

        url = reverse('onboardingplan-list')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3

    def test_retrieve_plan(self, authenticated_client):
        """Test retrieving a specific plan."""
        plan = OnboardingPlanFactory()

        url = reverse('onboardingplan-detail', kwargs={'pk': plan.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(plan.id)

    def test_filter_by_status(self, authenticated_client):
        """Test filtering plans by status."""
        OnboardingPlanFactory.create_batch(2, status='pending')
        OnboardingPlanFactory.create_batch(3, status='in_progress')

        url = reverse('onboardingplan-list')
        response = authenticated_client.get(url, {'status': 'in_progress'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3

    @patch('apps.onboarding.services.OnboardingService.assign_buddy')
    def test_assign_buddy(self, mock_assign, authenticated_client):
        """Test assigning a buddy to a plan."""
        plan = OnboardingPlanFactory()
        buddy = InternalUserFactory()
        mock_assign.return_value = plan

        url = reverse('onboardingplan-assign-buddy', kwargs={'pk': plan.id})
        response = authenticated_client.post(url, {'buddy_id': str(buddy.id)})

        assert response.status_code == status.HTTP_200_OK
        mock_assign.assert_called_once()

    @patch('apps.onboarding.services.OnboardingService.update_start_date')
    def test_update_start_date(self, mock_update, authenticated_client):
        """Test updating plan start date."""
        plan = OnboardingPlanFactory()
        new_date = timezone.now().date() + timedelta(days=30)
        mock_update.return_value = plan

        url = reverse('onboardingplan-update-start-date', kwargs={'pk': plan.id})
        response = authenticated_client.post(url, {'start_date': new_date})

        assert response.status_code == status.HTTP_200_OK
        mock_update.assert_called_once()


@pytest.mark.django_db
class TestOnboardingTaskViewSet:
    """Tests for internal management - OnboardingTaskViewSet."""

    def test_list_tasks_requires_auth(self, api_client):
        """Test that listing tasks requires authentication."""
        url = reverse('onboardingtask-list')
        response = api_client.get(url)

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_list_tasks(self, authenticated_client):
        """Test listing onboarding tasks."""
        OnboardingTaskFactory.create_batch(5)

        url = reverse('onboardingtask-list')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5

    def test_filter_by_plan(self, authenticated_client):
        """Test filtering tasks by plan."""
        plan = OnboardingPlanFactory()
        OnboardingTaskFactory.create_batch(3, plan=plan)
        OnboardingTaskFactory.create_batch(2)  # Different plans

        url = reverse('onboardingtask-list')
        response = authenticated_client.get(url, {'plan': plan.id})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3

    def test_filter_by_status(self, authenticated_client):
        """Test filtering tasks by status."""
        OnboardingTaskFactory.create_batch(2, status='pending')
        OnboardingTaskFactory.create_batch(3, status='completed')

        url = reverse('onboardingtask-list')
        response = authenticated_client.get(url, {'status': 'completed'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3

    def test_update_task(self, authenticated_client):
        """Test updating a task."""
        task = OnboardingTaskFactory(status='pending')

        url = reverse('onboardingtask-detail', kwargs={'pk': task.id})
        response = authenticated_client.patch(url, {'status': 'in_progress'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'in_progress'


@pytest.mark.django_db
class TestOnboardingDocumentViewSet:
    """Tests for internal management - OnboardingDocumentViewSet."""

    def test_list_documents_requires_auth(self, api_client):
        """Test that listing documents requires authentication."""
        url = reverse('onboardingdocument-list')
        response = api_client.get(url)

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_list_documents(self, authenticated_client):
        """Test listing onboarding documents."""
        OnboardingDocumentFactory.create_batch(4)

        url = reverse('onboardingdocument-list')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 4

    def test_filter_by_plan(self, authenticated_client):
        """Test filtering documents by plan."""
        plan = OnboardingPlanFactory()
        OnboardingDocumentFactory.create_batch(2, plan=plan)
        OnboardingDocumentFactory.create_batch(3)  # Different plans

        url = reverse('onboardingdocument-list')
        response = authenticated_client.get(url, {'plan': plan.id})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2

    def test_approve_document(self, authenticated_client):
        """Test approving a document."""
        document = OnboardingDocumentFactory(status='uploaded')

        url = reverse('onboardingdocument-approve', kwargs={'pk': document.id})
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK

        # Verify document was updated
        document.refresh_from_db()
        assert document.status == 'approved'
        assert document.reviewed_by is not None
        assert document.reviewed_at is not None

    def test_reject_document(self, authenticated_client):
        """Test rejecting a document."""
        document = OnboardingDocumentFactory(status='uploaded')

        url = reverse('onboardingdocument-reject', kwargs={'pk': document.id})
        response = authenticated_client.post(url, {'reason': 'Document is unclear'})

        assert response.status_code == status.HTTP_200_OK

        # Verify document was updated
        document.refresh_from_db()
        assert document.status == 'rejected'
        assert document.reviewed_by is not None
        assert document.rejection_reason == 'Document is unclear'


@pytest.mark.django_db
class TestOnboardingTemplateViewSet:
    """Tests for internal management - OnboardingTemplateViewSet."""

    def test_list_templates_requires_auth(self, api_client):
        """Test that listing templates requires authentication."""
        url = reverse('onboardingtemplate-list')
        response = api_client.get(url)

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_list_templates(self, authenticated_client):
        """Test listing onboarding templates."""
        OnboardingTemplateFactory.create_batch(3)

        url = reverse('onboardingtemplate-list')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3

    def test_create_template(self, authenticated_client):
        """Test creating an onboarding template."""
        url = reverse('onboardingtemplate-list')
        response = authenticated_client.post(
            url,
            {
                'name': 'New Template',
                'description': 'Test template',
                'is_active': True,
                'tasks': [],
                'required_documents': [],
                'forms': [],
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Template'

    def test_update_template(self, authenticated_client):
        """Test updating a template."""
        template = OnboardingTemplateFactory()

        url = reverse('onboardingtemplate-detail', kwargs={'pk': template.id})
        response = authenticated_client.patch(url, {'is_active': False})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_active'] is False

    def test_delete_template(self, authenticated_client):
        """Test deleting a template."""
        template = OnboardingTemplateFactory()

        url = reverse('onboardingtemplate-detail', kwargs={'pk': template.id})
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

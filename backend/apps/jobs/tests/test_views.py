"""Tests for jobs API views."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import InternalUserFactory

from .factories import (
    PipelineStageFactory,
    PublishedRequisitionFactory,
    RequisitionApprovalFactory,
    RequisitionFactory,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def internal_client():
    client = APIClient()
    internal = InternalUserFactory()
    client.force_authenticate(user=internal.user)
    return client, internal


# --- Public endpoint tests ---

@pytest.mark.django_db
class TestPublicJobList:
    def test_returns_only_published_jobs(self, api_client):
        PublishedRequisitionFactory(title='Published Job')
        RequisitionFactory(title='Draft Job', status='draft')

        response = api_client.get(reverse('public-job-list'))

        assert response.status_code == 200
        titles = [j['title'] for j in response.data['results']]
        assert 'Published Job' in titles
        assert 'Draft Job' not in titles

    def test_filter_by_employment_type(self, api_client):
        PublishedRequisitionFactory(
            title='Contract Role', employment_type='contract',
        )
        PublishedRequisitionFactory(
            title='Full-time Role', employment_type='full_time',
        )

        response = api_client.get(
            reverse('public-job-list'), {'employment_type': 'contract'},
        )

        assert response.status_code == 200
        titles = [j['title'] for j in response.data['results']]
        assert 'Contract Role' in titles
        assert 'Full-time Role' not in titles

    def test_filter_by_remote_policy(self, api_client):
        PublishedRequisitionFactory(
            title='Remote Job', remote_policy='remote',
        )
        PublishedRequisitionFactory(
            title='Onsite Job', remote_policy='onsite',
        )

        response = api_client.get(
            reverse('public-job-list'), {'remote_policy': 'remote'},
        )

        assert response.status_code == 200
        titles = [j['title'] for j in response.data['results']]
        assert 'Remote Job' in titles
        assert 'Onsite Job' not in titles

    def test_no_auth_required(self, api_client):
        response = api_client.get(reverse('public-job-list'))
        assert response.status_code == 200


@pytest.mark.django_db
class TestPublicJobDetail:
    def test_get_published_job_by_slug(self, api_client):
        job = PublishedRequisitionFactory(title='Senior Engineer')

        response = api_client.get(
            reverse('public-job-detail', kwargs={'slug': job.slug}),
        )

        assert response.status_code == 200
        assert response.data['title'] == 'Senior Engineer'
        assert 'description' in response.data

    def test_draft_job_returns_404(self, api_client):
        job = RequisitionFactory(title='Draft Role', status='draft')

        response = api_client.get(
            reverse('public-job-detail', kwargs={'slug': job.slug}),
        )

        assert response.status_code == 404


@pytest.mark.django_db
class TestPublicJobCategories:
    def test_returns_departments_with_counts(self, api_client):
        from apps.accounts.tests.factories import DepartmentFactory

        eng = DepartmentFactory(name='Engineering')
        PublishedRequisitionFactory(department=eng)
        PublishedRequisitionFactory(department=eng)

        response = api_client.get(reverse('public-job-categories'))

        assert response.status_code == 200
        eng_cat = next(
            c for c in response.data
            if c['department__name'] == 'Engineering'
        )
        assert eng_cat['job_count'] == 2


# --- Internal requisition tests ---

@pytest.mark.django_db
class TestRequisitionViewSet:
    def test_list_requires_auth(self, api_client):
        response = api_client.get(reverse('requisition-list'))
        assert response.status_code == 403

    def test_list_requires_internal_user(self, api_client):
        from apps.accounts.tests.factories import UserFactory

        user = UserFactory(is_internal=False)
        api_client.force_authenticate(user=user)
        response = api_client.get(reverse('requisition-list'))
        assert response.status_code == 403

    def test_list_returns_requisitions(self, internal_client):
        client, _internal = internal_client
        RequisitionFactory()

        response = client.get(reverse('requisition-list'))

        assert response.status_code == 200
        assert response.data['count'] >= 1

    def test_publish_action(self, internal_client):
        client, _internal = internal_client
        req = RequisitionFactory(status='approved')

        response = client.post(
            reverse('requisition-publish', kwargs={'pk': str(req.id)}),
        )

        assert response.status_code == 200
        assert response.data['status'] == 'open'
        assert response.data['published_at'] is not None

    def test_publish_draft_fails(self, internal_client):
        client, _internal = internal_client
        req = RequisitionFactory(status='draft')

        response = client.post(
            reverse('requisition-publish', kwargs={'pk': str(req.id)}),
        )

        assert response.status_code == 400

    def test_cancel_action(self, internal_client):
        client, _internal = internal_client
        req = PublishedRequisitionFactory()

        response = client.post(
            reverse('requisition-cancel', kwargs={'pk': str(req.id)}),
        )

        assert response.status_code == 200
        assert response.data['status'] == 'cancelled'

    def test_hold_and_reopen_flow(self, internal_client):
        client, _internal = internal_client
        req = PublishedRequisitionFactory()

        # Put on hold
        response = client.post(
            reverse('requisition-hold', kwargs={'pk': str(req.id)}),
        )
        assert response.status_code == 200
        assert response.data['status'] == 'on_hold'

        # Reopen
        response = client.post(
            reverse('requisition-reopen', kwargs={'pk': str(req.id)}),
        )
        assert response.status_code == 200
        assert response.data['status'] == 'open'

    def test_submit_for_approval(self, internal_client):
        client, internal = internal_client
        req = RequisitionFactory(status='draft')
        approver = InternalUserFactory()

        response = client.post(
            reverse('requisition-submit', kwargs={'pk': str(req.id)}),
            {'approver_ids': [str(approver.id)]},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['status'] == 'pending_approval'
        assert len(response.data['approvals']) == 1

    def test_approve_action(self, internal_client):
        client, internal = internal_client
        req = RequisitionFactory(status='pending_approval')
        RequisitionApprovalFactory(
            requisition=req, approver=internal, order=0,
        )

        response = client.post(
            reverse('requisition-approve-action', kwargs={'pk': str(req.id)}),
            {'comments': 'Approved!'},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['status'] == 'approved'

    def test_reject_action(self, internal_client):
        client, internal = internal_client
        req = RequisitionFactory(status='pending_approval')
        RequisitionApprovalFactory(
            requisition=req, approver=internal, order=0,
        )

        response = client.post(
            reverse('requisition-reject-action', kwargs={'pk': str(req.id)}),
            {'comments': 'Needs work'},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['status'] == 'draft'

    def test_clone_action(self, internal_client):
        client, internal = internal_client
        req = PublishedRequisitionFactory()
        PipelineStageFactory(requisition=req, order=0)

        response = client.post(
            reverse('requisition-clone', kwargs={'pk': str(req.id)}),
        )

        assert response.status_code == 201
        assert response.data['status'] == 'draft'
        assert response.data['requisition_id'] != req.requisition_id


@pytest.mark.django_db
class TestPendingApprovalsView:
    def test_list_pending_approvals(self, internal_client):
        client, internal = internal_client
        req = RequisitionFactory(status='pending_approval')
        RequisitionApprovalFactory(
            requisition=req, approver=internal, order=0,
        )
        # Another user's approval should not appear
        RequisitionApprovalFactory()

        response = client.get(reverse('pending-approvals'))

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['requisition']['requisition_id'] == req.requisition_id

    def test_pending_approvals_requires_auth(self, api_client):
        response = api_client.get(reverse('pending-approvals'))
        assert response.status_code == 403

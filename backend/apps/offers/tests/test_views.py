"""Tests for offers API views."""


import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.tests.factories import InternalUserFactory, UserFactory
from apps.applications.tests.factories import ApplicationFactory
from apps.offers.models import Offer
from apps.offers.tests.factories import OfferApprovalFactory, OfferFactory


@pytest.fixture
def api_client():
    """API client fixture."""
    return APIClient()


@pytest.fixture
def authenticated_user():
    """Create authenticated internal user."""
    user = UserFactory()
    internal_user = InternalUserFactory(user=user)
    return user, internal_user


@pytest.fixture
def authenticated_client(api_client, authenticated_user):
    """API client with authenticated user."""
    user, internal_user = authenticated_user
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
class TestOfferViewSet:
    """Tests for OfferViewSet."""

    def test_list_offers_requires_auth(self, api_client):
        """Unauthenticated requests are rejected."""
        response = api_client.get(reverse('offer-list'))
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_list_offers_success(self, authenticated_client):
        """Authenticated users can list offers."""
        OfferFactory.create_batch(3)

        response = authenticated_client.get(reverse('offer-list'))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

    def test_create_offer_success(self, authenticated_client, authenticated_user):
        """Create offer with valid data."""
        user, internal_user = authenticated_user
        application = ApplicationFactory()

        payload = {
            'application': application.id,
            'title': 'Senior Software Engineer',
            'level': application.requisition.level.id,
            'department': application.requisition.department.id,
            'base_salary_input': '120000.00',
            'salary_currency': 'USD',
            'salary_frequency': 'annual',
            'bonus_input': '10000.00',
            'equity': '1000 stock options',
            'sign_on_bonus_input': '5000.00',
            'relocation_input': '10000.00',
            'start_date': '2026-03-15',
            'expiration_date': '2026-02-28',
            'notes': 'Test offer',
        }

        response = authenticated_client.post(reverse('offer-list'), payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'Senior Software Engineer'
        assert response.data['status'] == 'draft'
        assert response.data['version'] == 1

        # Verify offer was created
        offer = Offer.objects.get(id=response.data['id'])
        assert offer.created_by == internal_user

    def test_submit_for_approval_success(self, authenticated_client):
        """Submit offer for approval with approvers."""
        offer = OfferFactory(status='draft')
        approvers = InternalUserFactory.create_batch(2)

        url = reverse('offer-submit-for-approval', args=[offer.id])
        # Convert UUIDs to strings for JSON serialization
        payload = {'approvers': [str(approver.pk) for approver in approvers]}

        response = authenticated_client.post(url, payload, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'pending_approval'

        offer.refresh_from_db()
        assert offer.approvals.count() == 2

    def test_submit_for_approval_requires_approvers(self, authenticated_client):
        """Submitting without approvers fails."""
        offer = OfferFactory(status='draft')

        url = reverse('offer-submit-for-approval', args=[offer.id])
        payload = {'approvers': []}

        response = authenticated_client.post(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_send_to_candidate_success(self, authenticated_client):
        """Send approved offer to candidate."""
        offer = OfferFactory(status='approved')

        url = reverse('offer-send-to-candidate', args=[offer.id])
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'sent'
        assert response.data['sent_at'] is not None

    def test_withdraw_offer_success(self, authenticated_client):
        """Withdraw offer."""
        offer = OfferFactory(status='sent')

        url = reverse('offer-withdraw', args=[offer.id])
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'withdrawn'

    def test_create_revision_success(self, authenticated_client):
        """Create new version of offer."""
        offer = OfferFactory(version=1)

        url = reverse('offer-create-revision', args=[offer.id])
        payload = {
            'base_salary_input': '130000.00',
            'bonus_input': '15000.00',
            'title': 'Staff Software Engineer',
        }

        response = authenticated_client.post(url, payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['version'] == 2
        assert response.data['title'] == 'Staff Software Engineer'
        assert response.data['offer_id'] == offer.offer_id


@pytest.mark.django_db
class TestOfferApprovalViewSet:
    """Tests for OfferApprovalViewSet."""

    def test_approve_success(self, authenticated_client):
        """Approve pending approval."""
        approval = OfferApprovalFactory(status='pending')

        url = reverse('offerapproval-approve', args=[approval.id])
        payload = {'comments': 'Approved - looks good'}

        response = authenticated_client.post(url, payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'approved'
        assert response.data['comments'] == 'Approved - looks good'

    def test_reject_success(self, authenticated_client):
        """Reject pending approval."""
        approval = OfferApprovalFactory(status='pending')

        url = reverse('offerapproval-reject', args=[approval.id])
        payload = {'comments': 'Salary exceeds budget'}

        response = authenticated_client.post(url, payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'rejected'
        assert response.data['comments'] == 'Salary exceeds budget'

    def test_reject_requires_comments(self, authenticated_client):
        """Rejection without comments fails."""
        approval = OfferApprovalFactory(status='pending')

        url = reverse('offerapproval-reject', args=[approval.id])
        payload = {'comments': ''}

        response = authenticated_client.post(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCandidateOfferViews:
    """Tests for candidate-facing offer views."""

    def test_candidate_view_offer_success(self, api_client):
        """Candidate can view offer via token."""
        offer = OfferFactory(status='sent')

        url = reverse(
            'candidate-view-offer', args=[offer.offer_id, 'dummy-token']
        )
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['offer_id'] == offer.offer_id
        assert 'base_salary_display' in response.data

        # Verify status changed to viewed
        offer.refresh_from_db()
        assert offer.status == 'viewed'
        assert offer.viewed_at is not None

    def test_candidate_view_offer_not_found(self, api_client):
        """Non-existent offer returns 404."""
        url = reverse(
            'candidate-view-offer', args=['OFR-2026-999', 'dummy-token']
        )
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_candidate_accept_offer_success(self, api_client):
        """Candidate accepts offer."""
        offer = OfferFactory(status='sent')

        url = reverse(
            'candidate-accept-offer', args=[offer.offer_id, 'dummy-token']
        )
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'accepted'

        offer.refresh_from_db()
        assert offer.status == 'accepted'
        assert offer.responded_at is not None

    def test_candidate_decline_offer_success(self, api_client):
        """Candidate declines offer."""
        offer = OfferFactory(status='viewed')

        url = reverse(
            'candidate-decline-offer', args=[offer.offer_id, 'dummy-token']
        )
        payload = {'reason': 'Accepted another position'}
        response = api_client.post(url, payload, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'declined'

        offer.refresh_from_db()
        assert offer.status == 'declined'
        assert offer.decline_reason == 'Accepted another position'

    def test_candidate_cannot_accept_withdrawn_offer(self, api_client):
        """Cannot accept withdrawn offer."""
        offer = OfferFactory(status='withdrawn')

        url = reverse(
            'candidate-accept-offer', args=[offer.offer_id, 'dummy-token']
        )
        response = api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

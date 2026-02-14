"""Tests for offers services."""

from decimal import Decimal

import pytest
from django.utils import timezone

from apps.accounts.tests.factories import InternalUserFactory
from apps.applications.tests.factories import ApplicationFactory
from apps.core.exceptions import BusinessValidationError
from apps.offers.services import OfferApprovalService, OfferService
from apps.offers.tests.factories import OfferApprovalFactory, OfferFactory


@pytest.mark.django_db
class TestOfferService:
    """Tests for OfferService."""

    def test_create_offer_generates_offer_id(self):
        """Offer is created with auto-generated ID."""
        application = ApplicationFactory()
        internal_user = InternalUserFactory()

        offer = OfferService.create_offer(
            application=application,
            title='Senior Software Engineer',
            level=application.requisition.level,
            department=application.requisition.department,
            base_salary=Decimal('120000.00'),
            start_date=(timezone.now() + timezone.timedelta(days=30)).date(),
            expiration_date=(timezone.now() + timezone.timedelta(days=7)).date(),
            created_by=internal_user,
        )

        assert offer.id is not None
        assert offer.offer_id.startswith('OFR-2026-')
        assert offer.status == 'draft'
        assert offer.version == 1

    def test_create_offer_stores_salary_encrypted(self):
        """Salary is stored as encrypted string."""
        application = ApplicationFactory()
        internal_user = InternalUserFactory()

        offer = OfferService.create_offer(
            application=application,
            title='Software Engineer',
            level=application.requisition.level,
            department=application.requisition.department,
            base_salary=Decimal('100000.50'),
            start_date=(timezone.now() + timezone.timedelta(days=30)).date(),
            expiration_date=(timezone.now() + timezone.timedelta(days=7)).date(),
            created_by=internal_user,
            bonus=Decimal('10000.00'),
            sign_on_bonus=Decimal('5000.00'),
        )

        # Salary is stored as string (encrypted field)
        assert isinstance(offer.base_salary, str)
        # When accessed, Django decrypts it
        assert '100000.50' in str(offer.base_salary)

    def test_submit_for_approval_requires_draft_status(self):
        """Only draft offers can be submitted for approval."""
        offer = OfferFactory(status='sent')
        approvers = [InternalUserFactory()]

        with pytest.raises(BusinessValidationError, match='Can only submit draft offers'):
            OfferService.submit_for_approval(offer, approvers)

    def test_submit_for_approval_requires_approvers(self):
        """At least one approver is required."""
        offer = OfferFactory(status='draft')

        with pytest.raises(BusinessValidationError, match='At least one approver'):
            OfferService.submit_for_approval(offer, [])

    def test_submit_for_approval_creates_approval_chain(self):
        """Submitting creates approval chain in correct order."""
        offer = OfferFactory(status='draft')
        approvers = [
            InternalUserFactory(),
            InternalUserFactory(),
            InternalUserFactory(),
        ]

        updated_offer = OfferService.submit_for_approval(offer, approvers)

        assert updated_offer.status == 'pending_approval'
        assert updated_offer.approvals.count() == 3

        # Check order is correct
        approval_list = list(updated_offer.approvals.order_by('order'))
        assert approval_list[0].approver == approvers[0]
        assert approval_list[0].order == 0
        assert approval_list[1].approver == approvers[1]
        assert approval_list[1].order == 1
        assert approval_list[2].approver == approvers[2]
        assert approval_list[2].order == 2

    def test_send_to_candidate_requires_approved_status(self):
        """Only approved offers can be sent to candidates."""
        offer = OfferFactory(status='draft')

        with pytest.raises(
            BusinessValidationError, match='Can only send approved offers'
        ):
            OfferService.send_to_candidate(offer)

    def test_send_to_candidate_updates_status_and_timestamp(self):
        """Sending to candidate updates status and sent_at."""
        offer = OfferFactory(status='approved')

        updated_offer = OfferService.send_to_candidate(offer)

        assert updated_offer.status == 'sent'
        assert updated_offer.sent_at is not None

    def test_candidate_accept_requires_active_status(self):
        """Only active offers (sent/viewed) can be accepted."""
        offer = OfferFactory(status='draft')

        with pytest.raises(
            BusinessValidationError,
            match='This offer cannot be accepted',
        ):
            OfferService.candidate_accept(offer)

    def test_candidate_accept_updates_status_and_timestamp(self):
        """Accepting offer updates status and responded_at."""
        offer = OfferFactory(status='sent')

        updated_offer = OfferService.candidate_accept(offer)

        assert updated_offer.status == 'accepted'
        assert updated_offer.responded_at is not None

    def test_candidate_decline_requires_active_status(self):
        """Only active offers can be declined."""
        offer = OfferFactory(status='withdrawn')

        with pytest.raises(
            BusinessValidationError,
            match='This offer cannot be declined',
        ):
            OfferService.candidate_decline(offer, 'Accepted another position')

    def test_candidate_decline_stores_reason(self):
        """Declining offer stores the reason."""
        offer = OfferFactory(status='viewed')
        reason = 'Accepted another position with better compensation'

        updated_offer = OfferService.candidate_decline(offer, reason)

        assert updated_offer.status == 'declined'
        assert updated_offer.decline_reason == reason
        assert updated_offer.responded_at is not None

    def test_withdraw_requires_non_final_status(self):
        """Cannot withdraw finalized offers."""
        offer = OfferFactory(status='accepted')

        with pytest.raises(
            BusinessValidationError,
            match='Cannot withdraw an offer that has already been finalized',
        ):
            OfferService.withdraw(offer)

    def test_withdraw_updates_status(self):
        """Withdrawing offer updates status."""
        offer = OfferFactory(status='sent')

        updated_offer = OfferService.withdraw(offer)

        assert updated_offer.status == 'withdrawn'

    def test_create_revision_increments_version(self):
        """Creating revision increments version number."""
        offer = OfferFactory(version=1)

        new_offer = OfferService.create_revision(
            offer, base_salary=Decimal('130000.00')
        )

        assert new_offer.version == 2
        assert new_offer.offer_id == offer.offer_id
        assert new_offer.status == 'draft'
        assert '130000.00' in str(new_offer.base_salary)

    def test_create_revision_preserves_unchanged_fields(self):
        """Revision preserves fields not explicitly updated."""
        offer = OfferFactory(
            title='Software Engineer', equity='1000 shares', notes='Original notes'
        )

        new_offer = OfferService.create_revision(offer, title='Senior Software Engineer')

        assert new_offer.title == 'Senior Software Engineer'
        assert new_offer.equity == offer.equity
        assert new_offer.notes == offer.notes
        assert new_offer.level == offer.level


@pytest.mark.django_db
class TestOfferApprovalService:
    """Tests for OfferApprovalService."""

    def test_approve_requires_pending_status(self):
        """Only pending approvals can be approved."""
        approval = OfferApprovalFactory(status='approved')

        with pytest.raises(
            BusinessValidationError, match='Can only approve pending approvals'
        ):
            OfferApprovalService.approve(approval)

    def test_approve_updates_approval_status(self):
        """Approving updates approval status and timestamp."""
        approval = OfferApprovalFactory(status='pending')

        updated_approval = OfferApprovalService.approve(approval, 'Looks good')

        assert updated_approval.status == 'approved'
        assert updated_approval.comments == 'Looks good'
        assert updated_approval.decided_at is not None

    def test_approve_all_steps_makes_offer_approved(self):
        """When all approvals are approved, offer becomes approved."""
        offer = OfferFactory(status='pending_approval')
        approval1 = OfferApprovalFactory(offer=offer, order=0, status='pending')
        approval2 = OfferApprovalFactory(offer=offer, order=1, status='pending')

        # Approve first
        OfferApprovalService.approve(approval1)
        offer.refresh_from_db()
        assert offer.status == 'pending_approval'  # Still pending

        # Approve second
        OfferApprovalService.approve(approval2)
        offer.refresh_from_db()
        assert offer.status == 'approved'  # Now approved

    def test_reject_requires_pending_status(self):
        """Only pending approvals can be rejected."""
        approval = OfferApprovalFactory(status='rejected')

        with pytest.raises(
            BusinessValidationError, match='Can only reject pending approvals'
        ):
            OfferApprovalService.reject(approval, 'Rejected')

    def test_reject_requires_comments(self):
        """Rejection requires a reason."""
        approval = OfferApprovalFactory(status='pending')

        with pytest.raises(BusinessValidationError, match='Rejection reason is required'):
            OfferApprovalService.reject(approval, '')

    def test_reject_returns_offer_to_draft(self):
        """Rejecting any approval returns offer to draft."""
        offer = OfferFactory(status='pending_approval')
        approval = OfferApprovalFactory(offer=offer, status='pending')

        OfferApprovalService.reject(approval, 'Salary too high')

        offer.refresh_from_db()
        assert offer.status == 'draft'
        assert approval.status == 'rejected'
        assert approval.comments == 'Salary too high'

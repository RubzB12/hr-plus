"""Tests for RequisitionService."""

import pytest

from apps.accounts.tests.factories import InternalUserFactory
from apps.core.exceptions import BusinessValidationError
from apps.jobs.models import PipelineStage
from apps.jobs.services import RequisitionService

from .factories import PipelineStageFactory, PublishedRequisitionFactory, RequisitionFactory


@pytest.mark.django_db
class TestRequisitionService:
    def test_create_requisition_generates_id(self):
        req = RequisitionFactory()
        data = {
            'title': 'Software Engineer',
            'department': req.department,
            'hiring_manager': req.hiring_manager,
            'recruiter': req.recruiter,
            'employment_type': 'full_time',
            'level': req.level,
            'location': req.location,
            'remote_policy': 'hybrid',
            'description': 'Build things.',
        }
        result = RequisitionService.create_requisition(
            data=data, created_by=req.created_by,
        )
        assert result.requisition_id.startswith('REQ-')
        assert result.status == 'draft'

    def test_create_requisition_creates_default_pipeline(self):
        req = RequisitionFactory()
        data = {
            'title': 'Designer',
            'department': req.department,
            'hiring_manager': req.hiring_manager,
            'recruiter': req.recruiter,
            'employment_type': 'full_time',
            'level': req.level,
            'location': req.location,
            'remote_policy': 'remote',
            'description': 'Design things.',
        }
        result = RequisitionService.create_requisition(
            data=data, created_by=req.created_by,
        )
        stages = PipelineStage.objects.filter(requisition=result).order_by('order')
        assert stages.count() == 7
        assert stages.first().name == 'Applied'
        assert stages.last().name == 'Hired'

    def test_publish_sets_status_and_timestamps(self):
        req = RequisitionFactory(status='approved')
        result = RequisitionService.publish(req)
        assert result.status == 'open'
        assert result.published_at is not None
        assert result.opened_at is not None

    def test_publish_rejects_draft(self):
        req = RequisitionFactory(status='draft')
        with pytest.raises(BusinessValidationError, match='approved'):
            RequisitionService.publish(req)

    def test_put_on_hold(self):
        req = PublishedRequisitionFactory()
        result = RequisitionService.put_on_hold(req)
        assert result.status == 'on_hold'

    def test_put_on_hold_rejects_non_open(self):
        req = RequisitionFactory(status='draft')
        with pytest.raises(BusinessValidationError, match='open'):
            RequisitionService.put_on_hold(req)

    def test_cancel_sets_closed_at(self):
        req = PublishedRequisitionFactory()
        result = RequisitionService.cancel(req)
        assert result.status == 'cancelled'
        assert result.closed_at is not None

    def test_cancel_rejects_already_cancelled(self):
        req = RequisitionFactory(status='cancelled')
        with pytest.raises(BusinessValidationError, match='already'):
            RequisitionService.cancel(req)

    def test_reopen_from_on_hold(self):
        req = RequisitionFactory(status='on_hold')
        result = RequisitionService.reopen(req)
        assert result.status == 'open'
        assert result.closed_at is None
        assert result.version == 2

    def test_reopen_rejects_open(self):
        req = PublishedRequisitionFactory()
        with pytest.raises(BusinessValidationError, match='on-hold or cancelled'):
            RequisitionService.reopen(req)


@pytest.mark.django_db
class TestApprovalWorkflow:
    def test_submit_for_approval(self):
        req = RequisitionFactory(status='draft')
        approvers = [InternalUserFactory(), InternalUserFactory()]

        result = RequisitionService.submit_for_approval(req, approvers)

        assert result.status == 'pending_approval'
        assert result.approvals.count() == 2
        assert result.approvals.first().approver == approvers[0]
        assert result.approvals.last().approver == approvers[1]

    def test_submit_requires_draft_status(self):
        req = RequisitionFactory(status='open')
        with pytest.raises(BusinessValidationError, match='draft'):
            RequisitionService.submit_for_approval(req, [InternalUserFactory()])

    def test_submit_requires_approvers(self):
        req = RequisitionFactory(status='draft')
        with pytest.raises(BusinessValidationError, match='approver'):
            RequisitionService.submit_for_approval(req, [])

    def test_approve_single_approver(self):
        req = RequisitionFactory(status='draft')
        approver = InternalUserFactory()
        RequisitionService.submit_for_approval(req, [approver])

        result = RequisitionService.approve(req, approver, comments='Looks good')

        assert result.status == 'approved'
        approval = result.approvals.first()
        assert approval.status == 'approved'
        assert approval.comments == 'Looks good'
        assert approval.decided_at is not None

    def test_approve_chain_partial(self):
        req = RequisitionFactory(status='draft')
        approver1 = InternalUserFactory()
        approver2 = InternalUserFactory()
        RequisitionService.submit_for_approval(req, [approver1, approver2])

        result = RequisitionService.approve(req, approver1)

        # Still pending because approver2 hasn't approved
        assert result.status == 'pending_approval'

    def test_approve_chain_complete(self):
        req = RequisitionFactory(status='draft')
        approver1 = InternalUserFactory()
        approver2 = InternalUserFactory()
        RequisitionService.submit_for_approval(req, [approver1, approver2])

        RequisitionService.approve(req, approver1)
        result = RequisitionService.approve(req, approver2)

        assert result.status == 'approved'

    def test_approve_wrong_approver(self):
        req = RequisitionFactory(status='draft')
        approver = InternalUserFactory()
        outsider = InternalUserFactory()
        RequisitionService.submit_for_approval(req, [approver])

        with pytest.raises(BusinessValidationError, match='not a pending approver'):
            RequisitionService.approve(req, outsider)

    def test_reject_returns_to_draft(self):
        req = RequisitionFactory(status='draft')
        approver1 = InternalUserFactory()
        approver2 = InternalUserFactory()
        RequisitionService.submit_for_approval(req, [approver1, approver2])

        result = RequisitionService.reject_approval(req, approver1, 'Needs revision')

        assert result.status == 'draft'
        # Rejecting approver is rejected
        a1 = result.approvals.get(approver=approver1)
        assert a1.status == 'rejected'
        assert a1.comments == 'Needs revision'
        # Remaining approver is skipped
        a2 = result.approvals.get(approver=approver2)
        assert a2.status == 'skipped'

    def test_reject_wrong_approver(self):
        req = RequisitionFactory(status='draft')
        approver = InternalUserFactory()
        outsider = InternalUserFactory()
        RequisitionService.submit_for_approval(req, [approver])

        with pytest.raises(BusinessValidationError, match='not a pending approver'):
            RequisitionService.reject_approval(req, outsider)

    def test_full_lifecycle_with_approval(self):
        """Test: draft → pending_approval → approved → open → cancelled."""
        req = RequisitionFactory(status='draft')
        approver = InternalUserFactory()

        RequisitionService.submit_for_approval(req, [approver])
        assert req.status == 'pending_approval'

        RequisitionService.approve(req, approver)
        assert req.status == 'approved'

        RequisitionService.publish(req)
        assert req.status == 'open'
        assert req.published_at is not None

        RequisitionService.cancel(req)
        assert req.status == 'cancelled'


@pytest.mark.django_db
class TestCloneRequisition:
    def test_clone_creates_draft_copy(self):
        req = PublishedRequisitionFactory()
        PipelineStageFactory(requisition=req, name='Applied', order=0)
        PipelineStageFactory(requisition=req, name='Interview', order=1)
        cloner = InternalUserFactory()

        clone = RequisitionService.clone(req, created_by=cloner)

        assert clone.id != req.id
        assert clone.requisition_id != req.requisition_id
        assert clone.title == req.title
        assert clone.status == 'draft'
        assert clone.created_by == cloner
        assert clone.published_at is None
        assert clone.opened_at is None

    def test_clone_copies_pipeline_stages(self):
        req = RequisitionFactory()
        PipelineStageFactory(requisition=req, name='Applied', order=0)
        PipelineStageFactory(requisition=req, name='Interview', order=1)
        PipelineStageFactory(requisition=req, name='Offer', order=2)

        clone = RequisitionService.clone(req, created_by=req.created_by)

        assert clone.stages.count() == 3
        stage_names = list(clone.stages.order_by('order').values_list('name', flat=True))
        assert stage_names == ['Applied', 'Interview', 'Offer']

    def test_clone_does_not_copy_approvals(self):
        req = RequisitionFactory(status='draft')
        approver = InternalUserFactory()
        RequisitionService.submit_for_approval(req, [approver])

        clone = RequisitionService.clone(req, created_by=req.created_by)

        assert clone.approvals.count() == 0

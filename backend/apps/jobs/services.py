"""Business logic for requisitions and job listings."""

from datetime import datetime

from django.db import transaction
from django.utils import timezone

from apps.core.exceptions import BusinessValidationError

from .models import PipelineStage, Requisition, RequisitionApproval

DEFAULT_PIPELINE = [
    ('Applied', 'application'),
    ('Screening', 'screening'),
    ('Phone Screen', 'phone_screen'),
    ('Interview', 'interview'),
    ('Assessment', 'assessment'),
    ('Offer', 'offer'),
    ('Hired', 'hired'),
]


class RequisitionService:
    """Manages requisition lifecycle."""

    @staticmethod
    def _generate_requisition_id() -> str:
        year = datetime.now().year
        last = (
            Requisition.objects
            .filter(requisition_id__startswith=f'REQ-{year}-')
            .order_by('-requisition_id')
            .values_list('requisition_id', flat=True)
            .first()
        )
        if last:
            seq = int(last.split('-')[-1]) + 1
        else:
            seq = 1
        return f'REQ-{year}-{seq:03d}'

    @staticmethod
    @transaction.atomic
    def create_requisition(data: dict, created_by) -> Requisition:
        """Create a new requisition with default pipeline stages."""
        requisition = Requisition.objects.create(
            requisition_id=RequisitionService._generate_requisition_id(),
            created_by=created_by,
            **data,
        )

        stages = [
            PipelineStage(
                requisition=requisition,
                name=name,
                stage_type=stage_type,
                order=idx,
            )
            for idx, (name, stage_type) in enumerate(DEFAULT_PIPELINE)
        ]
        PipelineStage.objects.bulk_create(stages)

        return requisition

    @staticmethod
    @transaction.atomic
    def submit_for_approval(
        requisition: Requisition, approvers: list,
    ) -> Requisition:
        """Submit a draft requisition for approval."""
        if requisition.status != 'draft':
            raise BusinessValidationError(
                'Only draft requisitions can be submitted for approval.'
            )
        if not approvers:
            raise BusinessValidationError(
                'At least one approver is required.'
            )

        requisition.status = 'pending_approval'
        requisition.save(update_fields=['status', 'updated_at'])

        approval_objs = [
            RequisitionApproval(
                requisition=requisition,
                approver=approver,
                order=idx,
            )
            for idx, approver in enumerate(approvers)
        ]
        RequisitionApproval.objects.bulk_create(approval_objs)

        return requisition

    @staticmethod
    @transaction.atomic
    def approve(requisition: Requisition, approver, comments: str = '') -> Requisition:
        """Approve a requisition by the current approver in the chain."""
        if requisition.status != 'pending_approval':
            raise BusinessValidationError(
                'Only pending-approval requisitions can be approved.'
            )

        approval = (
            RequisitionApproval.objects
            .filter(
                requisition=requisition,
                approver=approver,
                status='pending',
            )
            .first()
        )
        if not approval:
            raise BusinessValidationError(
                'You are not a pending approver for this requisition.'
            )

        approval.status = 'approved'
        approval.decided_at = timezone.now()
        approval.comments = comments
        approval.save(update_fields=[
            'status', 'decided_at', 'comments', 'updated_at',
        ])

        # Check if all approvals are done
        pending = requisition.approvals.filter(status='pending').exists()
        if not pending:
            requisition.status = 'approved'
            requisition.save(update_fields=['status', 'updated_at'])

        return requisition

    @staticmethod
    @transaction.atomic
    def reject_approval(
        requisition: Requisition, approver, comments: str = '',
    ) -> Requisition:
        """Reject a requisition — returns it to draft for revision."""
        if requisition.status != 'pending_approval':
            raise BusinessValidationError(
                'Only pending-approval requisitions can be rejected.'
            )

        approval = (
            RequisitionApproval.objects
            .filter(
                requisition=requisition,
                approver=approver,
                status='pending',
            )
            .first()
        )
        if not approval:
            raise BusinessValidationError(
                'You are not a pending approver for this requisition.'
            )

        approval.status = 'rejected'
        approval.decided_at = timezone.now()
        approval.comments = comments
        approval.save(update_fields=[
            'status', 'decided_at', 'comments', 'updated_at',
        ])

        # Return to draft so creator can revise
        requisition.status = 'draft'
        requisition.save(update_fields=['status', 'updated_at'])

        # Skip remaining pending approvals
        requisition.approvals.filter(status='pending').update(
            status='skipped',
            decided_at=timezone.now(),
        )

        return requisition

    @staticmethod
    @transaction.atomic
    def publish(requisition: Requisition) -> Requisition:
        """Publish a requisition — makes it visible on the career site."""
        if requisition.status not in ('approved', 'open'):
            raise BusinessValidationError(
                'Only approved or open requisitions can be published.'
            )
        requisition.status = 'open'
        requisition.published_at = timezone.now()
        if not requisition.opened_at:
            requisition.opened_at = timezone.now()
        requisition.save(update_fields=[
            'status', 'published_at', 'opened_at', 'updated_at',
        ])
        return requisition

    @staticmethod
    @transaction.atomic
    def put_on_hold(requisition: Requisition) -> Requisition:
        if requisition.status != 'open':
            raise BusinessValidationError(
                'Only open requisitions can be put on hold.'
            )
        requisition.status = 'on_hold'
        requisition.save(update_fields=['status', 'updated_at'])
        return requisition

    @staticmethod
    @transaction.atomic
    def cancel(requisition: Requisition) -> Requisition:
        if requisition.status in ('filled', 'cancelled'):
            raise BusinessValidationError(
                'Cannot cancel a requisition that is already filled or cancelled.'
            )
        requisition.status = 'cancelled'
        requisition.closed_at = timezone.now()
        requisition.save(update_fields=['status', 'closed_at', 'updated_at'])
        return requisition

    @staticmethod
    @transaction.atomic
    def reopen(requisition: Requisition) -> Requisition:
        if requisition.status not in ('on_hold', 'cancelled'):
            raise BusinessValidationError(
                'Only on-hold or cancelled requisitions can be reopened.'
            )
        requisition.status = 'open'
        requisition.closed_at = None
        requisition.version += 1
        requisition.save(update_fields=[
            'status', 'closed_at', 'version', 'updated_at',
        ])
        return requisition

    @staticmethod
    @transaction.atomic
    def clone(requisition: Requisition, created_by) -> Requisition:
        """Clone a requisition as a new draft, copying all fields and stages."""
        new_req = Requisition.objects.create(
            requisition_id=RequisitionService._generate_requisition_id(),
            title=requisition.title,
            department=requisition.department,
            team=requisition.team,
            hiring_manager=requisition.hiring_manager,
            recruiter=requisition.recruiter,
            status='draft',
            employment_type=requisition.employment_type,
            level=requisition.level,
            location=requisition.location,
            remote_policy=requisition.remote_policy,
            salary_min=requisition.salary_min,
            salary_max=requisition.salary_max,
            salary_currency=requisition.salary_currency,
            description=requisition.description,
            requirements_required=requisition.requirements_required,
            requirements_preferred=requisition.requirements_preferred,
            screening_questions=requisition.screening_questions,
            headcount=requisition.headcount,
            target_start_date=requisition.target_start_date,
            target_fill_date=requisition.target_fill_date,
            created_by=created_by,
        )

        # Clone pipeline stages
        original_stages = requisition.stages.order_by('order')
        new_stages = [
            PipelineStage(
                requisition=new_req,
                name=stage.name,
                order=stage.order,
                stage_type=stage.stage_type,
                auto_actions=stage.auto_actions,
            )
            for stage in original_stages
        ]
        if new_stages:
            PipelineStage.objects.bulk_create(new_stages)

        return new_req

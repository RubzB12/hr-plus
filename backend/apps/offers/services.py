"""Business logic for offers app."""

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.core.exceptions import BusinessValidationError

from .models import Offer, OfferApproval


class OfferService:
    """Service for managing job offers."""

    @staticmethod
    @transaction.atomic
    def create_offer(
        *,
        application,
        title: str,
        level,
        department,
        base_salary: Decimal,
        start_date,
        expiration_date,
        created_by,
        **kwargs,
    ) -> Offer:
        """
        Create a new job offer.

        Args:
            application: Application instance
            title: Job title
            level: JobLevel instance
            department: Department instance
            base_salary: Salary as Decimal
            start_date: Start date
            expiration_date: Offer expiration date
            created_by: InternalUser creating the offer
            **kwargs: Additional fields (bonus, equity, etc.)

        Returns:
            Created Offer instance
        """
        # Generate offer ID

        latest_offer = Offer.objects.order_by('-created_at').first()
        if latest_offer and latest_offer.offer_id:
            number = int(latest_offer.offer_id.split('-')[-1]) + 1
        else:
            number = 1

        offer_id = f'OFR-{timezone.now().year}-{number:03d}'

        # Create offer (salary stored as encrypted string)
        offer = Offer.objects.create(
            offer_id=offer_id,
            application=application,
            title=title,
            level=level,
            department=department,
            base_salary=str(base_salary),
            start_date=start_date,
            expiration_date=expiration_date,
            created_by=created_by,
            status='draft',
            version=1,
            salary_currency=kwargs.get('salary_currency', 'ZAR'),
            salary_frequency=kwargs.get('salary_frequency', 'annual'),
            bonus=str(kwargs['bonus']) if kwargs.get('bonus') else None,
            equity=kwargs.get('equity', ''),
            sign_on_bonus=str(kwargs['sign_on_bonus']) if kwargs.get('sign_on_bonus') else None,
            relocation=str(kwargs['relocation']) if kwargs.get('relocation') else None,
            reporting_to=kwargs.get('reporting_to'),
            notes=kwargs.get('notes', ''),
        )

        return offer

    @staticmethod
    @transaction.atomic
    def submit_for_approval(offer: Offer, approvers: list) -> Offer:
        """
        Submit offer for approval.

        Args:
            offer: Offer instance
            approvers: List of InternalUser instances (approval chain)

        Returns:
            Updated offer
        """
        if offer.status != 'draft':
            raise BusinessValidationError(f'Can only submit draft offers, current status: {offer.status}')

        if not approvers:
            raise BusinessValidationError('At least one approver is required')

        # Create approval chain
        for i, approver in enumerate(approvers):
            OfferApproval.objects.create(
                offer=offer,
                approver=approver,
                order=i,
                status='pending',
            )

        offer.status = 'pending_approval'
        offer.save(update_fields=['status', 'updated_at'])

        return offer

    @staticmethod
    @transaction.atomic
    def send_to_candidate(offer: Offer) -> Offer:
        """
        Send approved offer to candidate.

        Args:
            offer: Offer instance

        Returns:
            Updated offer
        """
        if offer.status != 'approved':
            raise BusinessValidationError('Can only send approved offers to candidates')

        offer.status = 'sent'
        offer.sent_at = timezone.now()
        offer.save(update_fields=['status', 'sent_at', 'updated_at'])

        # TODO: Send email to candidate with offer link
        # EmailService.send_offer_notification(offer)

        return offer

    @staticmethod
    @transaction.atomic
    def candidate_accept(offer: Offer) -> Offer:
        """
        Candidate accepts the offer.

        Args:
            offer: Offer instance

        Returns:
            Updated offer
        """
        if not offer.is_active:
            raise BusinessValidationError(
                'This offer cannot be accepted '
                '(either expired, withdrawn, or already responded to)'
            )

        offer.status = 'accepted'
        offer.responded_at = timezone.now()
        offer.save(update_fields=['status', 'responded_at', 'updated_at'])

        return offer

    @staticmethod
    @transaction.atomic
    def candidate_decline(offer: Offer, reason: str = '') -> Offer:
        """
        Candidate declines the offer.

        Args:
            offer: Offer instance
            reason: Optional decline reason

        Returns:
            Updated offer
        """
        if not offer.is_active:
            raise BusinessValidationError(
                'This offer cannot be declined '
                '(either expired, withdrawn, or already responded to)'
            )

        offer.status = 'declined'
        offer.responded_at = timezone.now()
        offer.decline_reason = reason
        offer.save(update_fields=['status', 'responded_at', 'decline_reason', 'updated_at'])

        return offer

    @staticmethod
    @transaction.atomic
    def withdraw(offer: Offer) -> Offer:
        """
        Withdraw an offer.

        Args:
            offer: Offer instance

        Returns:
            Updated offer
        """
        if offer.is_final:
            raise BusinessValidationError('Cannot withdraw an offer that has already been finalized')

        offer.status = 'withdrawn'
        offer.save(update_fields=['status', 'updated_at'])

        return offer

    @staticmethod
    @transaction.atomic
    def create_revision(offer: Offer, **updated_fields) -> Offer:
        """
        Create a new version of an offer (for negotiations).

        Args:
            offer: Original offer
            **updated_fields: Fields to update in new version

        Returns:
            New offer version
        """
        # Handle encrypted field updates
        def get_encrypted_value(field_name):
            if field_name in updated_fields:
                val = updated_fields[field_name]
                return str(val) if val is not None else None
            return getattr(offer, field_name)

        new_offer = Offer.objects.create(
            offer_id=offer.offer_id,
            application=offer.application,
            version=offer.version + 1,
            title=updated_fields.get('title', offer.title),
            level=updated_fields.get('level', offer.level),
            department=updated_fields.get('department', offer.department),
            reporting_to=updated_fields.get('reporting_to', offer.reporting_to),
            base_salary=str(updated_fields.get('base_salary', offer.base_salary)),
            salary_currency=updated_fields.get('salary_currency', offer.salary_currency),
            salary_frequency=updated_fields.get('salary_frequency', offer.salary_frequency),
            bonus=get_encrypted_value('bonus'),
            equity=updated_fields.get('equity', offer.equity),
            sign_on_bonus=get_encrypted_value('sign_on_bonus'),
            relocation=get_encrypted_value('relocation'),
            start_date=updated_fields.get('start_date', offer.start_date),
            expiration_date=updated_fields.get('expiration_date', offer.expiration_date),
            notes=updated_fields.get('notes', offer.notes),
            created_by=offer.created_by,
            status='draft',
        )

        return new_offer


class OfferApprovalService:
    """Service for offer approval workflow."""

    @staticmethod
    @transaction.atomic
    def approve(approval: OfferApproval, comments: str = '') -> OfferApproval:
        """
        Approve an offer approval step.

        Args:
            approval: OfferApproval instance
            comments: Optional approval comments

        Returns:
            Updated approval
        """
        if approval.status != 'pending':
            raise BusinessValidationError('Can only approve pending approvals')

        approval.status = 'approved'
        approval.comments = comments
        approval.decided_at = timezone.now()
        approval.save(update_fields=['status', 'comments', 'decided_at', 'updated_at'])

        # Check if all approvals are done
        offer = approval.offer
        all_approvals = offer.approvals.order_by('order')
        all_approved = all(a.status == 'approved' for a in all_approvals)

        if all_approved:
            offer.status = 'approved'
            offer.save(update_fields=['status', 'updated_at'])

        return approval

    @staticmethod
    @transaction.atomic
    def reject(approval: OfferApproval, comments: str) -> OfferApproval:
        """
        Reject an offer approval step.

        Args:
            approval: OfferApproval instance
            comments: Rejection reason (required)

        Returns:
            Updated approval
        """
        if approval.status != 'pending':
            raise BusinessValidationError('Can only reject pending approvals')

        if not comments:
            raise BusinessValidationError('Rejection reason is required')

        approval.status = 'rejected'
        approval.comments = comments
        approval.decided_at = timezone.now()
        approval.save(update_fields=['status', 'comments', 'decided_at', 'updated_at'])

        # Reject the entire offer
        offer = approval.offer
        offer.status = 'draft'  # Return to draft for revision
        offer.save(update_fields=['status', 'updated_at'])

        return approval


class OfferLetterService:
    """Service for generating offer letters."""

    @staticmethod
    def generate_offer_letter(offer: Offer) -> bytes:
        """
        Generate PDF offer letter from template.

        Args:
            offer: Offer instance

        Returns:
            PDF bytes

        Note:
            This is a placeholder. Real implementation would use WeasyPrint
            or similar to generate PDFs from HTML templates.
        """
        # TODO: Implement PDF generation
        # from weasyprint import HTML
        # html_content = render_to_string('offers/offer_letter.html', {'offer': offer})
        # pdf = HTML(string=html_content).write_pdf()
        # return pdf

        return b'PDF placeholder'

"""Models for offers app."""


from django.db import models
from encrypted_fields.fields import EncryptedTextField

from apps.core.models import BaseModel


class Offer(BaseModel):
    """Job offer extended to a candidate."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('sent', 'Sent to Candidate'),
        ('viewed', 'Viewed by Candidate'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
        ('withdrawn', 'Withdrawn'),
    ]

    SALARY_FREQUENCY_CHOICES = [
        ('hourly', 'Hourly'),
        ('annual', 'Annual'),
    ]

    offer_id = models.CharField(
        max_length=20,
        db_index=True,
        help_text='Auto-generated ID, e.g. OFR-2026-001 (can have multiple versions)',
    )
    application = models.ForeignKey(
        'applications.Application',
        on_delete=models.PROTECT,
        related_name='offers',
    )
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True,
    )

    # Position details
    title = models.CharField(max_length=200)
    level = models.ForeignKey(
        'accounts.JobLevel',
        on_delete=models.PROTECT,
        related_name='offers',
    )
    department = models.ForeignKey(
        'accounts.Department',
        on_delete=models.PROTECT,
        related_name='offers',
    )
    reporting_to = models.ForeignKey(
        'accounts.InternalUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='direct_reports_offers',
    )

    # Compensation (encrypted for PII - stored as text, accessed as Decimal)
    base_salary = EncryptedTextField(
        help_text='Encrypted salary amount (stored as string)',
    )
    salary_currency = models.CharField(max_length=3, default='ZAR')
    salary_frequency = models.CharField(
        max_length=10,
        choices=SALARY_FREQUENCY_CHOICES,
        default='annual',
    )
    bonus = EncryptedTextField(
        blank=True,
        null=True,
        help_text='Encrypted bonus amount (stored as string)',
    )
    equity = models.CharField(
        max_length=200,
        blank=True,
        help_text='Stock options/RSUs description',
    )
    sign_on_bonus = EncryptedTextField(
        blank=True,
        null=True,
        help_text='Encrypted sign-on bonus (stored as string)',
    )
    relocation = EncryptedTextField(
        blank=True,
        null=True,
        help_text='Encrypted relocation amount (stored as string)',
    )

    # Dates
    start_date = models.DateField()
    expiration_date = models.DateField(
        help_text='Date by which candidate must accept/decline',
    )

    # Documents
    offer_letter_pdf = models.FileField(
        upload_to='offers/%Y/%m/',
        blank=True,
        help_text='Generated offer letter PDF',
    )

    # Tracking
    notes = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    viewed_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    decline_reason = models.TextField(blank=True)

    # E-signature integration
    esignature_envelope_id = models.CharField(
        max_length=100,
        blank=True,
        help_text='DocuSign/HelloSign envelope ID',
    )

    # Metadata
    created_by = models.ForeignKey(
        'accounts.InternalUser',
        on_delete=models.PROTECT,
        related_name='created_offers',
    )

    class Meta:
        db_table = 'offers_offer'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['application', 'version']),
        ]

    def __str__(self):
        return f'{self.offer_id} - {self.title} for {self.application.candidate.user.get_full_name()}'

    @property
    def is_active(self):
        """Check if offer is in active state (can be responded to)."""
        return self.status in ['sent', 'viewed']

    @property
    def is_final(self):
        """Check if offer is in final state (no further action possible)."""
        return self.status in ['accepted', 'declined', 'expired', 'withdrawn']


class OfferNegotiationLog(BaseModel):
    """Log of negotiation discussions between recruiter and candidate."""

    offer = models.ForeignKey(
        Offer,
        on_delete=models.CASCADE,
        related_name='negotiation_logs',
    )
    logged_by = models.ForeignKey(
        'accounts.InternalUser',
        on_delete=models.PROTECT,
        related_name='offer_negotiations',
    )
    candidate_request = models.TextField(
        help_text='What the candidate is requesting',
    )
    internal_response = models.TextField(
        blank=True,
        help_text='Internal team response/decision',
    )
    outcome = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('declined', 'Declined'),
            ('revised_offer', 'Revised Offer Sent'),
        ],
        default='pending',
    )

    class Meta:
        db_table = 'offers_negotiation_log'
        ordering = ['-created_at']

    def __str__(self):
        return f'Negotiation for {self.offer.offer_id} - {self.outcome}'


class OfferApproval(BaseModel):
    """Approval step in the offer approval chain."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    offer = models.ForeignKey(
        Offer,
        on_delete=models.CASCADE,
        related_name='approvals',
    )
    approver = models.ForeignKey(
        'accounts.InternalUser',
        on_delete=models.PROTECT,
        related_name='offer_approvals',
    )
    order = models.PositiveIntegerField(
        help_text='Order in approval chain (0-indexed)',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
    )
    comments = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'offers_approval'
        ordering = ['offer', 'order']
        unique_together = [['offer', 'order']]

    def __str__(self):
        approver_name = self.approver.user.get_full_name()
        return (
            f'{self.offer.offer_id} - Approval {self.order + 1} '
            f'by {approver_name} ({self.status})'
        )

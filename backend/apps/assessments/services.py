"""Business logic for assessments app."""

import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.core.exceptions import BusinessValidationError

from .models import (
    Assessment,
    AssessmentTemplate,
    ReferenceCheckRequest,
    ReferenceCheckResponse,
)


class AssessmentService:
    """Service for managing assessments."""

    @staticmethod
    def generate_access_token():
        """Generate secure random token for assessment access."""
        return secrets.token_urlsafe(32)

    @staticmethod
    @transaction.atomic
    def assign_assessment(
        *,
        application,
        template: AssessmentTemplate,
        assigned_by,
        due_days: int = 7,
        **kwargs,
    ) -> Assessment:
        """
        Assign an assessment to a candidate.

        Args:
            application: Application instance
            template: AssessmentTemplate to assign
            assigned_by: InternalUser assigning the assessment
            due_days: Number of days until due (default 7)
            **kwargs: Additional fields (due_date override, notes, etc.)

        Returns:
            Created Assessment instance
        """
        if not template.is_active:
            raise BusinessValidationError('Cannot assign inactive assessment template')

        # Calculate due date
        due_date = kwargs.get('due_date')
        if not due_date and due_days:
            due_date = timezone.now() + timedelta(days=due_days)

        assessment = Assessment.objects.create(
            application=application,
            template=template,
            assigned_by=assigned_by,
            due_date=due_date,
            access_token=AssessmentService.generate_access_token(),
            status='assigned',
        )

        # TODO: Send notification email to candidate
        # from apps.communications.services import EmailService
        # EmailService.send_assessment_assigned(assessment)

        return assessment

    @staticmethod
    @transaction.atomic
    def start_assessment(assessment: Assessment) -> Assessment:
        """
        Mark assessment as in progress when candidate starts.

        Args:
            assessment: Assessment instance

        Returns:
            Updated Assessment
        """
        if assessment.status != 'assigned':
            raise BusinessValidationError(
                f'Cannot start assessment with status: {assessment.status}'
            )

        # Check if expired
        if assessment.is_overdue:
            assessment.status = 'expired'
            assessment.save(update_fields=['status', 'updated_at'])
            raise BusinessValidationError('Assessment has expired')

        assessment.status = 'in_progress'
        assessment.started_at = timezone.now()
        assessment.save(update_fields=['status', 'started_at', 'updated_at'])

        return assessment

    @staticmethod
    @transaction.atomic
    def submit_assessment(
        assessment: Assessment, responses: dict
    ) -> Assessment:
        """
        Submit completed assessment responses.

        Args:
            assessment: Assessment instance
            responses: Dictionary of question IDs to answers

        Returns:
            Updated Assessment
        """
        if assessment.status not in ['assigned', 'in_progress']:
            raise BusinessValidationError(
                f'Cannot submit assessment with status: {assessment.status}'
            )

        assessment.status = 'completed'
        assessment.completed_at = timezone.now()
        assessment.responses = responses
        assessment.save(
            update_fields=['status', 'completed_at', 'responses', 'updated_at']
        )

        # TODO: Auto-score if possible (for multiple choice, etc.)
        # AssessmentService.auto_score(assessment)

        return assessment

    @staticmethod
    @transaction.atomic
    def score_assessment(
        assessment: Assessment,
        *,
        score: float,
        evaluator,
        notes: str = '',
    ) -> Assessment:
        """
        Score a completed assessment.

        Args:
            assessment: Assessment instance
            score: Score value (e.g., 85.5)
            evaluator: InternalUser scoring the assessment
            notes: Optional evaluator notes

        Returns:
            Updated Assessment
        """
        if assessment.status != 'completed':
            raise BusinessValidationError('Can only score completed assessments')

        if score < 0 or score > 100:
            raise BusinessValidationError('Score must be between 0 and 100')

        assessment.score = score
        assessment.evaluated_by = evaluator
        assessment.evaluated_at = timezone.now()
        assessment.evaluator_notes = notes
        assessment.save(
            update_fields=[
                'score',
                'evaluated_by',
                'evaluated_at',
                'evaluator_notes',
                'updated_at',
            ]
        )

        return assessment

    @staticmethod
    @transaction.atomic
    def waive_assessment(assessment: Assessment, reason: str = '') -> Assessment:
        """
        Waive an assessment (skip it).

        Args:
            assessment: Assessment instance
            reason: Reason for waiving

        Returns:
            Updated Assessment
        """
        assessment.status = 'waived'
        assessment.evaluator_notes = f'Waived: {reason}' if reason else 'Waived'
        assessment.save(update_fields=['status', 'evaluator_notes', 'updated_at'])

        return assessment


class ReferenceCheckService:
    """Service for managing reference checks."""

    @staticmethod
    def generate_access_token():
        """Generate secure random token for reference access."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def default_questionnaire():
        """Return default reference check questionnaire."""
        return [
            {
                'id': 'relationship_duration',
                'question': 'How long have you known the candidate and in what capacity?',
                'type': 'text',
                'required': True,
            },
            {
                'id': 'performance_rating',
                'question': 'How would you rate their overall performance?',
                'type': 'rating',
                'scale': 5,
                'required': True,
            },
            {
                'id': 'strengths',
                'question': 'What are their key strengths?',
                'type': 'text',
                'required': True,
            },
            {
                'id': 'areas_for_improvement',
                'question': 'What areas could they improve?',
                'type': 'text',
                'required': True,
            },
            {
                'id': 'teamwork',
                'question': 'How well do they work in a team environment?',
                'type': 'rating',
                'scale': 5,
                'required': True,
            },
            {
                'id': 'communication',
                'question': 'How would you rate their communication skills?',
                'type': 'rating',
                'scale': 5,
                'required': True,
            },
            {
                'id': 'attendance',
                'question': 'How was their attendance and reliability?',
                'type': 'rating',
                'scale': 5,
                'required': True,
            },
        ]

    @staticmethod
    @transaction.atomic
    def create_reference_request(
        *,
        application,
        reference_name: str,
        reference_email: str,
        requested_by,
        relationship: str = 'manager',
        questionnaire: list = None,
        due_days: int = 14,
        **kwargs,
    ) -> ReferenceCheckRequest:
        """
        Create a reference check request.

        Args:
            application: Application instance
            reference_name: Name of reference
            reference_email: Email of reference
            requested_by: InternalUser requesting the reference
            relationship: Type of relationship (manager, colleague, etc.)
            questionnaire: Custom questionnaire (defaults to standard if None)
            due_days: Days until due (default 14)
            **kwargs: Additional fields

        Returns:
            Created ReferenceCheckRequest
        """
        # Check for duplicate
        if ReferenceCheckRequest.objects.filter(
            application=application,
            reference_email__iexact=reference_email,
            status__in=['pending', 'sent', 'in_progress'],
        ).exists():
            raise BusinessValidationError(
                f'Reference request already exists for {reference_email}'
            )

        due_date = kwargs.get('due_date')
        if not due_date and due_days:
            due_date = timezone.now() + timedelta(days=due_days)

        request = ReferenceCheckRequest.objects.create(
            application=application,
            reference_name=reference_name,
            reference_email=reference_email,
            reference_phone=kwargs.get('reference_phone', ''),
            reference_company=kwargs.get('reference_company', ''),
            reference_title=kwargs.get('reference_title', ''),
            relationship=relationship,
            requested_by=requested_by,
            due_date=due_date,
            questionnaire=questionnaire
            or ReferenceCheckService.default_questionnaire(),
            notes=kwargs.get('notes', ''),
            access_token=ReferenceCheckService.generate_access_token(),
        )

        return request

    @staticmethod
    @transaction.atomic
    def send_reference_request(request: ReferenceCheckRequest) -> ReferenceCheckRequest:
        """
        Send reference check request email.

        Args:
            request: ReferenceCheckRequest instance

        Returns:
            Updated request
        """
        if request.status not in ['pending']:
            raise BusinessValidationError(
                f'Cannot send request with status: {request.status}'
            )

        request.status = 'sent'
        request.sent_at = timezone.now()
        request.save(update_fields=['status', 'sent_at', 'updated_at'])

        # TODO: Send email via Celery task
        # from apps.assessments.tasks import send_reference_request_email
        # send_reference_request_email.delay(request.id)

        return request

    @staticmethod
    @transaction.atomic
    def submit_reference_response(
        request: ReferenceCheckRequest,
        *,
        responses: dict,
        overall_recommendation: str = None,
        would_rehire: bool = None,
        additional_comments: str = '',
        reference_ip: str = None,
    ) -> ReferenceCheckResponse:
        """
        Submit reference check response.

        Args:
            request: ReferenceCheckRequest instance
            responses: Answers to questionnaire
            overall_recommendation: Overall recommendation level
            would_rehire: Would hire again (for managers)
            additional_comments: Additional feedback
            reference_ip: IP address of submitter

        Returns:
            Created ReferenceCheckResponse
        """
        if request.status == 'completed':
            raise BusinessValidationError('Reference check already completed')

        if request.status == 'expired':
            raise BusinessValidationError('Reference check has expired')

        # Create response
        response = ReferenceCheckResponse.objects.create(
            request=request,
            responses=responses,
            overall_recommendation=overall_recommendation,
            would_rehire=would_rehire,
            additional_comments=additional_comments,
            reference_ip=reference_ip,
        )

        # Update request status
        request.status = 'completed'
        request.save(update_fields=['status', 'updated_at'])

        return response

    @staticmethod
    @transaction.atomic
    def decline_reference_request(request: ReferenceCheckRequest) -> ReferenceCheckRequest:
        """
        Decline to provide a reference.

        Args:
            request: ReferenceCheckRequest instance

        Returns:
            Updated request
        """
        if request.status in ['completed', 'declined']:
            raise BusinessValidationError(f'Request already {request.status}')

        request.status = 'declined'
        request.save(update_fields=['status', 'updated_at'])

        return request

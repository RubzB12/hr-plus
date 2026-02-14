"""Tests for assessments services."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.tests.factories import InternalUserFactory
from apps.applications.tests.factories import ApplicationFactory
from apps.assessments.services import AssessmentService, ReferenceCheckService
from apps.assessments.tests.factories import (
    AssessmentFactory,
    AssessmentTemplateFactory,
    ReferenceCheckRequestFactory,
)
from apps.core.exceptions import BusinessValidationError


@pytest.mark.django_db
class TestAssessmentService:
    """Tests for AssessmentService."""

    def test_assign_assessment_generates_access_token(self):
        """Assessment is assigned with unique access token."""
        application = ApplicationFactory()
        template = AssessmentTemplateFactory()
        internal_user = InternalUserFactory()

        assessment = AssessmentService.assign_assessment(
            application=application,
            template=template,
            assigned_by=internal_user,
            due_days=7,
        )

        assert assessment.id is not None
        assert assessment.access_token is not None
        assert len(assessment.access_token) > 20
        assert assessment.status == 'assigned'
        assert assessment.due_date is not None

    def test_assign_assessment_fails_for_inactive_template(self):
        """Cannot assign inactive assessment template."""
        application = ApplicationFactory()
        template = AssessmentTemplateFactory(is_active=False)
        internal_user = InternalUserFactory()

        with pytest.raises(
            BusinessValidationError, match='Cannot assign inactive assessment template'
        ):
            AssessmentService.assign_assessment(
                application=application,
                template=template,
                assigned_by=internal_user,
                due_days=7,
            )

    def test_start_assessment_requires_assigned_status(self):
        """Only assigned assessments can be started."""
        assessment = AssessmentFactory(status='completed')

        with pytest.raises(BusinessValidationError, match='Cannot start assessment'):
            AssessmentService.start_assessment(assessment)

    def test_start_assessment_updates_status_and_timestamp(self):
        """Starting assessment updates status and started_at."""
        assessment = AssessmentFactory(status='assigned')

        updated_assessment = AssessmentService.start_assessment(assessment)

        assert updated_assessment.status == 'in_progress'
        assert updated_assessment.started_at is not None

    def test_start_assessment_fails_if_expired(self):
        """Cannot start expired assessment."""
        assessment = AssessmentFactory(
            status='assigned', due_date=timezone.now() - timedelta(days=1)
        )

        with pytest.raises(BusinessValidationError, match='Assessment has expired'):
            AssessmentService.start_assessment(assessment)

    def test_submit_assessment_updates_status_and_responses(self):
        """Submitting assessment stores responses and updates status."""
        assessment = AssessmentFactory(status='in_progress')
        responses = {
            'question_1': 'answer_a',
            'question_2': 'answer_b',
        }

        updated_assessment = AssessmentService.submit_assessment(assessment, responses)

        assert updated_assessment.status == 'completed'
        assert updated_assessment.completed_at is not None
        assert updated_assessment.responses == responses

    def test_submit_assessment_requires_valid_status(self):
        """Cannot submit completed or waived assessments."""
        assessment = AssessmentFactory(status='completed')

        with pytest.raises(BusinessValidationError, match='Cannot submit assessment'):
            AssessmentService.submit_assessment(assessment, {})

    def test_score_assessment_requires_completed_status(self):
        """Only completed assessments can be scored."""
        assessment = AssessmentFactory(status='in_progress')
        evaluator = InternalUserFactory()

        with pytest.raises(BusinessValidationError, match='Can only score completed'):
            AssessmentService.score_assessment(
                assessment, score=85.0, evaluator=evaluator, notes='Good work'
            )

    def test_score_assessment_validates_range(self):
        """Score must be between 0 and 100."""
        assessment = AssessmentFactory(status='completed')
        evaluator = InternalUserFactory()

        with pytest.raises(BusinessValidationError, match='Score must be between 0 and 100'):
            AssessmentService.score_assessment(
                assessment, score=150.0, evaluator=evaluator, notes=''
            )

    def test_score_assessment_stores_score_and_evaluator(self):
        """Scoring stores score, evaluator, and notes."""
        assessment = AssessmentFactory(status='completed')
        evaluator = InternalUserFactory()

        updated_assessment = AssessmentService.score_assessment(
            assessment, score=88.5, evaluator=evaluator, notes='Excellent answers'
        )

        assert updated_assessment.score == 88.5
        assert updated_assessment.evaluated_by == evaluator
        assert updated_assessment.evaluated_at is not None
        assert updated_assessment.evaluator_notes == 'Excellent answers'

    def test_waive_assessment_updates_status(self):
        """Waiving assessment updates status."""
        assessment = AssessmentFactory(status='assigned')

        updated_assessment = AssessmentService.waive_assessment(
            assessment, reason='Candidate has relevant certification'
        )

        assert updated_assessment.status == 'waived'
        assert 'waived' in updated_assessment.evaluator_notes.lower()


@pytest.mark.django_db
class TestReferenceCheckService:
    """Tests for ReferenceCheckService."""

    def test_create_reference_request_generates_token(self):
        """Reference request is created with unique access token."""
        application = ApplicationFactory()
        internal_user = InternalUserFactory()

        request = ReferenceCheckService.create_reference_request(
            application=application,
            reference_name='Jane Smith',
            reference_email='jane@example.com',
            requested_by=internal_user,
            relationship='manager',
            due_days=14,
        )

        assert request.id is not None
        assert request.access_token is not None
        assert len(request.access_token) > 20
        assert request.status == 'pending'
        assert request.due_date is not None

    def test_create_reference_request_prevents_duplicates(self):
        """Cannot create duplicate reference request for same email."""
        application = ApplicationFactory()
        internal_user = InternalUserFactory()

        # Create first request
        ReferenceCheckService.create_reference_request(
            application=application,
            reference_name='Jane Smith',
            reference_email='jane@example.com',
            requested_by=internal_user,
        )

        # Try to create duplicate
        with pytest.raises(
            BusinessValidationError, match='Reference request already exists'
        ):
            ReferenceCheckService.create_reference_request(
                application=application,
                reference_name='Jane Smith',
                reference_email='jane@example.com',
                requested_by=internal_user,
            )

    def test_create_reference_request_uses_default_questionnaire(self):
        """Default questionnaire is used if none provided."""
        application = ApplicationFactory()
        internal_user = InternalUserFactory()

        request = ReferenceCheckService.create_reference_request(
            application=application,
            reference_name='Jane Smith',
            reference_email='jane@example.com',
            requested_by=internal_user,
        )

        assert isinstance(request.questionnaire, list)
        assert len(request.questionnaire) > 0
        assert request.questionnaire[0]['id'] == 'relationship_duration'

    def test_send_reference_request_updates_status(self):
        """Sending reference request updates status and timestamp."""
        ref_request = ReferenceCheckRequestFactory(status='pending')

        updated_request = ReferenceCheckService.send_reference_request(ref_request)

        assert updated_request.status == 'sent'
        assert updated_request.sent_at is not None

    def test_send_reference_request_requires_pending_status(self):
        """Only pending requests can be sent."""
        ref_request = ReferenceCheckRequestFactory(status='completed')

        with pytest.raises(BusinessValidationError, match='Cannot send request'):
            ReferenceCheckService.send_reference_request(ref_request)

    def test_submit_reference_response_creates_response(self):
        """Submitting reference creates response and updates request."""
        ref_request = ReferenceCheckRequestFactory(status='sent')
        responses = {
            'relationship_duration': '3 years',
            'performance_rating': 5,
        }

        response = ReferenceCheckService.submit_reference_response(
            ref_request,
            responses=responses,
            overall_recommendation='highly_recommend',
            would_rehire=True,
            additional_comments='Excellent candidate',
            reference_ip='192.168.1.1',
        )

        assert response.id is not None
        assert response.responses == responses
        assert response.overall_recommendation == 'highly_recommend'
        assert response.would_rehire is True
        assert response.reference_ip == '192.168.1.1'

        ref_request.refresh_from_db()
        assert ref_request.status == 'completed'

    def test_submit_reference_response_fails_if_completed(self):
        """Cannot submit response for completed request."""
        ref_request = ReferenceCheckRequestFactory(status='completed')

        with pytest.raises(
            BusinessValidationError, match='Reference check already completed'
        ):
            ReferenceCheckService.submit_reference_response(
                ref_request, responses={}, reference_ip='127.0.0.1'
            )

    def test_decline_reference_request_updates_status(self):
        """Declining reference updates status."""
        ref_request = ReferenceCheckRequestFactory(status='sent')

        updated_request = ReferenceCheckService.decline_reference_request(ref_request)

        assert updated_request.status == 'declined'

    def test_decline_reference_request_fails_if_already_completed(self):
        """Cannot decline completed request."""
        ref_request = ReferenceCheckRequestFactory(status='completed')

        with pytest.raises(BusinessValidationError, match='Request already completed'):
            ReferenceCheckService.decline_reference_request(ref_request)

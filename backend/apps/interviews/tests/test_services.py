"""Tests for interview services."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.core.exceptions import BusinessValidationError
from apps.interviews.services import DebriefService, InterviewService, ScorecardService

from .factories import (
    DebriefFactory,
    InterviewFactory,
    ScorecardFactory,
)


@pytest.mark.django_db
class TestInterviewService:
    def test_schedule_interview(self):
        """Successfully creates interview with participants."""
        from apps.accounts.tests.factories import InternalUserFactory
        from apps.applications.tests.factories import ApplicationFactory

        application = ApplicationFactory()
        interviewer = InternalUserFactory()
        start = timezone.now() + timedelta(days=7)
        end = start + timedelta(hours=1)

        interview = InterviewService.schedule(
            application=application,
            interview_type='video',
            scheduled_start=start,
            scheduled_end=end,
            video_link='https://zoom.us/test',
            created_by=application.candidate.user,
            interviewer_ids=[interviewer.id],
        )

        assert interview.application == application
        assert interview.status == 'scheduled'
        assert interview.participants.count() == 1
        assert interview.participants.first().role == 'lead'

    def test_schedule_validates_times(self):
        """Rejects end time before start time."""
        from apps.applications.tests.factories import ApplicationFactory

        application = ApplicationFactory()
        start = timezone.now() + timedelta(days=7)
        end = start - timedelta(hours=1)  # End before start

        with pytest.raises(BusinessValidationError, match='End time must be after start time'):
            InterviewService.schedule(
                application=application,
                interview_type='video',
                scheduled_start=start,
                scheduled_end=end,
                created_by=application.candidate.user,
            )

    def test_cancel_interview(self):
        """Marks status as cancelled, logs event."""
        from apps.accounts.tests.factories import InternalUserFactory

        interview = InterviewFactory()
        user = InternalUserFactory()

        result = InterviewService.cancel(
            interview,
            reason='Candidate unavailable',
            cancelled_by=user.user,
        )

        assert result.status == 'cancelled'
        assert result.cancelled_at is not None
        assert result.cancellation_reason == 'Candidate unavailable'

        event = interview.application.events.filter(event_type='interview.cancelled').first()
        assert event is not None

    def test_cannot_cancel_completed_interview(self):
        """Raises BusinessValidationError."""
        from apps.accounts.tests.factories import InternalUserFactory

        interview = InterviewFactory(status='completed')
        user = InternalUserFactory()

        with pytest.raises(BusinessValidationError, match='Cannot cancel interview'):
            InterviewService.cancel(interview, cancelled_by=user.user)

    def test_reschedule_interview(self):
        """Updates times, logs event."""
        from apps.accounts.tests.factories import InternalUserFactory

        interview = InterviewFactory()
        user = InternalUserFactory()
        new_start = timezone.now() + timedelta(days=14)
        new_end = new_start + timedelta(hours=1)

        result = InterviewService.reschedule(
            interview,
            scheduled_start=new_start,
            scheduled_end=new_end,
            rescheduled_by=user.user,
        )

        assert result.scheduled_start == new_start
        assert result.scheduled_end == new_end
        assert result.status == 'rescheduled'

        event = interview.application.events.filter(event_type='interview.rescheduled').first()
        assert event is not None

    def test_assign_participant(self):
        """Adds interviewer to interview."""
        from apps.accounts.tests.factories import InternalUserFactory

        interview = InterviewFactory()
        interviewer = InternalUserFactory()

        participant = InterviewService.assign_participant(
            interview,
            interviewer=interviewer,
            role='shadow',
        )

        assert participant.interview == interview
        assert participant.interviewer == interviewer
        assert participant.role == 'shadow'

    def test_mark_complete(self):
        """Updates status to completed."""
        from apps.accounts.tests.factories import InternalUserFactory

        interview = InterviewFactory()
        user = InternalUserFactory()

        result = InterviewService.mark_complete(interview, marked_by=user.user)

        assert result.status == 'completed'


@pytest.mark.django_db
class TestScorecardService:
    def test_create_scorecard_draft(self):
        """Creates draft scorecard."""
        from apps.accounts.tests.factories import InternalUserFactory

        interview = InterviewFactory()
        interviewer = InternalUserFactory()

        scorecard = ScorecardService.create_or_update_scorecard(
            interview=interview,
            interviewer=interviewer,
            overall_rating=4,
            recommendation='hire',
            is_draft=True,
        )

        assert scorecard.interview == interview
        assert scorecard.interviewer == interviewer
        assert scorecard.is_draft is True
        assert scorecard.submitted_at is None

    def test_submit_scorecard(self):
        """Marks as not draft, sets submitted_at, logs event."""
        from apps.accounts.tests.factories import InternalUserFactory

        scorecard = ScorecardFactory(overall_rating=4, recommendation='hire')
        user = InternalUserFactory()

        result = ScorecardService.submit_scorecard(scorecard, submitted_by=user.user)

        assert result.is_draft is False
        assert result.submitted_at is not None

        event = scorecard.interview.application.events.filter(
            event_type='scorecard.submitted'
        ).first()
        assert event is not None

    def test_cannot_submit_without_rating(self):
        """Raises error if overall_rating missing."""
        from apps.accounts.tests.factories import InternalUserFactory

        scorecard = ScorecardFactory(overall_rating=None, recommendation='hire')
        user = InternalUserFactory()

        with pytest.raises(
            BusinessValidationError,
            match='Overall rating and recommendation are required',
        ):
            ScorecardService.submit_scorecard(scorecard, submitted_by=user.user)

    def test_can_view_scorecards_after_submission(self):
        """Anti-bias check."""
        from apps.accounts.tests.factories import InternalUserFactory

        interview = InterviewFactory()
        interviewer = InternalUserFactory()

        # Create and submit scorecard
        ScorecardFactory(
            interview=interview,
            interviewer=interviewer,
            overall_rating=4,
            recommendation='hire',
            is_draft=False,
        )

        can_view = ScorecardService.can_view_scorecards(interview, interviewer.user)
        assert can_view is True

    def test_cannot_view_scorecards_before_submission(self):
        """Returns False."""
        from apps.accounts.tests.factories import InternalUserFactory

        interview = InterviewFactory()
        interviewer = InternalUserFactory()

        # No scorecard submitted
        can_view = ScorecardService.can_view_scorecards(interview, interviewer.user)
        assert can_view is False


@pytest.mark.django_db
class TestDebriefService:
    def test_create_debrief(self):
        """Creates debrief, logs event."""
        from apps.accounts.tests.factories import InternalUserFactory
        from apps.applications.tests.factories import ApplicationFactory

        application = ApplicationFactory()
        user = InternalUserFactory()
        scheduled_at = timezone.now() + timedelta(days=1)

        debrief = DebriefService.create_debrief(
            application=application,
            scheduled_at=scheduled_at,
            notes='Initial notes',
            created_by=user.user,
        )

        assert debrief.application == application
        assert debrief.scheduled_at == scheduled_at
        assert debrief.decision is None

        event = application.events.filter(event_type='debrief.scheduled').first()
        assert event is not None

    def test_record_decision(self):
        """Sets decision, decided_by, decided_at, logs event."""
        from apps.accounts.tests.factories import InternalUserFactory

        debrief = DebriefFactory()
        user = InternalUserFactory()

        result = DebriefService.record_decision(
            debrief,
            decision='advance',
            notes='Strong candidate',
            decided_by=user.user,
        )

        assert result.decision == 'advance'
        assert result.decided_by == user.user
        assert result.decided_at is not None

        event = debrief.application.events.filter(
            event_type='debrief.decision_made'
        ).first()
        assert event is not None
        assert event.metadata['decision'] == 'advance'

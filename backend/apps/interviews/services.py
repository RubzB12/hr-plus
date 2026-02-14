"""Business logic for interviews app."""

from django.db import transaction
from django.utils import timezone

from apps.applications.models import Application, ApplicationEvent
from apps.core.exceptions import BusinessValidationError

from .models import Debrief, Interview, InterviewParticipant, Scorecard, ScorecardCriterionRating


class InterviewService:
    """Service for managing interviews."""

    @staticmethod
    @transaction.atomic
    def schedule(
        *,
        application: Application,
        interview_type: str,
        scheduled_start,
        scheduled_end,
        timezone_str: str = 'UTC',
        location: str = '',
        video_link: str = '',
        prep_notes_interviewer: str = '',
        prep_notes_candidate: str = '',
        interview_plan_stage=None,
        scorecard_template=None,
        created_by,
        interviewer_ids: list = None,
    ) -> Interview:
        """
        Schedule a new interview.

        Args:
            application: Application being interviewed
            interview_type: Interview type (phone_screen, video, etc.)
            scheduled_start: Start datetime
            scheduled_end: End datetime
            timezone_str: Timezone string (default UTC)
            location: Physical location (if applicable)
            video_link: Video conferencing link
            prep_notes_interviewer: Notes for interviewer
            prep_notes_candidate: Notes for candidate
            interview_plan_stage: Pipeline stage (if interview is tied to stage)
            scorecard_template: Scorecard template to use
            created_by: User creating the interview
            interviewer_ids: List of internal user IDs to assign as interviewers

        Returns:
            Interview instance
        """
        if scheduled_end <= scheduled_start:
            raise BusinessValidationError('End time must be after start time')

        interview = Interview.objects.create(
            application=application,
            type=interview_type,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            timezone=timezone_str,
            location=location,
            video_link=video_link,
            prep_notes_interviewer=prep_notes_interviewer,
            prep_notes_candidate=prep_notes_candidate,
            interview_plan_stage=interview_plan_stage,
            scorecard_template=scorecard_template,
            created_by=created_by,
            status='scheduled',
        )

        # Assign interviewers
        if interviewer_ids:
            from apps.accounts.models import InternalUser

            interviewers = InternalUser.objects.filter(id__in=interviewer_ids)
            for idx, interviewer in enumerate(interviewers):
                InterviewParticipant.objects.create(
                    interview=interview,
                    interviewer=interviewer,
                    role='lead' if idx == 0 else 'shadow',
                    rsvp_status='pending',
                )

        # Log event
        ApplicationEvent.objects.create(
            application=application,
            event_type='interview.scheduled',
            actor=created_by,
            metadata={
                'interview_id': str(interview.id),
                'type': interview_type,
                'scheduled_start': scheduled_start.isoformat(),
            },
        )

        return interview

    @staticmethod
    @transaction.atomic
    def cancel(interview: Interview, *, reason: str = '', cancelled_by) -> Interview:
        """
        Cancel an interview.

        Args:
            interview: Interview to cancel
            reason: Cancellation reason
            cancelled_by: User cancelling the interview

        Returns:
            Updated interview instance
        """
        if interview.status in ['cancelled', 'completed']:
            raise BusinessValidationError(
                f'Cannot cancel interview with status {interview.status}',
            )

        interview.status = 'cancelled'
        interview.cancelled_at = timezone.now()
        interview.cancellation_reason = reason
        interview.save(update_fields=['status', 'cancelled_at', 'cancellation_reason', 'updated_at'])

        # Log event
        ApplicationEvent.objects.create(
            application=interview.application,
            event_type='interview.cancelled',
            actor=cancelled_by,
            metadata={
                'interview_id': str(interview.id),
                'reason': reason,
            },
        )

        return interview

    @staticmethod
    @transaction.atomic
    def reschedule(
        interview: Interview,
        *,
        scheduled_start,
        scheduled_end,
        rescheduled_by,
    ) -> Interview:
        """
        Reschedule an interview to a new time.

        Args:
            interview: Interview to reschedule
            scheduled_start: New start datetime
            scheduled_end: New end datetime
            rescheduled_by: User rescheduling

        Returns:
            Updated interview instance
        """
        if interview.status in ['cancelled', 'completed']:
            raise BusinessValidationError(
                f'Cannot reschedule interview with status {interview.status}',
            )

        if scheduled_end <= scheduled_start:
            raise BusinessValidationError('End time must be after start time')

        old_start = interview.scheduled_start

        interview.scheduled_start = scheduled_start
        interview.scheduled_end = scheduled_end
        interview.status = 'rescheduled'
        interview.save(update_fields=['scheduled_start', 'scheduled_end', 'status', 'updated_at'])

        # Log event
        ApplicationEvent.objects.create(
            application=interview.application,
            event_type='interview.rescheduled',
            actor=rescheduled_by,
            metadata={
                'interview_id': str(interview.id),
                'old_start': old_start.isoformat(),
                'new_start': scheduled_start.isoformat(),
            },
        )

        return interview

    @staticmethod
    @transaction.atomic
    def assign_participant(
        interview: Interview,
        *,
        interviewer,
        role: str = 'lead',
    ) -> InterviewParticipant:
        """
        Add an interviewer to an interview.

        Args:
            interview: Interview instance
            interviewer: InternalUser to add
            role: Participant role (lead/shadow/observer)

        Returns:
            InterviewParticipant instance
        """
        participant, created = InterviewParticipant.objects.get_or_create(
            interview=interview,
            interviewer=interviewer,
            defaults={'role': role, 'rsvp_status': 'pending'},
        )

        if not created:
            participant.role = role
            participant.save(update_fields=['role', 'updated_at'])

        return participant

    @staticmethod
    @transaction.atomic
    def mark_complete(interview: Interview, *, marked_by) -> Interview:
        """
        Mark an interview as completed.

        Args:
            interview: Interview to mark complete
            marked_by: User marking complete

        Returns:
            Updated interview instance
        """
        interview.status = 'completed'
        interview.save(update_fields=['status', 'updated_at'])

        ApplicationEvent.objects.create(
            application=interview.application,
            event_type='interview.completed',
            actor=marked_by,
            metadata={'interview_id': str(interview.id)},
        )

        return interview


class ScorecardService:
    """Service for managing interview scorecards."""

    @staticmethod
    @transaction.atomic
    def create_or_update_scorecard(
        *,
        interview: Interview,
        interviewer,
        overall_rating: int = None,
        recommendation: str = None,
        strengths: str = '',
        concerns: str = '',
        notes: str = '',
        criterion_ratings: list = None,
        is_draft: bool = True,
    ) -> Scorecard:
        """
        Create or update a scorecard (always in draft initially).

        Args:
            interview: Interview being evaluated
            interviewer: InternalUser submitting scorecard
            overall_rating: Overall rating (1-5)
            recommendation: Hiring recommendation
            strengths: Candidate strengths
            concerns: Candidate concerns
            notes: Additional notes
            criterion_ratings: List of dicts with criterion_id and rating
            is_draft: Whether scorecard is draft (True) or submitted (False)

        Returns:
            Scorecard instance
        """
        scorecard, created = Scorecard.objects.get_or_create(
            interview=interview,
            interviewer=interviewer,
            defaults={
                'overall_rating': overall_rating,
                'recommendation': recommendation,
                'strengths': strengths,
                'concerns': concerns,
                'notes': notes,
                'is_draft': is_draft,
            },
        )

        if not created:
            scorecard.overall_rating = overall_rating
            scorecard.recommendation = recommendation
            scorecard.strengths = strengths
            scorecard.concerns = concerns
            scorecard.notes = notes
            scorecard.is_draft = is_draft
            scorecard.save()

        # Update criterion ratings
        if criterion_ratings:
            from .models import ScorecardCriterion

            for cr in criterion_ratings:
                criterion = ScorecardCriterion.objects.get(id=cr['criterion_id'])
                ScorecardCriterionRating.objects.update_or_create(
                    scorecard=scorecard,
                    criterion=criterion,
                    defaults={
                        'rating': cr['rating'],
                        'comment': cr.get('comment', ''),
                    },
                )

        return scorecard

    @staticmethod
    @transaction.atomic
    def submit_scorecard(scorecard: Scorecard, *, submitted_by) -> Scorecard:
        """
        Submit a scorecard (finalize it).

        Args:
            scorecard: Scorecard to submit
            submitted_by: User submitting

        Returns:
            Updated scorecard
        """
        if not scorecard.is_draft:
            raise BusinessValidationError('Scorecard already submitted')

        if not scorecard.overall_rating or not scorecard.recommendation:
            raise BusinessValidationError(
                'Overall rating and recommendation are required to submit',
            )

        scorecard.is_draft = False
        scorecard.submitted_at = timezone.now()
        scorecard.save(update_fields=['is_draft', 'submitted_at', 'updated_at'])

        # Log event
        ApplicationEvent.objects.create(
            application=scorecard.interview.application,
            event_type='scorecard.submitted',
            actor=submitted_by,
            metadata={
                'interview_id': str(scorecard.interview.id),
                'scorecard_id': str(scorecard.id),
                'recommendation': scorecard.recommendation,
            },
        )

        return scorecard

    @staticmethod
    def can_view_scorecards(interview: Interview, user) -> bool:
        """
        Check if a user can view other scorecards for an interview.
        Anti-bias rule: Can only view after submitting own scorecard.

        Args:
            interview: Interview instance
            user: User requesting access

        Returns:
            True if user can view scorecards, False otherwise
        """
        # Check if user has a submitted (non-draft) scorecard
        has_submitted = Scorecard.objects.filter(
            interview=interview,
            interviewer__user=user,
            is_draft=False,
        ).exists()

        return has_submitted


class DebriefService:
    """Service for managing interview debriefs."""

    @staticmethod
    @transaction.atomic
    def create_debrief(
        *,
        application: Application,
        scheduled_at,
        notes: str = '',
        created_by,
    ) -> Debrief:
        """
        Create a debrief session.

        Args:
            application: Application being debriefed
            scheduled_at: When debrief is scheduled
            notes: Initial notes
            created_by: User creating debrief

        Returns:
            Debrief instance
        """
        debrief = Debrief.objects.create(
            application=application,
            scheduled_at=scheduled_at,
            notes=notes,
        )

        ApplicationEvent.objects.create(
            application=application,
            event_type='debrief.scheduled',
            actor=created_by,
            metadata={
                'debrief_id': str(debrief.id),
                'scheduled_at': scheduled_at.isoformat(),
            },
        )

        return debrief

    @staticmethod
    @transaction.atomic
    def record_decision(
        debrief: Debrief,
        *,
        decision: str,
        notes: str = '',
        decided_by,
    ) -> Debrief:
        """
        Record a hiring decision from a debrief.

        Args:
            debrief: Debrief instance
            decision: Decision (advance/reject/hold/pending)
            notes: Decision notes
            decided_by: User making decision

        Returns:
            Updated debrief
        """
        debrief.decision = decision
        debrief.notes = notes
        debrief.decided_by = decided_by
        debrief.decided_at = timezone.now()
        debrief.save(update_fields=['decision', 'notes', 'decided_by', 'decided_at', 'updated_at'])

        # Log event
        ApplicationEvent.objects.create(
            application=debrief.application,
            event_type='debrief.decision_made',
            actor=decided_by,
            metadata={
                'debrief_id': str(debrief.id),
                'decision': decision,
            },
        )

        return debrief

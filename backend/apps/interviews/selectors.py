"""Complex queries for interviews app."""

from django.db.models import Prefetch, Q
from django.utils import timezone

from .models import Interview, Scorecard


class InterviewSelector:
    """Selector for interview-related queries."""

    @staticmethod
    def get_upcoming_interviews(user=None, days_ahead: int = 7):
        """
        Get upcoming interviews within the next N days.

        Args:
            user: Optional user filter (internal user or candidate)
            days_ahead: Number of days to look ahead (default 7)

        Returns:
            QuerySet of Interview instances
        """
        now = timezone.now()
        end_date = now + timezone.timedelta(days=days_ahead)

        qs = Interview.objects.filter(
            scheduled_start__gte=now,
            scheduled_start__lte=end_date,
            status__in=['scheduled', 'confirmed', 'rescheduled'],
        ).select_related(
            'application__candidate__user',
            'application__requisition',
            'created_by',
            'scorecard_template',
        ).prefetch_related(
            'participants__interviewer__user',
        ).order_by('scheduled_start')

        if user:
            # Filter by interviewer or candidate
            qs = qs.filter(
                Q(participants__interviewer__user=user)
                | Q(application__candidate__user=user),
            ).distinct()

        return qs

    @staticmethod
    def get_pending_scorecards(interviewer):
        """
        Get interviews where interviewer has not yet submitted scorecard.

        Args:
            interviewer: InternalUser

        Returns:
            QuerySet of Interview instances
        """
        # Interviews where:
        # 1. User is a participant
        # 2. Interview is completed
        # 3. No submitted scorecard exists for this interviewer
        completed_interviews = Interview.objects.filter(
            participants__interviewer=interviewer,
            status='completed',
        ).select_related(
            'application__candidate__user',
            'application__requisition',
        ).order_by('-scheduled_start')

        # Exclude interviews where scorecard already submitted
        interviews_with_scorecard = Scorecard.objects.filter(
            interviewer=interviewer,
            is_draft=False,
        ).values_list('interview_id', flat=True)

        return completed_interviews.exclude(id__in=interviews_with_scorecard)

    @staticmethod
    def get_interviewer_availability(interviewer, start_date, end_date):
        """
        Get interviewer's scheduled interviews in a date range.
        Used to check availability when scheduling new interviews.

        Args:
            interviewer: InternalUser
            start_date: Start of date range
            end_date: End of date range

        Returns:
            QuerySet of Interview instances (scheduled conflicts)
        """
        return Interview.objects.filter(
            participants__interviewer=interviewer,
            scheduled_start__lt=end_date,
            scheduled_end__gt=start_date,
            status__in=['scheduled', 'confirmed', 'rescheduled'],
        ).select_related(
            'application__candidate__user',
            'application__requisition',
        ).order_by('scheduled_start')

    @staticmethod
    def get_interview_detail(interview_id: str):
        """
        Get full interview details with all related data.

        Args:
            interview_id: Interview UUID

        Returns:
            Interview instance with prefetched relations
        """
        return Interview.objects.select_related(
            'application__candidate__user',
            'application__requisition__department',
            'application__requisition__location',
            'application__current_stage',
            'interview_plan_stage',
            'scorecard_template',
            'created_by',
        ).prefetch_related(
            'participants__interviewer__user',
            Prefetch(
                'scorecards',
                queryset=Scorecard.objects.select_related(
                    'interviewer__user',
                ).prefetch_related('criterion_ratings__criterion'),
            ),
        ).get(id=interview_id)

    @staticmethod
    def get_application_interviews(application_id: str):
        """
        Get all interviews for an application.

        Args:
            application_id: Application UUID

        Returns:
            QuerySet of Interview instances
        """
        return Interview.objects.filter(
            application_id=application_id,
        ).select_related(
            'interview_plan_stage',
            'created_by',
        ).prefetch_related(
            'participants__interviewer__user',
        ).order_by('-scheduled_start')

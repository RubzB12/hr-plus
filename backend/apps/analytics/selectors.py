"""Selectors for analytics app."""

from django.db.models import Count, Q
from django.utils import timezone

from apps.applications.models import Application
from apps.jobs.models import Requisition


class DashboardSelector:
    """Selector for dashboard data aggregation."""

    @staticmethod
    def get_recruiter_dashboard(user):
        """
        Get recruiter dashboard data.

        Args:
            user: User requesting dashboard data

        Returns:
            Dictionary with dashboard metrics
        """
        # Get requisitions for departments user has access to
        if hasattr(user, 'internal_profile'):
            accessible_departments = [user.internal_profile.department_id] if user.internal_profile.department else []
        else:
            accessible_departments = []

        # Open requisitions
        open_reqs = Requisition.objects.filter(
            status='open',
        )
        if accessible_departments:
            open_reqs = open_reqs.filter(department_id__in=accessible_departments)

        open_reqs_count = open_reqs.count()

        # Active candidates (applied in last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        active_candidates = Application.objects.filter(
            applied_at__gte=thirty_days_ago,
            status__in=['applied', 'screening', 'interview'],
        )
        if accessible_departments:
            active_candidates = active_candidates.filter(
                requisition__department_id__in=accessible_departments,
            )

        active_candidates_count = active_candidates.count()

        # Pending scorecards for user
        if hasattr(user, 'internal_profile'):
            from apps.interviews.selectors import InterviewSelector

            pending_scorecards = InterviewSelector.get_pending_scorecards(
                user.internal_profile,
            )
            pending_scorecards_count = pending_scorecards.count()
        else:
            pending_scorecards_count = 0

        # Upcoming interviews (next 7 days) for user
        if hasattr(user, 'internal_profile'):
            from apps.interviews.selectors import InterviewSelector

            upcoming_interviews = InterviewSelector.get_upcoming_interviews(
                user=user,
                days_ahead=7,
            )
            upcoming_interviews_count = upcoming_interviews.count()
            upcoming_interviews_list = list(upcoming_interviews[:5])  # Top 5
        else:
            upcoming_interviews_count = 0
            upcoming_interviews_list = []

        # Pending approvals
        from apps.jobs.models import RequisitionApproval

        pending_approvals = RequisitionApproval.objects.filter(
            approver__user=user,
            status='pending',
        ).select_related('requisition')
        pending_approvals_count = pending_approvals.count()

        # Overdue actions (applications in screening/interview for > 14 days)
        fourteen_days_ago = timezone.now() - timezone.timedelta(days=14)
        overdue_applications = Application.objects.filter(
            status__in=['screening', 'interview'],
            updated_at__lt=fourteen_days_ago,
        )
        if accessible_departments:
            overdue_applications = overdue_applications.filter(
                requisition__department_id__in=accessible_departments,
            )

        overdue_actions_count = overdue_applications.count()

        return {
            'open_requisitions': open_reqs_count,
            'active_candidates': active_candidates_count,
            'pending_scorecards': pending_scorecards_count,
            'upcoming_interviews': upcoming_interviews_count,
            'upcoming_interviews_list': upcoming_interviews_list,
            'pending_approvals': pending_approvals_count,
            'overdue_actions': overdue_actions_count,
        }

    @staticmethod
    def get_pipeline_metrics(requisition_id: str):
        """
        Get pipeline metrics for a specific requisition.

        Args:
            requisition_id: Requisition UUID

        Returns:
            Dictionary with pipeline stage counts
        """
        from apps.jobs.models import PipelineStage

        stages = PipelineStage.objects.filter(
            requisition_id=requisition_id,
        ).annotate(
            application_count=Count(
                'applications',
                filter=Q(applications__status='active'),
            ),
        ).order_by('order')

        return {
            'stages': [
                {
                    'id': str(stage.id),
                    'name': stage.name,
                    'count': stage.application_count,
                }
                for stage in stages
            ],
        }

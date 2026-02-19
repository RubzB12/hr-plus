"""Complex queries for applications and pipeline boards."""

from django.db.models import Count, Prefetch, Q

from apps.jobs.models import PipelineStage

from .models import Application


class ApplicationSelector:
    """Optimized queries for application data."""

    @staticmethod
    def get_pipeline_board(requisition_id):
        """
        Returns pipeline stages with nested applications for a Kanban board.
        Optimized to avoid N+1 queries.
        """
        return (
            PipelineStage.objects
            .filter(requisition_id=requisition_id)
            .prefetch_related(
                Prefetch(
                    'applications',
                    queryset=Application.objects.select_related(
                        'candidate__user',
                        'candidate_score',
                    ).filter(
                        status__in=[
                            'applied', 'screening', 'interview',
                            'assessment', 'offer',
                        ],
                    ).order_by('-applied_at'),
                ),
            )
            .annotate(
                application_count=Count(
                    'applications',
                    filter=Q(applications__status__in=[
                        'applied', 'screening', 'interview',
                        'assessment', 'offer',
                    ]),
                ),
            )
            .order_by('order')
        )

    @staticmethod
    def get_application_detail(application_id):
        """
        Returns a fully loaded application for the detail view.
        """
        return (
            Application.objects
            .select_related(
                'candidate__user',
                'requisition__department',
                'requisition__location',
                'requisition__hiring_manager__user',
                'requisition__recruiter__user',
                'current_stage',
                'candidate_score',
            )
            .prefetch_related(
                'events__actor',
                'events__from_stage',
                'events__to_stage',
                'application_tags__tag',
                'notes__author__user',
            )
            .get(id=application_id)
        )

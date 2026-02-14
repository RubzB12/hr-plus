"""Complex queries for job listings."""

from django.db.models import Count, Q

from .models import Requisition


class JobSelector:
    """Queries for public job listings."""

    @staticmethod
    def get_active_jobs(filters: dict | None = None):
        """Return published, open requisitions for the public career site."""
        qs = (
            Requisition.objects
            .filter(status='open', published_at__isnull=False)
            .select_related('department', 'location', 'level')
            .only(
                'id', 'requisition_id', 'title', 'slug',
                'employment_type', 'remote_policy',
                'salary_min', 'salary_max', 'salary_currency',
                'department__name', 'location__name', 'location__city',
                'location__country', 'level__name',
                'published_at', 'created_at',
            )
        )

        if not filters:
            return qs.order_by('-published_at')

        if filters.get('department'):
            qs = qs.filter(department__name__iexact=filters['department'])
        if filters.get('location'):
            qs = qs.filter(
                Q(location__city__icontains=filters['location'])
                | Q(location__country__icontains=filters['location'])
            )
        if filters.get('employment_type'):
            qs = qs.filter(employment_type=filters['employment_type'])
        if filters.get('remote_policy'):
            qs = qs.filter(remote_policy=filters['remote_policy'])
        if filters.get('search'):
            term = filters['search']
            qs = qs.filter(
                Q(title__icontains=term)
                | Q(description__icontains=term)
            )

        return qs.order_by('-published_at')

    @staticmethod
    def get_job_by_slug(slug: str):
        """Return a single published job by slug with full detail."""
        return (
            Requisition.objects
            .filter(status='open', published_at__isnull=False, slug=slug)
            .select_related('department', 'location', 'level', 'team')
            .first()
        )

    @staticmethod
    def get_categories():
        """Return departments with counts of open jobs."""
        return (
            Requisition.objects
            .filter(status='open', published_at__isnull=False)
            .values('department__id', 'department__name')
            .annotate(job_count=Count('id'))
            .order_by('department__name')
        )

    @staticmethod
    def get_similar_jobs(requisition: Requisition, limit: int = 4):
        """Return similar jobs based on department and level."""
        return (
            Requisition.objects
            .filter(status='open', published_at__isnull=False)
            .filter(
                Q(department=requisition.department)
                | Q(level=requisition.level)
            )
            .exclude(id=requisition.id)
            .select_related('department', 'location', 'level')
            .order_by('-published_at')[:limit]
        )

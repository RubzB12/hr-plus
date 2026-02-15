"""Job search service using Elasticsearch."""

from elasticsearch_dsl import Q
from elasticsearch_dsl.query import MultiMatch

from .documents import JobDocument
from .models import Requisition


class JobSearchService:
    """Search jobs using Elasticsearch with database fallback."""

    @staticmethod
    def search(
        query: str = '',
        *,
        department: str | None = None,
        location_city: str | None = None,
        location_country: str | None = None,
        employment_type: str | None = None,
        remote_policy: str | None = None,
        salary_min: int | None = None,
        limit: int = 100,
    ):
        """
        Search jobs with filters.

        Uses Elasticsearch for full-text search with fallback to database.
        """
        try:
            return JobSearchService._elasticsearch_search(
                query=query,
                department=department,
                location_city=location_city,
                location_country=location_country,
                employment_type=employment_type,
                remote_policy=remote_policy,
                salary_min=salary_min,
                limit=limit,
            )
        except Exception as e:
            # Fallback to database search
            print(f'Elasticsearch search failed: {e}, falling back to database')
            return JobSearchService._database_search(
                query=query,
                department=department,
                location_city=location_city,
                employment_type=employment_type,
                remote_policy=remote_policy,
                limit=limit,
            )

    @staticmethod
    def _elasticsearch_search(
        query: str = '',
        *,
        department: str | None = None,
        location_city: str | None = None,
        location_country: str | None = None,
        employment_type: str | None = None,
        remote_policy: str | None = None,
        salary_min: int | None = None,
        limit: int = 100,
    ):
        """Elasticsearch-based job search."""
        search = JobDocument.search()

        # Only search open jobs
        search = search.filter('term', status='open')

        # Full-text search across job fields
        if query:
            search = search.query(
                MultiMatch(
                    query=query,
                    fields=[
                        'title^3',  # Boost title matches
                        'description^2',
                        'requirements_required',
                        'requirements_preferred',
                        'department',
                        'location',
                    ],
                    fuzziness='AUTO',  # Typo tolerance
                    operator='or',
                ),
            )

        # Apply filters
        filters = []

        if department:
            filters.append(Q('match', department=department))

        if location_city:
            filters.append(Q('match', location_city=location_city))

        if location_country:
            filters.append(Q('term', location_country=location_country))

        if employment_type:
            filters.append(Q('term', employment_type=employment_type))

        if remote_policy:
            filters.append(Q('term', remote_policy=remote_policy))

        if salary_min is not None:
            # Job's max salary should be >= candidate's min requirement
            filters.append(
                Q('range', salary_max={'gte': salary_min}) |
                Q('bool', must_not=[Q('exists', field='salary_max')]),
            )

        # Apply all filters
        if filters:
            search = search.query('bool', filter=filters)

        # Sort by relevance (score) by default, then published date
        search = search.sort('-_score', '-published_at')

        # Execute search
        search = search[:limit]
        response = search.execute()

        # Convert to queryset
        job_ids = [hit.meta.id for hit in response]
        queryset = Requisition.objects.filter(
            id__in=job_ids,
            status='open',
        ).select_related('department', 'location', 'level')

        # Preserve search order
        id_to_job = {str(j.id): j for j in queryset}
        ordered_jobs = [id_to_job[jid] for jid in job_ids if jid in id_to_job]

        return ordered_jobs

    @staticmethod
    def _database_search(
        query: str = '',
        *,
        department: str | None = None,
        location_city: str | None = None,
        employment_type: str | None = None,
        remote_policy: str | None = None,
        limit: int = 100,
    ):
        """Database fallback using ILIKE search."""
        from django.db.models import Q as DbQ

        queryset = Requisition.objects.filter(
            status='open',
        ).select_related('department', 'location', 'level')

        # Full-text search approximation
        if query:
            queryset = queryset.filter(
                DbQ(title__icontains=query) |
                DbQ(description__icontains=query) |
                DbQ(requirements_required__icontains=query) |
                DbQ(department__name__icontains=query),
            )

        # Apply filters
        if department:
            queryset = queryset.filter(department__name__icontains=department)

        if location_city:
            queryset = queryset.filter(location__city__icontains=location_city)

        if employment_type:
            queryset = queryset.filter(employment_type=employment_type)

        if remote_policy:
            queryset = queryset.filter(remote_policy=remote_policy)

        return list(queryset.order_by('-published_at')[:limit])

    @staticmethod
    def suggest_jobs(query: str, limit: int = 5):
        """
        Get job title suggestions for autocomplete.

        Uses Elasticsearch completion suggester.
        """
        try:
            search = JobDocument.search()
            search = search.filter('term', status='open')
            search = search.suggest(
                'job_suggestions',
                query,
                completion={'field': 'title.suggest', 'size': limit},
            )
            response = search.execute()

            if hasattr(response, 'suggest') and 'job_suggestions' in response.suggest:
                suggestions = response.suggest.job_suggestions[0].options
                return [s.text for s in suggestions]
            return []
        except Exception:
            # Fallback to simple title prefix match
            jobs = Requisition.objects.filter(
                status='open',
                title__istartswith=query,
            ).values_list('title', flat=True)[:limit]
            return list(jobs)

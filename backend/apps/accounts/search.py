"""Candidate search service using Elasticsearch."""

from django.conf import settings
from .models import CandidateProfile

# Conditionally import Elasticsearch dependencies
ELASTICSEARCH_AVAILABLE = False
try:
    if settings.ELASTICSEARCH_ENABLED:
        from elasticsearch_dsl import Q
        from elasticsearch_dsl.query import MultiMatch
        from .documents import CandidateDocument
        ELASTICSEARCH_AVAILABLE = True
except (ImportError, AttributeError):
    pass


class CandidateSearchService:
    """Search candidates using Elasticsearch with database fallback."""

    @staticmethod
    def search(
        query: str = '',
        *,
        skills: list[str] | None = None,
        location_city: str | None = None,
        location_country: str | None = None,
        experience_min: int | None = None,
        experience_max: int | None = None,
        work_authorization: str | None = None,
        source: str | None = None,
        salary_max: int | None = None,
        limit: int = 100,
    ):
        """
        Search candidates with filters.

        Uses Elasticsearch for full-text search with fallback to database.
        """
        # Use database search if Elasticsearch is not available
        if not ELASTICSEARCH_AVAILABLE:
            return CandidateSearchService._database_search(
                query=query,
                skills=skills,
                location_city=location_city,
                location_country=location_country,
                source=source,
                limit=limit,
            )

        try:
            return CandidateSearchService._elasticsearch_search(
                query=query,
                skills=skills,
                location_city=location_city,
                location_country=location_country,
                experience_min=experience_min,
                experience_max=experience_max,
                work_authorization=work_authorization,
                source=source,
                salary_max=salary_max,
                limit=limit,
            )
        except Exception as e:
            # Fallback to database search
            print(f'Elasticsearch search failed: {e}, falling back to database')
            return CandidateSearchService._database_search(
                query=query,
                skills=skills,
                location_city=location_city,
                location_country=location_country,
                source=source,
                limit=limit,
            )

    @staticmethod
    def _elasticsearch_search(
        query: str = '',
        *,
        skills: list[str] | None = None,
        location_city: str | None = None,
        location_country: str | None = None,
        experience_min: int | None = None,
        experience_max: int | None = None,
        work_authorization: str | None = None,
        source: str | None = None,
        salary_max: int | None = None,
        limit: int = 100,
    ):
        """Elasticsearch-based search."""
        search = CandidateDocument.search()

        # Full-text search across multiple fields
        if query:
            search = search.query(
                MultiMatch(
                    query=query,
                    fields=[
                        'full_name^3',  # Boost name matches
                        'email^2',
                        'skills^2',
                        'resume_parsed.summary',
                        'location_city',
                    ],
                    fuzziness='AUTO',  # Typo tolerance
                    operator='or',
                ),
            )

        # Apply filters
        filters = []

        if skills:
            # Match any of the specified skills
            skill_queries = [Q('match', skills=skill) for skill in skills]
            filters.append(Q('bool', should=skill_queries, minimum_should_match=1))

        if location_city:
            filters.append(Q('match', location_city=location_city))

        if location_country:
            filters.append(Q('term', location_country=location_country))

        if experience_min is not None:
            filters.append(Q('range', experience_years={'gte': experience_min}))

        if experience_max is not None:
            filters.append(Q('range', experience_years={'lte': experience_max}))

        if work_authorization:
            filters.append(Q('term', work_authorization=work_authorization))

        if source:
            filters.append(Q('term', source=source))

        if salary_max is not None:
            # Candidate's minimum salary preference should be <= employer's max
            filters.append(
                Q('range', preferred_salary_min={'lte': salary_max}) |
                Q('bool', must_not=[Q('exists', field='preferred_salary_min')]),
            )

        # Apply all filters
        if filters:
            search = search.query('bool', filter=filters)

        # Execute search
        search = search[:limit]
        response = search.execute()

        # Convert to queryset
        candidate_ids = [hit.meta.id for hit in response]
        queryset = CandidateProfile.objects.filter(
            id__in=candidate_ids,
        ).select_related('user')

        # Preserve search order
        id_to_candidate = {str(c.id): c for c in queryset}
        ordered_candidates = [
            id_to_candidate[cid] for cid in candidate_ids if cid in id_to_candidate
        ]

        return ordered_candidates

    @staticmethod
    def _database_search(
        query: str = '',
        *,
        skills: list[str] | None = None,
        location_city: str | None = None,
        location_country: str | None = None,
        source: str | None = None,
        limit: int = 100,
    ):
        """Database fallback using ILIKE search."""
        from django.db.models import Q as DbQ

        queryset = CandidateProfile.objects.select_related('user')

        # Full-text search approximation
        if query:
            queryset = queryset.filter(
                DbQ(user__first_name__icontains=query) |
                DbQ(user__last_name__icontains=query) |
                DbQ(user__email__icontains=query) |
                DbQ(location_city__icontains=query),
            )

        # Apply filters
        if skills:
            # Simple contains check - not as sophisticated as ES
            for skill in skills:
                queryset = queryset.filter(
                    DbQ(resume_parsed__icontains=skill),
                )

        if location_city:
            queryset = queryset.filter(location_city__icontains=location_city)

        if location_country:
            queryset = queryset.filter(location_country=location_country)

        if source:
            queryset = queryset.filter(source=source)

        return list(queryset[:limit])

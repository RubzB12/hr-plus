"""Celery tasks for accounts app."""

from celery import shared_task
from django_elasticsearch_dsl.registries import registry


@shared_task
def index_candidate(candidate_id):
    """Index a single candidate in Elasticsearch."""
    from .models import CandidateProfile

    try:
        candidate = CandidateProfile.objects.get(id=candidate_id)
        registry.update(candidate)
        return f'Indexed candidate {candidate_id}'
    except CandidateProfile.DoesNotExist:
        return f'Candidate {candidate_id} not found'
    except Exception as e:
        return f'Error indexing candidate {candidate_id}: {str(e)}'


@shared_task
def delete_candidate_from_index(candidate_id):
    """Remove a candidate from Elasticsearch index."""
    from .documents import CandidateDocument

    try:
        CandidateDocument().get(id=candidate_id).delete()
        return f'Deleted candidate {candidate_id} from index'
    except Exception as e:
        return f'Error deleting candidate {candidate_id}: {str(e)}'


@shared_task
def reindex_all_candidates():
    """Reindex all candidates in Elasticsearch."""
    from .documents import CandidateDocument

    try:
        # Rebuild the entire index
        CandidateDocument().init()
        count = 0
        for candidate in CandidateDocument().get_queryset():
            registry.update(candidate)
            count += 1
        return f'Reindexed {count} candidates'
    except Exception as e:
        return f'Error reindexing candidates: {str(e)}'

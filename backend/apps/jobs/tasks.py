"""Celery tasks for jobs app."""

from celery import shared_task
from django_elasticsearch_dsl.registries import registry


@shared_task
def index_job(requisition_id):
    """Index a single job in Elasticsearch."""
    from .models import Requisition

    try:
        requisition = Requisition.objects.get(id=requisition_id)
        # Only index if job is open
        if requisition.status == 'open':
            registry.update(requisition)
            return f'Indexed job {requisition_id}'
        return f'Job {requisition_id} not open, skipping index'
    except Requisition.DoesNotExist:
        return f'Job {requisition_id} not found'
    except Exception as e:
        return f'Error indexing job {requisition_id}: {str(e)}'


@shared_task
def delete_job_from_index(requisition_id):
    """Remove a job from Elasticsearch index."""
    from .documents import JobDocument

    try:
        JobDocument().get(id=requisition_id).delete()
        return f'Deleted job {requisition_id} from index'
    except Exception as e:
        return f'Error deleting job {requisition_id}: {str(e)}'


@shared_task
def reindex_all_jobs():
    """Reindex all open jobs in Elasticsearch."""
    from .documents import JobDocument

    try:
        # Rebuild the entire index
        JobDocument().init()
        count = 0
        for job in JobDocument().get_queryset():
            registry.update(job)
            count += 1
        return f'Reindexed {count} jobs'
    except Exception as e:
        return f'Error reindexing jobs: {str(e)}'

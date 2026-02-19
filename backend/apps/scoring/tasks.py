"""Celery tasks for async scoring and batch re-scoring."""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name='scoring.score_application_task',
)
def score_application_task(self, application_id: str) -> dict:
    """Score a single application asynchronously."""
    try:
        from apps.applications.models import Application
        from .services import ScoringService

        application = Application.objects.get(id=application_id)
        score = ScoringService.score_application(application)
        return {
            'application_id': str(application_id),
            'final_score': score.final_score,
        }
    except Exception as exc:
        logger.exception(
            'score_application_task failed for application_id=%s', application_id
        )
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    name='scoring.rescore_requisition_task',
    time_limit=600,
)
def rescore_requisition_task(self, requisition_id: str) -> dict:
    """Re-score all active applications for a requisition after criteria change."""
    try:
        from apps.applications.models import Application
        from .services import ScoringService

        applications = Application.objects.filter(
            requisition_id=requisition_id,
            status__in=['applied', 'screening', 'interview', 'assessment', 'offer'],
        )

        count = 0
        for app in applications.iterator():
            try:
                ScoringService.score_application(app)
                count += 1
            except Exception:
                logger.exception(
                    'Failed to score application %s during batch rescore', app.id
                )

        return {
            'requisition_id': str(requisition_id),
            'scored_count': count,
        }
    except Exception as exc:
        logger.exception(
            'rescore_requisition_task failed for requisition_id=%s', requisition_id
        )
        raise self.retry(exc=exc)

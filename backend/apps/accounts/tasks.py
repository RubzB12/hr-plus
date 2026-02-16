"""Celery tasks for accounts app."""

from celery import shared_task
from django.conf import settings
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


@shared_task
def send_job_alerts_for_saved_search(saved_search_id):
    """
    Check for new jobs matching a saved search and send alerts.

    Called when a new job is published or on a scheduled basis.
    """
    from django.utils import timezone
    from django.db.models import Q
    from .models import SavedSearch, JobAlert
    from apps.jobs.models import Requisition
    from apps.communications.services import EmailService

    try:
        saved_search = SavedSearch.objects.select_related('candidate__user').get(
            id=saved_search_id,
            is_active=True,
        )
    except SavedSearch.DoesNotExist:
        return f'SavedSearch {saved_search_id} not found or inactive'

    # Build queryset based on search params
    queryset = Requisition.objects.filter(
        status='open',
        is_published=True,
    )
    params = saved_search.search_params

    # Apply filters
    if params.get('keywords'):
        queryset = queryset.filter(
            Q(title__icontains=params['keywords']) |
            Q(description__icontains=params['keywords'])
        )

    if params.get('department'):
        queryset = queryset.filter(department__name__icontains=params['department'])

    if params.get('location_city'):
        queryset = queryset.filter(location__city__icontains=params['location_city'])

    if params.get('employment_type'):
        queryset = queryset.filter(employment_type=params['employment_type'])

    if params.get('remote_policy'):
        queryset = queryset.filter(remote_policy=params['remote_policy'])

    # Get jobs published since last notification
    if saved_search.last_notified_at:
        queryset = queryset.filter(published_at__gt=saved_search.last_notified_at)

    # Exclude jobs already sent
    already_sent_ids = JobAlert.objects.filter(
        saved_search=saved_search
    ).values_list('requisition_id', flat=True)
    queryset = queryset.exclude(id__in=already_sent_ids)

    new_jobs = list(queryset.select_related('department', 'location')[:10])

    if not new_jobs:
        return f'No new jobs for saved search {saved_search_id}'

    # Create JobAlert records
    alerts_created = []
    for job in new_jobs:
        alert, created = JobAlert.objects.get_or_create(
            saved_search=saved_search,
            requisition=job,
        )
        if created:
            alerts_created.append(alert)

    # Send email with new job matches
    if alerts_created:
        try:
            EmailService.send_templated_email(
                template_name='Job Alert',
                recipient=saved_search.candidate.user.email,
                context={
                    'user_name': saved_search.candidate.user.get_full_name(),
                    'search_name': saved_search.name,
                    'jobs': [
                        {
                            'title': job.title,
                            'department': job.department.name,
                            'location': job.location.name if job.location else 'Remote',
                            'url': f'{settings.PUBLIC_CAREERS_URL}/jobs/{job.slug}',
                        }
                        for job in new_jobs
                    ],
                    'job_count': len(new_jobs),
                    'manage_alerts_url': f'{settings.PUBLIC_CAREERS_URL}/dashboard/saved-searches',
                },
            )

            # Update last_notified_at
            saved_search.last_notified_at = timezone.now()
            saved_search.match_count = Requisition.objects.filter(
                status='open', is_published=True
            ).count()
            saved_search.save(update_fields=['last_notified_at', 'match_count'])

            return f'Sent {len(alerts_created)} job alerts for saved search {saved_search_id}'

        except Exception as e:
            return f'Error sending email for saved search {saved_search_id}: {str(e)}'

    return f'Created {len(alerts_created)} alerts but no email sent'


@shared_task
def process_all_job_alerts():
    """
    Process all active saved searches and send alerts.

    Should be called periodically (e.g., daily via Celery Beat).
    """
    from .models import SavedSearch
    from django.utils import timezone
    from datetime import timedelta

    # Process instant alerts (not notified in last hour)
    instant_searches = SavedSearch.objects.filter(
        is_active=True,
        alert_frequency='instant',
    ).filter(
        Q(last_notified_at__isnull=True) |
        Q(last_notified_at__lt=timezone.now() - timedelta(hours=1))
    )

    for search in instant_searches:
        send_job_alerts_for_saved_search.delay(search.id)

    # Process daily alerts (not notified today)
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    daily_searches = SavedSearch.objects.filter(
        is_active=True,
        alert_frequency='daily',
    ).filter(
        Q(last_notified_at__isnull=True) |
        Q(last_notified_at__lt=today_start)
    )

    for search in daily_searches:
        send_job_alerts_for_saved_search.delay(search.id)

    # Process weekly alerts (not notified in last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    weekly_searches = SavedSearch.objects.filter(
        is_active=True,
        alert_frequency='weekly',
    ).filter(
        Q(last_notified_at__isnull=True) |
        Q(last_notified_at__lt=week_ago)
    )

    for search in weekly_searches:
        send_job_alerts_for_saved_search.delay(search.id)

    total = instant_searches.count() + daily_searches.count() + weekly_searches.count()
    return f'Queued job alerts for {total} saved searches'

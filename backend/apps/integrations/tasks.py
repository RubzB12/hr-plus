"""Celery tasks for integrations."""

import hashlib
import hmac
import json
import logging

import requests
from celery import shared_task
from django.utils import timezone

from .models import Integration, WebhookDelivery
from .services import IntegrationService, JobBoardService, WebhookService

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='integrations.deliver_webhook', max_retries=3)
def deliver_webhook(self, delivery_id: str):
    """
    Deliver webhook to external endpoint with retry logic.

    This task is queued by WebhookService.dispatch_event() and will
    retry up to 3 times with exponential backoff on failure.

    Args:
        delivery_id: UUID of WebhookDelivery instance
    """
    try:
        delivery = WebhookDelivery.objects.select_related('endpoint').get(id=delivery_id)
    except WebhookDelivery.DoesNotExist:
        logger.error(f'WebhookDelivery {delivery_id} not found')
        return {'success': False, 'message': 'Delivery not found'}

    endpoint = delivery.endpoint

    if not endpoint.is_active:
        logger.warning(f'Webhook endpoint {endpoint.url} is not active')
        return {'success': False, 'message': 'Endpoint is not active'}

    try:
        # Sign payload
        signature = WebhookService.sign_payload(delivery.payload, endpoint.secret)

        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Signature': signature,
            'X-Event-Type': delivery.event_type,
            'User-Agent': 'HR-Plus-Webhook/1.0',
        }

        # Add custom headers from endpoint
        if endpoint.headers:
            headers.update(endpoint.headers)

        # Make HTTP POST request
        response = requests.post(
            endpoint.url,
            json=delivery.payload,
            headers=headers,
            timeout=30,  # 30 second timeout
        )

        # Update delivery record
        delivery.response_status = response.status_code
        delivery.response_body = response.text[:1000]  # Truncate to 1000 chars

        # Check if successful (2xx status code)
        if 200 <= response.status_code < 300:
            delivery.delivered_at = timezone.now()
            delivery.save()

            # Reset endpoint failure count on success
            if endpoint.failure_count > 0:
                endpoint.failure_count = 0
                endpoint.last_success = timezone.now()
                endpoint.save(update_fields=['failure_count', 'last_success', 'updated_at'])

            logger.info(
                f'Successfully delivered webhook {delivery_id} to {endpoint.url} '
                f'(status: {response.status_code})'
            )

            return {
                'success': True,
                'message': 'Webhook delivered successfully',
                'status_code': response.status_code,
            }
        else:
            # Non-2xx status - count as failure
            delivery.error_message = f'HTTP {response.status_code}: {response.text[:500]}'
            delivery.save()

            # Increment endpoint failure count
            endpoint.failure_count += 1
            endpoint.last_failure = timezone.now()
            endpoint.save(update_fields=['failure_count', 'last_failure', 'updated_at'])

            # Auto-disable endpoint if too many failures
            if endpoint.should_disable:
                WebhookService.disable_failing_endpoint(endpoint)

            # Retry
            raise Exception(f'Webhook delivery failed with status {response.status_code}')

    except requests.exceptions.Timeout:
        logger.error(f'Webhook delivery {delivery_id} timed out')
        delivery.error_message = 'Request timed out'
        delivery.save()

        # Retry with exponential backoff
        raise self.retry(exc=Exception('Timeout'), countdown=60 * (2 ** self.request.retries))

    except requests.exceptions.RequestException as exc:
        logger.error(f'Webhook delivery {delivery_id} failed: {str(exc)}')
        delivery.error_message = str(exc)[:500]
        delivery.save()

        # Increment endpoint failure count
        endpoint.failure_count += 1
        endpoint.last_failure = timezone.now()
        endpoint.save(update_fields=['failure_count', 'last_failure', 'updated_at'])

        # Auto-disable endpoint if too many failures
        if endpoint.should_disable:
            WebhookService.disable_failing_endpoint(endpoint)

        # Retry with exponential backoff (60s, 120s, 240s)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(name='integrations.sync_job_to_board')
def sync_job_to_board(requisition_id: str, integration_id: str):
    """
    Post or update job on external job board.

    Args:
        requisition_id: UUID of Requisition
        integration_id: UUID of Integration (job board)

    Returns:
        Dict with success status and posting details
    """
    from apps.jobs.models import Requisition

    try:
        requisition = Requisition.objects.get(id=requisition_id)
        integration = Integration.objects.get(id=integration_id)

        # Post job to board
        posting = JobBoardService.post_job(requisition, integration)

        return {
            'success': True,
            'message': 'Job posted successfully',
            'posting_id': str(posting.id),
            'external_id': posting.external_id,
            'url': posting.url,
        }

    except Requisition.DoesNotExist:
        logger.error(f'Requisition {requisition_id} not found')
        return {'success': False, 'message': 'Requisition not found'}
    except Integration.DoesNotExist:
        logger.error(f'Integration {integration_id} not found')
        return {'success': False, 'message': 'Integration not found'}
    except Exception as e:
        logger.error(f'Failed to sync job to board: {str(e)}')
        return {'success': False, 'message': str(e)}


@shared_task(name='integrations.import_board_applications')
def import_board_applications():
    """
    Import new applications from all active job boards.

    This task should be scheduled to run periodically (e.g., every 15 minutes).
    """
    # Get all active job board integrations
    job_boards = Integration.objects.filter(
        category='job_board', is_active=True, sync_status__in=['idle', 'success']
    )

    total_imported = 0
    boards_synced = 0

    for integration in job_boards:
        try:
            # Mark as syncing
            IntegrationService.mark_sync_status(integration, 'syncing')

            # Import applications
            applications = JobBoardService.import_applications(integration)
            total_imported += len(applications)

            # Mark as successful
            IntegrationService.mark_sync_status(integration, 'success')
            boards_synced += 1

            logger.info(
                f'Imported {len(applications)} applications from {integration.provider}'
            )

        except Exception as e:
            logger.error(f'Failed to import applications from {integration.provider}: {str(e)}')
            IntegrationService.mark_sync_status(integration, 'error', str(e))

    return {
        'success': True,
        'boards_synced': boards_synced,
        'total_imported': total_imported,
        'message': f'Imported {total_imported} applications from {boards_synced} job boards',
    }


@shared_task(name='integrations.sync_hris_departments')
def sync_hris_departments():
    """
    Sync departments from all active HRIS integrations.

    This task should be scheduled to run daily.
    """
    from .services import HRISService

    # Get all active HRIS integrations
    hris_systems = Integration.objects.filter(
        category='hris', is_active=True, sync_status__in=['idle', 'success']
    )

    total_created = 0
    total_updated = 0
    systems_synced = 0

    for integration in hris_systems:
        try:
            # Sync departments
            result = HRISService.sync_departments(integration)
            total_created += result['created']
            total_updated += result['updated']
            systems_synced += 1

            logger.info(
                f'Synced departments from {integration.provider}: '
                f'{result["created"]} created, {result["updated"]} updated'
            )

        except Exception as e:
            logger.error(f'Failed to sync departments from {integration.provider}: {str(e)}')
            IntegrationService.mark_sync_status(integration, 'error', str(e))

    return {
        'success': True,
        'systems_synced': systems_synced,
        'departments_created': total_created,
        'departments_updated': total_updated,
        'message': f'Synced {total_created + total_updated} departments from {systems_synced} HRIS systems',
    }


@shared_task(name='integrations.refresh_integration_tokens')
def refresh_integration_tokens():
    """
    Refresh OAuth tokens for integrations that need it.

    This task should be scheduled to run hourly to prevent token expiration.
    """
    from datetime import timedelta

    # Get integrations with tokens expiring in next 2 hours
    expiry_threshold = timezone.now() + timedelta(hours=2)

    integrations = Integration.objects.filter(
        is_active=True,
        oauth_token__isnull=False,
        oauth_refresh_token__isnull=False,
        oauth_expires_at__lt=expiry_threshold,
    )

    refreshed_count = 0
    failed_count = 0

    for integration in integrations:
        try:
            # Refresh token
            IntegrationService.refresh_oauth_token(integration)
            refreshed_count += 1

            logger.info(f'Refreshed OAuth token for {integration}')

        except Exception as e:
            logger.error(f'Failed to refresh OAuth token for {integration}: {str(e)}')
            failed_count += 1

    return {
        'success': True,
        'refreshed': refreshed_count,
        'failed': failed_count,
        'message': f'Refreshed {refreshed_count} OAuth tokens, {failed_count} failed',
    }

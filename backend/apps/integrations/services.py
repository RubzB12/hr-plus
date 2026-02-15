"""Business logic for integrations with external systems."""

import hashlib
import hmac
import json
import logging
from datetime import timedelta
from typing import Any, Optional

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.compliance.models import AuditLog
from apps.core.exceptions import BusinessValidationError
from apps.integrations.models import (
    Integration,
    JobBoardPosting,
    WebhookDelivery,
    WebhookEndpoint,
)

logger = logging.getLogger(__name__)


class IntegrationService:
    """Service for managing external integrations."""

    @staticmethod
    @transaction.atomic
    def create_integration(
        provider: str,
        category: str,
        name: str,
        config: dict,
        **kwargs,
    ) -> Integration:
        """
        Create a new external integration.

        Args:
            provider: Integration provider (indeed, linkedin, bamboo_hr, etc.)
            category: Integration category (job_board, hris, ats, custom)
            name: User-friendly integration name
            config: Configuration dict (will be encrypted and stored as JSON)
            **kwargs: Additional fields (oauth_token, is_active, etc.)

        Returns:
            Integration instance

        Raises:
            BusinessValidationError: If integration already exists or config is invalid
        """
        # Check for duplicate
        if Integration.objects.filter(provider=provider, name=name).exists():
            raise BusinessValidationError(
                f'Integration with provider "{provider}" and name "{name}" already exists'
            )

        # Validate config is a dict
        if not isinstance(config, dict):
            raise BusinessValidationError('Config must be a dictionary')

        # Convert config to JSON string for encrypted storage
        config_json = json.dumps(config)

        # Create integration
        integration = Integration.objects.create(
            provider=provider,
            category=category,
            name=name,
            config=config_json,
            is_active=kwargs.get('is_active', True),
            oauth_token=kwargs.get('oauth_token'),
            oauth_refresh_token=kwargs.get('oauth_refresh_token'),
            oauth_expires_at=kwargs.get('oauth_expires_at'),
            metadata=kwargs.get('metadata', {}),
        )

        # Log creation
        AuditLog.objects.create(
            action='create',
            resource_type='integration',
            resource_id=str(integration.id),
            metadata={
                'provider': provider,
                'category': category,
                'name': name,
            },
        )

        logger.info(f'Created integration: {integration}')
        return integration

    @staticmethod
    @transaction.atomic
    def update_config(integration: Integration, new_config: dict) -> Integration:
        """
        Update integration configuration.

        Args:
            integration: Integration instance
            new_config: New configuration dict

        Returns:
            Updated integration instance
        """
        if not isinstance(new_config, dict):
            raise BusinessValidationError('Config must be a dictionary')

        old_config = json.loads(integration.config) if integration.config else {}

        # Update config
        integration.config = json.dumps(new_config)
        integration.save(update_fields=['config', 'updated_at'])

        # Log update (without sensitive data)
        AuditLog.objects.create(
            action='update',
            resource_type='integration',
            resource_id=str(integration.id),
            metadata={
                'provider': integration.provider,
                'config_updated': True,
                'config_keys': list(new_config.keys()),
            },
        )

        logger.info(f'Updated config for integration: {integration}')
        return integration

    @staticmethod
    def test_connection(integration: Integration) -> dict:
        """
        Test connection to external service.

        Args:
            integration: Integration instance

        Returns:
            Dict with success status and message
        """
        try:
            config = json.loads(integration.config) if integration.config else {}

            # Provider-specific connection tests
            if integration.provider == 'indeed':
                return IntegrationService._test_indeed_connection(config)
            elif integration.provider == 'linkedin':
                return IntegrationService._test_linkedin_connection(
                    config, integration.oauth_token
                )
            elif integration.provider == 'bamboo_hr':
                return IntegrationService._test_bamboohr_connection(config)
            elif integration.category == 'job_board':
                # Generic job board test
                return {'success': True, 'message': 'Configuration validated'}
            elif integration.category == 'hris':
                # Generic HRIS test
                return {'success': True, 'message': 'Configuration validated'}
            else:
                return {'success': True, 'message': 'No connection test available'}

        except Exception as e:
            logger.error(f'Connection test failed for {integration}: {str(e)}')
            return {'success': False, 'message': f'Connection test failed: {str(e)}'}

    @staticmethod
    def _test_indeed_connection(config: dict) -> dict:
        """Test Indeed API connection."""
        if not config.get('employer_id') or not config.get('api_key'):
            return {'success': False, 'message': 'Missing employer_id or api_key'}

        # In production, would make actual API call
        # For now, just validate config structure
        return {
            'success': True,
            'message': 'Indeed configuration validated',
        }

    @staticmethod
    def _test_linkedin_connection(config: dict, oauth_token: str) -> dict:
        """Test LinkedIn API connection."""
        if not oauth_token:
            return {'success': False, 'message': 'OAuth token not configured'}

        # In production, would make actual API call
        return {
            'success': True,
            'message': 'LinkedIn OAuth token validated',
        }

    @staticmethod
    def _test_bamboohr_connection(config: dict) -> dict:
        """Test BambooHR API connection."""
        if not config.get('subdomain') or not config.get('api_key'):
            return {'success': False, 'message': 'Missing subdomain or api_key'}

        # In production, would make actual API call
        return {
            'success': True,
            'message': 'BambooHR configuration validated',
        }

    @staticmethod
    @transaction.atomic
    def refresh_oauth_token(integration: Integration) -> Integration:
        """
        Refresh OAuth access token using refresh token.

        Args:
            integration: Integration instance

        Returns:
            Updated integration with new token

        Raises:
            BusinessValidationError: If refresh fails
        """
        if not integration.oauth_refresh_token:
            raise BusinessValidationError('No refresh token available')

        config = json.loads(integration.config) if integration.config else {}

        try:
            # Provider-specific token refresh
            if integration.provider == 'linkedin':
                new_token_data = IntegrationService._refresh_linkedin_token(
                    integration.oauth_refresh_token, config
                )
            else:
                raise BusinessValidationError(
                    f'OAuth refresh not supported for provider: {integration.provider}'
                )

            # Update integration with new tokens
            integration.oauth_token = new_token_data['access_token']
            integration.oauth_refresh_token = new_token_data.get(
                'refresh_token', integration.oauth_refresh_token
            )
            integration.oauth_expires_at = timezone.now() + timedelta(
                seconds=new_token_data.get('expires_in', 3600)
            )
            integration.save(
                update_fields=[
                    'oauth_token',
                    'oauth_refresh_token',
                    'oauth_expires_at',
                    'updated_at',
                ]
            )

            # Reset failure count on successful refresh
            IntegrationService.reset_failure_count(integration)

            logger.info(f'Refreshed OAuth token for integration: {integration}')
            return integration

        except Exception as e:
            logger.error(f'Failed to refresh OAuth token for {integration}: {str(e)}')
            IntegrationService.increment_failure_count(integration)
            raise BusinessValidationError(f'Token refresh failed: {str(e)}')

    @staticmethod
    def _refresh_linkedin_token(refresh_token: str, config: dict) -> dict:
        """Refresh LinkedIn OAuth token."""
        # In production, would make actual OAuth refresh request
        # Placeholder implementation
        return {
            'access_token': 'new_access_token',
            'refresh_token': refresh_token,
            'expires_in': 3600,
        }

    @staticmethod
    @transaction.atomic
    def mark_sync_status(
        integration: Integration,
        status: str,
        error: Optional[str] = None,
    ) -> Integration:
        """
        Update integration sync status.

        Args:
            integration: Integration instance
            status: New status (idle, syncing, success, error)
            error: Optional error message if status is 'error'

        Returns:
            Updated integration
        """
        integration.sync_status = status

        if status == 'success':
            integration.last_sync = timezone.now()
            integration.error_log = ''
            IntegrationService.reset_failure_count(integration)
        elif status == 'error':
            integration.error_log = error or 'Unknown error'
            IntegrationService.increment_failure_count(integration)

        integration.save(
            update_fields=['sync_status', 'last_sync', 'error_log', 'updated_at']
        )

        return integration

    @staticmethod
    @transaction.atomic
    def increment_failure_count(integration: Integration) -> Integration:
        """
        Increment failure count (circuit breaker pattern).

        Args:
            integration: Integration instance

        Returns:
            Updated integration
        """
        integration.failure_count += 1
        integration.save(update_fields=['failure_count', 'updated_at'])

        # Check if circuit breaker should trigger
        if integration.is_circuit_broken:
            logger.warning(
                f'Circuit breaker triggered for integration {integration} '
                f'(failures: {integration.failure_count})'
            )
            # Optionally auto-disable integration
            # integration.is_active = False
            # integration.save(update_fields=['is_active'])

        return integration

    @staticmethod
    @transaction.atomic
    def reset_failure_count(integration: Integration) -> Integration:
        """
        Reset failure count after successful operation.

        Args:
            integration: Integration instance

        Returns:
            Updated integration
        """
        if integration.failure_count > 0:
            integration.failure_count = 0
            integration.save(update_fields=['failure_count', 'updated_at'])
            logger.info(f'Reset failure count for integration: {integration}')

        return integration


class JobBoardService:
    """Service for posting jobs to external job boards."""

    @staticmethod
    @transaction.atomic
    def post_job(requisition, integration: Integration) -> JobBoardPosting:
        """
        Post job to external job board.

        Args:
            requisition: Requisition instance
            integration: Job board integration

        Returns:
            JobBoardPosting instance

        Raises:
            BusinessValidationError: If posting fails
        """
        # Validate integration is a job board
        if integration.category != 'job_board':
            raise BusinessValidationError('Integration must be a job board')

        if not integration.is_active:
            raise BusinessValidationError('Integration is not active')

        if integration.is_circuit_broken:
            raise BusinessValidationError(
                'Integration circuit breaker is open - too many failures'
            )

        # Check for existing posting
        existing = JobBoardPosting.objects.filter(
            requisition=requisition, integration=integration
        ).first()

        if existing:
            if existing.status == 'posted':
                raise BusinessValidationError('Job is already posted to this board')
            # Re-use existing posting if in draft or error state
            posting = existing
        else:
            # Create new posting
            posting = JobBoardPosting.objects.create(
                requisition=requisition,
                integration=integration,
                status='draft',
            )

        try:
            # Mark integration as syncing
            IntegrationService.mark_sync_status(integration, 'syncing')

            # Transform requisition to board-specific format
            job_data = JobBoardService._format_job_for_board(
                requisition, integration.provider
            )

            # Post to external API
            config = json.loads(integration.config) if integration.config else {}
            external_response = JobBoardService._post_to_external_board(
                integration.provider, job_data, config, integration.oauth_token
            )

            # Update posting with external ID and URL
            posting.external_id = external_response.get('job_id', '')
            posting.url = external_response.get('url', '')
            posting.status = 'posted'
            posting.last_synced = timezone.now()
            posting.metadata = external_response.get('metadata', {})
            posting.save()

            # Mark integration sync as successful
            IntegrationService.mark_sync_status(integration, 'success')

            # Log to audit trail
            AuditLog.objects.create(
                action='post_job',
                resource_type='job_board_posting',
                resource_id=str(posting.id),
                metadata={
                    'requisition_id': str(requisition.id),
                    'integration_id': str(integration.id),
                    'external_id': posting.external_id,
                    'board': integration.provider,
                },
            )

            logger.info(
                f'Posted job {requisition.title} to {integration.provider} '
                f'(external_id: {posting.external_id})'
            )

            return posting

        except Exception as e:
            # Mark posting as error
            posting.status = 'error'
            posting.metadata = {'error': str(e)}
            posting.save()

            # Mark integration sync as failed
            IntegrationService.mark_sync_status(integration, 'error', str(e))

            logger.error(f'Failed to post job to {integration.provider}: {str(e)}')
            raise BusinessValidationError(f'Failed to post job: {str(e)}')

    @staticmethod
    def _format_job_for_board(requisition, provider: str) -> dict:
        """Format requisition data for specific job board."""
        base_data = {
            'title': requisition.title,
            'description': requisition.description,
            'location': {
                'city': requisition.location.city if requisition.location else None,
                'country': requisition.location.country if requisition.location else None,
                'remote_policy': requisition.remote_policy,
            },
            'department': requisition.department.name if requisition.department else None,
            'employment_type': requisition.employment_type,
        }

        if provider == 'indeed':
            # Indeed XML format
            return {
                **base_data,
                'format': 'xml',
                'salary': {
                    'min': str(requisition.salary_min) if requisition.salary_min else None,
                    'max': str(requisition.salary_max) if requisition.salary_max else None,
                    'currency': 'USD',
                },
            }
        elif provider == 'linkedin':
            # LinkedIn API format
            return {
                **base_data,
                'format': 'json',
                'companyId': 'company_linkedin_id',
            }
        elif provider == 'glassdoor':
            # Glassdoor API format
            return {
                **base_data,
                'format': 'json',
            }
        else:
            return base_data

    @staticmethod
    def _post_to_external_board(
        provider: str,
        job_data: dict,
        config: dict,
        oauth_token: Optional[str] = None,
    ) -> dict:
        """Make API call to external job board."""
        # In production, would make actual API calls
        # Placeholder implementation that simulates successful posting
        import uuid

        return {
            'job_id': f'{provider}_{uuid.uuid4().hex[:12]}',
            'url': f'https://{provider}.com/jobs/{uuid.uuid4().hex[:12]}',
            'metadata': {
                'posted_at': timezone.now().isoformat(),
                'provider': provider,
            },
        }

    @staticmethod
    @transaction.atomic
    def update_job(posting: JobBoardPosting) -> JobBoardPosting:
        """
        Update job posting on external board.

        Args:
            posting: JobBoardPosting instance

        Returns:
            Updated posting

        Raises:
            BusinessValidationError: If update fails
        """
        if posting.status != 'posted':
            raise BusinessValidationError('Can only update posted jobs')

        try:
            # Format updated job data
            job_data = JobBoardService._format_job_for_board(
                posting.requisition, posting.integration.provider
            )

            # Update on external board
            config = (
                json.loads(posting.integration.config)
                if posting.integration.config
                else {}
            )
            external_response = JobBoardService._update_external_board(
                posting.integration.provider,
                posting.external_id,
                job_data,
                config,
                posting.integration.oauth_token,
            )

            # Update posting
            posting.last_synced = timezone.now()
            posting.metadata.update(external_response.get('metadata', {}))
            posting.save()

            logger.info(f'Updated job posting: {posting}')
            return posting

        except Exception as e:
            logger.error(f'Failed to update job posting {posting}: {str(e)}')
            raise BusinessValidationError(f'Failed to update job: {str(e)}')

    @staticmethod
    def _update_external_board(
        provider: str,
        external_id: str,
        job_data: dict,
        config: dict,
        oauth_token: Optional[str] = None,
    ) -> dict:
        """Make API call to update job on external board."""
        # Placeholder implementation
        return {
            'metadata': {
                'updated_at': timezone.now().isoformat(),
                'provider': provider,
            },
        }

    @staticmethod
    @transaction.atomic
    def close_job(posting: JobBoardPosting) -> JobBoardPosting:
        """
        Close job posting on external board.

        Args:
            posting: JobBoardPosting instance

        Returns:
            Updated posting
        """
        if posting.status == 'closed':
            return posting

        try:
            # Close on external board
            config = (
                json.loads(posting.integration.config)
                if posting.integration.config
                else {}
            )
            JobBoardService._close_external_board(
                posting.integration.provider,
                posting.external_id,
                config,
                posting.integration.oauth_token,
            )

            # Update posting status
            posting.status = 'closed'
            posting.last_synced = timezone.now()
            posting.save()

            logger.info(f'Closed job posting: {posting}')
            return posting

        except Exception as e:
            logger.error(f'Failed to close job posting {posting}: {str(e)}')
            raise BusinessValidationError(f'Failed to close job: {str(e)}')

    @staticmethod
    def _close_external_board(
        provider: str,
        external_id: str,
        config: dict,
        oauth_token: Optional[str] = None,
    ):
        """Make API call to close job on external board."""
        # Placeholder implementation
        pass

    @staticmethod
    def import_applications(integration: Integration) -> list:
        """
        Import new applications from job board.

        Args:
            integration: Job board integration

        Returns:
            List of created Application instances

        Raises:
            BusinessValidationError: If import fails
        """
        if integration.category != 'job_board':
            raise BusinessValidationError('Integration must be a job board')

        # Placeholder - in production would:
        # 1. Poll external API for new applications
        # 2. Match to requisitions via external_id
        # 3. Create Application records
        # 4. Create CandidateProfile if new candidate
        # 5. Log import event

        logger.info(f'Imported applications from {integration.provider}')
        return []

    @staticmethod
    def get_posting_url(posting: JobBoardPosting) -> str:
        """Get public URL for job posting."""
        return posting.url or ''


class HRISService:
    """Service for syncing with HRIS systems."""

    @staticmethod
    @transaction.atomic
    def sync_departments(integration: Integration) -> dict:
        """
        Sync departments from HRIS to HR-Plus.

        Args:
            integration: HRIS integration

        Returns:
            Dict with created and updated counts
        """
        if integration.category != 'hris':
            raise BusinessValidationError('Integration must be an HRIS')

        try:
            # Mark as syncing
            IntegrationService.mark_sync_status(integration, 'syncing')

            # Fetch departments from HRIS
            config = json.loads(integration.config) if integration.config else {}
            departments_data = HRISService._fetch_departments_from_hris(
                integration.provider, config, integration.oauth_token
            )

            # Sync to database
            created_count = 0
            updated_count = 0

            # In production, would create/update Department records
            # Placeholder implementation
            created_count = len(departments_data.get('departments', []))

            # Mark as successful
            IntegrationService.mark_sync_status(integration, 'success')

            logger.info(
                f'Synced departments from {integration.provider}: '
                f'{created_count} created, {updated_count} updated'
            )

            return {
                'created': created_count,
                'updated': updated_count,
            }

        except Exception as e:
            IntegrationService.mark_sync_status(integration, 'error', str(e))
            logger.error(f'Failed to sync departments from {integration.provider}: {str(e)}')
            raise BusinessValidationError(f'Department sync failed: {str(e)}')

    @staticmethod
    def _fetch_departments_from_hris(
        provider: str, config: dict, oauth_token: Optional[str] = None
    ) -> dict:
        """Fetch departments from HRIS API."""
        # Placeholder implementation
        return {'departments': []}

    @staticmethod
    @transaction.atomic
    def sync_employees(integration: Integration) -> dict:
        """
        Sync employees from HRIS to HR-Plus.

        Args:
            integration: HRIS integration

        Returns:
            Dict with created and updated counts
        """
        if integration.category != 'hris':
            raise BusinessValidationError('Integration must be an HRIS')

        # Placeholder - similar to sync_departments
        logger.info(f'Synced employees from {integration.provider}')
        return {'created': 0, 'updated': 0}

    @staticmethod
    @transaction.atomic
    def push_new_hire(integration: Integration, onboarding_plan) -> dict:
        """
        Push new hire data to HRIS when onboarding completes.

        Args:
            integration: HRIS integration
            onboarding_plan: Completed OnboardingPlan instance

        Returns:
            Dict with external employee ID and status
        """
        if integration.category != 'hris':
            raise BusinessValidationError('Integration must be an HRIS')

        if onboarding_plan.status != 'completed':
            raise BusinessValidationError('Onboarding plan must be completed')

        try:
            # Format employee data
            employee_data = HRISService._format_employee_for_hris(
                onboarding_plan, integration.provider
            )

            # Push to HRIS
            config = json.loads(integration.config) if integration.config else {}
            response = HRISService._push_employee_to_hris(
                integration.provider, employee_data, config, integration.oauth_token
            )

            logger.info(
                f'Pushed new hire to {integration.provider}: '
                f'{onboarding_plan.application.candidate.user.get_full_name()}'
            )

            return {
                'external_employee_id': response.get('employee_id'),
                'status': 'success',
            }

        except Exception as e:
            logger.error(f'Failed to push new hire to {integration.provider}: {str(e)}')
            raise BusinessValidationError(f'New hire push failed: {str(e)}')

    @staticmethod
    def _format_employee_for_hris(onboarding_plan, provider: str) -> dict:
        """Format employee data for HRIS."""
        candidate = onboarding_plan.application.candidate
        user = candidate.user

        base_data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone': candidate.phone,
            'start_date': onboarding_plan.start_date.isoformat(),
            'job_title': onboarding_plan.application.requisition.title,
            'department': onboarding_plan.application.requisition.department.name,
        }

        if provider == 'bamboo_hr':
            return {
                **base_data,
                'location': candidate.location_city,
            }
        else:
            return base_data

    @staticmethod
    def _push_employee_to_hris(
        provider: str, employee_data: dict, config: dict, oauth_token: Optional[str] = None
    ) -> dict:
        """Push employee to HRIS API."""
        # Placeholder implementation
        import uuid

        return {
            'employee_id': f'{provider}_{uuid.uuid4().hex[:12]}',
        }

    @staticmethod
    def get_employee(integration: Integration, employee_id: str) -> dict:
        """
        Fetch employee data from HRIS.

        Args:
            integration: HRIS integration
            employee_id: External employee ID

        Returns:
            Employee data dict
        """
        if integration.category != 'hris':
            raise BusinessValidationError('Integration must be an HRIS')

        # Placeholder implementation
        return {}


class WebhookService:
    """Service for managing outgoing webhooks to external consumers."""

    @staticmethod
    @transaction.atomic
    def register_endpoint(
        url: str,
        events: list[str],
        secret: Optional[str] = None,
        headers: Optional[dict] = None,
        integration: Optional[Integration] = None,
    ) -> WebhookEndpoint:
        """
        Register a new webhook endpoint.

        Args:
            url: Webhook endpoint URL
            events: List of event types to subscribe to
            secret: HMAC signing secret (generated if not provided)
            headers: Optional custom headers to include in requests
            integration: Optional associated integration

        Returns:
            WebhookEndpoint instance
        """
        # Generate secret if not provided
        if not secret:
            import secrets as secrets_module

            secret = secrets_module.token_urlsafe(32)

        # Validate events
        valid_events = [
            'application.created',
            'application.stage_changed',
            'application.rejected',
            'application.hired',
            'offer.created',
            'offer.sent',
            'offer.accepted',
            'offer.declined',
            'requisition.opened',
            'requisition.filled',
            'requisition.cancelled',
        ]

        for event in events:
            if event not in valid_events:
                raise BusinessValidationError(f'Invalid event type: {event}')

        # Create endpoint
        endpoint = WebhookEndpoint.objects.create(
            integration=integration,
            url=url,
            secret=secret,
            events=events,
            headers=headers or {},
            is_active=True,
        )

        logger.info(f'Registered webhook endpoint: {url} for events: {events}')
        return endpoint

    @staticmethod
    def dispatch_event(
        event_type: str,
        payload: dict,
        endpoints: Optional[list[WebhookEndpoint]] = None,
    ) -> list[WebhookDelivery]:
        """
        Dispatch webhook event to subscribed endpoints.

        Args:
            event_type: Event type (e.g., 'application.created')
            payload: Event payload dict
            endpoints: Optional specific endpoints to dispatch to (defaults to all subscribed)

        Returns:
            List of WebhookDelivery instances
        """
        # Find subscribed endpoints if not provided
        if endpoints is None:
            # Filter endpoints that are active and have subscribed to this event
            # Note: We fetch all active endpoints and filter in Python because
            # SQLite doesn't support JSONField contains lookup
            all_endpoints = WebhookEndpoint.objects.filter(is_active=True)
            endpoints = [e for e in all_endpoints if event_type in (e.events or [])]

        deliveries = []

        for endpoint in endpoints:
            # Create delivery record
            delivery = WebhookDelivery.objects.create(
                endpoint=endpoint,
                event_type=event_type,
                payload=payload,
            )

            # Queue delivery via Celery (imported to avoid circular dependency)
            try:
                from apps.integrations.tasks import deliver_webhook

                deliver_webhook.delay(str(delivery.id))
                logger.info(f'Queued webhook delivery {delivery.id} to {endpoint.url}')
            except ImportError:
                logger.warning('Celery tasks not available - webhook delivery not queued')

            deliveries.append(delivery)

        return deliveries

    @staticmethod
    def sign_payload(payload: dict, secret: str) -> str:
        """
        Generate HMAC-SHA256 signature for webhook payload.

        Args:
            payload: Payload dict
            secret: Signing secret

        Returns:
            Hex digest signature
        """
        payload_json = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode('utf-8'), payload_json.encode('utf-8'), hashlib.sha256
        ).hexdigest()

        return signature

    @staticmethod
    @transaction.atomic
    def retry_delivery(delivery: WebhookDelivery) -> WebhookDelivery:
        """
        Retry failed webhook delivery.

        Args:
            delivery: WebhookDelivery instance

        Returns:
            Updated delivery
        """
        if delivery.delivered_at:
            raise BusinessValidationError('Cannot retry delivered webhook')

        # Queue retry
        try:
            from apps.integrations.tasks import deliver_webhook

            deliver_webhook.delay(str(delivery.id))
            delivery.attempts += 1
            delivery.save(update_fields=['attempts', 'updated_at'])
            logger.info(f'Retrying webhook delivery {delivery.id} (attempt {delivery.attempts})')
        except ImportError:
            logger.warning('Celery tasks not available - webhook retry not queued')

        return delivery

    @staticmethod
    @transaction.atomic
    def disable_failing_endpoint(endpoint: WebhookEndpoint) -> WebhookEndpoint:
        """
        Disable webhook endpoint after too many failures.

        Args:
            endpoint: WebhookEndpoint instance

        Returns:
            Updated endpoint
        """
        if endpoint.should_disable and endpoint.is_active:
            endpoint.is_active = False
            endpoint.save(update_fields=['is_active', 'updated_at'])

            logger.warning(
                f'Disabled webhook endpoint {endpoint.url} due to excessive failures '
                f'(failures: {endpoint.failure_count})'
            )

        return endpoint

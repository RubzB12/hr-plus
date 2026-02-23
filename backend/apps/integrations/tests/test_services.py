"""Tests for integration services."""

from unittest.mock import MagicMock, patch

import pytest

from apps.core.exceptions import BusinessValidationError
from apps.integrations.services import (
    IntegrationService,
    JobBoardService,
    WebhookService,
)
from apps.jobs.tests.factories import RequisitionFactory

from .factories import IntegrationFactory, JobBoardPostingFactory, WebhookEndpointFactory


@pytest.mark.django_db
class TestIntegrationService:
    """Tests for IntegrationService."""

    def test_create_integration_success(self):
        """Test successfully creating an integration."""
        config = {'api_key': 'test_key', 'employer_id': '12345'}

        integration = IntegrationService.create_integration(
            provider='indeed',
            category='job_board',
            name='Test Indeed Integration',
            config=config,
        )

        assert integration.id is not None
        assert integration.provider == 'indeed'
        assert integration.is_active is True

    def test_create_integration_duplicate(self):
        """Test that duplicate integrations are rejected."""
        config = {'api_key': 'test_key'}

        # Create first integration
        IntegrationService.create_integration(
            provider='indeed',
            category='job_board',
            name='Test Integration',
            config=config,
        )

        # Attempt to create duplicate
        with pytest.raises(BusinessValidationError, match='already exists'):
            IntegrationService.create_integration(
                provider='indeed',
                category='job_board',
                name='Test Integration',
                config=config,
            )

    def test_update_config(self):
        """Test updating integration config."""
        integration = IntegrationFactory()
        new_config = {'api_key': 'new_key', 'new_field': 'value'}

        updated = IntegrationService.update_config(integration, new_config)

        assert updated.id == integration.id
        # Config is encrypted, so just verify it was updated
        assert updated.config is not None

    def test_test_connection_indeed(self):
        """Test connection test for Indeed integration."""
        integration = IntegrationFactory(
            provider='indeed',
            config='{"api_key": "test_key", "employer_id": "12345"}',
        )

        result = IntegrationService.test_connection(integration)

        assert result['success'] is True
        assert 'validated' in result['message'].lower()

    def test_increment_failure_count(self):
        """Test incrementing failure count."""
        integration = IntegrationFactory(failure_count=0)

        updated = IntegrationService.increment_failure_count(integration)

        assert updated.failure_count == 1

    def test_reset_failure_count(self):
        """Test resetting failure count."""
        integration = IntegrationFactory(failure_count=5)

        updated = IntegrationService.reset_failure_count(integration)

        assert updated.failure_count == 0

    def test_mark_sync_status_success(self):
        """Test marking sync status as success."""
        integration = IntegrationFactory(sync_status='syncing', failure_count=3)

        updated = IntegrationService.mark_sync_status(integration, 'success')

        assert updated.sync_status == 'success'
        assert updated.last_sync is not None
        assert updated.failure_count == 0  # Should reset on success
        assert updated.error_log == ''

    def test_mark_sync_status_error(self):
        """Test marking sync status as error."""
        integration = IntegrationFactory(sync_status='syncing', failure_count=2)

        updated = IntegrationService.mark_sync_status(integration, 'error', 'Test error')

        assert updated.sync_status == 'error'
        assert updated.error_log == 'Test error'
        assert updated.failure_count == 3  # Should increment on error


@pytest.mark.django_db
class TestJobBoardService:
    """Tests for JobBoardService."""

    @patch('apps.integrations.services.JobBoardService._post_to_external_board')
    def test_post_job_success(self, mock_post):
        """Test successfully posting job to board."""
        mock_post.return_value = {
            'job_id': 'indeed_123',
            'url': 'https://indeed.com/job/123',
            'metadata': {},
        }

        requisition = RequisitionFactory()
        integration = IntegrationFactory(category='job_board', is_active=True)

        posting = JobBoardService.post_job(requisition, integration)

        assert posting.id is not None
        assert posting.requisition == requisition
        assert posting.integration == integration
        assert posting.external_id == 'indeed_123'
        assert posting.status == 'posted'

    def test_post_job_not_job_board(self):
        """Test that posting fails for non-job-board integrations."""
        requisition = RequisitionFactory()
        hris_integration = IntegrationFactory(category='hris')

        with pytest.raises(BusinessValidationError, match='must be a job board'):
            JobBoardService.post_job(requisition, hris_integration)

    def test_post_job_inactive_integration(self):
        """Test that posting fails for inactive integrations."""
        requisition = RequisitionFactory()
        integration = IntegrationFactory(category='job_board', is_active=False)

        with pytest.raises(BusinessValidationError, match='not active'):
            JobBoardService.post_job(requisition, integration)

    def test_post_job_circuit_broken(self):
        """Test that posting fails when circuit breaker is open."""
        requisition = RequisitionFactory()
        integration = IntegrationFactory(category='job_board', failure_count=10)

        with pytest.raises(BusinessValidationError, match='circuit breaker'):
            JobBoardService.post_job(requisition, integration)

    def test_post_job_duplicate(self):
        """Test that duplicate posting is rejected."""
        posting = JobBoardPostingFactory(status='posted')

        with pytest.raises(BusinessValidationError, match='already posted'):
            JobBoardService.post_job(posting.requisition, posting.integration)

    @patch('apps.integrations.services.JobBoardService._update_external_board')
    def test_update_job_success(self, mock_update):
        """Test successfully updating job posting."""
        mock_update.return_value = {'metadata': {}}

        posting = JobBoardPostingFactory(status='posted')

        updated = JobBoardService.update_job(posting)

        assert updated.id == posting.id
        assert updated.last_synced is not None

    @patch('apps.integrations.services.JobBoardService._close_external_board')
    def test_close_job_success(self, mock_close):
        """Test successfully closing job posting."""
        mock_close.return_value = None

        posting = JobBoardPostingFactory(status='posted')

        closed = JobBoardService.close_job(posting)

        assert closed.status == 'closed'
        assert closed.last_synced is not None


@pytest.mark.django_db
class TestWebhookService:
    """Tests for WebhookService."""

    def test_register_endpoint(self):
        """Test registering a webhook endpoint."""
        endpoint = WebhookService.register_endpoint(
            url='https://example.com/webhook',
            events=['application.created', 'offer.accepted'],
        )

        assert endpoint.id is not None
        assert endpoint.url == 'https://example.com/webhook'
        assert len(endpoint.events) == 2
        assert endpoint.is_active is True
        assert endpoint.secret is not None  # Should auto-generate

    def test_register_endpoint_with_secret(self):
        """Test registering endpoint with custom secret."""
        custom_secret = 'my_custom_secret_123'  # noqa: S105

        endpoint = WebhookService.register_endpoint(
            url='https://example.com/webhook',
            events=['application.created'],
            secret=custom_secret,  # noqa: S106
        )

        # Secret is encrypted, so verify it's set
        assert endpoint.secret is not None

    def test_register_endpoint_invalid_event(self):
        """Test that invalid event types are rejected."""
        with pytest.raises(BusinessValidationError, match='Invalid event type'):
            WebhookService.register_endpoint(
                url='https://example.com/webhook', events=['invalid.event']
            )

    @patch('apps.integrations.tasks.deliver_webhook.delay')
    def test_dispatch_event(self, mock_task):
        """Test dispatching webhook event."""
        endpoint = WebhookEndpointFactory(events=['application.created'])

        payload = {'application_id': '123', 'status': 'applied'}

        deliveries = WebhookService.dispatch_event('application.created', payload)

        assert len(deliveries) == 1
        assert deliveries[0].endpoint == endpoint
        assert deliveries[0].event_type == 'application.created'
        assert deliveries[0].payload == payload

        # Verify task was queued
        mock_task.assert_called_once()

    def test_sign_payload(self):
        """Test HMAC payload signing."""
        payload = {'test': 'data'}
        secret = 'test_secret'

        signature = WebhookService.sign_payload(payload, secret)

        assert signature is not None
        assert len(signature) == 64  # SHA256 hex digest is 64 chars

        # Verify signature is consistent
        signature2 = WebhookService.sign_payload(payload, secret)
        assert signature == signature2

    def test_retry_delivery(self):
        """Test retrying failed delivery."""
        from .factories import WebhookDeliveryFactory

        delivery = WebhookDeliveryFactory(attempts=1, delivered_at=None)

        with patch('apps.integrations.tasks.deliver_webhook.delay') as mock_task:
            retried = WebhookService.retry_delivery(delivery)

            assert retried.attempts == 2
            mock_task.assert_called_once()

    def test_retry_delivery_already_delivered(self):
        """Test that delivered webhooks cannot be retried."""
        from django.utils import timezone

        from .factories import WebhookDeliveryFactory

        delivered_delivery = WebhookDeliveryFactory(delivered_at=timezone.now())

        with pytest.raises(BusinessValidationError, match='Cannot retry delivered'):
            WebhookService.retry_delivery(delivered_delivery)

    def test_disable_failing_endpoint(self):
        """Test disabling endpoint after failures."""
        endpoint = WebhookEndpointFactory(failure_count=10, is_active=True)

        disabled = WebhookService.disable_failing_endpoint(endpoint)

        assert disabled.is_active is False

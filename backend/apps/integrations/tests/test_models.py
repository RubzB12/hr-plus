"""Tests for integration models."""

from datetime import timedelta

import pytest
from django.utils import timezone

from .factories import (
    IntegrationFactory,
    JobBoardPostingFactory,
    WebhookDeliveryFactory,
    WebhookEndpointFactory,
)


@pytest.mark.django_db
class TestIntegrationModel:
    """Tests for Integration model."""

    def test_create_integration(self):
        """Test creating an integration."""
        integration = IntegrationFactory()

        assert integration.id is not None
        assert integration.provider == 'indeed'
        assert integration.is_active is True

    def test_unique_together_constraint(self):
        """Test that provider + name must be unique."""
        IntegrationFactory(provider='indeed', name='Test Integration')

        # Attempting to create duplicate should fail
        with pytest.raises(Exception):
            IntegrationFactory(provider='indeed', name='Test Integration')

    def test_is_oauth_configured(self):
        """Test is_oauth_configured property."""
        integration_without_oauth = IntegrationFactory(oauth_token=None)
        integration_with_oauth = IntegrationFactory(oauth_token='test_token')

        assert integration_without_oauth.is_oauth_configured is False
        assert integration_with_oauth.is_oauth_configured is True

    def test_needs_token_refresh(self):
        """Test needs_token_refresh property."""
        # Token expires in 5 minutes - should need refresh
        soon = timezone.now() + timedelta(minutes=5)
        integration_expiring_soon = IntegrationFactory(oauth_expires_at=soon)

        # Token expires in 2 hours - should not need refresh
        later = timezone.now() + timedelta(hours=2)
        integration_expiring_later = IntegrationFactory(oauth_expires_at=later)

        assert integration_expiring_soon.needs_token_refresh is True
        assert integration_expiring_later.needs_token_refresh is False

    def test_is_circuit_broken(self):
        """Test circuit breaker property."""
        integration_ok = IntegrationFactory(failure_count=5)
        integration_broken = IntegrationFactory(failure_count=10)

        assert integration_ok.is_circuit_broken is False
        assert integration_broken.is_circuit_broken is True


@pytest.mark.django_db
class TestWebhookEndpointModel:
    """Tests for WebhookEndpoint model."""

    def test_create_webhook_endpoint(self):
        """Test creating a webhook endpoint."""
        endpoint = WebhookEndpointFactory()

        assert endpoint.id is not None
        assert endpoint.is_active is True
        assert len(endpoint.events) > 0

    def test_should_disable_property(self):
        """Test should_disable property."""
        endpoint_ok = WebhookEndpointFactory(failure_count=5)
        endpoint_failing = WebhookEndpointFactory(failure_count=10)

        assert endpoint_ok.should_disable is False
        assert endpoint_failing.should_disable is True


@pytest.mark.django_db
class TestWebhookDeliveryModel:
    """Tests for WebhookDelivery model."""

    def test_create_delivery(self):
        """Test creating a delivery record."""
        delivery = WebhookDeliveryFactory()

        assert delivery.id is not None
        assert delivery.endpoint is not None

    def test_is_delivered_property(self):
        """Test is_delivered property."""
        pending_delivery = WebhookDeliveryFactory(delivered_at=None)
        delivered_delivery = WebhookDeliveryFactory(delivered_at=timezone.now())

        assert pending_delivery.is_delivered is False
        assert delivered_delivery.is_delivered is True

    def test_is_success_property(self):
        """Test is_success property."""
        success_delivery = WebhookDeliveryFactory(response_status=200)
        error_delivery = WebhookDeliveryFactory(response_status=500)
        pending_delivery = WebhookDeliveryFactory(response_status=None)

        assert success_delivery.is_success is True
        assert error_delivery.is_success is False
        assert pending_delivery.is_success is False


@pytest.mark.django_db
class TestJobBoardPostingModel:
    """Tests for JobBoardPosting model."""

    def test_create_posting(self):
        """Test creating a job board posting."""
        posting = JobBoardPostingFactory()

        assert posting.id is not None
        assert posting.requisition is not None
        assert posting.integration is not None

    def test_unique_together_constraint(self):
        """Test that requisition + integration must be unique."""
        posting = JobBoardPostingFactory()

        # Attempting to create duplicate should fail
        with pytest.raises(Exception):
            JobBoardPostingFactory(
                requisition=posting.requisition, integration=posting.integration
            )

    def test_is_active_property(self):
        """Test is_active property."""
        posted_posting = JobBoardPostingFactory(status='posted')
        closed_posting = JobBoardPostingFactory(status='closed')

        assert posted_posting.is_active is True
        assert closed_posting.is_active is False

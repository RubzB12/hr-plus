"""Factories for integration tests."""

import factory
from factory.django import DjangoModelFactory

from apps.integrations.models import Integration, JobBoardPosting, WebhookDelivery, WebhookEndpoint
from apps.jobs.tests.factories import RequisitionFactory


class IntegrationFactory(DjangoModelFactory):
    """Factory for Integration model."""

    class Meta:
        model = Integration

    provider = 'indeed'
    category = 'job_board'
    name = factory.Sequence(lambda n: f'Test Integration {n}')
    is_active = True
    config = '{"api_key": "test_key", "employer_id": "12345"}'
    sync_status = 'idle'
    failure_count = 0
    metadata = {}


class WebhookEndpointFactory(DjangoModelFactory):
    """Factory for WebhookEndpoint model."""

    class Meta:
        model = WebhookEndpoint

    url = factory.Sequence(lambda n: f'https://example.com/webhook/{n}')
    secret = 'test_secret_key_12345'
    events = ['application.created', 'offer.accepted']
    is_active = True
    failure_count = 0
    headers = {}


class WebhookDeliveryFactory(DjangoModelFactory):
    """Factory for WebhookDelivery model."""

    class Meta:
        model = WebhookDelivery

    endpoint = factory.SubFactory(WebhookEndpointFactory)
    event_type = 'application.created'
    payload = {'test': 'data'}
    attempts = 1


class JobBoardPostingFactory(DjangoModelFactory):
    """Factory for JobBoardPosting model."""

    class Meta:
        model = JobBoardPosting

    requisition = factory.SubFactory(RequisitionFactory)
    integration = factory.SubFactory(IntegrationFactory, category='job_board')
    external_id = factory.Sequence(lambda n: f'job_{n}')
    status = 'posted'
    url = factory.Sequence(lambda n: f'https://indeed.com/jobs/{n}')
    metadata = {}

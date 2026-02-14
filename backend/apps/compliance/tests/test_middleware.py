"""Tests for audit log middleware."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.compliance.models import AuditLog


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestAuditLogMiddleware:
    def test_api_request_creates_audit_log(self, api_client):
        """API requests should be logged in the audit log."""
        api_client.get(reverse('auth-me'))

        log = AuditLog.objects.first()
        assert log is not None
        assert log.action == 'GET'
        assert '/api/' in log.resource_id

    def test_health_check_not_logged(self, api_client):
        """Health check endpoint should not be logged."""
        api_client.get(reverse('health-check'))

        assert AuditLog.objects.count() == 0

    def test_audit_log_captures_status_code(self, api_client):
        """Audit log should capture the response status code."""
        api_client.get(reverse('auth-me'))

        log = AuditLog.objects.first()
        assert log is not None
        assert log.metadata['status_code'] == 403

    def test_audit_log_captures_user_agent(self, api_client):
        """Audit log should capture user agent."""
        api_client.get(reverse('auth-me'), HTTP_USER_AGENT='TestAgent/1.0')

        log = AuditLog.objects.first()
        assert log is not None
        assert log.metadata['user_agent'] == 'TestAgent/1.0'

    def test_audit_log_captures_authenticated_user(self, api_client):
        """Audit log should reference the authenticated user."""
        from apps.accounts.tests.factories import UserFactory

        user = UserFactory()
        api_client.force_authenticate(user=user)
        api_client.get(reverse('auth-me'))

        log = AuditLog.objects.first()
        assert log is not None
        assert log.actor == user

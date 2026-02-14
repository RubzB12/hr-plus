"""Tests for communications services."""

import pytest
from django.utils import timezone

from apps.accounts.tests.factories import UserFactory
from apps.applications.tests.factories import ApplicationFactory
from apps.communications.models import EmailLog, EmailTemplate, Notification
from apps.communications.services import EmailService, NotificationService, TemplateService
from apps.core.exceptions import BusinessValidationError


@pytest.mark.django_db
class TestTemplateService:
    """Tests for TemplateService."""

    def test_render_template_success(self):
        """Template renders correctly with all required variables."""
        template = EmailTemplate.objects.create(
            name='Test Template',
            category='general',
            subject='Hello {{ name }}',
            body_html='<p>Welcome {{ name }} to {{ company }}!</p>',
            body_text='Welcome {{ name }} to {{ company }}!',
            variables={'name': 'string', 'company': 'string'},
        )

        context = {
            'name': 'John Doe',
            'company': 'HR-Plus',
        }

        subject, body_html, body_text = TemplateService.render_template(template, context)

        assert subject == 'Hello John Doe'
        assert 'Welcome John Doe to HR-Plus!' in body_html
        assert 'Welcome John Doe to HR-Plus!' in body_text

    def test_render_template_missing_variable(self):
        """Template rendering fails if required variable is missing."""
        template = EmailTemplate.objects.create(
            name='Test Template',
            category='general',
            subject='Hello {{ name }}',
            body_html='<p>Welcome {{ name }}!</p>',
            body_text='Welcome {{ name }}!',
            variables={'name': 'string', 'company': 'string'},
        )

        context = {'name': 'John Doe'}  # Missing 'company'

        with pytest.raises(BusinessValidationError, match='Missing required merge fields'):
            TemplateService.render_template(template, context)

    def test_extract_variables(self):
        """Extract variables from template text."""
        template_text = 'Hello {{ name }}, welcome to {{ company }}! Your ID is {{ user_id }}.'

        variables = TemplateService.extract_variables(template_text)

        assert set(variables) == {'name', 'company', 'user_id'}

    def test_validate_template_syntax_valid(self):
        """Valid template syntax passes validation."""
        subject = 'Hello {{ name }}'
        body_html = '<p>{{ content }}</p>'
        body_text = '{{ content }}'

        result = TemplateService.validate_template_syntax(subject, body_html, body_text)

        assert result is True

    def test_validate_template_syntax_invalid(self):
        """Invalid template syntax raises error."""
        # Django template with unknown filter/tag raises error
        subject = 'Hello {{ name }}'
        body_html = '<p>{% unknown_tag %}</p>'  # Unknown tag
        body_text = '{{ content }}'

        with pytest.raises(BusinessValidationError, match='Invalid template syntax'):
            TemplateService.validate_template_syntax(subject, body_html, body_text)


@pytest.mark.django_db
class TestEmailService:
    """Tests for EmailService."""

    def test_send_email_creates_log(self):
        """Sending email creates EmailLog entry."""
        email_log = EmailService.send_email(
            recipient='test@example.com',
            subject='Test Email',
            body_text='Test body',
            body_html='<p>Test body</p>',
        )

        assert email_log.id is not None
        assert email_log.recipient == 'test@example.com'
        assert email_log.subject == 'Test Email'
        assert email_log.status == 'queued'

    def test_send_templated_email_success(self):
        """Send email using template."""
        template = EmailTemplate.objects.create(
            name='Test Template',
            category='general',
            subject='Hello {{ name }}',
            body_html='<p>Welcome {{ name }}!</p>',
            body_text='Welcome {{ name }}!',
            variables={'name': 'string'},
            is_active=True,
        )

        email_log = EmailService.send_templated_email(
            template_name='Test Template',
            recipient='test@example.com',
            context={'name': 'John Doe'},
        )

        assert email_log.subject == 'Hello John Doe'
        assert email_log.template == template

    def test_send_templated_email_template_not_found(self):
        """Sending with non-existent template raises error."""
        with pytest.raises(BusinessValidationError, match='Email template "NonExistent" not found'):
            EmailService.send_templated_email(
                template_name='NonExistent',
                recipient='test@example.com',
                context={},
            )

    def test_send_email_sync_success(self, mailoutbox):
        """Email is sent successfully via SMTP."""
        email_log = EmailLog.objects.create(
            sender='noreply@hrplus.com',
            recipient='test@example.com',
            subject='Test',
            body_text='Test body',
            body_html='<p>Test body</p>',
            status='queued',
        )

        updated_log = EmailService.send_email_sync(email_log)

        assert updated_log.status == 'sent'
        assert updated_log.sent_at is not None
        assert len(mailoutbox) == 1
        assert mailoutbox[0].subject == 'Test'

    def test_send_application_confirmation(self):
        """Application confirmation email is sent."""
        # Create test data using factories
        application = ApplicationFactory()

        # Create required template
        EmailTemplate.objects.create(
            name='Application Confirmation',
            category='application',
            subject='Application Received',
            body_html='<p>{{ candidate_name }}</p>',
            body_text='{{ candidate_name }}',
            variables={
                'candidate_name': 'string',
                'job_title': 'string',
                'application_id': 'string',
                'company_name': 'string',
            },
            is_active=True,
        )

        email_log = EmailService.send_application_confirmation(application)

        assert email_log.recipient == application.candidate.user.email
        assert email_log.application == application


@pytest.mark.django_db
class TestNotificationService:
    """Tests for NotificationService."""

    def test_create_notification(self):
        """Notification is created successfully."""
        user = UserFactory()

        notification = NotificationService.create_notification(
            recipient=user,
            notification_type='application',
            title='New Application',
            body='You have a new application',
            link='/applications/123',
            metadata={'application_id': '123'},
        )

        assert notification.id is not None
        assert notification.recipient == user
        assert notification.type == 'application'
        assert notification.is_read is False

    def test_mark_as_read(self):
        """Notification is marked as read."""
        user = UserFactory()
        notification = Notification.objects.create(
            recipient=user,
            type='application',
            title='Test',
            body='Test body',
        )

        assert notification.is_read is False
        assert notification.read_at is None

        updated = NotificationService.mark_as_read(notification)

        assert updated.is_read is True
        assert updated.read_at is not None

    def test_mark_as_read_already_read(self):
        """Marking already-read notification is idempotent."""
        user = UserFactory()
        notification = Notification.objects.create(
            recipient=user,
            type='application',
            title='Test',
            body='Test body',
            is_read=True,
            read_at=timezone.now(),
        )

        original_read_at = notification.read_at
        updated = NotificationService.mark_as_read(notification)

        assert updated.is_read is True
        assert updated.read_at == original_read_at

    def test_mark_all_as_read(self):
        """All unread notifications are marked as read."""
        user = UserFactory()

        # Create 3 unread notifications
        for i in range(3):
            Notification.objects.create(
                recipient=user,
                type='application',
                title=f'Test {i}',
                body='Test body',
            )

        # Create 1 already read
        Notification.objects.create(
            recipient=user,
            type='application',
            title='Already Read',
            body='Test body',
            is_read=True,
            read_at=timezone.now(),
        )

        count = NotificationService.mark_all_as_read(user)

        assert count == 3
        assert Notification.objects.filter(recipient=user, is_read=False).count() == 0

    def test_get_unread_count(self):
        """Unread count is calculated correctly."""
        user = UserFactory()

        # Create 2 unread
        for i in range(2):
            Notification.objects.create(
                recipient=user,
                type='application',
                title=f'Test {i}',
                body='Test body',
            )

        # Create 1 read
        Notification.objects.create(
            recipient=user,
            type='application',
            title='Read',
            body='Test body',
            is_read=True,
            read_at=timezone.now(),
        )

        count = NotificationService.get_unread_count(user)

        assert count == 2

"""Tests for communications services."""

import pytest
from django.utils import timezone

from apps.accounts.tests.factories import UserFactory
from apps.applications.tests.factories import ApplicationFactory
from apps.communications.models import EmailLog, EmailTemplate, Message, MessageThread, Notification
from apps.communications.services import EmailService, MessagingService, NotificationService, TemplateService
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


@pytest.mark.django_db
class TestMessagingService:
    """Tests for MessagingService."""

    def test_create_thread_success(self):
        """Message thread is created with participants."""
        user1 = UserFactory()
        user2 = UserFactory()
        creator = UserFactory()

        thread = MessagingService.create_thread(
            subject='Test Thread',
            participants=[user1, user2],
            created_by=creator,
        )

        assert thread.id is not None
        assert thread.subject == 'Test Thread'
        assert thread.participants.count() == 3  # user1, user2, and creator
        assert user1 in thread.participants.all()
        assert user2 in thread.participants.all()
        assert creator in thread.participants.all()

    def test_create_thread_no_participants(self):
        """Creating thread without participants raises error."""
        creator = UserFactory()

        with pytest.raises(BusinessValidationError, match='at least one participant'):
            MessagingService.create_thread(
                subject='Test',
                participants=[],
                created_by=creator,
            )

    def test_create_thread_single_participant(self):
        """Creating thread with single participant raises error."""
        user1 = UserFactory()
        creator = UserFactory()

        with pytest.raises(BusinessValidationError, match='at least two participants'):
            MessagingService.create_thread(
                subject='Test',
                participants=[user1],
                created_by=creator,
            )

    def test_create_thread_with_application(self):
        """Thread can be linked to an application."""
        user1 = UserFactory()
        user2 = UserFactory()
        application = ApplicationFactory()

        thread = MessagingService.create_thread(
            subject='About Application',
            participants=[user1, user2],
            application=application,
            created_by=user1,
        )

        assert thread.application == application

    def test_send_message_success(self):
        """Message is sent successfully."""
        user1 = UserFactory()
        user2 = UserFactory()

        thread = MessagingService.create_thread(
            subject='Test',
            participants=[user1, user2],
            created_by=user1,
        )

        message = MessagingService.send_message(
            thread=thread,
            sender=user1,
            body='Hello, this is a test message',
        )

        assert message.id is not None
        assert message.thread == thread
        assert message.sender == user1
        assert message.body == 'Hello, this is a test message'
        assert message.is_system_message is False
        # Sender should have message marked as read
        assert str(user1.id) in message.read_by

    def test_send_message_non_participant(self):
        """Non-participant cannot send message."""
        user1 = UserFactory()
        user2 = UserFactory()
        outsider = UserFactory()

        thread = MessagingService.create_thread(
            subject='Test',
            participants=[user1, user2],
            created_by=user1,
        )

        with pytest.raises(BusinessValidationError, match='not a participant'):
            MessagingService.send_message(
                thread=thread,
                sender=outsider,
                body='I should not be able to send this',
            )

    def test_send_message_with_attachments(self):
        """Message can include attachments."""
        user1 = UserFactory()
        user2 = UserFactory()

        thread = MessagingService.create_thread(
            subject='Test',
            participants=[user1, user2],
            created_by=user1,
        )

        attachments = [
            {'filename': 'doc.pdf', 'url': 'https://example.com/doc.pdf'},
            {'filename': 'image.png', 'url': 'https://example.com/image.png'},
        ]

        message = MessagingService.send_message(
            thread=thread,
            sender=user1,
            body='Check these files',
            attachments=attachments,
        )

        assert len(message.attachments) == 2
        assert message.attachments[0]['filename'] == 'doc.pdf'

    def test_send_system_message(self):
        """System messages can be sent."""
        user1 = UserFactory()
        user2 = UserFactory()

        thread = MessagingService.create_thread(
            subject='Test',
            participants=[user1, user2],
            created_by=user1,
        )

        message = MessagingService.send_message(
            thread=thread,
            sender=user1,
            body='User joined the conversation',
            is_system_message=True,
        )

        assert message.is_system_message is True

    def test_mark_as_read(self):
        """Message is marked as read by user."""
        user1 = UserFactory()
        user2 = UserFactory()

        thread = MessagingService.create_thread(
            subject='Test',
            participants=[user1, user2],
            created_by=user1,
        )

        message = MessagingService.send_message(
            thread=thread,
            sender=user1,
            body='Test message',
        )

        # Initially only sender has read it
        assert str(user2.id) not in message.read_by

        # User2 marks as read
        updated = MessagingService.mark_as_read(message, user2)

        assert str(user2.id) in updated.read_by

    def test_mark_thread_as_read(self):
        """All messages in thread are marked as read."""
        user1 = UserFactory()
        user2 = UserFactory()

        thread = MessagingService.create_thread(
            subject='Test',
            participants=[user1, user2],
            created_by=user1,
        )

        # User1 sends 3 messages
        for i in range(3):
            MessagingService.send_message(
                thread=thread,
                sender=user1,
                body=f'Message {i}',
            )

        # User2 marks all as read
        count = MessagingService.mark_thread_as_read(thread, user2)

        assert count == 3

        # Verify all are marked as read
        for message in thread.messages.all():
            assert str(user2.id) in message.read_by

    def test_get_unread_count(self):
        """Unread message count is calculated correctly."""
        user1 = UserFactory()
        user2 = UserFactory()

        thread = MessagingService.create_thread(
            subject='Test',
            participants=[user1, user2],
            created_by=user1,
        )

        # User1 sends 5 messages
        for i in range(5):
            MessagingService.send_message(
                thread=thread,
                sender=user1,
                body=f'Message {i}',
            )

        # User2 should have 5 unread
        count = MessagingService.get_unread_count(user2, thread=thread)
        assert count == 5

        # User1 should have 0 unread (sent by themselves)
        count = MessagingService.get_unread_count(user1, thread=thread)
        assert count == 0

    def test_get_unread_count_all_threads(self):
        """Unread count across all threads."""
        user1 = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()

        # Create two threads
        thread1 = MessagingService.create_thread(
            subject='Thread 1',
            participants=[user1, user2],
            created_by=user1,
        )

        thread2 = MessagingService.create_thread(
            subject='Thread 2',
            participants=[user1, user3],
            created_by=user1,
        )

        # User2 sends 2 messages in thread1
        for i in range(2):
            MessagingService.send_message(
                thread=thread1,
                sender=user2,
                body=f'Message {i}',
            )

        # User3 sends 3 messages in thread2
        for i in range(3):
            MessagingService.send_message(
                thread=thread2,
                sender=user3,
                body=f'Message {i}',
            )

        # User1 should have 5 unread total (2 + 3)
        count = MessagingService.get_unread_count(user1)
        assert count == 5

    def test_archive_thread(self):
        """Thread is archived."""
        user1 = UserFactory()
        user2 = UserFactory()

        thread = MessagingService.create_thread(
            subject='Test',
            participants=[user1, user2],
            created_by=user1,
        )

        assert thread.is_archived is False
        assert thread.archived_at is None

        archived = MessagingService.archive_thread(thread, user1)

        assert archived.is_archived is True
        assert archived.archived_at is not None

    def test_archive_thread_non_participant(self):
        """Non-participant cannot archive thread."""
        user1 = UserFactory()
        user2 = UserFactory()
        outsider = UserFactory()

        thread = MessagingService.create_thread(
            subject='Test',
            participants=[user1, user2],
            created_by=user1,
        )

        with pytest.raises(BusinessValidationError, match='not a participant'):
            MessagingService.archive_thread(thread, outsider)

    def test_add_participant(self):
        """Participant is added to thread."""
        user1 = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()

        thread = MessagingService.create_thread(
            subject='Test',
            participants=[user1, user2],
            created_by=user1,
        )

        assert thread.participants.count() == 2

        updated = MessagingService.add_participant(thread, user3, user1)

        assert updated.participants.count() == 3
        assert user3 in updated.participants.all()

        # Should create system message
        last_message = thread.messages.last()
        assert last_message.is_system_message is True
        assert user3.get_full_name() in last_message.body

    def test_add_participant_non_participant_adder(self):
        """Non-participant cannot add others."""
        user1 = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()
        outsider = UserFactory()

        thread = MessagingService.create_thread(
            subject='Test',
            participants=[user1, user2],
            created_by=user1,
        )

        with pytest.raises(BusinessValidationError, match='not a participant'):
            MessagingService.add_participant(thread, user3, outsider)

    def test_add_existing_participant_idempotent(self):
        """Adding existing participant is idempotent."""
        user1 = UserFactory()
        user2 = UserFactory()

        thread = MessagingService.create_thread(
            subject='Test',
            participants=[user1, user2],
            created_by=user1,
        )

        original_count = thread.participants.count()

        # Try to add user2 again
        updated = MessagingService.add_participant(thread, user2, user1)

        assert updated.participants.count() == original_count

    def test_remove_participant(self):
        """Participant is removed from thread."""
        user1 = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()

        thread = MessagingService.create_thread(
            subject='Test',
            participants=[user1, user2, user3],
            created_by=user1,
        )

        assert thread.participants.count() == 3

        updated = MessagingService.remove_participant(thread, user3, user1)

        assert updated.participants.count() == 2
        assert user3 not in updated.participants.all()

        # Should create system message
        last_message = thread.messages.last()
        assert last_message.is_system_message is True

    def test_remove_participant_self_leave(self):
        """User can leave thread themselves."""
        user1 = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()

        thread = MessagingService.create_thread(
            subject='Test',
            participants=[user1, user2, user3],
            created_by=user1,
        )

        updated = MessagingService.remove_participant(thread, user3, user3)

        assert user3 not in updated.participants.all()

        # System message should say "left"
        last_message = thread.messages.last()
        assert 'left' in last_message.body

    def test_remove_participant_from_two_person_thread(self):
        """Cannot remove from thread with only 2 participants."""
        user1 = UserFactory()
        user2 = UserFactory()

        thread = MessagingService.create_thread(
            subject='Test',
            participants=[user1, user2],
            created_by=user1,
        )

        with pytest.raises(BusinessValidationError, match='only 2 participants'):
            MessagingService.remove_participant(thread, user2, user1)

    def test_remove_participant_non_participant_remover(self):
        """Non-participant cannot remove others."""
        user1 = UserFactory()
        user2 = UserFactory()
        user3 = UserFactory()
        outsider = UserFactory()

        thread = MessagingService.create_thread(
            subject='Test',
            participants=[user1, user2, user3],
            created_by=user1,
        )

        with pytest.raises(BusinessValidationError, match='not a participant'):
            MessagingService.remove_participant(thread, user3, outsider)

"""Business logic for communications app."""

import re
from typing import Any

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template import Context, Template
from django.utils import timezone

from apps.core.exceptions import BusinessValidationError

from .models import EmailLog, EmailTemplate, Message, MessageThread, Notification


class TemplateService:
    """Service for managing email templates."""

    @staticmethod
    def render_template(template: EmailTemplate, context: dict[str, Any]) -> tuple[str, str, str]:
        """
        Render an email template with merge fields.

        Args:
            template: EmailTemplate instance
            context: Dictionary of merge field values

        Returns:
            Tuple of (subject, body_html, body_text)

        Raises:
            BusinessValidationError: If required merge fields are missing
        """
        # Validate required fields
        required_fields = set(template.variables.keys())
        provided_fields = set(context.keys())
        missing_fields = required_fields - provided_fields

        if missing_fields:
            raise BusinessValidationError(
                f'Missing required merge fields: {", ".join(missing_fields)}',
            )

        # Render templates
        django_context = Context(context)

        subject_template = Template(template.subject)
        subject = subject_template.render(django_context)

        html_template = Template(template.body_html)
        body_html = html_template.render(django_context)

        text_template = Template(template.body_text)
        body_text = text_template.render(django_context)

        return subject, body_html, body_text

    @staticmethod
    def extract_variables(template_text: str) -> list[str]:
        """
        Extract variable names from Django template syntax.

        Args:
            template_text: Template text with {{ variable }} placeholders

        Returns:
            List of variable names found
        """
        pattern = r'\{\{\s*(\w+)\s*\}\}'
        matches = re.findall(pattern, template_text)
        return list(set(matches))

    @staticmethod
    def validate_template_syntax(subject: str, body_html: str, body_text: str) -> bool:
        """
        Validate Django template syntax.

        Args:
            subject: Subject template
            body_html: HTML body template
            body_text: Text body template

        Returns:
            True if valid

        Raises:
            BusinessValidationError: If template syntax is invalid
        """
        try:
            Template(subject)
            Template(body_html)
            Template(body_text)
            return True
        except Exception as e:
            raise BusinessValidationError(f'Invalid template syntax: {e}') from e


class EmailService:
    """Service for sending emails."""

    @staticmethod
    @transaction.atomic
    def send_email(
        *,
        recipient: str,
        subject: str,
        body_text: str,
        body_html: str = '',
        sender: str = None,
        template: EmailTemplate = None,
        application=None,
        metadata: dict = None,
    ) -> EmailLog:
        """
        Send an email (queued via Celery in production).

        Args:
            recipient: Recipient email address
            subject: Email subject
            body_text: Plain text body
            body_html: HTML body (optional)
            sender: Sender email (defaults to settings.DEFAULT_FROM_EMAIL)
            template: EmailTemplate if rendered from template
            application: Related application (optional)
            metadata: Additional metadata

        Returns:
            EmailLog instance
        """
        if not sender:
            sender = settings.DEFAULT_FROM_EMAIL

        # Create email log
        email_log = EmailLog.objects.create(
            template=template,
            application=application,
            sender=sender,
            recipient=recipient,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            status='queued',
            metadata=metadata or {},
        )

        # In production, this would queue a Celery task
        # For now, send synchronously in development
        from .tasks import send_email_task

        send_email_task.delay(email_log.id)

        return email_log

    @staticmethod
    def send_email_sync(email_log: EmailLog) -> EmailLog:
        """
        Actually send the email via SMTP (called by Celery task).

        Args:
            email_log: EmailLog instance to send

        Returns:
            Updated EmailLog instance
        """
        try:
            msg = EmailMultiAlternatives(
                subject=email_log.subject,
                body=email_log.body_text,
                from_email=email_log.sender,
                to=[email_log.recipient],
            )

            if email_log.body_html:
                msg.attach_alternative(email_log.body_html, 'text/html')

            msg.send(fail_silently=False)

            email_log.status = 'sent'
            email_log.sent_at = timezone.now()
            email_log.save(update_fields=['status', 'sent_at', 'updated_at'])

        except Exception as e:
            email_log.status = 'failed'
            email_log.error_message = str(e)
            email_log.save(update_fields=['status', 'error_message', 'updated_at'])

        return email_log

    @staticmethod
    @transaction.atomic
    def send_templated_email(
        *,
        template_name: str,
        recipient: str,
        context: dict[str, Any],
        application=None,
    ) -> EmailLog:
        """
        Send an email using a named template.

        Args:
            template_name: Name of EmailTemplate
            recipient: Recipient email
            context: Merge field values
            application: Related application (optional)

        Returns:
            EmailLog instance
        """
        try:
            template = EmailTemplate.objects.get(name=template_name, is_active=True)
        except EmailTemplate.DoesNotExist as e:
            raise BusinessValidationError(f'Email template "{template_name}" not found') from e

        subject, body_html, body_text = TemplateService.render_template(template, context)

        return EmailService.send_email(
            recipient=recipient,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            template=template,
            application=application,
            metadata={'context': context},
        )

    # Auto-triggered email methods

    @staticmethod
    def send_application_confirmation(application):
        """Send application confirmation email to candidate."""
        context = {
            'candidate_name': application.candidate.user.get_full_name(),
            'job_title': application.requisition.title,
            'application_id': application.application_id,
            'company_name': 'HR-Plus',  # Could come from settings
        }

        return EmailService.send_templated_email(
            template_name='Application Confirmation',
            recipient=application.candidate.user.email,
            context=context,
            application=application,
        )

    @staticmethod
    def send_interview_scheduled(interview):
        """Send interview scheduled notification."""

        context = {
            'candidate_name': interview.application.candidate.user.get_full_name(),
            'job_title': interview.application.requisition.title,
            'interview_type': interview.get_type_display(),
            'interview_date': interview.scheduled_start.strftime('%B %d, %Y'),
            'interview_time': interview.scheduled_start.strftime('%I:%M %p'),
            'interview_location': interview.location or 'See details below',
            'video_link': interview.video_link,
            'prep_notes': interview.prep_notes_candidate,
        }

        return EmailService.send_templated_email(
            template_name='Interview Scheduled',
            recipient=interview.application.candidate.user.email,
            context=context,
            application=interview.application,
        )

    @staticmethod
    def send_interview_reminder(interview, recipient, hours_until: int):
        """Send interview reminder."""
        context = {
            'recipient_name': recipient.get_full_name(),
            'candidate_name': interview.application.candidate.user.get_full_name(),
            'job_title': interview.application.requisition.title,
            'interview_type': interview.get_type_display(),
            'interview_date': interview.scheduled_start.strftime('%B %d, %Y'),
            'interview_time': interview.scheduled_start.strftime('%I:%M %p'),
            'hours_until': hours_until,
            'video_link': interview.video_link,
        }

        template_name = f'Interview Reminder {hours_until}h'

        return EmailService.send_templated_email(
            template_name=template_name,
            recipient=recipient.email,
            context=context,
            application=interview.application,
        )

    @staticmethod
    def send_scorecard_reminder(interview, recipient):
        """Send scorecard submission reminder."""
        context = {
            'interviewer_name': recipient.get_full_name(),
            'candidate_name': interview.application.candidate.user.get_full_name(),
            'job_title': interview.application.requisition.title,
            'interview_date': interview.scheduled_start.strftime('%B %d, %Y'),
        }

        return EmailService.send_templated_email(
            template_name='Scorecard Reminder',
            recipient=recipient.email,
            context=context,
            application=interview.application,
        )

    @staticmethod
    def send_application_status_update(application, new_status: str):
        """Send application status update to candidate."""
        context = {
            'candidate_name': application.candidate.user.get_full_name(),
            'job_title': application.requisition.title,
            'new_status': new_status.replace('_', ' ').title(),
        }

        return EmailService.send_templated_email(
            template_name='Application Status Update',
            recipient=application.candidate.user.email,
            context=context,
            application=application,
        )

    @staticmethod
    def send_onboarding_welcome(plan):
        """Send onboarding welcome email to new hire."""
        context = {
            'candidate_name': plan.application.candidate.user.get_full_name(),
            'job_title': plan.application.requisition.title,
            'start_date': plan.start_date.strftime('%B %d, %Y'),
            'portal_url': f'{settings.FRONTEND_URL}/onboarding/{plan.access_token}',
            'access_token': plan.access_token,
            'company_name': 'HR-Plus',
        }

        return EmailService.send_templated_email(
            template_name='Onboarding Welcome',
            recipient=plan.application.candidate.user.email,
            context=context,
            application=plan.application,
        )

    @staticmethod
    def send_onboarding_completed(plan):
        """Send onboarding completion notification."""
        # Notify candidate
        candidate_context = {
            'candidate_name': plan.application.candidate.user.get_full_name(),
            'job_title': plan.application.requisition.title,
            'completion_date': plan.completed_at.strftime('%B %d, %Y'),
            'company_name': 'HR-Plus',
        }

        EmailService.send_templated_email(
            template_name='Onboarding Completed',
            recipient=plan.application.candidate.user.email,
            context=candidate_context,
            application=plan.application,
        )

        # Notify HR contact if assigned
        if plan.hr_contact:
            hr_context = {
                'hr_name': plan.hr_contact.user.get_full_name(),
                'candidate_name': plan.application.candidate.user.get_full_name(),
                'job_title': plan.application.requisition.title,
                'completion_date': plan.completed_at.strftime('%B %d, %Y'),
            }

            EmailService.send_templated_email(
                template_name='Onboarding Completed (HR)',
                recipient=plan.hr_contact.user.email,
                context=hr_context,
                application=plan.application,
            )

    @staticmethod
    def send_task_reminder(task):
        """Send task reminder to assignee."""
        context = {
            'assignee_name': task.assigned_to.get_full_name(),
            'task_title': task.title,
            'task_description': task.description,
            'due_date': task.due_date.strftime('%B %d, %Y'),
            'candidate_name': task.plan.application.candidate.user.get_full_name(),
            'company_name': 'HR-Plus',
        }

        return EmailService.send_templated_email(
            template_name='Onboarding Task Reminder',
            recipient=task.assigned_to.email,
            context=context,
            application=task.plan.application,
        )


class NotificationService:
    """Service for managing in-app notifications."""

    @staticmethod
    @transaction.atomic
    def create_notification(
        *,
        recipient,
        notification_type: str,
        title: str,
        body: str,
        link: str = '',
        metadata: dict = None,
    ) -> Notification:
        """
        Create an in-app notification.

        Args:
            recipient: User who will receive the notification
            notification_type: Notification type (application/interview/scorecard/etc.)
            title: Notification title
            body: Notification body text
            link: Internal app link (optional)
            metadata: Additional context (optional)

        Returns:
            Notification instance
        """
        return Notification.objects.create(
            recipient=recipient,
            type=notification_type,
            title=title,
            body=body,
            link=link,
            metadata=metadata or {},
        )

    @staticmethod
    @transaction.atomic
    def mark_as_read(notification: Notification) -> Notification:
        """
        Mark a notification as read.

        Args:
            notification: Notification instance

        Returns:
            Updated notification
        """
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=['is_read', 'read_at', 'updated_at'])

        return notification

    @staticmethod
    @transaction.atomic
    def mark_all_as_read(user) -> int:
        """
        Mark all notifications as read for a user.

        Args:
            user: User instance

        Returns:
            Number of notifications marked as read
        """
        count = Notification.objects.filter(
            recipient=user,
            is_read=False,
        ).update(
            is_read=True,
            read_at=timezone.now(),
        )

        return count

    @staticmethod
    def get_unread_count(user) -> int:
        """
        Get count of unread notifications for a user.

        Args:
            user: User instance

        Returns:
            Count of unread notifications
        """
        return Notification.objects.filter(
            recipient=user,
            is_read=False,
        ).count()

    @staticmethod
    def notify_new_message(message: 'Message') -> Notification:
        """
        Create notification for new message.

        Args:
            message: Message instance

        Returns:
            Notification instance
        """
        thread = message.thread
        subject = thread.subject or 'New Message'

        # Notify all participants except sender
        notifications = []
        for participant in thread.participants.exclude(id=message.sender.id):
            notification = NotificationService.create_notification(
                recipient=participant,
                notification_type='message',
                title=f'New message from {message.sender.get_full_name()}',
                body=f'{subject}: {message.body[:100]}...' if len(message.body) > 100 else message.body,
                link=f'/messages/{thread.id}',
                metadata={'thread_id': str(thread.id), 'message_id': str(message.id)},
            )
            notifications.append(notification)

        return notifications[0] if notifications else None


class MessagingService:
    """Service for managing in-app messaging."""

    @staticmethod
    @transaction.atomic
    def create_thread(
        *,
        subject: str = '',
        participants: list,
        application=None,
        created_by,
    ) -> MessageThread:
        """
        Create a new message thread.

        Args:
            subject: Thread subject (optional)
            participants: List of User instances who will participate
            application: Related application (optional)
            created_by: User creating the thread

        Returns:
            MessageThread instance

        Raises:
            BusinessValidationError: If participants list is invalid
        """
        if not participants:
            raise BusinessValidationError('Thread must have at least one participant')

        if len(participants) < 2:
            raise BusinessValidationError('Thread must have at least two participants')

        thread = MessageThread.objects.create(
            subject=subject,
            application=application,
        )

        # Add participants (including creator)
        all_participants = set(participants)
        all_participants.add(created_by)
        thread.participants.set(all_participants)

        return thread

    @staticmethod
    @transaction.atomic
    def send_message(
        *,
        thread: MessageThread,
        sender,
        body: str,
        attachments: list = None,
        is_system_message: bool = False,
    ) -> Message:
        """
        Send a message in a thread.

        Args:
            thread: MessageThread instance
            sender: User sending the message
            body: Message body text
            attachments: List of attachment metadata (optional)
            is_system_message: Whether this is a system-generated message

        Returns:
            Message instance

        Raises:
            BusinessValidationError: If sender is not a participant
        """
        # Verify sender is a participant
        if not is_system_message and not thread.participants.filter(id=sender.id).exists():
            raise BusinessValidationError('You are not a participant in this thread')

        message = Message.objects.create(
            thread=thread,
            sender=sender,
            body=body,
            attachments=attachments or [],
            is_system_message=is_system_message,
        )

        # Mark as read by sender immediately
        message.mark_as_read(sender)

        # Update thread timestamp
        thread.save(update_fields=['updated_at'])

        # Send notifications to other participants
        if not is_system_message:
            NotificationService.notify_new_message(message)

        return message

    @staticmethod
    @transaction.atomic
    def mark_as_read(message: Message, user) -> Message:
        """
        Mark a message as read by a user.

        Args:
            message: Message instance
            user: User marking as read

        Returns:
            Updated message
        """
        message.mark_as_read(user)
        return message

    @staticmethod
    @transaction.atomic
    def mark_thread_as_read(thread: MessageThread, user) -> int:
        """
        Mark all messages in a thread as read.

        Args:
            thread: MessageThread instance
            user: User marking as read

        Returns:
            Number of messages marked as read
        """
        count = 0
        for message in thread.messages.exclude(sender=user):
            if str(user.id) not in message.read_by:
                message.mark_as_read(user)
                count += 1

        return count

    @staticmethod
    def get_unread_count(user, thread: MessageThread = None) -> int:
        """
        Get count of unread messages for a user.

        Args:
            user: User instance
            thread: Optional specific thread to count

        Returns:
            Count of unread messages
        """
        messages_qs = Message.objects.filter(
            thread__participants=user,
        ).exclude(
            sender=user,
        )

        if thread:
            messages_qs = messages_qs.filter(thread=thread)

        # Count messages where user.id is not in read_by
        count = 0
        for message in messages_qs:
            if str(user.id) not in message.read_by:
                count += 1

        return count

    @staticmethod
    @transaction.atomic
    def archive_thread(thread: MessageThread, user) -> MessageThread:
        """
        Archive a thread.

        Args:
            thread: MessageThread instance
            user: User archiving (must be participant)

        Returns:
            Updated thread

        Raises:
            BusinessValidationError: If user is not a participant
        """
        if not thread.participants.filter(id=user.id).exists():
            raise BusinessValidationError('You are not a participant in this thread')

        if not thread.is_archived:
            thread.is_archived = True
            thread.archived_at = timezone.now()
            thread.save(update_fields=['is_archived', 'archived_at', 'updated_at'])

        return thread

    @staticmethod
    @transaction.atomic
    def add_participant(thread: MessageThread, user, added_by) -> MessageThread:
        """
        Add a participant to a thread.

        Args:
            thread: MessageThread instance
            user: User to add
            added_by: User adding the participant

        Returns:
            Updated thread

        Raises:
            BusinessValidationError: If added_by is not a participant
        """
        if not thread.participants.filter(id=added_by.id).exists():
            raise BusinessValidationError('You are not a participant in this thread')

        if not thread.participants.filter(id=user.id).exists():
            thread.participants.add(user)

            # Create system message
            MessagingService.send_message(
                thread=thread,
                sender=added_by,
                body=f'{added_by.get_full_name()} added {user.get_full_name()} to the conversation',
                is_system_message=True,
            )

        return thread

    @staticmethod
    @transaction.atomic
    def remove_participant(thread: MessageThread, user, removed_by) -> MessageThread:
        """
        Remove a participant from a thread.

        Args:
            thread: MessageThread instance
            user: User to remove
            removed_by: User removing the participant

        Returns:
            Updated thread

        Raises:
            BusinessValidationError: If removed_by is not a participant or trying to leave
        """
        if not thread.participants.filter(id=removed_by.id).exists():
            raise BusinessValidationError('You are not a participant in this thread')

        if thread.participants.count() <= 2:
            raise BusinessValidationError('Cannot remove participant from a thread with only 2 participants')

        if thread.participants.filter(id=user.id).exists():
            thread.participants.remove(user)

            # Create system message
            action = 'left' if user.id == removed_by.id else 'was removed from'
            MessagingService.send_message(
                thread=thread,
                sender=removed_by,
                body=f'{user.get_full_name()} {action} the conversation',
                is_system_message=True,
            )

        return thread

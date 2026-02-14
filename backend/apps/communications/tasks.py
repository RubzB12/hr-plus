"""Celery tasks for communications app."""

from celery import shared_task

from .models import EmailLog


@shared_task
def send_email_task(email_log_id: str):
    """
    Async task to send an email.

    Args:
        email_log_id: UUID of EmailLog to send

    Returns:
        Email status
    """
    from .services import EmailService

    try:
        email_log = EmailLog.objects.get(id=email_log_id)
        email_log = EmailService.send_email_sync(email_log)
        return {'status': email_log.status, 'email_log_id': str(email_log.id)}
    except EmailLog.DoesNotExist:
        return {'status': 'failed', 'error': f'EmailLog {email_log_id} not found'}


@shared_task
def process_email_events():
    """
    Process email delivery events from email provider webhooks.
    This would typically poll or process webhooks from services like SendGrid, AWS SES, etc.

    Returns:
        Summary of processed events
    """
    # Placeholder for webhook processing
    # In production, this would:
    # 1. Fetch delivery/open/bounce events from email provider API
    # 2. Update EmailLog records with status changes
    # 3. Mark emails as delivered/opened/bounced

    return {'processed': 0, 'message': 'Webhook processing not yet implemented'}


@shared_task
def cleanup_old_email_logs():
    """
    Clean up old email logs (keep last 90 days).
    Runs weekly.

    Returns:
        Number of logs deleted
    """
    from datetime import timedelta

    from django.utils import timezone

    ninety_days_ago = timezone.now() - timedelta(days=90)

    count, _ = EmailLog.objects.filter(created_at__lt=ninety_days_ago).delete()

    return {'deleted': count}

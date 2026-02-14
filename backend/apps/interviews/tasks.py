"""Celery tasks for interviews app."""

from datetime import timedelta

from django.utils import timezone

from apps.communications.services import EmailService
from apps.interviews.models import Interview, Scorecard
from celery import shared_task


@shared_task
def send_interview_reminders():
    """
    Send interview reminders 24h and 1h before scheduled time.
    Runs every 15 minutes via celery beat.
    """
    now = timezone.now()

    # 24-hour reminders
    reminder_24h_start = now + timedelta(hours=23, minutes=45)
    reminder_24h_end = now + timedelta(hours=24, minutes=15)

    interviews_24h = Interview.objects.filter(
        scheduled_start__gte=reminder_24h_start,
        scheduled_start__lt=reminder_24h_end,
        status__in=['scheduled', 'confirmed', 'rescheduled'],
    ).select_related(
        'application__candidate__user',
        'application__requisition',
    ).prefetch_related(
        'participants__interviewer__user',
    )

    for interview in interviews_24h:
        # Send to candidate
        EmailService.send_interview_reminder(
            interview=interview,
            recipient=interview.application.candidate.user,
            hours_until=24,
        )

        # Send to interviewers
        for participant in interview.participants.all():
            EmailService.send_interview_reminder(
                interview=interview,
                recipient=participant.interviewer.user,
                hours_until=24,
            )

    # 1-hour reminders
    reminder_1h_start = now + timedelta(minutes=45)
    reminder_1h_end = now + timedelta(hours=1, minutes=15)

    interviews_1h = Interview.objects.filter(
        scheduled_start__gte=reminder_1h_start,
        scheduled_start__lt=reminder_1h_end,
        status__in=['scheduled', 'confirmed', 'rescheduled'],
    ).select_related(
        'application__candidate__user',
        'application__requisition',
    ).prefetch_related(
        'participants__interviewer__user',
    )

    for interview in interviews_1h:
        # Send to candidate
        EmailService.send_interview_reminder(
            interview=interview,
            recipient=interview.application.candidate.user,
            hours_until=1,
        )

        # Send to interviewers
        for participant in interview.participants.all():
            EmailService.send_interview_reminder(
                interview=interview,
                recipient=participant.interviewer.user,
                hours_until=1,
            )

    return {
        '24h_reminders': interviews_24h.count(),
        '1h_reminders': interviews_1h.count(),
    }


@shared_task
def send_scorecard_reminders():
    """
    Send scorecard submission reminders for completed interviews.
    Runs daily at 9 AM.
    """
    # Find interviews completed in last 7 days without submitted scorecards
    seven_days_ago = timezone.now() - timedelta(days=7)

    completed_interviews = Interview.objects.filter(
        status='completed',
        scheduled_end__gte=seven_days_ago,
    ).select_related(
        'application__candidate__user',
        'application__requisition',
    ).prefetch_related(
        'participants__interviewer__user',
        'scorecards',
    )

    reminder_count = 0

    for interview in completed_interviews:
        # Check each participant
        for participant in interview.participants.all():
            # Check if they've submitted their scorecard
            has_submitted = Scorecard.objects.filter(
                interview=interview,
                interviewer=participant.interviewer,
                is_draft=False,
            ).exists()

            if not has_submitted:
                EmailService.send_scorecard_reminder(
                    interview=interview,
                    recipient=participant.interviewer.user,
                )
                reminder_count += 1

    return {'reminders_sent': reminder_count}


@shared_task
def auto_complete_past_interviews():
    """
    Auto-complete interviews that ended more than 1 hour ago.
    Runs hourly.
    """
    one_hour_ago = timezone.now() - timedelta(hours=1)

    interviews = Interview.objects.filter(
        scheduled_end__lt=one_hour_ago,
        status__in=['scheduled', 'confirmed', 'rescheduled'],
    )

    count = interviews.count()
    interviews.update(status='completed', updated_at=timezone.now())

    return {'auto_completed': count}

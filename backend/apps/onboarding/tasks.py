"""Celery tasks for onboarding."""

from celery import shared_task
from django.utils import timezone

from apps.offers.models import Offer

from .services import OnboardingService


@shared_task(name='onboarding.create_plan_on_offer_acceptance')
def create_plan_on_offer_acceptance(offer_id: str):
    """
    Create onboarding plan when offer is accepted.

    This task should be triggered by the offer acceptance workflow.
    """
    try:
        offer = Offer.objects.select_related(
            'application__candidate__user', 'application__requisition'
        ).get(id=offer_id)

        if offer.status != 'accepted':
            return {
                'success': False,
                'message': f'Offer {offer_id} is not in accepted status',
            }

        # Check if plan already exists
        if hasattr(offer, 'onboarding_plan'):
            return {
                'success': True,
                'message': 'Onboarding plan already exists',
                'plan_id': str(offer.onboarding_plan.id),
                'access_token': offer.onboarding_plan.access_token,
            }

        # Use start date from offer, or default to 2 weeks from acceptance
        start_date = offer.start_date or (timezone.now().date() + timezone.timedelta(days=14))

        # Create onboarding plan
        plan = OnboardingService.create_plan_from_offer(offer, start_date=start_date)

        return {
            'success': True,
            'message': 'Onboarding plan created successfully',
            'plan_id': str(plan.id),
            'access_token': plan.access_token,
        }

    except Offer.DoesNotExist:
        return {'success': False, 'message': f'Offer {offer_id} not found'}
    except Exception as e:
        return {'success': False, 'message': f'Error creating onboarding plan: {str(e)}'}


@shared_task(name='onboarding.send_upcoming_task_reminders')
def send_upcoming_task_reminders():
    """
    Send reminders for tasks due in next 3 days.

    This task should be scheduled to run daily.
    """
    from datetime import timedelta

    from apps.communications.services import EmailService

    from .models import OnboardingTask

    # Get tasks due in next 3 days
    today = timezone.now().date()
    three_days = today + timedelta(days=3)

    upcoming_tasks = OnboardingTask.objects.filter(
        due_date__gte=today, due_date__lte=three_days, status='pending'
    ).select_related('plan__application__candidate__user', 'assigned_to')

    reminders_sent = 0

    for task in upcoming_tasks:
        if task.assigned_to:
            # Send reminder email
            EmailService.send_task_reminder(task)
            reminders_sent += 1

    return {
        'success': True,
        'reminders_sent': reminders_sent,
        'message': f'Sent {reminders_sent} task reminders',
    }


@shared_task(name='onboarding.send_overdue_task_notifications')
def send_overdue_task_notifications():
    """
    Send notifications for overdue tasks.

    This task should be scheduled to run daily.
    """
    from apps.communications.services import NotificationService

    from .models import OnboardingTask

    # Get overdue tasks
    today = timezone.now().date()

    overdue_tasks = OnboardingTask.objects.filter(
        due_date__lt=today, status__in=['pending', 'in_progress']
    ).select_related('plan__application__candidate__user', 'plan__hr_contact__user', 'assigned_to')

    notifications_sent = 0

    for task in overdue_tasks:
        # Notify assignee
        if task.assigned_to:
            NotificationService.create_notification(
                recipient=task.assigned_to,
                notification_type='onboarding_task_overdue',
                title='Onboarding Task Overdue',
                body=f'Task "{task.title}" is overdue (was due {task.due_date})',
                link=f'/onboarding/tasks/{task.id}',
                metadata={'task_id': str(task.id), 'plan_id': str(task.plan.id)},
            )
            notifications_sent += 1

        # Notify HR contact
        if task.plan.hr_contact and task.plan.hr_contact.user != task.assigned_to:
            NotificationService.create_notification(
                recipient=task.plan.hr_contact.user,
                notification_type='onboarding_task_overdue',
                title='Onboarding Task Overdue',
                body=f'Task "{task.title}" for {task.plan.application.candidate.user.get_full_name()} is overdue',
                link=f'/onboarding/tasks/{task.id}',
                metadata={'task_id': str(task.id), 'plan_id': str(task.plan.id), 'candidate_id': str(task.plan.application.candidate.id)},
            )
            notifications_sent += 1

    return {
        'success': True,
        'notifications_sent': notifications_sent,
        'overdue_tasks': overdue_tasks.count(),
        'message': f'Sent {notifications_sent} overdue task notifications',
    }


@shared_task(name='onboarding.auto_complete_stale_plans')
def auto_complete_stale_plans():
    """
    Auto-complete onboarding plans that are past start date + 30 days with all tasks done.

    This task should be scheduled to run daily.
    """
    from datetime import timedelta

    from .models import OnboardingPlan

    # Get plans that are past start date + 30 days, still in progress, with all tasks complete
    cutoff_date = timezone.now().date() - timedelta(days=30)

    plans = OnboardingPlan.objects.filter(
        status='in_progress', start_date__lt=cutoff_date
    ).prefetch_related('tasks')

    completed_count = 0

    for plan in plans:
        # Check if all tasks are complete
        if not plan.tasks.exclude(status='completed').exists():
            OnboardingService.complete_plan(plan)
            completed_count += 1

    return {
        'success': True,
        'completed_count': completed_count,
        'message': f'Auto-completed {completed_count} onboarding plans',
    }

"""Django signals for the applications app."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ApplicationEvent


@receiver(post_save, sender=ApplicationEvent)
def on_application_event_created(sender, instance, created, **kwargs):
    """Trigger candidate notifications when application events are created."""
    if not created:
        return

    from .candidate_notifications import CandidateNotificationService

    if instance.event_type == 'application.stage_changed':
        CandidateNotificationService.notify_stage_change(instance)
    elif instance.event_type == 'application.created':
        CandidateNotificationService.notify_application_received(instance)

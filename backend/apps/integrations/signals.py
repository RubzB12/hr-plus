"""Signal handlers for integrations app.

Auto-dispatch webhook events on model changes.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.applications.models import Application
from apps.offers.models import Offer

from .services import WebhookService

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Application)
def dispatch_application_webhook(sender, instance, created, **kwargs):
    """
    Dispatch webhook events when Application changes.

    Events:
    - application.created: When application is first submitted
    - application.stage_changed: When moved to different pipeline stage
    - application.rejected: When application is rejected
    - application.hired: When candidate is hired
    """
    # Skip if in raw mode (e.g., during migrations or fixtures)
    if kwargs.get('raw'):
        return

    try:
        from apps.applications.serializers import ApplicationSerializer

        # Prepare payload
        payload = ApplicationSerializer(instance).data

        # Dispatch event based on state
        if created:
            # New application created
            WebhookService.dispatch_event('application.created', payload)
            logger.info(f'Dispatched application.created webhook for {instance.id}')

        else:
            # Application updated - check what changed
            if instance.status == 'rejected':
                WebhookService.dispatch_event('application.rejected', payload)
                logger.info(f'Dispatched application.rejected webhook for {instance.id}')

            elif instance.status == 'hired':
                WebhookService.dispatch_event('application.hired', payload)
                logger.info(f'Dispatched application.hired webhook for {instance.id}')

            # Check if stage changed
            # Note: This would require tracking previous state, which we'll handle in service layer
            # For now, we can dispatch stage_changed event whenever current_stage is updated

    except Exception as e:
        logger.error(f'Failed to dispatch application webhook: {str(e)}')
        # Don't raise - webhook dispatch should not break application save


@receiver(post_save, sender=Offer)
def dispatch_offer_webhook(sender, instance, created, **kwargs):
    """
    Dispatch webhook events when Offer changes.

    Events:
    - offer.created: When offer is created
    - offer.sent: When offer is sent to candidate
    - offer.accepted: When candidate accepts offer
    - offer.declined: When candidate declines offer
    """
    # Skip if in raw mode
    if kwargs.get('raw'):
        return

    try:
        from apps.offers.serializers import OfferSerializer

        # Prepare payload
        payload = OfferSerializer(instance).data

        # Dispatch event based on state
        if created:
            # New offer created
            WebhookService.dispatch_event('offer.created', payload)
            logger.info(f'Dispatched offer.created webhook for {instance.id}')

        else:
            # Offer updated - check status
            if instance.status == 'sent':
                WebhookService.dispatch_event('offer.sent', payload)
                logger.info(f'Dispatched offer.sent webhook for {instance.id}')

            elif instance.status == 'accepted':
                WebhookService.dispatch_event('offer.accepted', payload)
                logger.info(f'Dispatched offer.accepted webhook for {instance.id}')

            elif instance.status == 'declined':
                WebhookService.dispatch_event('offer.declined', payload)
                logger.info(f'Dispatched offer.declined webhook for {instance.id}')

    except Exception as e:
        logger.error(f'Failed to dispatch offer webhook: {str(e)}')
        # Don't raise - webhook dispatch should not break offer save


# Note: Requisition webhooks could be added here in future
# For now, these would be manually triggered via services when requisitions open/fill/cancel

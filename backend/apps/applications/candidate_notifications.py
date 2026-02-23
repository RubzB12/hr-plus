"""Service for creating candidate-facing in-app notifications."""

import logging

from apps.communications.models import Notification

logger = logging.getLogger(__name__)


class CandidateNotificationService:
    """Creates in-app notifications for candidates based on application events."""

    @staticmethod
    def notify_stage_change(event) -> None:
        """Create a notification when an application moves to a new stage."""
        try:
            application = event.application
            candidate_user = application.candidate.user
            job_title = application.requisition.title
            stage_name = event.to_stage.name if event.to_stage else 'a new stage'

            Notification.objects.create(
                recipient=candidate_user,
                type='stage_change',
                title=f'Update on your {job_title} application',
                body=f'Your application has moved to the {stage_name} stage.',
                link=f'/dashboard/applications/{application.id}',
                metadata={
                    'application_id': str(application.id),
                    'to_stage': stage_name,
                    'job_title': job_title,
                },
            )
        except Exception as e:
            logger.error(f'Failed to create stage change notification: {e}', exc_info=True)

    @staticmethod
    def notify_application_received(event) -> None:
        """Create a notification confirming an application was received."""
        try:
            application = event.application
            candidate_user = application.candidate.user
            job_title = application.requisition.title

            Notification.objects.create(
                recipient=candidate_user,
                type='application_received',
                title=f'Application received — {job_title}',
                body=(
                    f'We received your application for {job_title}. '
                    'Our team will review it and be in touch soon.'
                ),
                link=f'/dashboard/applications/{application.id}',
                metadata={
                    'application_id': str(application.id),
                    'job_title': job_title,
                },
            )
        except Exception as e:
            logger.error(f'Failed to create application received notification: {e}', exc_info=True)

"""Business logic for candidate applications."""

from datetime import datetime

from django.db import transaction
from django.utils import timezone

from apps.core.exceptions import BusinessValidationError

from .models import Application, ApplicationEvent, ApplicationTag, CandidateNote, Tag


class ApplicationService:
    """Manages the application lifecycle."""

    @staticmethod
    def _generate_application_id() -> str:
        year = datetime.now().year
        last = (
            Application.objects
            .filter(application_id__startswith=f'APP-{year}-')
            .order_by('-application_id')
            .values_list('application_id', flat=True)
            .first()
        )
        if last:
            seq = int(last.split('-')[-1]) + 1
        else:
            seq = 1
        return f'APP-{year}-{seq:05d}'

    @staticmethod
    @transaction.atomic
    def create_application(
        candidate,
        requisition,
        *,
        cover_letter: str = '',
        screening_responses: dict | None = None,
        source: str = 'career_site',
    ) -> Application:
        """
        Create a new application with duplicate detection.

        - Prevents duplicate applications to the same requisition
        - Auto-assigns to the first pipeline stage
        - Snapshots resume data
        - Logs creation event
        """
        if Application.objects.filter(
            candidate=candidate,
            requisition=requisition,
        ).exists():
            raise BusinessValidationError(
                'You have already applied to this position.'
            )

        if requisition.status != 'open':
            raise BusinessValidationError(
                'This position is not currently accepting applications.'
            )

        first_stage = requisition.stages.order_by('order').first()

        resume_snapshot = None
        if candidate.resume_parsed:
            resume_snapshot = candidate.resume_parsed

        application = Application.objects.create(
            application_id=ApplicationService._generate_application_id(),
            candidate=candidate,
            requisition=requisition,
            status='applied',
            current_stage=first_stage,
            source=source,
            cover_letter=cover_letter,
            screening_responses=screening_responses or {},
            resume_snapshot=resume_snapshot,
        )

        ApplicationEvent.objects.create(
            application=application,
            event_type='application.created',
            actor=candidate.user,
            to_stage=first_stage,
            metadata={'source': source},
        )

        return application

    @staticmethod
    @transaction.atomic
    def withdraw(application: Application, actor) -> Application:
        """Withdraw an application."""
        if application.status in ('withdrawn', 'rejected', 'hired'):
            raise BusinessValidationError(
                'Cannot withdraw an application that is already '
                f'{application.status}.'
            )

        application.status = 'withdrawn'
        application.withdrawn_at = timezone.now()
        application.save(update_fields=['status', 'withdrawn_at', 'updated_at'])

        ApplicationEvent.objects.create(
            application=application,
            event_type='application.withdrawn',
            actor=actor,
        )

        return application

    @staticmethod
    @transaction.atomic
    def reject(
        application: Application, *, reason: str = '', actor=None,
    ) -> Application:
        """Reject an application."""
        if application.status in ('rejected', 'withdrawn', 'hired'):
            raise BusinessValidationError(
                f'Cannot reject an application that is {application.status}.'
            )

        application.status = 'rejected'
        application.rejection_reason = reason
        application.rejected_at = timezone.now()
        application.save(update_fields=[
            'status', 'rejection_reason', 'rejected_at', 'updated_at',
        ])

        ApplicationEvent.objects.create(
            application=application,
            event_type='application.rejected',
            actor=actor,
            metadata={'reason': reason},
        )

        return application

    @staticmethod
    @transaction.atomic
    def move_to_stage(application: Application, stage, actor) -> Application:
        """Move an application to a different pipeline stage."""
        if application.current_stage == stage:
            return application

        old_stage = application.current_stage
        application.current_stage = stage
        application.save(update_fields=['current_stage', 'updated_at'])

        ApplicationEvent.objects.create(
            application=application,
            event_type='application.stage_changed',
            actor=actor,
            from_stage=old_stage,
            to_stage=stage,
        )

        return application

    @staticmethod
    def add_note(
        application: Application, *, author, body: str, is_private: bool = False,
    ) -> CandidateNote:
        """Add an internal note to an application."""
        note = CandidateNote.objects.create(
            application=application,
            author=author,
            body=body,
            is_private=is_private,
        )

        ApplicationEvent.objects.create(
            application=application,
            event_type='note.added',
            actor=author.user,
            metadata={'note_id': str(note.id), 'is_private': is_private},
        )

        return note

    @staticmethod
    def add_tag(application: Application, tag_name: str, actor) -> ApplicationTag:
        """Add a tag to an application (creates tag if it doesn't exist)."""
        tag, _ = Tag.objects.get_or_create(
            name=tag_name.strip().lower(),
        )
        app_tag, created = ApplicationTag.objects.get_or_create(
            application=application,
            tag=tag,
            defaults={'added_by': actor},
        )
        return app_tag

    @staticmethod
    def remove_tag(application: Application, tag_name: str) -> None:
        """Remove a tag from an application."""
        ApplicationTag.objects.filter(
            application=application,
            tag__name=tag_name.strip().lower(),
        ).delete()

    @staticmethod
    @transaction.atomic
    def bulk_move_to_stage(application_ids: list, stage, actor) -> int:
        """Move multiple applications to a stage. Returns count moved."""
        applications = Application.objects.filter(
            id__in=application_ids,
        ).exclude(current_stage=stage)

        count = 0
        for app in applications:
            ApplicationService.move_to_stage(app, stage, actor)
            count += 1
        return count

    @staticmethod
    @transaction.atomic
    def bulk_reject(
        application_ids: list, *, reason: str = '', actor=None,
    ) -> int:
        """Reject multiple applications. Returns count rejected."""
        applications = Application.objects.filter(
            id__in=application_ids,
        ).exclude(status__in=['rejected', 'withdrawn', 'hired'])

        count = 0
        for app in applications:
            ApplicationService.reject(app, reason=reason, actor=actor)
            count += 1
        return count

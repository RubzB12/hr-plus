"""Tests for ApplicationService."""

import pytest

from apps.accounts.tests.factories import CandidateProfileFactory, InternalUserFactory
from apps.applications.models import ApplicationEvent
from apps.applications.services import ApplicationService
from apps.core.exceptions import BusinessValidationError
from apps.jobs.tests.factories import PipelineStageFactory, PublishedRequisitionFactory, RequisitionFactory

from .factories import ApplicationFactory


@pytest.mark.django_db
class TestApplicationServiceCreate:
    def test_create_application_success(self):
        candidate = CandidateProfileFactory()
        requisition = PublishedRequisitionFactory()
        PipelineStageFactory(requisition=requisition, name='Applied', order=0)

        app = ApplicationService.create_application(
            candidate=candidate,
            requisition=requisition,
            cover_letter='I am excited!',
        )

        assert app.application_id.startswith('APP-')
        assert app.status == 'applied'
        assert app.current_stage.name == 'Applied'
        assert app.cover_letter == 'I am excited!'

    def test_create_application_logs_event(self):
        candidate = CandidateProfileFactory()
        requisition = PublishedRequisitionFactory()
        PipelineStageFactory(requisition=requisition, name='Applied', order=0)

        app = ApplicationService.create_application(
            candidate=candidate,
            requisition=requisition,
        )

        event = ApplicationEvent.objects.filter(application=app).first()
        assert event is not None
        assert event.event_type == 'application.created'
        assert event.actor == candidate.user

    def test_create_application_prevents_duplicate(self):
        candidate = CandidateProfileFactory()
        requisition = PublishedRequisitionFactory()
        PipelineStageFactory(requisition=requisition, order=0)

        ApplicationService.create_application(
            candidate=candidate, requisition=requisition,
        )

        with pytest.raises(BusinessValidationError, match='already applied'):
            ApplicationService.create_application(
                candidate=candidate, requisition=requisition,
            )

    def test_create_application_rejects_closed_requisition(self):
        candidate = CandidateProfileFactory()
        requisition = RequisitionFactory(status='cancelled')

        with pytest.raises(BusinessValidationError, match='not currently accepting'):
            ApplicationService.create_application(
                candidate=candidate, requisition=requisition,
            )

    def test_create_application_snapshots_resume(self):
        candidate = CandidateProfileFactory()
        candidate.resume_parsed = {'skills': ['Python', 'Django']}
        candidate.save()

        requisition = PublishedRequisitionFactory()
        PipelineStageFactory(requisition=requisition, order=0)

        app = ApplicationService.create_application(
            candidate=candidate, requisition=requisition,
        )

        assert app.resume_snapshot == {'skills': ['Python', 'Django']}


@pytest.mark.django_db
class TestApplicationServiceWithdraw:
    def test_withdraw_success(self):
        app = ApplicationFactory()
        result = ApplicationService.withdraw(app, actor=app.candidate.user)

        assert result.status == 'withdrawn'
        assert result.withdrawn_at is not None

    def test_withdraw_logs_event(self):
        app = ApplicationFactory()
        ApplicationService.withdraw(app, actor=app.candidate.user)

        event = app.events.filter(event_type='application.withdrawn').first()
        assert event is not None

    def test_cannot_withdraw_rejected(self):
        app = ApplicationFactory(status='rejected')

        with pytest.raises(BusinessValidationError, match='Cannot withdraw'):
            ApplicationService.withdraw(app, actor=app.candidate.user)

    def test_cannot_withdraw_hired(self):
        app = ApplicationFactory(status='hired')

        with pytest.raises(BusinessValidationError, match='Cannot withdraw'):
            ApplicationService.withdraw(app, actor=app.candidate.user)


@pytest.mark.django_db
class TestApplicationServiceReject:
    def test_reject_success(self):
        app = ApplicationFactory()
        result = ApplicationService.reject(app, reason='Not a fit')

        assert result.status == 'rejected'
        assert result.rejection_reason == 'Not a fit'
        assert result.rejected_at is not None

    def test_reject_logs_event(self):
        app = ApplicationFactory()
        ApplicationService.reject(app, reason='Not a fit')

        event = app.events.filter(event_type='application.rejected').first()
        assert event is not None
        assert event.metadata['reason'] == 'Not a fit'


@pytest.mark.django_db
class TestApplicationServiceMoveStage:
    def test_move_to_stage(self):
        app = ApplicationFactory()
        new_stage = PipelineStageFactory(
            requisition=app.requisition, name='Interview', order=1,
        )

        result = ApplicationService.move_to_stage(
            app, new_stage, actor=app.candidate.user,
        )

        assert result.current_stage == new_stage

    def test_move_to_stage_logs_event(self):
        app = ApplicationFactory()
        old_stage = app.current_stage
        new_stage = PipelineStageFactory(
            requisition=app.requisition, name='Interview', order=1,
        )

        ApplicationService.move_to_stage(
            app, new_stage, actor=app.candidate.user,
        )

        event = app.events.filter(
            event_type='application.stage_changed',
        ).first()
        assert event is not None
        assert event.from_stage == old_stage
        assert event.to_stage == new_stage

    def test_move_to_same_stage_is_noop(self):
        app = ApplicationFactory()
        same_stage = app.current_stage

        ApplicationService.move_to_stage(
            app, same_stage, actor=app.candidate.user,
        )

        assert app.events.filter(
            event_type='application.stage_changed',
        ).count() == 0


@pytest.mark.django_db
class TestApplicationServiceNotes:
    def test_add_note(self):
        app = ApplicationFactory()
        author = InternalUserFactory()
        note = ApplicationService.add_note(
            app, author=author, body='Great candidate!',
        )

        assert note.application == app
        assert note.body == 'Great candidate!'
        assert note.is_private is False

    def test_add_note_logs_event(self):
        app = ApplicationFactory()
        author = InternalUserFactory()
        ApplicationService.add_note(
            app, author=author, body='Note here',
        )

        event = app.events.filter(event_type='note.added').first()
        assert event is not None
        assert event.actor == author.user

    def test_add_private_note(self):
        app = ApplicationFactory()
        author = InternalUserFactory()
        note = ApplicationService.add_note(
            app, author=author, body='Private!', is_private=True,
        )

        assert note.is_private is True


@pytest.mark.django_db
class TestApplicationServiceTags:
    def test_add_tag_creates_tag(self):
        app = ApplicationFactory()
        author = InternalUserFactory()
        app_tag = ApplicationService.add_tag(
            app, 'senior', actor=author.user,
        )

        assert app_tag.tag.name == 'senior'
        assert app.application_tags.count() == 1

    def test_add_tag_idempotent(self):
        app = ApplicationFactory()
        author = InternalUserFactory()
        ApplicationService.add_tag(app, 'senior', actor=author.user)
        ApplicationService.add_tag(app, 'senior', actor=author.user)

        assert app.application_tags.count() == 1

    def test_remove_tag(self):
        app = ApplicationFactory()
        author = InternalUserFactory()
        ApplicationService.add_tag(app, 'senior', actor=author.user)
        ApplicationService.remove_tag(app, 'senior')

        assert app.application_tags.count() == 0


@pytest.mark.django_db
class TestApplicationServiceBulk:
    def test_bulk_move_to_stage(self):
        app1 = ApplicationFactory()
        app2 = ApplicationFactory(
            requisition=app1.requisition,
            current_stage=app1.current_stage,
        )
        new_stage = PipelineStageFactory(
            requisition=app1.requisition, name='Interview', order=1,
        )

        count = ApplicationService.bulk_move_to_stage(
            [app1.id, app2.id], new_stage, actor=app1.candidate.user,
        )

        assert count == 2
        app1.refresh_from_db()
        app2.refresh_from_db()
        assert app1.current_stage == new_stage
        assert app2.current_stage == new_stage

    def test_bulk_reject(self):
        app1 = ApplicationFactory()
        app2 = ApplicationFactory()
        author = InternalUserFactory()

        count = ApplicationService.bulk_reject(
            [app1.id, app2.id], reason='Not qualified', actor=author.user,
        )

        assert count == 2
        app1.refresh_from_db()
        app2.refresh_from_db()
        assert app1.status == 'rejected'
        assert app2.status == 'rejected'

    def test_bulk_reject_skips_already_rejected(self):
        app1 = ApplicationFactory(status='rejected')
        app2 = ApplicationFactory()

        count = ApplicationService.bulk_reject(
            [app1.id, app2.id], reason='Not fit',
        )

        assert count == 1

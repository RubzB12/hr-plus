"""Factory Boy factories for applications app."""

import factory

from apps.accounts.tests.factories import CandidateProfileFactory, InternalUserFactory
from apps.applications.models import (
    Application,
    ApplicationEvent,
    CandidateNote,
    Tag,
    TalentPool,
)
from apps.jobs.tests.factories import PipelineStageFactory, PublishedRequisitionFactory


class ApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Application
        django_get_or_create = ()
        # Skip auto_now_add validation to allow setting applied_at in tests
        skip_postgeneration_save = True

    application_id = factory.Sequence(lambda n: f'APP-2026-{n:05d}')
    candidate = factory.SubFactory(CandidateProfileFactory)
    requisition = factory.SubFactory(PublishedRequisitionFactory)
    status = 'applied'
    source = 'career_site'
    current_stage = factory.SubFactory(
        PipelineStageFactory,
        requisition=factory.SelfAttribute('..requisition'),
        order=0,
    )

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override _create to allow setting applied_at despite auto_now_add."""
        # Extract applied_at if provided
        applied_at = kwargs.pop('applied_at', None)

        # Create instance
        instance = super()._create(model_class, *args, **kwargs)

        # If applied_at was provided, update it directly (bypassing auto_now_add)
        if applied_at is not None:
            model_class.objects.filter(pk=instance.pk).update(applied_at=applied_at)
            instance.refresh_from_db()

        return instance


class ApplicationEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ApplicationEvent

    application = factory.SubFactory(ApplicationFactory)
    event_type = 'application.created'


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag

    name = factory.Sequence(lambda n: f'tag-{n}')
    color = '#6366f1'


class CandidateNoteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CandidateNote

    application = factory.SubFactory(ApplicationFactory)
    author = factory.SubFactory(InternalUserFactory)
    body = factory.Faker('paragraph')
    is_private = False


class TalentPoolFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TalentPool

    name = factory.Sequence(lambda n: f'Talent Pool {n}')
    description = factory.Faker('paragraph')
    owner = factory.SubFactory(InternalUserFactory)
    is_dynamic = False
    search_criteria = factory.LazyFunction(dict)

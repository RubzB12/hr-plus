"""Factory Boy factories for applications app."""

import factory

from apps.accounts.tests.factories import CandidateProfileFactory, InternalUserFactory
from apps.applications.models import Application, ApplicationEvent, CandidateNote, Tag
from apps.jobs.tests.factories import PipelineStageFactory, PublishedRequisitionFactory


class ApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Application

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

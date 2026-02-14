"""Factory Boy factories for interviews app."""

from datetime import timedelta

import factory
from django.utils import timezone

from apps.accounts.tests.factories import InternalUserFactory
from apps.applications.tests.factories import ApplicationFactory
from apps.interviews.models import (
    Debrief,
    Interview,
    InterviewParticipant,
    Scorecard,
    ScorecardCriterion,
    ScorecardCriterionRating,
    ScorecardTemplate,
)


class ScorecardTemplateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ScorecardTemplate

    name = factory.Sequence(lambda n: f'Scorecard Template {n}')
    description = factory.Faker('paragraph')
    rating_scale_min = 1
    rating_scale_max = 5
    is_active = True


class ScorecardCriterionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ScorecardCriterion

    template = factory.SubFactory(ScorecardTemplateFactory)
    name = factory.Sequence(lambda n: f'Criterion {n}')
    description = factory.Faker('sentence')
    category = 'technical'
    order = factory.Sequence(lambda n: n)
    weight = 1.0


class InterviewFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Interview

    application = factory.SubFactory(ApplicationFactory)
    type = 'video'
    status = 'scheduled'
    scheduled_start = factory.LazyFunction(lambda: timezone.now() + timedelta(days=7))
    scheduled_end = factory.LazyAttribute(lambda obj: obj.scheduled_start + timedelta(hours=1))
    timezone = 'UTC'
    location = ''
    video_link = factory.Faker('url')
    prep_notes_interviewer = factory.Faker('paragraph')
    prep_notes_candidate = factory.Faker('paragraph')
    created_by = factory.LazyAttribute(lambda _: ApplicationFactory().candidate.user)


class InterviewParticipantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InterviewParticipant

    interview = factory.SubFactory(InterviewFactory)
    interviewer = factory.SubFactory(InternalUserFactory)
    role = 'lead'
    rsvp_status = 'pending'


class ScorecardFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Scorecard

    interview = factory.SubFactory(InterviewFactory)
    interviewer = factory.SubFactory(InternalUserFactory)
    overall_rating = 4
    recommendation = 'hire'
    strengths = factory.Faker('paragraph')
    concerns = factory.Faker('paragraph')
    notes = factory.Faker('paragraph')
    is_draft = True


class ScorecardCriterionRatingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ScorecardCriterionRating

    scorecard = factory.SubFactory(ScorecardFactory)
    criterion = factory.SubFactory(ScorecardCriterionFactory)
    rating = 4
    comment = factory.Faker('sentence')


class DebriefFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Debrief

    application = factory.SubFactory(ApplicationFactory)
    scheduled_at = factory.LazyFunction(lambda: timezone.now() + timedelta(days=1))
    decision = None
    notes = factory.Faker('paragraph')

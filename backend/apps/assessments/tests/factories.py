"""Factories for assessments app tests."""

from datetime import timedelta

import factory
from django.utils import timezone

from apps.accounts.tests.factories import InternalUserFactory
from apps.applications.tests.factories import ApplicationFactory
from apps.assessments.models import (
    Assessment,
    AssessmentTemplate,
    ReferenceCheckRequest,
    ReferenceCheckResponse,
)


class AssessmentTemplateFactory(factory.django.DjangoModelFactory):
    """Factory for AssessmentTemplate model."""

    class Meta:
        model = AssessmentTemplate

    name = factory.Faker('sentence', nb_words=3)
    type = 'technical'
    description = factory.Faker('paragraph')
    instructions = factory.Faker('paragraph')
    duration = 60
    passing_score = 70.00
    scoring_rubric = factory.Dict({})
    questions = factory.List([])
    external_url = ''
    is_active = True


class AssessmentFactory(factory.django.DjangoModelFactory):
    """Factory for Assessment model."""

    class Meta:
        model = Assessment

    application = factory.SubFactory(ApplicationFactory)
    template = factory.SubFactory(AssessmentTemplateFactory)
    status = 'assigned'
    assigned_by = factory.SubFactory(InternalUserFactory)
    due_date = factory.LazyFunction(lambda: timezone.now() + timedelta(days=7))
    access_token = factory.Faker('sha256')
    started_at = None
    completed_at = None
    responses = factory.Dict({})
    score = None
    evaluated_by = None
    evaluated_at = None
    evaluator_notes = ''


class ReferenceCheckRequestFactory(factory.django.DjangoModelFactory):
    """Factory for ReferenceCheckRequest model."""

    class Meta:
        model = ReferenceCheckRequest

    application = factory.SubFactory(ApplicationFactory)
    reference_name = factory.Faker('name')
    reference_email = factory.Faker('email')
    reference_phone = factory.Faker('phone_number')
    reference_company = factory.Faker('company')
    reference_title = factory.Faker('job')
    relationship = 'manager'
    requested_by = factory.SubFactory(InternalUserFactory)
    status = 'pending'
    questionnaire = factory.List([
        factory.Dict({
            'id': 'relationship_duration',
            'question': 'How long have you known the candidate?',
            'type': 'text',
            'required': True,
        })
    ])
    notes = ''
    due_date = factory.LazyFunction(lambda: timezone.now() + timedelta(days=14))
    sent_at = None
    access_token = factory.Faker('sha256')


class ReferenceCheckResponseFactory(factory.django.DjangoModelFactory):
    """Factory for ReferenceCheckResponse model."""

    class Meta:
        model = ReferenceCheckResponse

    request = factory.SubFactory(ReferenceCheckRequestFactory)
    responses = factory.Dict({
        'relationship_duration': '2 years as direct manager',
    })
    overall_recommendation = 'recommend'
    would_rehire = True
    additional_comments = factory.Faker('paragraph')
    reference_ip = '127.0.0.1'

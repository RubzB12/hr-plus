"""Factories for onboarding tests."""

import secrets
from datetime import timedelta

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from apps.accounts.tests.factories import DepartmentFactory, InternalUserFactory, JobLevelFactory
from apps.applications.tests.factories import ApplicationFactory
from apps.offers.tests.factories import OfferFactory


class OnboardingTemplateFactory(DjangoModelFactory):
    """Factory for OnboardingTemplate model."""

    class Meta:
        model = 'onboarding.OnboardingTemplate'

    name = factory.Sequence(lambda n: f'Onboarding Template {n}')
    description = factory.Faker('paragraph')
    department = factory.SubFactory(DepartmentFactory)
    job_level = factory.SubFactory(JobLevelFactory)
    is_active = True
    tasks = factory.LazyFunction(
        lambda: [
            {
                'title': 'Complete I-9 Form',
                'description': 'Submit I-9 form with proper documentation',
                'category': 'document',
                'days_offset': 0,
                'assigned_to': 'candidate',
            },
            {
                'title': 'Setup Workstation',
                'description': 'Configure laptop and development environment',
                'category': 'equipment',
                'days_offset': 1,
                'assigned_to': 'hr',
            },
            {
                'title': 'Team Introduction',
                'description': 'Meet the team and get oriented',
                'category': 'meeting',
                'days_offset': 1,
                'assigned_to': 'buddy',
            },
        ]
    )
    required_documents = factory.LazyFunction(
        lambda: ['i9', 'w4', 'direct_deposit', 'signed_offer']
    )
    forms = factory.LazyFunction(lambda: ['equipment_preferences', 'emergency_contact'])


class OnboardingPlanFactory(DjangoModelFactory):
    """Factory for OnboardingPlan model."""

    class Meta:
        model = 'onboarding.OnboardingPlan'

    application = factory.SubFactory(ApplicationFactory)
    offer = factory.SubFactory(OfferFactory)
    template = factory.SubFactory(OnboardingTemplateFactory)
    status = 'pending'
    start_date = factory.LazyFunction(lambda: timezone.now().date() + timedelta(days=14))
    buddy = factory.SubFactory(InternalUserFactory)
    hr_contact = factory.SubFactory(InternalUserFactory)
    access_token = factory.LazyFunction(lambda: secrets.token_urlsafe(32))
    completed_at = None
    notes = factory.Faker('paragraph')


class OnboardingTaskFactory(DjangoModelFactory):
    """Factory for OnboardingTask model."""

    class Meta:
        model = 'onboarding.OnboardingTask'

    plan = factory.SubFactory(OnboardingPlanFactory)
    title = factory.Sequence(lambda n: f'Task {n}')
    description = factory.Faker('paragraph')
    category = 'other'
    assigned_to = None
    due_date = factory.LazyFunction(lambda: timezone.now().date() + timedelta(days=7))
    status = 'pending'
    completed_at = None
    completed_by = None
    order = factory.Sequence(lambda n: n)
    notes = ''


class OnboardingDocumentFactory(DjangoModelFactory):
    """Factory for OnboardingDocument model."""

    class Meta:
        model = 'onboarding.OnboardingDocument'

    plan = factory.SubFactory(OnboardingPlanFactory)
    document_type = 'i9'
    file = None
    status = 'pending'
    uploaded_by = None
    uploaded_at = None
    reviewed_by = None
    reviewed_at = None
    rejection_reason = ''
    notes = ''


class OnboardingFormFactory(DjangoModelFactory):
    """Factory for OnboardingForm model."""

    class Meta:
        model = 'onboarding.OnboardingForm'

    plan = factory.SubFactory(OnboardingPlanFactory)
    form_type = 'equipment_preferences'
    data = factory.LazyFunction(
        lambda: {
            'laptop': 'MacBook Pro',
            'monitor': '27 inch',
            'keyboard': 'Mechanical',
            'mouse': 'Wireless',
        }
    )
    submitted_at = None
    submitted_by = None

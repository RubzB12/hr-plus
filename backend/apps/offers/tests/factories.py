"""Factories for offers app tests."""


import factory
from django.utils import timezone

from apps.accounts.tests.factories import (
    DepartmentFactory,
    InternalUserFactory,
    JobLevelFactory,
)
from apps.applications.tests.factories import ApplicationFactory
from apps.offers.models import Offer, OfferApproval, OfferNegotiationLog


class OfferFactory(factory.django.DjangoModelFactory):
    """Factory for Offer model."""

    class Meta:
        model = Offer

    offer_id = factory.Sequence(lambda n: f'OFR-2026-{n:03d}')
    application = factory.SubFactory(ApplicationFactory)
    version = 1
    status = 'draft'
    title = factory.Faker('job')
    level = factory.SubFactory(JobLevelFactory)
    department = factory.SubFactory(DepartmentFactory)
    base_salary = '100000.00'
    salary_currency = 'USD'
    salary_frequency = 'annual'
    bonus = '10000.00'
    equity = 'Stock options: 1000 shares'
    sign_on_bonus = '5000.00'
    relocation = '10000.00'
    start_date = factory.LazyFunction(
        lambda: (timezone.now() + timezone.timedelta(days=30)).date()
    )
    expiration_date = factory.LazyFunction(
        lambda: (timezone.now() + timezone.timedelta(days=7)).date()
    )
    notes = ''
    created_by = factory.SubFactory(InternalUserFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override _create to allow setting created_at despite auto_now_add."""
        # Extract created_at if provided
        created_at = kwargs.pop('created_at', None)

        # Create instance
        instance = super()._create(model_class, *args, **kwargs)

        # If created_at was provided, update it directly (bypassing auto_now_add)
        if created_at is not None:
            model_class.objects.filter(pk=instance.pk).update(created_at=created_at)
            instance.refresh_from_db()

        return instance


class OfferApprovalFactory(factory.django.DjangoModelFactory):
    """Factory for OfferApproval model."""

    class Meta:
        model = OfferApproval

    offer = factory.SubFactory(OfferFactory)
    approver = factory.SubFactory(InternalUserFactory)
    order = 0
    status = 'pending'
    comments = ''


class OfferNegotiationLogFactory(factory.django.DjangoModelFactory):
    """Factory for OfferNegotiationLog model."""

    class Meta:
        model = OfferNegotiationLog

    offer = factory.SubFactory(OfferFactory)
    logged_by = factory.SubFactory(InternalUserFactory)
    candidate_request = factory.Faker('paragraph')
    internal_response = factory.Faker('paragraph')
    outcome = 'pending'

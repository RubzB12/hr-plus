"""Factory Boy factories for jobs app."""

import factory
from django.utils import timezone

from apps.accounts.tests.factories import (
    DepartmentFactory,
    InternalUserFactory,
    JobLevelFactory,
    LocationFactory,
    TeamFactory,
)
from apps.jobs.models import PipelineStage, Requisition, RequisitionApproval


class RequisitionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Requisition

    requisition_id = factory.Sequence(lambda n: f'REQ-2026-{n:03d}')
    title = factory.Faker('job')
    slug = factory.LazyAttribute(
        lambda o: f'{o.title.lower().replace(" ", "-")}-{o.requisition_id}'
    )
    department = factory.SubFactory(DepartmentFactory)
    team = factory.SubFactory(TeamFactory, department=factory.SelfAttribute('..department'))
    hiring_manager = factory.SubFactory(InternalUserFactory)
    recruiter = factory.SubFactory(InternalUserFactory)
    status = 'draft'
    employment_type = 'full_time'
    level = factory.SubFactory(JobLevelFactory)
    location = factory.SubFactory(LocationFactory)
    remote_policy = 'hybrid'
    salary_min = factory.LazyFunction(lambda: 80000)
    salary_max = factory.LazyFunction(lambda: 120000)
    salary_currency = 'ZAR'
    description = factory.Faker('paragraph', nb_sentences=5)
    headcount = 1
    created_by = factory.LazyAttribute(lambda o: o.recruiter)


class PublishedRequisitionFactory(RequisitionFactory):
    """A requisition that is published and visible on the career site."""

    status = 'open'
    published_at = factory.LazyFunction(timezone.now)
    opened_at = factory.LazyFunction(timezone.now)


class PipelineStageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PipelineStage

    requisition = factory.SubFactory(RequisitionFactory)
    name = factory.Sequence(lambda n: f'Stage {n}')
    order = factory.Sequence(lambda n: n)
    stage_type = 'custom'


class RequisitionApprovalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RequisitionApproval

    requisition = factory.SubFactory(RequisitionFactory, status='pending_approval')
    approver = factory.SubFactory(InternalUserFactory)
    order = factory.Sequence(lambda n: n)
    status = 'pending'

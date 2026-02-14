"""Factory Boy factories for accounts app."""

import factory
from django.contrib.auth import get_user_model

from apps.accounts.models import (
    CandidateProfile,
    Department,
    InternalUser,
    JobLevel,
    Location,
    Permission,
    Role,
    Team,
)

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}@example.com')
    email = factory.LazyAttribute(lambda o: o.username)
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_internal = False

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop('password', 'TestPass123!')  # noqa: S106
        user = super()._create(model_class, *args, **kwargs)
        user.set_password(password)
        user.save(update_fields=['password'])
        return user


class InternalUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InternalUser

    user = factory.SubFactory(UserFactory, is_internal=True, is_staff=True)
    employee_id = factory.Sequence(lambda n: f'EMP{n:05d}')
    title = factory.Faker('job')
    is_active = True


class CandidateProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CandidateProfile

    user = factory.SubFactory(UserFactory, is_internal=False)
    location_city = factory.Faker('city')
    location_country = factory.Faker('country')
    source = 'direct'


class PermissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Permission

    codename = factory.Sequence(lambda n: f'test.permission_{n}')
    name = factory.Sequence(lambda n: f'Test Permission {n}')
    module = 'accounts'
    action = 'view'


class RoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Role

    name = factory.Sequence(lambda n: f'Test Role {n}')
    description = factory.Faker('sentence')
    is_system = False


class DepartmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Department

    name = factory.Sequence(lambda n: f'Department {n}')
    is_active = True


class TeamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Team

    name = factory.Sequence(lambda n: f'Team {n}')
    department = factory.SubFactory(DepartmentFactory)
    is_active = True


class LocationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Location

    name = factory.Sequence(lambda n: f'Office {n}')
    city = factory.Faker('city')
    country = factory.Faker('country')
    is_active = True


class JobLevelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = JobLevel

    name = factory.Sequence(lambda n: f'Level {n}')
    level_number = factory.Sequence(lambda n: n + 1)

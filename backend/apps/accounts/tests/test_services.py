"""Tests for accounts services."""

import pytest
from django.contrib.auth import get_user_model

from apps.accounts.models import CandidateProfile
from apps.accounts.services import AuthService, UserService
from apps.core.exceptions import BusinessValidationError, DuplicateError

from .factories import DepartmentFactory, RoleFactory, UserFactory

_TEST_PASSWORD = 'SecurePass123!'  # noqa: S105

User = get_user_model()


@pytest.mark.django_db
class TestAuthService:
    def test_register_candidate_creates_user_and_profile(self):
        user = AuthService.register_candidate({
            'email': 'candidate@example.com',
            'password': _TEST_PASSWORD,
            'first_name': 'Jane',
            'last_name': 'Doe',
        })

        assert user.email == 'candidate@example.com'
        assert user.first_name == 'Jane'
        assert user.is_internal is False
        assert user.check_password('SecurePass123!')
        assert CandidateProfile.objects.filter(user=user).exists()

    def test_register_candidate_duplicate_email_raises(self):
        UserFactory(email='dupe@example.com')

        with pytest.raises(DuplicateError, match='email already exists'):
            AuthService.register_candidate({
                'email': 'dupe@example.com',
                'password': _TEST_PASSWORD,
                'first_name': 'Dupe',
                'last_name': 'User',
            })

    def test_register_candidate_creates_source(self):
        user = AuthService.register_candidate({
            'email': 'sourced@example.com',
            'password': _TEST_PASSWORD,
            'first_name': 'Sourced',
            'last_name': 'User',
            'source': 'linkedin',
        })

        profile = CandidateProfile.objects.get(user=user)
        assert profile.source == 'linkedin'

    def test_generate_password_reset_token(self):
        user = UserFactory()
        token_data = AuthService.generate_password_reset_token(user)

        assert 'uid' in token_data
        assert 'token' in token_data

    def test_reset_password_with_valid_token(self):
        user = UserFactory()
        token_data = AuthService.generate_password_reset_token(user)
        combined_token = f"{token_data['uid']}:{token_data['token']}"

        result = AuthService.reset_password(combined_token, 'NewSecurePass456!')
        assert result is True

        user.refresh_from_db()
        assert user.check_password('NewSecurePass456!')

    def test_reset_password_with_invalid_token(self):
        with pytest.raises(BusinessValidationError, match='Invalid'):
            AuthService.reset_password('invalid:token', 'NewPass123!')


@pytest.mark.django_db
class TestUserService:
    def test_create_internal_user(self):
        dept = DepartmentFactory()
        role = RoleFactory()

        internal_user = UserService.create_internal_user(
            email='recruiter@company.com',
            first_name='Bob',
            last_name='Smith',
            employee_id='EMP001',
            title='Senior Recruiter',
            password='StaffPass123!',  # noqa: S106
            department=dept,
            role_ids=[role.id],
        )

        assert internal_user.employee_id == 'EMP001'
        assert internal_user.user.email == 'recruiter@company.com'
        assert internal_user.user.is_internal is True
        assert internal_user.user.is_staff is True
        assert internal_user.department == dept
        assert role in internal_user.roles.all()

    def test_create_internal_user_duplicate_email_raises(self):
        UserFactory(email='existing@company.com')

        with pytest.raises(DuplicateError, match='email already exists'):
            UserService.create_internal_user(
                email='existing@company.com',
                first_name='Dupe',
                last_name='User',
                employee_id='EMP999',
                title='Manager',
            )

    def test_create_internal_user_duplicate_employee_id_raises(self):
        dept = DepartmentFactory()
        UserService.create_internal_user(
            email='first@company.com',
            first_name='First',
            last_name='User',
            employee_id='EMP001',
            title='Manager',
            department=dept,
        )

        with pytest.raises(DuplicateError, match='employee with this ID'):
            UserService.create_internal_user(
                email='second@company.com',
                first_name='Second',
                last_name='User',
                employee_id='EMP001',
                title='Manager',
                department=dept,
            )

    def test_deactivate_user(self):
        internal_user = UserService.create_internal_user(
            email='deactivate@company.com',
            first_name='Deact',
            last_name='User',
            employee_id='EMP_DEACT',
            title='Analyst',
        )

        UserService.deactivate_user(internal_user)

        internal_user.refresh_from_db()
        assert internal_user.is_active is False
        assert internal_user.user.is_active is False

    def test_assign_roles(self):
        internal_user = UserService.create_internal_user(
            email='roles@company.com',
            first_name='Role',
            last_name='User',
            employee_id='EMP_ROLE',
            title='Analyst',
        )
        role1 = RoleFactory(name='Recruiter')
        role2 = RoleFactory(name='Admin')

        UserService.assign_roles(internal_user, [role1, role2])

        assert set(internal_user.roles.all()) == {role1, role2}

"""Tests for accounts views."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import CandidateProfile

from .factories import (
    CandidateProfileFactory,
    DepartmentFactory,
    InternalUserFactory,
    RoleFactory,
    UserFactory,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def candidate_user():
    user = UserFactory(email='candidate@test.com', is_internal=False)
    CandidateProfileFactory(user=user)
    return user


@pytest.fixture
def internal_user():
    return InternalUserFactory()


@pytest.mark.django_db
class TestRegisterView:
    def test_register_candidate_success(self, api_client):
        response = api_client.post(
            reverse('auth-register'),
            {
                'email': 'new@example.com',
                'password': 'SecurePass123!',
                'first_name': 'New',
                'last_name': 'Candidate',
            },
            format='json',
        )

        assert response.status_code == 201
        assert response.data['email'] == 'new@example.com'
        assert response.data['is_internal'] is False
        assert CandidateProfile.objects.filter(user__email='new@example.com').exists()

    def test_register_duplicate_email_fails(self, api_client):
        UserFactory(email='existing@example.com')

        response = api_client.post(
            reverse('auth-register'),
            {
                'email': 'existing@example.com',
                'password': 'SecurePass123!',
                'first_name': 'Dupe',
                'last_name': 'User',
            },
            format='json',
        )

        assert response.status_code == 400

    def test_register_weak_password_fails(self, api_client):
        response = api_client.post(
            reverse('auth-register'),
            {
                'email': 'weak@example.com',
                'password': '123',
                'first_name': 'Weak',
                'last_name': 'Pass',
            },
            format='json',
        )

        assert response.status_code == 400


@pytest.mark.django_db
class TestLoginView:
    def test_login_success(self, api_client):
        UserFactory(email='login@test.com')

        response = api_client.post(
            reverse('auth-login'),
            {'email': 'login@test.com', 'password': 'TestPass123!'},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['email'] == 'login@test.com'

    def test_login_wrong_password(self, api_client):
        UserFactory(email='login@test.com')

        response = api_client.post(
            reverse('auth-login'),
            {'email': 'login@test.com', 'password': 'WrongPass!'},
            format='json',
        )

        assert response.status_code == 400

    def test_login_nonexistent_user(self, api_client):
        response = api_client.post(
            reverse('auth-login'),
            {'email': 'ghost@test.com', 'password': 'Whatever123!'},
            format='json',
        )

        assert response.status_code == 400


@pytest.mark.django_db
class TestLogoutView:
    def test_logout_success(self, api_client, candidate_user):
        api_client.force_authenticate(user=candidate_user)
        response = api_client.post(reverse('auth-logout'))
        assert response.status_code == 204

    def test_logout_unauthenticated(self, api_client):
        response = api_client.post(reverse('auth-logout'))
        assert response.status_code == 403


@pytest.mark.django_db
class TestMeView:
    def test_me_authenticated(self, api_client, candidate_user):
        api_client.force_authenticate(user=candidate_user)
        response = api_client.get(reverse('auth-me'))

        assert response.status_code == 200
        assert response.data['email'] == 'candidate@test.com'

    def test_me_unauthenticated(self, api_client):
        response = api_client.get(reverse('auth-me'))
        assert response.status_code == 403

    def test_me_returns_internal_profile(self, api_client, internal_user):
        api_client.force_authenticate(user=internal_user.user)
        response = api_client.get(reverse('auth-me'))

        assert response.status_code == 200
        assert response.data['is_internal'] is True
        assert response.data['internal_profile'] is not None


@pytest.mark.django_db
class TestPasswordResetView:
    def test_password_reset_request_always_200(self, api_client):
        """Should return success even for non-existent emails (prevent enumeration)."""
        response = api_client.post(
            reverse('auth-password-reset'),
            {'email': 'nonexistent@test.com'},
            format='json',
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestCandidateProfileView:
    def test_get_profile(self, api_client, candidate_user):
        api_client.force_authenticate(user=candidate_user)
        response = api_client.get(reverse('candidate-profile'))

        assert response.status_code == 200
        assert response.data['user']['email'] == 'candidate@test.com'

    def test_update_profile(self, api_client, candidate_user):
        api_client.force_authenticate(user=candidate_user)
        response = api_client.put(
            reverse('candidate-profile'),
            {
                'phone': '+1234567890',
                'location_city': 'New York',
                'location_country': 'US',
            },
            format='json',
        )

        assert response.status_code == 200
        profile = CandidateProfile.objects.get(user=candidate_user)
        assert profile.phone == '+1234567890'
        assert profile.location_city == 'New York'

    def test_internal_user_cannot_access(self, api_client, internal_user):
        api_client.force_authenticate(user=internal_user.user)
        response = api_client.get(reverse('candidate-profile'))
        assert response.status_code == 403


@pytest.mark.django_db
class TestInternalUserViewSet:
    def test_list_requires_internal_user(self, api_client, candidate_user):
        api_client.force_authenticate(user=candidate_user)
        response = api_client.get(reverse('internal-user-list'))
        assert response.status_code == 403

    def test_list_internal_users(self, api_client, internal_user):
        api_client.force_authenticate(user=internal_user.user)
        response = api_client.get(reverse('internal-user-list'))
        assert response.status_code == 200

    def test_deactivate_user(self, api_client, internal_user):
        target = InternalUserFactory()
        api_client.force_authenticate(user=internal_user.user)

        response = api_client.post(
            reverse('internal-user-deactivate', args=[target.id]),
        )
        assert response.status_code == 200
        target.refresh_from_db()
        assert target.is_active is False


@pytest.mark.django_db
class TestDepartmentViewSet:
    def test_list_departments(self, api_client, internal_user):
        DepartmentFactory.create_batch(3)
        api_client.force_authenticate(user=internal_user.user)

        response = api_client.get(reverse('department-list'))
        assert response.status_code == 200
        assert response.data['count'] == 3

    def test_create_department(self, api_client, internal_user):
        api_client.force_authenticate(user=internal_user.user)
        response = api_client.post(
            reverse('department-list'),
            {'name': 'Engineering'},
            format='json',
        )
        assert response.status_code == 201
        assert response.data['name'] == 'Engineering'


@pytest.mark.django_db
class TestRoleViewSet:
    def test_cannot_delete_system_role(self, api_client, internal_user):
        role = RoleFactory(name='Super Admin', is_system=True)
        api_client.force_authenticate(user=internal_user.user)

        response = api_client.delete(reverse('role-detail', args=[role.id]))
        assert response.status_code == 400

"""Tests for talent pool functionality."""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.tests.factories import CandidateProfileFactory, InternalUserFactory, UserFactory
from apps.applications.models import TalentPool
from apps.applications.services import TalentPoolService
from apps.applications.tests.factories import TalentPoolFactory
from apps.core.exceptions import BusinessValidationError


@pytest.fixture
def authenticated_client(db):
    """Create authenticated internal user API client."""
    user = UserFactory(is_internal=True)
    InternalUserFactory(user=user)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.mark.django_db
class TestTalentPoolService:
    """Tests for TalentPoolService."""

    def test_create_pool_static(self):
        """Can create a static talent pool."""
        owner = InternalUserFactory()
        pool = TalentPoolService.create_pool(
            name='Senior Engineers',
            description='Experienced backend engineers',
            owner=owner,
            is_dynamic=False,
        )

        assert pool.id is not None
        assert pool.name == 'Senior Engineers'
        assert pool.owner == owner
        assert not pool.is_dynamic
        assert pool.search_criteria == {}

    def test_create_pool_dynamic(self):
        """Can create a dynamic talent pool with search criteria."""
        owner = InternalUserFactory()
        criteria = {'skills': ['Python', 'Django'], 'experience_min': 5}

        pool = TalentPoolService.create_pool(
            name='Python Experts',
            description='Experienced Python developers',
            owner=owner,
            is_dynamic=True,
            search_criteria=criteria,
        )

        assert pool.is_dynamic
        assert pool.search_criteria == criteria

    def test_add_candidates_to_pool(self):
        """Can add candidates to a talent pool."""
        pool = TalentPoolFactory()
        candidates = CandidateProfileFactory.create_batch(3)
        candidate_ids = [c.id for c in candidates]

        count = TalentPoolService.add_candidates(pool, candidate_ids)

        assert count == 3
        assert pool.candidates.count() == 3

    def test_add_candidates_duplicate_prevention(self):
        """Adding same candidate twice doesn't create duplicates."""
        pool = TalentPoolFactory()
        candidate = CandidateProfileFactory()

        TalentPoolService.add_candidates(pool, [candidate.id])
        count = TalentPoolService.add_candidates(pool, [candidate.id])

        assert count == 0  # No new candidates added
        assert pool.candidates.count() == 1

    def test_remove_candidates_from_pool(self):
        """Can remove candidates from a talent pool."""
        pool = TalentPoolFactory()
        candidates = CandidateProfileFactory.create_batch(3)
        candidate_ids = [c.id for c in candidates]
        pool.candidates.add(*candidates)

        count = TalentPoolService.remove_candidates(pool, candidate_ids[:2])

        assert count == 2
        assert pool.candidates.count() == 1

    def test_update_pool_details(self):
        """Can update talent pool metadata."""
        pool = TalentPoolFactory(name='Old Name', is_dynamic=False)

        updated = TalentPoolService.update_pool_details(
            pool,
            name='New Name',
            description='Updated description',
            is_dynamic=True,
        )

        assert updated.name == 'New Name'
        assert updated.description == 'Updated description'
        assert updated.is_dynamic

    def test_update_dynamic_pool_requires_dynamic(self):
        """Cannot update a static pool as dynamic."""
        pool = TalentPoolFactory(is_dynamic=False)

        with pytest.raises(BusinessValidationError, match='dynamic pools'):
            TalentPoolService.update_dynamic_pool(pool)


@pytest.mark.django_db
class TestTalentPoolViewSet:
    """Tests for TalentPoolViewSet API endpoints."""

    def test_list_talent_pools_requires_auth(self, client: APIClient):
        """Unauthenticated requests are rejected."""
        url = reverse('talent-pool-list')
        response = client.get(url)
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_list_talent_pools_success(self, authenticated_client: APIClient):
        """Authenticated users can list talent pools."""
        TalentPoolFactory.create_batch(3)
        url = reverse('talent-pool-list')

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

    def test_create_talent_pool_success(self, authenticated_client: APIClient):
        """Can create a talent pool via API."""
        url = reverse('talent-pool-list')
        payload = {
            'name': 'Frontend Specialists',
            'description': 'React and TypeScript experts',
            'is_dynamic': False,
        }

        response = authenticated_client.post(url, payload, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Frontend Specialists'
        assert response.data['is_dynamic'] is False

    def test_create_dynamic_pool_with_criteria(self, authenticated_client: APIClient):
        """Can create a dynamic pool with search criteria."""
        url = reverse('talent-pool-list')
        criteria = {'skills': ['React', 'TypeScript'], 'location': 'San Francisco'}
        payload = {
            'name': 'SF React Devs',
            'description': 'React developers in SF',
            'is_dynamic': True,
            'search_criteria': criteria,
        }

        response = authenticated_client.post(url, payload, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['is_dynamic'] is True
        # Retrieve full detail to check criteria
        pool = TalentPool.objects.get(id=response.data['id'])
        assert pool.search_criteria == criteria

    def test_retrieve_talent_pool_detail(self, authenticated_client: APIClient):
        """Can retrieve talent pool with candidate list."""
        pool = TalentPoolFactory()
        candidates = CandidateProfileFactory.create_batch(2)
        pool.candidates.add(*candidates)

        url = reverse('talent-pool-detail', args=[pool.id])
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == pool.name
        assert len(response.data['candidates']) == 2

    def test_update_talent_pool_success(self, authenticated_client: APIClient):
        """Can update a talent pool."""
        pool = TalentPoolFactory(name='Old Name')
        url = reverse('talent-pool-detail', args=[pool.id])
        payload = {'name': 'Updated Name'}

        response = authenticated_client.patch(url, payload, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Name'

    def test_delete_talent_pool_success(self, authenticated_client: APIClient):
        """Can delete a talent pool."""
        pool = TalentPoolFactory()
        url = reverse('talent-pool-detail', args=[pool.id])

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not TalentPool.objects.filter(id=pool.id).exists()

    def test_add_candidates_to_pool_via_api(self, authenticated_client: APIClient):
        """Can add candidates to a pool via API."""
        pool = TalentPoolFactory()
        candidates = CandidateProfileFactory.create_batch(3)
        url = reverse('talent-pool-add-candidates', args=[pool.id])
        payload = {'candidate_ids': [str(c.id) for c in candidates]}

        response = authenticated_client.post(url, payload, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['added'] == 3
        assert pool.candidates.count() == 3

    def test_remove_candidates_from_pool_via_api(self, authenticated_client: APIClient):
        """Can remove candidates from a pool via API."""
        pool = TalentPoolFactory()
        candidates = CandidateProfileFactory.create_batch(3)
        pool.candidates.add(*candidates)

        url = reverse('talent-pool-remove-candidates', args=[pool.id])
        payload = {'candidate_ids': [str(candidates[0].id), str(candidates[1].id)]}

        response = authenticated_client.post(url, payload, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['removed'] == 2
        assert pool.candidates.count() == 1

    def test_refresh_dynamic_pool_via_api(self, authenticated_client: APIClient):
        """Can refresh a dynamic pool via API."""
        pool = TalentPoolFactory(is_dynamic=True)
        candidates = CandidateProfileFactory.create_batch(2)
        pool.candidates.add(*candidates)

        url = reverse('talent-pool-refresh', args=[pool.id])
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'candidate_count' in response.data
        assert response.data['candidate_count'] == 2

    def test_refresh_static_pool_fails(self, authenticated_client: APIClient):
        """Cannot refresh a static pool."""
        pool = TalentPoolFactory(is_dynamic=False)
        url = reverse('talent-pool-refresh', args=[pool.id])

        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

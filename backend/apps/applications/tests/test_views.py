"""Tests for applications API views."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.tests.factories import CandidateProfileFactory, InternalUserFactory
from apps.jobs.tests.factories import PipelineStageFactory, PublishedRequisitionFactory

from .factories import ApplicationFactory, CandidateNoteFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def candidate_client():
    client = APIClient()
    candidate = CandidateProfileFactory()
    client.force_authenticate(user=candidate.user)
    return client, candidate


@pytest.fixture
def internal_client():
    client = APIClient()
    internal = InternalUserFactory()
    client.force_authenticate(user=internal.user)
    return client, internal


# --- Candidate endpoint tests ---

@pytest.mark.django_db
class TestCandidateApplicationCreate:
    def test_create_application(self, candidate_client):
        client, candidate = candidate_client
        req = PublishedRequisitionFactory()
        PipelineStageFactory(requisition=req, order=0)

        response = client.post(
            reverse('candidate-application-create'),
            {
                'requisition_id': str(req.id),
                'cover_letter': 'I am interested!',
                'source': 'career_site',
            },
            format='json',
        )

        assert response.status_code == 201
        assert response.data['status'] == 'applied'

    def test_duplicate_application_fails(self, candidate_client):
        client, candidate = candidate_client
        req = PublishedRequisitionFactory()
        PipelineStageFactory(requisition=req, order=0)

        # First application
        client.post(
            reverse('candidate-application-create'),
            {'requisition_id': str(req.id)},
            format='json',
        )

        # Duplicate
        response = client.post(
            reverse('candidate-application-create'),
            {'requisition_id': str(req.id)},
            format='json',
        )

        assert response.status_code == 400

    def test_requires_auth(self, api_client):
        response = api_client.post(
            reverse('candidate-application-create'),
            {'requisition_id': '00000000-0000-0000-0000-000000000000'},
            format='json',
        )
        assert response.status_code == 403

    def test_internal_user_cannot_apply(self, internal_client):
        client, _internal = internal_client
        response = client.post(
            reverse('candidate-application-create'),
            {'requisition_id': '00000000-0000-0000-0000-000000000000'},
            format='json',
        )
        assert response.status_code == 403


@pytest.mark.django_db
class TestCandidateApplicationList:
    def test_list_own_applications(self, candidate_client):
        client, candidate = candidate_client
        ApplicationFactory(candidate=candidate)
        ApplicationFactory()  # Other candidate

        response = client.get(reverse('candidate-application-list'))

        assert response.status_code == 200
        assert response.data['count'] == 1

    def test_cannot_see_others_applications(self, candidate_client):
        client, _candidate = candidate_client
        ApplicationFactory()  # Other candidate

        response = client.get(reverse('candidate-application-list'))

        assert response.data['count'] == 0


@pytest.mark.django_db
class TestCandidateApplicationDetail:
    def test_get_detail_with_events(self, candidate_client):
        client, candidate = candidate_client
        app = ApplicationFactory(candidate=candidate)

        response = client.get(
            reverse('candidate-application-detail', kwargs={'pk': str(app.id)}),
        )

        assert response.status_code == 200
        assert response.data['application_id'] == app.application_id
        assert 'events' in response.data

    def test_cannot_view_others_application(self, candidate_client):
        client, _candidate = candidate_client
        other_app = ApplicationFactory()

        response = client.get(
            reverse(
                'candidate-application-detail',
                kwargs={'pk': str(other_app.id)},
            ),
        )

        assert response.status_code == 404


@pytest.mark.django_db
class TestCandidateApplicationWithdraw:
    def test_withdraw_application(self, candidate_client):
        client, candidate = candidate_client
        app = ApplicationFactory(candidate=candidate)

        response = client.post(
            reverse(
                'candidate-application-withdraw',
                kwargs={'pk': str(app.id)},
            ),
        )

        assert response.status_code == 200
        assert response.data['status'] == 'withdrawn'

    def test_cannot_withdraw_others_application(self, candidate_client):
        client, _candidate = candidate_client
        other_app = ApplicationFactory()

        response = client.post(
            reverse(
                'candidate-application-withdraw',
                kwargs={'pk': str(other_app.id)},
            ),
        )

        assert response.status_code != 200


@pytest.mark.django_db
class TestInternalApplicationViewSet:
    def test_list_requires_internal_user(self, api_client):
        response = api_client.get(reverse('internal-application-list'))
        assert response.status_code == 403

    def test_list_all_applications(self, internal_client):
        client, _internal = internal_client
        ApplicationFactory()
        ApplicationFactory()

        response = client.get(reverse('internal-application-list'))

        assert response.status_code == 200
        assert response.data['count'] == 2

    def test_reject_action(self, internal_client):
        client, _internal = internal_client
        app = ApplicationFactory()

        response = client.post(
            reverse(
                'internal-application-reject',
                kwargs={'pk': str(app.id)},
            ),
            {'reason': 'Not qualified'},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['status'] == 'rejected'

    def test_star_toggle(self, internal_client):
        client, _internal = internal_client
        app = ApplicationFactory(is_starred=False)

        response = client.post(
            reverse(
                'internal-application-star',
                kwargs={'pk': str(app.id)},
            ),
        )

        assert response.status_code == 200
        assert response.data['is_starred'] is True

    def test_move_stage_action(self, internal_client):
        client, _internal = internal_client
        app = ApplicationFactory()
        new_stage = PipelineStageFactory(
            requisition=app.requisition, name='Interview', order=1,
        )

        response = client.post(
            reverse(
                'internal-application-move-stage',
                kwargs={'pk': str(app.id)},
            ),
            {'stage_id': str(new_stage.id)},
            format='json',
        )

        assert response.status_code == 200

    def test_add_note(self, internal_client):
        client, _internal = internal_client
        app = ApplicationFactory()

        response = client.post(
            reverse(
                'internal-application-notes',
                kwargs={'pk': str(app.id)},
            ),
            {'body': 'Great candidate!'},
            format='json',
        )

        assert response.status_code == 201
        assert response.data['body'] == 'Great candidate!'

    def test_list_notes(self, internal_client):
        client, _internal = internal_client
        app = ApplicationFactory()
        CandidateNoteFactory(application=app)

        response = client.get(
            reverse(
                'internal-application-notes',
                kwargs={'pk': str(app.id)},
            ),
        )

        assert response.status_code == 200
        assert len(response.data) == 1

    def test_add_tag(self, internal_client):
        client, _internal = internal_client
        app = ApplicationFactory()

        response = client.post(
            reverse(
                'internal-application-add-tag',
                kwargs={'pk': str(app.id)},
            ),
            {'tag_name': 'senior'},
            format='json',
        )

        assert response.status_code == 200

    def test_retrieve_detail(self, internal_client):
        client, _internal = internal_client
        app = ApplicationFactory()

        response = client.get(
            reverse(
                'internal-application-detail',
                kwargs={'pk': str(app.id)},
            ),
        )

        assert response.status_code == 200
        assert response.data['application_id'] == app.application_id
        assert 'events' in response.data
        assert 'notes' in response.data
        assert 'tags' in response.data


@pytest.mark.django_db
class TestPipelineBoard:
    def test_pipeline_board(self, internal_client):
        client, _internal = internal_client
        from apps.jobs.tests.factories import PublishedRequisitionFactory
        req = PublishedRequisitionFactory()
        stage = PipelineStageFactory(requisition=req, name='Applied', order=0)
        ApplicationFactory(requisition=req, current_stage=stage)

        response = client.get(
            reverse('pipeline-board', kwargs={'requisition_id': str(req.id)}),
        )

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['name'] == 'Applied'
        assert response.data[0]['application_count'] == 1

    def test_pipeline_board_requires_auth(self, api_client):
        response = api_client.get(
            reverse(
                'pipeline-board',
                kwargs={
                    'requisition_id': '00000000-0000-0000-0000-000000000000',
                },
            ),
        )
        assert response.status_code == 403


@pytest.mark.django_db
class TestBulkActions:
    def test_bulk_reject(self, internal_client):
        client, _internal = internal_client
        app1 = ApplicationFactory()
        app2 = ApplicationFactory()

        response = client.post(
            reverse('bulk-reject'),
            {
                'application_ids': [str(app1.id), str(app2.id)],
                'reason': 'Not qualified',
            },
            format='json',
        )

        assert response.status_code == 200
        assert response.data['rejected'] == 2

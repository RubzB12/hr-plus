"""URL routing for applications app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(
    r'internal/applications',
    views.InternalApplicationViewSet,
    basename='internal-application',
)
router.register(
    r'internal/talent-pools',
    views.TalentPoolViewSet,
    basename='talent-pool',
)

urlpatterns = [
    # Candidate-facing endpoints
    path(
        'applications/',
        views.CandidateApplicationListView.as_view(),
        name='candidate-application-list',
    ),
    path(
        'applications/apply/',
        views.CandidateApplicationCreateView.as_view(),
        name='candidate-application-create',
    ),
    path(
        'applications/<uuid:pk>/',
        views.CandidateApplicationDetailView.as_view(),
        name='candidate-application-detail',
    ),
    path(
        'applications/<uuid:pk>/withdraw/',
        views.CandidateApplicationWithdrawView.as_view(),
        name='candidate-application-withdraw',
    ),

    # Draft application endpoints
    path(
        'applications/drafts/',
        views.DraftApplicationListView.as_view(),
        name='draft-application-list',
    ),
    path(
        'applications/drafts/save/',
        views.DraftApplicationSaveView.as_view(),
        name='draft-application-save',
    ),
    path(
        'applications/drafts/<uuid:pk>/',
        views.DraftApplicationDetailView.as_view(),
        name='draft-application-detail',
    ),
    path(
        'applications/drafts/<uuid:pk>/delete/',
        views.DraftApplicationDeleteView.as_view(),
        name='draft-application-delete',
    ),
    path(
        'applications/drafts/<uuid:pk>/submit/',
        views.DraftApplicationSubmitView.as_view(),
        name='draft-application-submit',
    ),

    # Internal bulk endpoints (before router to avoid pk conflict)
    path(
        'internal/applications/bulk/move-stage/',
        views.BulkMoveStageView.as_view(),
        name='bulk-move-stage',
    ),
    path(
        'internal/applications/bulk/reject/',
        views.BulkRejectView.as_view(),
        name='bulk-reject',
    ),
    path(
        'internal/requisitions/<uuid:requisition_id>/pipeline/',
        views.PipelineBoardView.as_view(),
        name='pipeline-board',
    ),

    # Internal viewset endpoints
    path('', include(router.urls)),
]

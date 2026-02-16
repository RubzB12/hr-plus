"""URL routing for jobs app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(
    r'internal/requisitions',
    views.RequisitionViewSet,
    basename='requisition',
)

urlpatterns = [
    # Public career-site endpoints
    path(
        'jobs/',
        views.PublicJobListView.as_view(),
        name='public-job-list',
    ),
    path(
        'jobs/categories/',
        views.PublicJobCategoryView.as_view(),
        name='public-job-categories',
    ),
    path(
        'jobs/facets/',
        views.PublicJobFacetsView.as_view(),
        name='public-job-facets',
    ),
    path(
        'jobs/<slug:slug>/',
        views.PublicJobDetailView.as_view(),
        name='public-job-detail',
    ),
    path(
        'jobs/<slug:slug>/similar/',
        views.PublicSimilarJobsView.as_view(),
        name='public-job-similar',
    ),
    path(
        'locations/',
        views.PublicLocationListView.as_view(),
        name='public-location-list',
    ),

    # Internal requisition endpoints
    path('', include(router.urls)),
    path(
        'internal/pending-approvals/',
        views.PendingApprovalsView.as_view(),
        name='pending-approvals',
    ),
]

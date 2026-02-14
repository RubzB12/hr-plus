"""URL patterns for interviews app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CandidateInterviewListView,
    DebriefViewSet,
    InternalInterviewViewSet,
    PendingScorecardsView,
    UpcomingInterviewsView,
)

# Internal router
internal_router = DefaultRouter()
internal_router.register('interviews', InternalInterviewViewSet, basename='internal-interview')
internal_router.register('debriefs', DebriefViewSet, basename='debrief')

urlpatterns = [
    # Candidate-facing endpoints
    path('interviews/upcoming/', CandidateInterviewListView.as_view(), name='candidate-interview-list'),

    # Internal endpoints
    path('internal/interviews/upcoming/', UpcomingInterviewsView.as_view(), name='upcoming-interviews'),
    path('internal/interviews/pending-scorecards/', PendingScorecardsView.as_view(), name='pending-scorecards'),
    path('internal/', include(internal_router.urls)),
]

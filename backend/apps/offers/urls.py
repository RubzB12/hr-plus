"""URL configuration for offers app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'offers', views.OfferViewSet, basename='offer')
router.register(r'approvals', views.OfferApprovalViewSet, basename='offerapproval')
router.register(
    r'negotiations', views.OfferNegotiationLogViewSet, basename='offernegotiation'
)

urlpatterns = [
    # Internal API endpoints
    path('', include(router.urls)),
    # Candidate-facing endpoints (token-based)
    path(
        'candidate/<str:offer_id>/<str:token>/',
        views.candidate_view_offer,
        name='candidate-view-offer',
    ),
    path(
        'candidate/<str:offer_id>/<str:token>/accept/',
        views.candidate_accept_offer,
        name='candidate-accept-offer',
    ),
    path(
        'candidate/<str:offer_id>/<str:token>/decline/',
        views.candidate_decline_offer,
        name='candidate-decline-offer',
    ),
]

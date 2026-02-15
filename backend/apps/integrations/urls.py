"""URL configuration for integrations app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    IntegrationViewSet,
    JobBoardPostingViewSet,
    WebhookEndpointViewSet,
    WebhookReceiverView,
)

# Create router for viewsets
router = DefaultRouter()
router.register(r'integrations', IntegrationViewSet, basename='integration')
router.register(r'webhooks', WebhookEndpointViewSet, basename='webhook')
router.register(r'job-postings', JobBoardPostingViewSet, basename='jobposting')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    # Webhook receiver endpoint
    path(
        'receive/<uuid:integration_id>/',
        WebhookReceiverView.as_view(),
        name='webhook-receive',
    ),
]

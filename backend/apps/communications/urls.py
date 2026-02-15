"""URL patterns for communications app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BulkEmailView,
    EmailLogViewSet,
    EmailTemplateViewSet,
    MessageThreadViewSet,
    NotificationViewSet,
    SendEmailToApplicationView,
)

# Router for viewsets
router = DefaultRouter()
router.register('email-templates', EmailTemplateViewSet, basename='email-template')
router.register('email-logs', EmailLogViewSet, basename='email-log')
router.register('notifications', NotificationViewSet, basename='notification')
router.register('threads', MessageThreadViewSet, basename='message-thread')

urlpatterns = [
    # Send email to application candidate
    path(
        'internal/applications/<uuid:application_id>/send-email/',
        SendEmailToApplicationView.as_view(),
        name='send-email-to-application',
    ),
    # Bulk email
    path(
        'internal/bulk-email/',
        BulkEmailView.as_view(),
        name='bulk-email',
    ),
    # All viewset routes
    path('', include(router.urls)),
]

"""URL patterns for communications app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    EmailLogViewSet,
    EmailTemplateViewSet,
    NotificationViewSet,
    SendEmailToApplicationView,
)

# Router for viewsets
router = DefaultRouter()
router.register('email-templates', EmailTemplateViewSet, basename='email-template')
router.register('email-logs', EmailLogViewSet, basename='email-log')
router.register('notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    # Send email to application candidate
    path(
        'internal/applications/<uuid:application_id>/send-email/',
        SendEmailToApplicationView.as_view(),
        name='send-email-to-application',
    ),
    # All viewset routes
    path('', include(router.urls)),
]

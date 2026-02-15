"""Onboarding URL configuration."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    OnboardingDocumentViewSet,
    OnboardingPlanViewSet,
    OnboardingPortalDocumentUploadView,
    OnboardingPortalFormSubmitView,
    OnboardingPortalTaskCompleteView,
    OnboardingPortalTasksView,
    OnboardingPortalView,
    OnboardingTaskViewSet,
    OnboardingTemplateViewSet,
)

# Candidate portal URLs (token-based, no auth required)
candidate_urlpatterns = [
    # Portal overview
    path(
        '<str:token>/',
        OnboardingPortalView.as_view(),
        name='onboarding-portal',
    ),
    # Tasks
    path(
        '<str:token>/tasks/',
        OnboardingPortalTasksView.as_view(),
        name='onboarding-portal-tasks',
    ),
    path(
        '<str:token>/tasks/<uuid:task_id>/complete/',
        OnboardingPortalTaskCompleteView.as_view(),
        name='onboarding-portal-task-complete',
    ),
    # Documents
    path(
        '<str:token>/documents/',
        OnboardingPortalDocumentUploadView.as_view(),
        name='onboarding-portal-document-upload',
    ),
    # Forms
    path(
        '<str:token>/forms/',
        OnboardingPortalFormSubmitView.as_view(),
        name='onboarding-portal-form-submit',
    ),
]

# Internal management URLs (authentication required)
router = DefaultRouter()
router.register(r'plans', OnboardingPlanViewSet, basename='onboardingplan')
router.register(r'tasks', OnboardingTaskViewSet, basename='onboardingtask')
router.register(r'documents', OnboardingDocumentViewSet, basename='onboardingdocument')
router.register(r'templates', OnboardingTemplateViewSet, basename='onboardingtemplate')

internal_urlpatterns = [
    path('', include(router.urls)),
]

urlpatterns = [
    # Candidate portal (public, token-based)
    path('portal/', include(candidate_urlpatterns)),
    # Internal management
    path('internal/', include(internal_urlpatterns)),
]

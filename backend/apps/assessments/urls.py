"""URL configuration for assessments app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

# Create router for internal staff endpoints
router = DefaultRouter()
router.register(r'templates', views.AssessmentTemplateViewSet, basename='assessmenttemplate')
router.register(r'assessments', views.AssessmentViewSet, basename='assessment')
router.register(
    r'reference-checks', views.ReferenceCheckRequestViewSet, basename='referencecheck'
)

# URL patterns
urlpatterns = [
    # Internal staff endpoints (authenticated)
    path('assessments/internal/', include(router.urls)),
    # Token-based candidate assessment endpoints (public)
    path(
        'assessments/candidate/<str:token>/',
        views.assessment_by_token,
        name='assessment-by-token',
    ),
    path(
        'assessments/candidate/<str:token>/start/',
        views.start_assessment,
        name='assessment-start',
    ),
    path(
        'assessments/candidate/<str:token>/submit/',
        views.submit_assessment,
        name='assessment-submit',
    ),
    # Token-based reference check endpoints (public)
    path(
        'assessments/reference/<str:token>/',
        views.reference_check_by_token,
        name='reference-by-token',
    ),
    path(
        'assessments/reference/<str:token>/submit/',
        views.submit_reference_check,
        name='reference-submit',
    ),
    path(
        'assessments/reference/<str:token>/decline/',
        views.decline_reference_check,
        name='reference-decline',
    ),
]

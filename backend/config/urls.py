"""HR-Plus URL Configuration."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.core.views import health_check

urlpatterns = [
    # Health check
    path('api/health/', health_check, name='health-check'),

    # API documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Accounts (auth, candidates, internal users)
    path('api/v1/', include('apps.accounts.urls')),

    # Jobs (public listings, internal requisitions)
    path('api/v1/', include('apps.jobs.urls')),

    # Applications (candidate + internal)
    path('api/v1/', include('apps.applications.urls')),

    # Interviews (candidate + internal)
    path('api/v1/', include('apps.interviews.urls')),

    # Communications (email, notifications)
    path('api/v1/', include('apps.communications.urls')),

    # Offers (internal + candidate token-based)
    path('api/v1/', include('apps.offers.urls')),

    # Assessments (internal + candidate/reference token-based)
    path('api/v1/', include('apps.assessments.urls')),

    # Analytics (internal)
    path('api/v1/internal/analytics/', include('apps.analytics.urls')),

    # Compliance (candidate + internal)
    path('api/v1/compliance/', include('apps.compliance.urls')),

    # Onboarding (candidate portal + internal)
    path('api/v1/onboarding/', include('apps.onboarding.urls')),

    # Integrations (internal)
    path('api/v1/integrations/', include('apps.integrations.urls')),

    # Admin
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

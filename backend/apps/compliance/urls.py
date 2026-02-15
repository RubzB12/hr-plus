"""Compliance URL configuration."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AdverseImpactAnalysisView,
    AnonymizationRecordViewSet,
    AuditLogViewSet,
    CandidateAnonymizationView,
    CandidateDataExportView,
    ConsentManagementView,
    ConsentRecordViewSet,
    DataRetentionPolicyViewSet,
    EEODataView,
    EEOReportView,
)

router = DefaultRouter()
router.register(r'audit-logs', AuditLogViewSet, basename='auditlog')
router.register(r'consents', ConsentRecordViewSet, basename='consentrecord')
router.register(
    r'retention-policies', DataRetentionPolicyViewSet, basename='dataretentionpolicy'
)
router.register(
    r'anonymizations', AnonymizationRecordViewSet, basename='anonymizationrecord'
)

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    # Candidate GDPR endpoints
    path('data-export/', CandidateDataExportView.as_view(), name='data-export'),
    path('anonymize/', CandidateAnonymizationView.as_view(), name='anonymize'),
    path('consent/', ConsentManagementView.as_view(), name='consent-management'),
    # EEO endpoints
    path('eeo/', EEODataView.as_view(), name='eeo-data'),
    path('eeo/report/', EEOReportView.as_view(), name='eeo-report'),
    path(
        'eeo/adverse-impact/',
        AdverseImpactAnalysisView.as_view(),
        name='adverse-impact-analysis',
    ),
]

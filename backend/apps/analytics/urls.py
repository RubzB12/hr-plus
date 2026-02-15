"""URL patterns for analytics app."""

from django.urls import path

from .views import (
    ExecutiveDashboardView,
    GenerateReportView,
    InterviewerCalibrationView,
    PipelineAnalyticsView,
    RecruiterDashboardView,
    ScheduleReportView,
    SourceEffectivenessView,
    TimeToFillAnalyticsView,
)

urlpatterns = [
    # Dashboard
    path(
        'dashboard/executive/',
        ExecutiveDashboardView.as_view(),
        name='executive-dashboard',
    ),
    path(
        'dashboard/recruiter/',
        RecruiterDashboardView.as_view(),
        name='recruiter-dashboard',
    ),
    # Analytics endpoints
    path(
        'pipeline/<uuid:requisition_id>/',
        PipelineAnalyticsView.as_view(),
        name='pipeline-analytics',
    ),
    path(
        'time-to-fill/',
        TimeToFillAnalyticsView.as_view(),
        name='time-to-fill',
    ),
    path(
        'source-effectiveness/',
        SourceEffectivenessView.as_view(),
        name='source-effectiveness',
    ),
    path(
        'interviewer-calibration/',
        InterviewerCalibrationView.as_view(),
        name='interviewer-calibration',
    ),
    # Reports
    path(
        'reports/generate/',
        GenerateReportView.as_view(),
        name='generate-report',
    ),
    path(
        'reports/schedule/',
        ScheduleReportView.as_view(),
        name='schedule-report',
    ),
]

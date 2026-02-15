"""API views for analytics app."""

from django.http import HttpResponse
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsInternalUser

from .selectors import DashboardSelector, ExecutiveDashboardSelector, ReportSelector
from .serializers import DateRangeSerializer, GenerateReportSerializer, ScheduleReportSerializer
from .services import ReportScheduleService, ReportService


class ExecutiveDashboardView(generics.GenericAPIView):
    """View for executive dashboard metrics."""

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = DateRangeSerializer

    def get(self, request):
        """Get executive dashboard data."""
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        data = ExecutiveDashboardSelector.get_dashboard_data(
            start_date=serializer.validated_data.get('start_date'),
            end_date=serializer.validated_data.get('end_date'),
            department_id=serializer.validated_data.get('department_id'),
        )

        return Response(data, status=status.HTTP_200_OK)


class RecruiterDashboardView(generics.GenericAPIView):
    """View for recruiter dashboard metrics."""

    permission_classes = [IsAuthenticated, IsInternalUser]

    def get(self, request):
        """Get recruiter dashboard data."""
        data = DashboardSelector.get_recruiter_dashboard(request.user)

        return Response(data, status=status.HTTP_200_OK)


class PipelineAnalyticsView(generics.GenericAPIView):
    """View for pipeline analytics for a specific requisition."""

    permission_classes = [IsAuthenticated, IsInternalUser]

    def get(self, request, requisition_id):
        """Get pipeline analytics for a requisition."""
        from django.shortcuts import get_object_or_404

        from apps.jobs.models import Requisition

        # Verify requisition exists
        get_object_or_404(Requisition, id=requisition_id)

        from .selectors import DashboardSelector

        data = DashboardSelector.get_pipeline_metrics(requisition_id)

        return Response(data, status=status.HTTP_200_OK)


class TimeToFillAnalyticsView(generics.GenericAPIView):
    """View for time-to-fill analytics."""

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = DateRangeSerializer

    def get(self, request):
        """Get time-to-fill analytics."""
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        data = ReportSelector.get_time_to_fill_report(
            start_date=serializer.validated_data.get('start_date'),
            end_date=serializer.validated_data.get('end_date'),
            department_id=serializer.validated_data.get('department_id'),
        )

        return Response(data, status=status.HTTP_200_OK)


class SourceEffectivenessView(generics.GenericAPIView):
    """View for source effectiveness analytics."""

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = DateRangeSerializer

    def get(self, request):
        """Get source effectiveness analytics."""
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        data = ReportSelector.get_source_effectiveness_report(
            start_date=serializer.validated_data.get('start_date'),
            end_date=serializer.validated_data.get('end_date'),
            department_id=serializer.validated_data.get('department_id'),
        )

        return Response(data, status=status.HTTP_200_OK)


class InterviewerCalibrationView(generics.GenericAPIView):
    """View for interviewer calibration analytics."""

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = DateRangeSerializer

    def get(self, request):
        """Get interviewer calibration analytics."""
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        data = ReportSelector.get_interviewer_calibration_report(
            start_date=serializer.validated_data.get('start_date'),
            end_date=serializer.validated_data.get('end_date'),
        )

        return Response(data, status=status.HTTP_200_OK)


class GenerateReportView(generics.GenericAPIView):
    """View for generating custom reports."""

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = GenerateReportSerializer

    def post(self, request):
        """Generate a report."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = ReportService.generate_report(
            report_type=serializer.validated_data['report_type'],
            format=serializer.validated_data.get('format', 'json'),
            start_date=serializer.validated_data.get('start_date'),
            end_date=serializer.validated_data.get('end_date'),
            department_id=serializer.validated_data.get('department_id'),
        )

        # Handle different formats
        report_format = serializer.validated_data.get('format', 'json')

        if report_format == 'json':
            return Response(data, status=status.HTTP_200_OK)
        elif report_format == 'csv':
            response = HttpResponse(data, content_type='text/csv')
            response['Content-Disposition'] = (
                f'attachment; filename="{serializer.validated_data["report_type"]}.csv"'
            )
            return response
        elif report_format == 'excel':
            response = HttpResponse(
                data,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            response['Content-Disposition'] = (
                f'attachment; filename="{serializer.validated_data["report_type"]}.xlsx"'
            )
            return response


class ScheduleReportView(generics.GenericAPIView):
    """View for scheduling recurring reports."""

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = ScheduleReportSerializer

    def post(self, request):
        """Schedule a recurring report."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        schedule = ReportScheduleService.schedule_report(
            report_type=serializer.validated_data['report_type'],
            format=serializer.validated_data['format'],
            frequency=serializer.validated_data['frequency'],
            recipients=serializer.validated_data['recipients'],
            department_id=serializer.validated_data.get('department_id'),
            created_by=request.user,
        )

        return Response(schedule, status=status.HTTP_201_CREATED)

"""Serializers for analytics app."""

from rest_framework import serializers


class DateRangeSerializer(serializers.Serializer):
    """Serializer for date range parameters."""

    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    department_id = serializers.UUIDField(required=False, allow_null=True)


class GenerateReportSerializer(serializers.Serializer):
    """Serializer for report generation requests."""

    report_type = serializers.ChoiceField(
        choices=[
            'pipeline_conversion',
            'time_to_fill',
            'source_effectiveness',
            'offer_analysis',
            'interviewer_calibration',
            'requisition_aging',
        ],
    )
    format = serializers.ChoiceField(
        choices=['json', 'csv', 'excel'],
        default='json',
    )
    start_date = serializers.DateTimeField(required=False, allow_null=True)
    end_date = serializers.DateTimeField(required=False, allow_null=True)
    department_id = serializers.UUIDField(required=False, allow_null=True)


class ScheduleReportSerializer(serializers.Serializer):
    """Serializer for scheduling recurring reports."""

    report_type = serializers.ChoiceField(
        choices=[
            'pipeline_conversion',
            'time_to_fill',
            'source_effectiveness',
            'offer_analysis',
            'interviewer_calibration',
            'requisition_aging',
        ],
    )
    format = serializers.ChoiceField(
        choices=['csv', 'excel'],
        help_text='JSON is not supported for scheduled reports',
    )
    frequency = serializers.ChoiceField(
        choices=['daily', 'weekly', 'monthly'],
    )
    recipients = serializers.ListField(
        child=serializers.EmailField(),
        min_length=1,
        max_length=10,
    )
    department_id = serializers.UUIDField(required=False, allow_null=True)

"""Compliance views."""

from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import CandidateProfile
from apps.core.exceptions import BusinessValidationError
from apps.core.permissions import IsComplianceAdmin, IsInternalUser

from .models import AnonymizationRecord, AuditLog, ConsentRecord, DataRetentionPolicy
from .serializers import (
    AdverseImpactAnalysisRequestSerializer,
    AnonymizationRecordSerializer,
    AnonymizationRequestSerializer,
    AuditLogFilterSerializer,
    AuditLogSerializer,
    ConsentRecordSerializer,
    ConsentSubmitSerializer,
    ConsentWithdrawSerializer,
    DataExportRequestSerializer,
    DataRetentionPolicySerializer,
    EEODataSerializer,
    EEODataSubmitSerializer,
    EEOReportRequestSerializer,
)
from .services import EEOService, GDPRService


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for audit logs (read-only).

    Only compliance admins can view audit logs.
    """

    permission_classes = [IsAuthenticated, IsComplianceAdmin]
    serializer_class = AuditLogSerializer
    filterset_fields = ['action', 'resource_type', 'resource_id']
    search_fields = ['action', 'resource_type', 'resource_id']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    def get_queryset(self):
        queryset = AuditLog.objects.select_related('actor').all()

        # Apply custom filters
        serializer = AuditLogFilterSerializer(data=self.request.query_params)
        if serializer.is_valid():
            filters = serializer.validated_data

            if 'actor_id' in filters:
                queryset = queryset.filter(actor_id=filters['actor_id'])

            if 'action' in filters:
                queryset = queryset.filter(action=filters['action'])

            if 'resource_type' in filters:
                queryset = queryset.filter(resource_type=filters['resource_type'])

            if 'resource_id' in filters:
                queryset = queryset.filter(resource_id=filters['resource_id'])

            if 'start_date' in filters:
                queryset = queryset.filter(timestamp__gte=filters['start_date'])

            if 'end_date' in filters:
                queryset = queryset.filter(timestamp__lte=filters['end_date'])

        return queryset


class ConsentRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for consent records.

    Users can view their own consents.
    Compliance admins can view all consents.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ConsentRecordSerializer
    filterset_fields = ['consent_type', 'withdrawn_at']
    ordering_fields = ['given_at', 'withdrawn_at']
    ordering = ['-given_at']

    def get_queryset(self):
        user = self.request.user

        # Compliance admins can see all
        if user.has_perm('compliance.view_consentrecord'):
            return ConsentRecord.objects.select_related('user').all()

        # Regular users see only their own
        return ConsentRecord.objects.filter(user=user)


class DataRetentionPolicyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for data retention policies.

    Only compliance admins can create/update policies.
    """

    permission_classes = [IsAuthenticated, IsComplianceAdmin]
    serializer_class = DataRetentionPolicySerializer
    queryset = DataRetentionPolicy.objects.all()
    filterset_fields = ['data_type', 'is_active']
    ordering_fields = ['data_type', 'retention_days']
    ordering = ['data_type']


class AnonymizationRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for anonymization records (read-only).

    Only compliance admins can view anonymization records.
    """

    permission_classes = [IsAuthenticated, IsComplianceAdmin]
    serializer_class = AnonymizationRecordSerializer
    queryset = AnonymizationRecord.objects.select_related('anonymized_by').all()
    ordering_fields = ['anonymized_at']
    ordering = ['-anonymized_at']


class CandidateDataExportView(generics.GenericAPIView):
    """
    View for candidates to export their personal data (GDPR Right to Access).

    Candidates can only export their own data.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = DataExportRequestSerializer

    def post(self, request):
        """Export candidate's personal data."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get candidate profile
        try:
            candidate = CandidateProfile.objects.get(user=request.user)
        except CandidateProfile.DoesNotExist:
            return Response(
                {'detail': 'No candidate profile found for your account.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Send via email or return JSON
        if serializer.validated_data.get('email', False):
            GDPRService.send_data_export(candidate)
            return Response(
                {'detail': 'Your data export has been sent to your email address.'},
                status=status.HTTP_200_OK,
            )
        else:
            data = GDPRService.export_candidate_data(candidate)
            return Response(data, status=status.HTTP_200_OK)


class CandidateAnonymizationView(generics.GenericAPIView):
    """
    View for candidates to request anonymization (GDPR Right to Erasure).

    This is IRREVERSIBLE - all PII will be permanently removed.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = AnonymizationRequestSerializer

    def post(self, request):
        """Anonymize candidate's personal data."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get candidate profile
        try:
            candidate = CandidateProfile.objects.get(user=request.user)
        except CandidateProfile.DoesNotExist:
            return Response(
                {'detail': 'No candidate profile found for your account.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Anonymize
        record = GDPRService.anonymize_candidate(
            candidate,
            reason=serializer.validated_data.get('reason'),
            anonymized_by=request.user,
        )

        return Response(
            {
                'detail': 'Your account has been anonymized. All personal information has been removed.',
                'anonymization_id': str(record.id),
                'anonymized_at': record.anonymized_at.isoformat(),
            },
            status=status.HTTP_200_OK,
        )


class ConsentManagementView(generics.GenericAPIView):
    """
    View for managing user consents.

    Users can give or withdraw consent for various data processing purposes.
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ConsentSubmitSerializer
        return ConsentWithdrawSerializer

    def post(self, request):
        """Record user consent."""
        serializer = ConsentSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        consent = GDPRService.record_consent(
            user=request.user,
            consent_type=serializer.validated_data['consent_type'],
            ip_address=serializer.validated_data.get('ip_address'),
            user_agent=serializer.validated_data.get('user_agent', ''),
        )

        return Response(
            ConsentRecordSerializer(consent).data, status=status.HTTP_201_CREATED
        )

    def delete(self, request):
        """Withdraw user consent."""
        serializer = ConsentWithdrawSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            GDPRService.withdraw_consent(
                user=request.user, consent_type=serializer.validated_data['consent_type']
            )
        except BusinessValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {'detail': 'Consent has been withdrawn.'}, status=status.HTTP_200_OK
        )


class EEODataView(generics.GenericAPIView):
    """
    View for candidates to submit EEO self-identification data.

    CRITICAL: This data is ONLY accessible to the candidate who submitted it
    and compliance admins for aggregate reporting.
    It is NEVER shown to hiring team.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = EEODataSubmitSerializer

    def get(self, request):
        """Get candidate's EEO data."""
        try:
            candidate = CandidateProfile.objects.get(user=request.user)
        except CandidateProfile.DoesNotExist:
            return Response(
                {'detail': 'No candidate profile found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not hasattr(candidate, 'eeo_data'):
            return Response(
                {'detail': 'No EEO data has been submitted.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            EEODataSerializer(candidate.eeo_data).data, status=status.HTTP_200_OK
        )

    def post(self, request):
        """Submit or update EEO data."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            candidate = CandidateProfile.objects.get(user=request.user)
        except CandidateProfile.DoesNotExist:
            return Response(
                {'detail': 'No candidate profile found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        eeo_data = EEOService.collect_eeo_data(candidate=candidate, **serializer.validated_data)

        return Response(
            EEODataSerializer(eeo_data).data, status=status.HTTP_201_CREATED
        )


class EEOReportView(generics.GenericAPIView):
    """
    View for generating aggregated EEO reports.

    Only compliance admins can access this.
    Returns ONLY aggregate statistics, never individual data.
    """

    permission_classes = [IsAuthenticated, IsComplianceAdmin]
    serializer_class = EEOReportRequestSerializer

    def post(self, request):
        """Generate EEO report."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        report = EEOService.generate_eeo_report(
            start_date=serializer.validated_data.get('start_date'),
            end_date=serializer.validated_data.get('end_date'),
            department_id=serializer.validated_data.get('department_id'),
        )

        return Response(report, status=status.HTTP_200_OK)


class AdverseImpactAnalysisView(generics.GenericAPIView):
    """
    View for generating adverse impact analysis.

    Only compliance admins can access this.
    Uses the 4/5ths rule to identify potential disparate impact.
    """

    permission_classes = [IsAuthenticated, IsComplianceAdmin]
    serializer_class = AdverseImpactAnalysisRequestSerializer

    def post(self, request):
        """Generate adverse impact analysis."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        analysis = EEOService.adverse_impact_analysis(
            requisition_id=serializer.validated_data.get('requisition_id'),
            start_date=serializer.validated_data.get('start_date'),
            end_date=serializer.validated_data.get('end_date'),
        )

        return Response(analysis, status=status.HTTP_200_OK)

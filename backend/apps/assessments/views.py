"""Views for assessments app."""

from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.core.exceptions import BusinessValidationError

from .models import (
    Assessment,
    AssessmentTemplate,
    ReferenceCheckRequest,
)
from .serializers import (
    AssessmentCreateSerializer,
    AssessmentListSerializer,
    AssessmentScoreSerializer,
    AssessmentSerializer,
    AssessmentSubmitSerializer,
    AssessmentTemplateListSerializer,
    AssessmentTemplateSerializer,
    ReferenceCheckRequestCreateSerializer,
    ReferenceCheckRequestListSerializer,
    ReferenceCheckRequestSerializer,
    ReferenceCheckResponseSubmitSerializer,
)
from .services import AssessmentService, ReferenceCheckService

# ============================================================================
# Internal Staff Views (Authenticated)
# ============================================================================


class AssessmentTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for managing assessment templates (internal staff only)."""

    permission_classes = [IsAuthenticated]
    queryset = AssessmentTemplate.objects.all().order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'list':
            return AssessmentTemplateListSerializer
        return AssessmentTemplateSerializer


class AssessmentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing assessments (internal staff only)."""

    permission_classes = [IsAuthenticated]
    queryset = Assessment.objects.select_related(
        'application__candidate__user',
        'application__requisition',
        'template',
        'assigned_by__user',
        'evaluated_by__user',
    ).order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'list':
            return AssessmentListSerializer
        if self.action == 'create':
            return AssessmentCreateSerializer
        if self.action == 'score':
            return AssessmentScoreSerializer
        return AssessmentSerializer

    def create(self, request, *args, **kwargs):
        """Assign assessment to candidate."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            assessment = AssessmentService.assign_assessment(
                application=serializer.validated_data['application'],
                template=serializer.validated_data['template'],
                assigned_by=request.user.internal_profile,
                due_days=serializer.validated_data.get('due_days', 7),
                due_date=serializer.validated_data.get('due_date'),
            )

            response_serializer = AssessmentSerializer(assessment)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except BusinessValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def score(self, request, pk=None):
        """Score a completed assessment."""
        assessment = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated_assessment = AssessmentService.score_assessment(
                assessment,
                score=serializer.validated_data['score'],
                evaluator=request.user.internal_profile,
                notes=serializer.validated_data.get('notes', ''),
            )

            response_serializer = AssessmentSerializer(updated_assessment)
            return Response(response_serializer.data)

        except BusinessValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def waive(self, request, pk=None):
        """Waive/skip an assessment."""
        assessment = self.get_object()
        reason = request.data.get('reason', '')

        try:
            updated_assessment = AssessmentService.waive_assessment(assessment, reason)
            response_serializer = AssessmentSerializer(updated_assessment)
            return Response(response_serializer.data)

        except BusinessValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ReferenceCheckRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for managing reference check requests (internal staff only)."""

    permission_classes = [IsAuthenticated]
    queryset = ReferenceCheckRequest.objects.select_related(
        'application__candidate__user',
        'application__requisition',
        'requested_by__user',
    ).prefetch_related('response').order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'list':
            return ReferenceCheckRequestListSerializer
        if self.action == 'create':
            return ReferenceCheckRequestCreateSerializer
        return ReferenceCheckRequestSerializer

    def create(self, request, *args, **kwargs):
        """Create a reference check request."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            ref_request = ReferenceCheckService.create_reference_request(
                application=serializer.validated_data['application'],
                reference_name=serializer.validated_data['reference_name'],
                reference_email=serializer.validated_data['reference_email'],
                requested_by=request.user.internal_profile,
                reference_phone=serializer.validated_data.get('reference_phone', ''),
                reference_company=serializer.validated_data.get('reference_company', ''),
                reference_title=serializer.validated_data.get('reference_title', ''),
                relationship=serializer.validated_data.get('relationship', 'manager'),
                questionnaire=serializer.validated_data.get('questionnaire'),
                due_days=serializer.validated_data.get('due_days', 14),
                due_date=serializer.validated_data.get('due_date'),
                notes=serializer.validated_data.get('notes', ''),
            )

            response_serializer = ReferenceCheckRequestSerializer(ref_request)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except BusinessValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """Send reference check request email."""
        ref_request = self.get_object()

        try:
            updated_request = ReferenceCheckService.send_reference_request(ref_request)
            response_serializer = ReferenceCheckRequestSerializer(updated_request)
            return Response(response_serializer.data)

        except BusinessValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# Token-Based Candidate Assessment Views (Public Access)
# ============================================================================


@api_view(['GET'])
@permission_classes([AllowAny])
def assessment_by_token(request, token):
    """
    Retrieve assessment by access token (for candidates).
    Public endpoint - no authentication required.
    """
    assessment = get_object_or_404(Assessment, access_token=token)

    # Return assessment without sensitive data
    data = {
        'id': str(assessment.id),
        'template_name': assessment.template.name,
        'template_type': assessment.template.type,
        'description': assessment.template.description,
        'instructions': assessment.template.instructions,
        'duration': assessment.template.duration,
        'questions': assessment.template.questions,
        'status': assessment.status,
        'due_date': assessment.due_date,
        'started_at': assessment.started_at,
        'completed_at': assessment.completed_at,
        'responses': assessment.responses if assessment.status != 'assigned' else {},
    }

    return Response(data)


@api_view(['POST'])
@permission_classes([AllowAny])
def start_assessment(request, token):
    """
    Start an assessment (for candidates).
    Public endpoint - no authentication required.
    """
    assessment = get_object_or_404(Assessment, access_token=token)

    try:
        updated_assessment = AssessmentService.start_assessment(assessment)
        data = {
            'id': str(updated_assessment.id),
            'status': updated_assessment.status,
            'started_at': updated_assessment.started_at,
        }
        return Response(data)

    except BusinessValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def submit_assessment(request, token):
    """
    Submit assessment responses (for candidates).
    Public endpoint - no authentication required.
    """
    assessment = get_object_or_404(Assessment, access_token=token)

    serializer = AssessmentSubmitSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        updated_assessment = AssessmentService.submit_assessment(
            assessment, serializer.validated_data['responses']
        )

        data = {
            'id': str(updated_assessment.id),
            'status': updated_assessment.status,
            'completed_at': updated_assessment.completed_at,
            'message': 'Assessment submitted successfully',
        }
        return Response(data)

    except BusinessValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# Token-Based Reference Check Views (Public Access)
# ============================================================================


@api_view(['GET'])
@permission_classes([AllowAny])
def reference_check_by_token(request, token):
    """
    Retrieve reference check request by access token.
    Public endpoint - no authentication required.
    """
    ref_request = get_object_or_404(ReferenceCheckRequest, access_token=token)

    # Return request without sensitive internal data
    data = {
        'id': str(ref_request.id),
        'candidate_name': ref_request.application.candidate.user.get_full_name(),
        'position_title': ref_request.application.requisition.title,
        'reference_name': ref_request.reference_name,
        'relationship': ref_request.relationship,
        'questionnaire': ref_request.questionnaire,
        'status': ref_request.status,
        'due_date': ref_request.due_date,
    }

    return Response(data)


@api_view(['POST'])
@permission_classes([AllowAny])
def submit_reference_check(request, token):
    """
    Submit reference check response.
    Public endpoint - no authentication required.
    """
    ref_request = get_object_or_404(ReferenceCheckRequest, access_token=token)

    serializer = ReferenceCheckResponseSubmitSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        # Get reference IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            reference_ip = x_forwarded_for.split(',')[0]
        else:
            reference_ip = request.META.get('REMOTE_ADDR')

        response = ReferenceCheckService.submit_reference_response(
            ref_request,
            responses=serializer.validated_data['responses'],
            overall_recommendation=serializer.validated_data.get(
                'overall_recommendation'
            ),
            would_rehire=serializer.validated_data.get('would_rehire'),
            additional_comments=serializer.validated_data.get(
                'additional_comments', ''
            ),
            reference_ip=reference_ip,
        )

        data = {
            'id': str(response.id),
            'message': 'Reference check submitted successfully. Thank you!',
        }
        return Response(data, status=status.HTTP_201_CREATED)

    except BusinessValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def decline_reference_check(request, token):
    """
    Decline to provide a reference.
    Public endpoint - no authentication required.
    """
    ref_request = get_object_or_404(ReferenceCheckRequest, access_token=token)

    try:
        updated_request = ReferenceCheckService.decline_reference_request(ref_request)

        data = {
            'id': str(updated_request.id),
            'status': updated_request.status,
            'message': 'Your response has been recorded. Thank you.',
        }
        return Response(data)

    except BusinessValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

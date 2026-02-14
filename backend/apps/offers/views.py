"""Views for offers app."""

from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.core.exceptions import BusinessValidationError

from .models import Offer, OfferApproval, OfferNegotiationLog
from .serializers import (
    CandidateOfferSerializer,
    OfferApprovalSerializer,
    OfferCreateSerializer,
    OfferNegotiationLogSerializer,
    OfferSerializer,
)
from .services import OfferApprovalService, OfferLetterService, OfferService


class OfferViewSet(viewsets.ModelViewSet):
    """ViewSet for managing offers (internal staff only)."""

    permission_classes = [IsAuthenticated]
    queryset = Offer.objects.select_related(
        'application__candidate__user',
        'application__requisition',
        'level',
        'department',
        'created_by__user',
    ).prefetch_related('approvals__approver__user')
    serializer_class = OfferSerializer
    filterset_fields = ['status', 'application', 'department']
    search_fields = [
        'offer_id',
        'title',
        'application__candidate__user__email',
        'application__candidate__user__first_name',
        'application__candidate__user__last_name',
    ]
    ordering_fields = ['created_at', 'start_date', 'expiration_date']

    def get_serializer_class(self):
        if self.action == 'create':
            return OfferCreateSerializer
        return OfferSerializer

    def create(self, request, *args, **kwargs):
        """Override create to use OfferSerializer for response."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        # Create via service
        offer = OfferService.create_offer(
            application=validated_data['application'],
            title=validated_data['title'],
            level=validated_data['level'],
            department=validated_data['department'],
            base_salary=validated_data['base_salary_input'],
            start_date=validated_data['start_date'],
            expiration_date=validated_data['expiration_date'],
            created_by=request.user.internal_profile,
            salary_currency=validated_data.get('salary_currency', 'USD'),
            salary_frequency=validated_data.get('salary_frequency', 'annual'),
            bonus=validated_data.get('bonus_input'),
            equity=validated_data.get('equity', ''),
            sign_on_bonus=validated_data.get('sign_on_bonus_input'),
            relocation=validated_data.get('relocation_input'),
            reporting_to=validated_data.get('reporting_to'),
            notes=validated_data.get('notes', ''),
        )

        # Use OfferSerializer for response
        response_serializer = OfferSerializer(offer)
        headers = self.get_success_headers(response_serializer.data)
        return Response(
            response_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @action(detail=True, methods=['post'])
    def submit_for_approval(self, request, pk=None):
        """Submit offer for approval."""
        offer = self.get_object()
        approver_ids = request.data.get('approvers', [])

        if not approver_ids:
            raise BusinessValidationError('At least one approver is required')

        from uuid import UUID

        from apps.accounts.models import InternalUser

        # Normalize IDs - handle both UUID objects/strings and integers (SQLite tests)
        normalized_ids = []
        for aid in approver_ids:
            if isinstance(aid, UUID | int):
                normalized_ids.append(aid)
            else:
                # Try to parse as UUID, fall back to treating as integer
                try:
                    normalized_ids.append(UUID(aid))
                except (ValueError, AttributeError):
                    try:
                        normalized_ids.append(int(aid))
                    except (ValueError, TypeError):
                        normalized_ids.append(aid)

        approvers = InternalUser.objects.filter(id__in=normalized_ids)

        if len(approvers) != len(approver_ids):
            raise BusinessValidationError('One or more approvers not found')

        updated_offer = OfferService.submit_for_approval(offer, list(approvers))

        return Response(OfferSerializer(updated_offer).data)

    @action(detail=True, methods=['post'])
    def send_to_candidate(self, request, pk=None):
        """Send approved offer to candidate."""
        offer = self.get_object()
        updated_offer = OfferService.send_to_candidate(offer)

        return Response(OfferSerializer(updated_offer).data)

    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        """Withdraw offer."""
        offer = self.get_object()
        updated_offer = OfferService.withdraw(offer)

        return Response(OfferSerializer(updated_offer).data)

    @action(detail=True, methods=['post'])
    def create_revision(self, request, pk=None):
        """Create new version of offer (for negotiations)."""
        offer = self.get_object()
        # Make mutable copy - use .dict() to avoid list conversion
        updated_fields = request.data.dict() if hasattr(request.data, 'dict') else dict(request.data)

        # Convert salary inputs if provided
        if 'base_salary_input' in updated_fields:
            updated_fields['base_salary'] = updated_fields.pop('base_salary_input')
        if 'bonus_input' in updated_fields:
            updated_fields['bonus'] = updated_fields.pop('bonus_input')
        if 'sign_on_bonus_input' in updated_fields:
            updated_fields['sign_on_bonus'] = updated_fields.pop('sign_on_bonus_input')
        if 'relocation_input' in updated_fields:
            updated_fields['relocation'] = updated_fields.pop('relocation_input')

        new_offer = OfferService.create_revision(offer, **updated_fields)

        return Response(
            OfferSerializer(new_offer).data, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get'])
    def generate_letter(self, request, pk=None):
        """Generate offer letter PDF."""
        offer = self.get_object()
        pdf_bytes = OfferLetterService.generate_offer_letter(offer)

        from django.http import HttpResponse

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="offer_{offer.offer_id}.pdf"'
        )
        return response


class OfferApprovalViewSet(viewsets.ModelViewSet):
    """ViewSet for offer approvals."""

    permission_classes = [IsAuthenticated]
    queryset = OfferApproval.objects.select_related(
        'offer', 'approver__user'
    ).prefetch_related('offer__approvals')
    serializer_class = OfferApprovalSerializer
    filterset_fields = ['offer', 'approver', 'status']
    ordering_fields = ['order', 'decided_at', 'created_at']

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve this approval step."""
        approval = self.get_object()
        comments = request.data.get('comments', '')

        updated_approval = OfferApprovalService.approve(approval, comments)

        return Response(OfferApprovalSerializer(updated_approval).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject this approval step."""
        approval = self.get_object()
        comments = request.data.get('comments', '')

        if not comments:
            raise BusinessValidationError('Comments required for rejection')

        updated_approval = OfferApprovalService.reject(approval, comments)

        return Response(OfferApprovalSerializer(updated_approval).data)


class OfferNegotiationLogViewSet(viewsets.ModelViewSet):
    """ViewSet for offer negotiation logs."""

    permission_classes = [IsAuthenticated]
    queryset = OfferNegotiationLog.objects.select_related('offer', 'logged_by__user')
    serializer_class = OfferNegotiationLogSerializer
    filterset_fields = ['offer', 'outcome']
    ordering_fields = ['created_at']


# Candidate-facing views (token-based authentication)


@api_view(['GET'])
@permission_classes([AllowAny])
def candidate_view_offer(request, offer_id: str, token: str):
    """
    Candidate views their offer via secure token link.
    Token is generated and sent via email.
    """
    # TODO: Implement token verification
    # For now, simple lookup by offer_id
    try:
        offer = Offer.objects.select_related('level').get(
            offer_id=offer_id, status__in=['sent', 'viewed']
        )
    except Offer.DoesNotExist:
        return Response(
            {'error': 'Offer not found or no longer available'},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Mark as viewed if first time
    if offer.status == 'sent':
        from django.utils import timezone

        offer.status = 'viewed'
        offer.viewed_at = timezone.now()
        offer.save(update_fields=['status', 'viewed_at', 'updated_at'])

    return Response(CandidateOfferSerializer(offer).data)


@api_view(['POST'])
@permission_classes([AllowAny])
def candidate_accept_offer(request, offer_id: str, token: str):
    """Candidate accepts offer."""
    # TODO: Implement token verification
    try:
        offer = Offer.objects.get(offer_id=offer_id)
    except Offer.DoesNotExist:
        return Response(
            {'error': 'Offer not found'}, status=status.HTTP_404_NOT_FOUND
        )

    try:
        updated_offer = OfferService.candidate_accept(offer)
        return Response(CandidateOfferSerializer(updated_offer).data)
    except BusinessValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def candidate_decline_offer(request, offer_id: str, token: str):
    """Candidate declines offer."""
    # TODO: Implement token verification
    try:
        offer = Offer.objects.get(offer_id=offer_id)
    except Offer.DoesNotExist:
        return Response(
            {'error': 'Offer not found'}, status=status.HTTP_404_NOT_FOUND
        )

    reason = request.data.get('reason', '')

    try:
        updated_offer = OfferService.candidate_decline(offer, reason)
        return Response(CandidateOfferSerializer(updated_offer).data)
    except BusinessValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

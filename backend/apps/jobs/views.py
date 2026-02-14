"""API views for jobs app."""

from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import InternalUser
from apps.accounts.permissions import IsInternalUser

from .filters import PublicJobFilter, RequisitionFilter
from .models import Requisition, RequisitionApproval
from .selectors import JobSelector
from .serializers import (
    ApprovalActionSerializer,
    JobCategorySerializer,
    PendingApprovalSerializer,
    PublicJobDetailSerializer,
    PublicJobListSerializer,
    RequisitionCreateSerializer,
    RequisitionDetailSerializer,
    RequisitionListSerializer,
    SubmitForApprovalSerializer,
)
from .services import RequisitionService

# --- Public views (career site) ---

class PublicJobListView(generics.ListAPIView):
    """Public job listing with filtering and search."""

    permission_classes = [AllowAny]
    serializer_class = PublicJobListSerializer
    filterset_class = PublicJobFilter
    search_fields = ['title', 'description']
    ordering_fields = ['published_at', 'title']

    def get_queryset(self):
        return (
            Requisition.objects
            .filter(status='open', published_at__isnull=False)
            .select_related('department', 'location', 'level')
            .order_by('-published_at')
        )


class PublicJobDetailView(generics.RetrieveAPIView):
    """Public job detail by slug."""

    permission_classes = [AllowAny]
    serializer_class = PublicJobDetailSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        return (
            Requisition.objects
            .filter(status='open', published_at__isnull=False)
            .select_related('department', 'location', 'level', 'team')
        )


class PublicJobCategoryView(generics.ListAPIView):
    """Departments with open job counts."""

    permission_classes = [AllowAny]
    serializer_class = JobCategorySerializer
    pagination_class = None

    def get_queryset(self):
        return JobSelector.get_categories()


class PublicSimilarJobsView(generics.ListAPIView):
    """Similar jobs for a given job."""

    permission_classes = [AllowAny]
    serializer_class = PublicJobListSerializer
    pagination_class = None

    def get_queryset(self):
        slug = self.kwargs['slug']
        job = JobSelector.get_job_by_slug(slug)
        if not job:
            return Requisition.objects.none()
        return JobSelector.get_similar_jobs(job)


class PublicLocationListView(generics.ListAPIView):
    """Public list of office locations."""

    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        from apps.accounts.models import Location
        return Location.objects.filter(is_active=True)

    def get_serializer_class(self):
        from apps.accounts.serializers import LocationSerializer
        return LocationSerializer


# --- Internal views (dashboard) ---

class RequisitionViewSet(viewsets.ModelViewSet):
    """Full CRUD for requisitions (internal users only)."""

    permission_classes = [IsAuthenticated, IsInternalUser]
    filterset_class = RequisitionFilter
    search_fields = ['title', 'requisition_id', 'description']
    ordering_fields = ['created_at', 'opened_at', 'target_fill_date']

    def get_queryset(self):
        return (
            Requisition.objects
            .select_related(
                'department', 'team', 'location', 'level',
                'hiring_manager__user', 'recruiter__user',
                'created_by__user',
            )
            .prefetch_related('stages', 'approvals__approver__user')
            .order_by('-created_at')
        )

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RequisitionCreateSerializer
        if self.action == 'retrieve':
            return RequisitionDetailSerializer
        return RequisitionListSerializer

    def perform_create(self, serializer):
        internal_user = self.request.user.internal_profile
        RequisitionService.create_requisition(
            data=serializer.validated_data,
            created_by=internal_user,
        )

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit for approval with a list of approver IDs."""
        requisition = self.get_object()
        serializer = SubmitForApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approver_ids = serializer.validated_data['approver_ids']
        approvers_qs = InternalUser.objects.filter(id__in=approver_ids)
        approvers_by_id = {a.id: a for a in approvers_qs}
        approvers = [approvers_by_id[uid] for uid in approver_ids if uid in approvers_by_id]

        RequisitionService.submit_for_approval(requisition, approvers)
        requisition.refresh_from_db()
        return Response(
            RequisitionDetailSerializer(requisition).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='approve')
    def approve_action(self, request, pk=None):
        """Approve this requisition."""
        requisition = self.get_object()
        serializer = ApprovalActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approver = request.user.internal_profile
        RequisitionService.approve(
            requisition,
            approver=approver,
            comments=serializer.validated_data.get('comments', ''),
        )
        requisition.refresh_from_db()
        return Response(
            RequisitionDetailSerializer(requisition).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='reject')
    def reject_action(self, request, pk=None):
        """Reject this requisition."""
        requisition = self.get_object()
        serializer = ApprovalActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approver = request.user.internal_profile
        RequisitionService.reject_approval(
            requisition,
            approver=approver,
            comments=serializer.validated_data.get('comments', ''),
        )
        requisition.refresh_from_db()
        return Response(
            RequisitionDetailSerializer(requisition).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        requisition = self.get_object()
        RequisitionService.publish(requisition)
        return Response(
            RequisitionDetailSerializer(requisition).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'])
    def hold(self, request, pk=None):
        requisition = self.get_object()
        RequisitionService.put_on_hold(requisition)
        return Response(
            RequisitionDetailSerializer(requisition).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        requisition = self.get_object()
        RequisitionService.cancel(requisition)
        return Response(
            RequisitionDetailSerializer(requisition).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        requisition = self.get_object()
        RequisitionService.reopen(requisition)
        return Response(
            RequisitionDetailSerializer(requisition).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        """Clone this requisition as a new draft."""
        requisition = self.get_object()
        internal_user = request.user.internal_profile
        new_req = RequisitionService.clone(requisition, created_by=internal_user)
        return Response(
            RequisitionDetailSerializer(new_req).data,
            status=status.HTTP_201_CREATED,
        )


class PendingApprovalsView(generics.ListAPIView):
    """List pending approvals for the current user."""

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = PendingApprovalSerializer
    pagination_class = None

    def get_queryset(self):
        return (
            RequisitionApproval.objects
            .filter(
                approver=self.request.user.internal_profile,
                status='pending',
            )
            .select_related(
                'requisition__department',
                'requisition__location',
                'requisition__hiring_manager__user',
                'requisition__recruiter__user',
            )
            .order_by('created_at')
        )

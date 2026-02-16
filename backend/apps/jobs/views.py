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


class PublicJobFacetsView(generics.GenericAPIView):
    """
    Return aggregated facet counts for all filter dimensions.
    This powers the advanced search UI with real-time filter counts.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        from django.db.models import Count, Q

        # Base queryset - only published, open jobs
        base_qs = Requisition.objects.filter(status='open', published_at__isnull=False)

        # Apply current filters if any (to show counts for remaining options)
        search = request.query_params.get('search', '').strip()
        department = request.query_params.get('department', '').strip()
        location = request.query_params.get('location', '').strip()
        employment_type = request.query_params.get('employment_type', '').strip()
        remote_policy = request.query_params.get('remote_policy', '').strip()
        level = request.query_params.get('level', '').strip()

        if search:
            base_qs = base_qs.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        # For each facet, calculate counts with and without that specific filter applied
        # This gives users accurate counts showing "what if I apply this filter?"

        # Department facets
        dept_qs = base_qs
        if location:
            dept_qs = dept_qs.filter(location__name=location)
        if employment_type:
            dept_qs = dept_qs.filter(employment_type=employment_type)
        if remote_policy:
            dept_qs = dept_qs.filter(remote_policy=remote_policy)
        if level:
            dept_qs = dept_qs.filter(level__name=level)

        departments = (
            dept_qs
            .values('department__id', 'department__name')
            .annotate(count=Count('id'))
            .order_by('department__name')
        )

        # Location facets
        loc_qs = base_qs
        if department:
            loc_qs = loc_qs.filter(department__name=department)
        if employment_type:
            loc_qs = loc_qs.filter(employment_type=employment_type)
        if remote_policy:
            loc_qs = loc_qs.filter(remote_policy=remote_policy)
        if level:
            loc_qs = loc_qs.filter(level__name=level)

        locations = (
            loc_qs
            .values('location__id', 'location__name')
            .annotate(count=Count('id'))
            .order_by('location__name')
        )

        # Employment type facets
        type_qs = base_qs
        if department:
            type_qs = type_qs.filter(department__name=department)
        if location:
            type_qs = type_qs.filter(location__name=location)
        if remote_policy:
            type_qs = type_qs.filter(remote_policy=remote_policy)
        if level:
            type_qs = type_qs.filter(level__name=level)

        employment_types = (
            type_qs
            .values('employment_type')
            .annotate(count=Count('id'))
            .order_by('employment_type')
        )

        # Remote policy facets
        remote_qs = base_qs
        if department:
            remote_qs = remote_qs.filter(department__name=department)
        if location:
            remote_qs = remote_qs.filter(location__name=location)
        if employment_type:
            remote_qs = remote_qs.filter(employment_type=employment_type)
        if level:
            remote_qs = remote_qs.filter(level__name=level)

        remote_policies = (
            remote_qs
            .values('remote_policy')
            .annotate(count=Count('id'))
            .order_by('remote_policy')
        )

        # Level facets
        level_qs = base_qs
        if department:
            level_qs = level_qs.filter(department__name=department)
        if location:
            level_qs = level_qs.filter(location__name=location)
        if employment_type:
            level_qs = level_qs.filter(employment_type=employment_type)
        if remote_policy:
            level_qs = level_qs.filter(remote_policy=remote_policy)

        levels = (
            level_qs
            .values('level__id', 'level__name')
            .annotate(count=Count('id'))
            .order_by('level__level_number')
        )

        return Response({
            'departments': [
                {'id': str(d['department__id']), 'name': d['department__name'], 'count': d['count']}
                for d in departments if d['department__name']
            ],
            'locations': [
                {'id': str(l['location__id']), 'name': l['location__name'], 'count': l['count']}
                for l in locations if l['location__name']
            ],
            'employment_types': [
                {'value': et['employment_type'], 'count': et['count']}
                for et in employment_types
            ],
            'remote_policies': [
                {'value': rp['remote_policy'], 'count': rp['count']}
                for rp in remote_policies
            ],
            'levels': [
                {'id': str(lv['level__id']), 'name': lv['level__name'], 'count': lv['count']}
                for lv in levels if lv['level__name']
            ],
        })


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

"""API views for applications app."""

from django.db import models as db_models
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import CandidateProfile
from apps.accounts.permissions import IsCandidate, IsInternalUser
from apps.jobs.models import PipelineStage, Requisition

from .filters import ApplicationFilter
from .models import Application, TalentPool
from .selectors import ApplicationSelector
from .serializers import (
    AddTagSerializer,
    ApplicationCreateSerializer,
    BulkActionSerializer,
    BulkRejectSerializer,
    CandidateApplicationDetailSerializer,
    CandidateApplicationListSerializer,
    CandidateNoteCreateSerializer,
    CandidateNoteSerializer,
    InternalApplicationDetailSerializer,
    InternalApplicationListSerializer,
    MoveToStageSerializer,
    PipelineStageSerializer,
    TalentPoolAddCandidatesSerializer,
    TalentPoolCreateSerializer,
    TalentPoolDetailSerializer,
    TalentPoolRemoveCandidatesSerializer,
    TalentPoolSerializer,
    TalentPoolUpdateSerializer,
)
from .services import ApplicationService, TalentPoolService

# --- Candidate-facing views ---

class CandidateApplicationListView(generics.ListAPIView):
    """List a candidate's own applications."""

    permission_classes = [IsAuthenticated, IsCandidate]
    serializer_class = CandidateApplicationListSerializer

    def get_queryset(self):
        return (
            Application.objects
            .filter(candidate__user=self.request.user)
            .select_related(
                'requisition__department',
                'current_stage',
            )
            .order_by('-applied_at')
        )


class CandidateApplicationDetailView(generics.RetrieveAPIView):
    """Application detail with event timeline for the candidate."""

    permission_classes = [IsAuthenticated, IsCandidate]
    serializer_class = CandidateApplicationDetailSerializer

    def get_queryset(self):
        return (
            Application.objects
            .filter(candidate__user=self.request.user)
            .select_related(
                'requisition__department',
                'requisition__location',
                'current_stage',
            )
            .prefetch_related(
                'events__actor',
                'events__from_stage',
                'events__to_stage',
            )
        )


class CandidateApplicationCreateView(generics.CreateAPIView):
    """Submit a new application."""

    permission_classes = [IsAuthenticated, IsCandidate]
    serializer_class = ApplicationCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        candidate = CandidateProfile.objects.get(user=request.user)
        requisition = Requisition.objects.get(
            id=serializer.validated_data['requisition_id'],
        )

        application = ApplicationService.create_application(
            candidate=candidate,
            requisition=requisition,
            cover_letter=serializer.validated_data.get('cover_letter', ''),
            screening_responses=serializer.validated_data.get(
                'screening_responses', {},
            ),
            source=serializer.validated_data.get('source', 'career_site'),
        )

        return Response(
            CandidateApplicationDetailSerializer(application).data,
            status=status.HTTP_201_CREATED,
        )


class CandidateApplicationWithdrawView(generics.GenericAPIView):
    """Withdraw an application."""

    permission_classes = [IsAuthenticated, IsCandidate]

    def post(self, request, pk):
        from django.shortcuts import get_object_or_404

        application = get_object_or_404(
            Application, id=pk, candidate__user=request.user,
        )
        ApplicationService.withdraw(application, actor=request.user)
        return Response(
            CandidateApplicationDetailSerializer(application).data,
            status=status.HTTP_200_OK,
        )


# --- Internal views ---

class InternalApplicationViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only access to all applications for internal users."""

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = InternalApplicationListSerializer
    filterset_class = ApplicationFilter
    search_fields = [
        'candidate__user__email',
        'candidate__user__first_name',
        'candidate__user__last_name',
        'application_id',
    ]
    ordering_fields = ['applied_at', 'updated_at', 'status']

    def get_queryset(self):
        return (
            Application.objects
            .select_related(
                'candidate__user',
                'requisition',
                'current_stage',
            )
            .order_by('-applied_at')
        )

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        application = self.get_object()
        reason = request.data.get('reason', '')
        ApplicationService.reject(
            application, reason=reason, actor=request.user,
        )
        return Response(
            InternalApplicationListSerializer(application).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'])
    def star(self, request, pk=None):
        application = self.get_object()
        application.is_starred = not application.is_starred
        application.save(update_fields=['is_starred', 'updated_at'])
        return Response(
            InternalApplicationListSerializer(application).data,
            status=status.HTTP_200_OK,
        )

    def retrieve(self, request, *args, **kwargs):
        application = ApplicationSelector.get_application_detail(
            self.kwargs['pk'],
        )
        return Response(
            InternalApplicationDetailSerializer(application).data,
        )

    @action(detail=True, methods=['post'], url_path='move-stage')
    def move_stage(self, request, pk=None):
        """Move an application to a different pipeline stage."""
        application = self.get_object()
        serializer = MoveToStageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        stage = PipelineStage.objects.get(
            id=serializer.validated_data['stage_id'],
        )
        ApplicationService.move_to_stage(
            application, stage, actor=request.user,
        )
        return Response(
            InternalApplicationListSerializer(application).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post', 'get'])
    def notes(self, request, pk=None):
        """Add or list notes for an application."""
        application = self.get_object()

        if request.method == 'GET':
            notes_qs = application.notes.select_related('author__user')
            internal_user = request.user.internal_profile
            notes_qs = notes_qs.filter(
                db_models.Q(is_private=False)
                | db_models.Q(author=internal_user),
            )
            return Response(
                CandidateNoteSerializer(notes_qs, many=True).data,
            )

        serializer = CandidateNoteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note = ApplicationService.add_note(
            application,
            author=request.user.internal_profile,
            body=serializer.validated_data['body'],
            is_private=serializer.validated_data.get('is_private', False),
        )
        return Response(
            CandidateNoteSerializer(note).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'], url_path='add-tag')
    def add_tag(self, request, pk=None):
        application = self.get_object()
        serializer = AddTagSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ApplicationService.add_tag(
            application,
            tag_name=serializer.validated_data['tag_name'],
            actor=request.user,
        )
        return Response(
            InternalApplicationListSerializer(application).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='remove-tag')
    def remove_tag(self, request, pk=None):
        application = self.get_object()
        serializer = AddTagSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ApplicationService.remove_tag(
            application,
            tag_name=serializer.validated_data['tag_name'],
        )
        return Response(
            InternalApplicationListSerializer(application).data,
            status=status.HTTP_200_OK,
        )


class PipelineBoardView(generics.GenericAPIView):
    """Pipeline board for a requisition (Kanban view)."""

    permission_classes = [IsAuthenticated, IsInternalUser]

    def get(self, request, requisition_id):
        stages = ApplicationSelector.get_pipeline_board(requisition_id)
        return Response(
            PipelineStageSerializer(stages, many=True).data,
        )


class BulkMoveStageView(generics.GenericAPIView):
    """Bulk move applications to a stage."""

    permission_classes = [IsAuthenticated, IsInternalUser]

    def post(self, request):
        serializer = BulkActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        stage_id = request.data.get('stage_id')
        stage = PipelineStage.objects.get(id=stage_id)

        count = ApplicationService.bulk_move_to_stage(
            serializer.validated_data['application_ids'],
            stage,
            actor=request.user,
        )
        return Response({'moved': count}, status=status.HTTP_200_OK)


class BulkRejectView(generics.GenericAPIView):
    """Bulk reject applications."""

    permission_classes = [IsAuthenticated, IsInternalUser]

    def post(self, request):
        serializer = BulkRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        count = ApplicationService.bulk_reject(
            serializer.validated_data['application_ids'],
            reason=serializer.validated_data.get('reason', ''),
            actor=request.user,
        )
        return Response({'rejected': count}, status=status.HTTP_200_OK)


class TalentPoolViewSet(viewsets.ModelViewSet):
    """Manage talent pools for proactive recruiting."""

    permission_classes = [IsAuthenticated, IsInternalUser]
    queryset = TalentPool.objects.all().select_related('owner__user')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TalentPoolDetailSerializer
        if self.action == 'create':
            return TalentPoolCreateSerializer
        if self.action in ['update', 'partial_update']:
            return TalentPoolUpdateSerializer
        if self.action == 'add_candidates':
            return TalentPoolAddCandidatesSerializer
        if self.action == 'remove_candidates':
            return TalentPoolRemoveCandidatesSerializer
        return TalentPoolSerializer

    def perform_create(self, serializer):
        pool = TalentPoolService.create_pool(
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description', ''),
            owner=self.request.user.internal_profile,
            is_dynamic=serializer.validated_data.get('is_dynamic', False),
            search_criteria=serializer.validated_data.get('search_criteria', {}),
        )
        return pool

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pool = self.perform_create(serializer)
        return Response(
            TalentPoolSerializer(pool).data,
            status=status.HTTP_201_CREATED,
        )

    def perform_update(self, serializer):
        pool = self.get_object()
        return TalentPoolService.update_pool_details(
            pool,
            name=serializer.validated_data.get('name'),
            description=serializer.validated_data.get('description'),
            is_dynamic=serializer.validated_data.get('is_dynamic'),
            search_criteria=serializer.validated_data.get('search_criteria'),
        )

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        pool = self.perform_update(serializer)
        return Response(TalentPoolSerializer(pool).data)

    @action(detail=True, methods=['post'])
    def add_candidates(self, request, pk=None):
        """Add candidates to the talent pool."""
        pool = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        count = TalentPoolService.add_candidates(
            pool,
            serializer.validated_data['candidate_ids'],
        )
        return Response(
            {'added': count},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'])
    def remove_candidates(self, request, pk=None):
        """Remove candidates from the talent pool."""
        pool = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        count = TalentPoolService.remove_candidates(
            pool,
            serializer.validated_data['candidate_ids'],
        )
        return Response(
            {'removed': count},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'])
    def refresh(self, request, pk=None):
        """Refresh a dynamic talent pool based on search criteria."""
        pool = self.get_object()
        count = TalentPoolService.update_dynamic_pool(pool)
        return Response(
            {'candidate_count': count},
            status=status.HTTP_200_OK,
        )

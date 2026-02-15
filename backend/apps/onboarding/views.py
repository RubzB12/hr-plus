"""Onboarding views."""

from django.utils import timezone
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.core.permissions import IsInternalUser

from .models import (
    OnboardingDocument,
    OnboardingForm,
    OnboardingPlan,
    OnboardingTask,
    OnboardingTemplate,
)
from .serializers import (
    AssignBuddySerializer,
    DocumentUploadSerializer,
    FormSubmitSerializer,
    OnboardingDocumentSerializer,
    OnboardingFormSerializer,
    OnboardingPlanDetailSerializer,
    OnboardingPlanSerializer,
    OnboardingTaskSerializer,
    OnboardingTemplateSerializer,
    TaskCompleteSerializer,
    UpdateStartDateSerializer,
)
from .services import OnboardingService


# Candidate Portal Views (Token-based, no authentication required)


class OnboardingPortalView(generics.RetrieveAPIView):
    """
    Candidate onboarding portal (token-based access).

    GET /api/v1/onboarding/{token}/ - Get full onboarding plan with tasks, documents, forms
    """

    permission_classes = [AllowAny]
    serializer_class = OnboardingPlanDetailSerializer
    lookup_field = 'access_token'
    lookup_url_kwarg = 'token'
    queryset = OnboardingPlan.objects.select_related(
        'application__candidate__user',
        'application__requisition',
        'offer',
        'template',
        'buddy__user',
        'hr_contact__user',
    ).prefetch_related('tasks', 'documents', 'forms')


class OnboardingPortalTasksView(generics.ListAPIView):
    """
    Get tasks for onboarding plan (token-based).

    GET /api/v1/onboarding/{token}/tasks/
    """

    permission_classes = [AllowAny]
    serializer_class = OnboardingTaskSerializer

    def get_queryset(self):
        token = self.kwargs['token']
        plan = OnboardingService.get_plan_by_token(token)
        return plan.tasks.all()


class OnboardingPortalTaskCompleteView(generics.GenericAPIView):
    """
    Mark task as complete (token-based).

    POST /api/v1/onboarding/{token}/tasks/{task_id}/complete/
    """

    permission_classes = [AllowAny]
    serializer_class = TaskCompleteSerializer

    def post(self, request, token, task_id):
        plan = OnboardingService.get_plan_by_token(token)

        # Get task
        try:
            task = plan.tasks.get(id=task_id)
        except OnboardingTask.DoesNotExist:
            return Response(
                {'detail': 'Task not found'}, status=status.HTTP_404_NOT_FOUND
            )

        # Verify task is assigned to candidate (None means it's for the candidate themselves)
        if task.assigned_to is not None and task.assigned_to != plan.application.candidate.user:
            return Response(
                {'detail': 'You are not assigned to this task'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Complete task
        if serializer.validated_data.get('notes'):
            task.notes = serializer.validated_data['notes']
            task.save(update_fields=['notes'])

        task = OnboardingService.complete_task(
            task, completed_by=plan.application.candidate.user
        )

        return Response(
            OnboardingTaskSerializer(task).data, status=status.HTTP_200_OK
        )


class OnboardingPortalDocumentUploadView(generics.GenericAPIView):
    """
    Upload onboarding document (token-based).

    POST /api/v1/onboarding/{token}/documents/
    """

    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser]
    serializer_class = DocumentUploadSerializer

    def post(self, request, token):
        plan = OnboardingService.get_plan_by_token(token)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        document = OnboardingService.upload_document(
            plan,
            document_type=serializer.validated_data['document_type'],
            file=serializer.validated_data['file'],
            uploaded_by=plan.application.candidate.user,
        )

        return Response(
            OnboardingDocumentSerializer(document).data,
            status=status.HTTP_201_CREATED,
        )


class OnboardingPortalFormSubmitView(generics.GenericAPIView):
    """
    Submit onboarding form (token-based).

    POST /api/v1/onboarding/{token}/forms/
    """

    permission_classes = [AllowAny]
    serializer_class = FormSubmitSerializer

    def post(self, request, token):
        plan = OnboardingService.get_plan_by_token(token)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        form = OnboardingService.submit_form(
            plan,
            form_type=serializer.validated_data['form_type'],
            data=serializer.validated_data['data'],
            submitted_by=plan.application.candidate.user,
        )

        return Response(
            OnboardingFormSerializer(form).data, status=status.HTTP_201_CREATED
        )


# Internal Views (Authentication required)


class OnboardingPlanViewSet(viewsets.ModelViewSet):
    """
    Internal onboarding plan management.

    GET /api/v1/internal/onboarding/ - List all onboarding plans
    POST /api/v1/internal/onboarding/ - Create onboarding plan
    GET /api/v1/internal/onboarding/{id}/ - Get plan details
    PUT /api/v1/internal/onboarding/{id}/ - Update plan
    DELETE /api/v1/internal/onboarding/{id}/ - Delete plan
    """

    permission_classes = [IsAuthenticated, IsInternalUser]
    queryset = OnboardingPlan.objects.select_related(
        'application__candidate__user',
        'application__requisition',
        'offer',
        'template',
        'buddy__user',
        'hr_contact__user',
    ).prefetch_related('tasks', 'documents', 'forms')
    filterset_fields = ['status', 'start_date']
    search_fields = [
        'application__candidate__user__first_name',
        'application__candidate__user__last_name',
        'application__candidate__user__email',
    ]
    ordering_fields = ['start_date', 'created_at', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OnboardingPlanDetailSerializer
        return OnboardingPlanSerializer

    @action(detail=True, methods=['post'], url_path='assign-buddy')
    def assign_buddy(self, request, pk=None):
        """Assign buddy to onboarding plan."""
        plan = self.get_object()
        serializer = AssignBuddySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from apps.accounts.models import InternalUser

        try:
            buddy = InternalUser.objects.get(id=serializer.validated_data['buddy_id'])
        except InternalUser.DoesNotExist:
            return Response(
                {'detail': 'Buddy not found'}, status=status.HTTP_404_NOT_FOUND
            )

        plan = OnboardingService.assign_buddy(plan, buddy=buddy)

        return Response(
            OnboardingPlanSerializer(plan).data, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='update-start-date')
    def update_start_date(self, request, pk=None):
        """Update start date and recalculate task due dates."""
        plan = self.get_object()
        serializer = UpdateStartDateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan = OnboardingService.update_start_date(
            plan, new_start_date=serializer.validated_data['start_date']
        )

        return Response(
            OnboardingPlanDetailSerializer(plan).data, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark onboarding plan as completed."""
        plan = self.get_object()
        plan = OnboardingService.complete_plan(plan)

        return Response(
            OnboardingPlanSerializer(plan).data, status=status.HTTP_200_OK
        )


class OnboardingTaskViewSet(viewsets.ModelViewSet):
    """
    Internal onboarding task management.

    GET /api/v1/internal/onboarding/tasks/ - List all tasks
    POST /api/v1/internal/onboarding/tasks/ - Create task
    PUT /api/v1/internal/onboarding/tasks/{id}/ - Update task
    DELETE /api/v1/internal/onboarding/tasks/{id}/ - Delete task
    """

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = OnboardingTaskSerializer
    queryset = OnboardingTask.objects.select_related(
        'plan__application__candidate__user', 'assigned_to', 'completed_by'
    )
    filterset_fields = ['plan', 'status', 'category', 'assigned_to']
    search_fields = ['title', 'description']
    ordering_fields = ['due_date', 'order', 'status']
    ordering = ['order', 'due_date']

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark task as complete."""
        task = self.get_object()
        serializer = TaskCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data.get('notes'):
            task.notes = serializer.validated_data['notes']
            task.save(update_fields=['notes'])

        task = OnboardingService.complete_task(task, completed_by=request.user)

        return Response(
            OnboardingTaskSerializer(task).data, status=status.HTTP_200_OK
        )


class OnboardingDocumentViewSet(viewsets.ModelViewSet):
    """
    Internal onboarding document management.

    GET /api/v1/internal/onboarding/documents/ - List all documents
    PUT /api/v1/internal/onboarding/documents/{id}/ - Update document (review/approve)
    """

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = OnboardingDocumentSerializer
    queryset = OnboardingDocument.objects.select_related(
        'plan__application__candidate__user', 'uploaded_by', 'reviewed_by'
    )
    filterset_fields = ['plan', 'status', 'document_type']
    ordering_fields = ['uploaded_at', 'status']
    ordering = ['-uploaded_at']

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve document."""
        document = self.get_object()
        document.status = 'approved'
        document.reviewed_by = request.user
        document.reviewed_at = timezone.now()
        document.save(
            update_fields=['status', 'reviewed_by', 'reviewed_at', 'updated_at']
        )

        return Response(
            OnboardingDocumentSerializer(document).data, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject document with reason."""
        document = self.get_object()
        reason = request.data.get('reason', '')

        if not reason:
            return Response(
                {'detail': 'Rejection reason is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        document.status = 'rejected'
        document.reviewed_by = request.user
        document.reviewed_at = timezone.now()
        document.rejection_reason = reason
        document.save(
            update_fields=[
                'status',
                'reviewed_by',
                'reviewed_at',
                'rejection_reason',
                'updated_at',
            ]
        )

        return Response(
            OnboardingDocumentSerializer(document).data, status=status.HTTP_200_OK
        )


class OnboardingTemplateViewSet(viewsets.ModelViewSet):
    """
    Internal onboarding template management.

    GET /api/v1/internal/onboarding/templates/ - List all templates
    POST /api/v1/internal/onboarding/templates/ - Create template
    PUT /api/v1/internal/onboarding/templates/{id}/ - Update template
    DELETE /api/v1/internal/onboarding/templates/{id}/ - Delete template
    """

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = OnboardingTemplateSerializer
    queryset = OnboardingTemplate.objects.select_related('department', 'job_level')
    filterset_fields = ['department', 'job_level', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

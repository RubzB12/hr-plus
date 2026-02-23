"""API views for interviews app."""

from rest_framework import generics, status, viewsets
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsCandidate, IsInternalUser
from apps.applications.models import Application
from apps.jobs.models import PipelineStage

from .models import Debrief, Interview, Scorecard, ScorecardTemplate
from .selectors import InterviewSelector
from .serializers import (
    CancelInterviewSerializer,
    CandidateInterviewSerializer,
    CreateDebriefSerializer,
    CreateScorecardSerializer,
    DebriefSerializer,
    InterviewDetailSerializer,
    InterviewListSerializer,
    RecordDecisionSerializer,
    RescheduleInterviewSerializer,
    ScheduleInterviewSerializer,
    ScorecardSerializer,
)
from .services import DebriefService, InterviewService, ScorecardService

# --- Internal views ---

class InternalInterviewViewSet(viewsets.ModelViewSet):
    """ViewSet for managing interviews (internal users only)."""

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = InterviewListSerializer

    def get_queryset(self):
        return Interview.objects.select_related(
            'application__candidate__user',
            'application__requisition',
            'interview_plan_stage',
        ).prefetch_related(
            'participants__interviewer__user',
        ).order_by('-scheduled_start')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return InterviewDetailSerializer
        return InterviewListSerializer

    def create(self, request, *args, **kwargs):
        """Schedule a new interview."""
        serializer = ScheduleInterviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        application = Application.objects.get(id=data['application_id'])

        interview_plan_stage = None
        if data.get('interview_plan_stage_id'):
            interview_plan_stage = PipelineStage.objects.get(
                id=data['interview_plan_stage_id'],
            )

        scorecard_template = None
        if data.get('scorecard_template_id'):
            scorecard_template = ScorecardTemplate.objects.get(
                id=data['scorecard_template_id'],
            )

        interview = InterviewService.schedule(
            application=application,
            interview_type=data['type'],
            scheduled_start=data['scheduled_start'],
            scheduled_end=data['scheduled_end'],
            timezone_str=data.get('timezone', 'UTC'),
            location=data.get('location', ''),
            video_link=data.get('video_link', ''),
            prep_notes_interviewer=data.get('prep_notes_interviewer', ''),
            prep_notes_candidate=data.get('prep_notes_candidate', ''),
            interview_plan_stage=interview_plan_stage,
            scorecard_template=scorecard_template,
            created_by=request.user,
            interviewer_ids=data.get('interviewer_ids', []),
        )

        return Response(
            InterviewDetailSerializer(interview).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an interview."""
        interview = self.get_object()
        serializer = CancelInterviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        interview = InterviewService.cancel(
            interview,
            reason=serializer.validated_data.get('reason', ''),
            cancelled_by=request.user,
        )

        return Response(
            InterviewDetailSerializer(interview).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        """Reschedule an interview."""
        interview = self.get_object()
        serializer = RescheduleInterviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        interview = InterviewService.reschedule(
            interview,
            scheduled_start=serializer.validated_data['scheduled_start'],
            scheduled_end=serializer.validated_data['scheduled_end'],
            rescheduled_by=request.user,
        )

        return Response(
            InterviewDetailSerializer(interview).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark an interview as completed."""
        interview = self.get_object()
        interview = InterviewService.mark_complete(
            interview,
            marked_by=request.user,
        )

        return Response(
            InterviewDetailSerializer(interview).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['get', 'post'], url_path='scorecards')
    def scorecards(self, request, pk=None):
        """Get or create scorecard for an interview."""
        interview = self.get_object()

        if request.method == 'GET':
            # Check if user can view scorecards (anti-bias rule)
            if not ScorecardService.can_view_scorecards(interview, request.user):
                return Response(
                    {'detail': 'You must submit your own scorecard before viewing others'},
                    status=status.HTTP_403_FORBIDDEN,
                )

            scorecards = Scorecard.objects.filter(
                interview=interview,
                is_draft=False,
            ).select_related('interviewer__user').prefetch_related(
                'criterion_ratings__criterion',
            )

            return Response(
                ScorecardSerializer(scorecards, many=True).data,
            )

        # POST - create/update scorecard
        serializer = CreateScorecardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        interviewer = request.user.internal_profile

        scorecard = ScorecardService.create_or_update_scorecard(
            interview=interview,
            interviewer=interviewer,
            overall_rating=serializer.validated_data.get('overall_rating'),
            recommendation=serializer.validated_data.get('recommendation'),
            strengths=serializer.validated_data.get('strengths', ''),
            concerns=serializer.validated_data.get('concerns', ''),
            notes=serializer.validated_data.get('notes', ''),
            criterion_ratings=serializer.validated_data.get('criterion_ratings', []),
            is_draft=serializer.validated_data.get('is_draft', True),
        )

        # If not draft, submit it
        if not serializer.validated_data.get('is_draft', True):
            scorecard = ScorecardService.submit_scorecard(
                scorecard,
                submitted_by=request.user,
            )

        return Response(
            ScorecardSerializer(scorecard).data,
            status=status.HTTP_201_CREATED,
        )


class DebriefViewSet(viewsets.ModelViewSet):
    """ViewSet for managing debriefs (internal users only)."""

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = DebriefSerializer

    def get_queryset(self):
        return Debrief.objects.select_related(
            'application__candidate__user',
            'application__requisition',
            'decided_by',
        ).order_by('-scheduled_at')

    def create(self, request, *args, **kwargs):
        """Create a new debrief."""
        serializer = CreateDebriefSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        application = Application.objects.get(
            id=serializer.validated_data['application_id'],
        )

        debrief = DebriefService.create_debrief(
            application=application,
            scheduled_at=serializer.validated_data['scheduled_at'],
            notes=serializer.validated_data.get('notes', ''),
            created_by=request.user,
        )

        return Response(
            DebriefSerializer(debrief).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'], url_path='record-decision')
    def record_decision(self, request, pk=None):
        """Record a hiring decision from a debrief."""
        debrief = self.get_object()
        serializer = RecordDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        debrief = DebriefService.record_decision(
            debrief,
            decision=serializer.validated_data['decision'],
            notes=serializer.validated_data.get('notes', ''),
            decided_by=request.user,
        )

        return Response(
            DebriefSerializer(debrief).data,
            status=status.HTTP_200_OK,
        )


class UpcomingInterviewsView(generics.ListAPIView):
    """Get upcoming interviews for internal users."""

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = InterviewListSerializer

    def get_queryset(self):
        days_ahead = int(self.request.query_params.get('days', 7))
        return InterviewSelector.get_upcoming_interviews(
            user=self.request.user,
            days_ahead=days_ahead,
        )


class PendingScorecardsView(generics.ListAPIView):
    """Get interviews pending scorecard submission for a user."""

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = InterviewListSerializer

    def get_queryset(self):
        interviewer = self.request.user.internal_profile
        return InterviewSelector.get_pending_scorecards(interviewer)


# --- Candidate views ---

class CandidateInterviewListView(generics.ListAPIView):
    """List upcoming interviews for a candidate."""

    permission_classes = [IsAuthenticated, IsCandidate]
    serializer_class = CandidateInterviewSerializer

    def get_queryset(self):
        return InterviewSelector.get_upcoming_interviews(
            user=self.request.user,
        )


class CandidateAllInterviewsView(generics.ListAPIView):
    """
    GET /api/v1/interviews/

    List all interviews (upcoming and past) for the authenticated candidate.
    """

    permission_classes = [IsAuthenticated, IsCandidate]
    serializer_class = CandidateInterviewSerializer

    def get_queryset(self):
        return (
            Interview.objects
            .filter(application__candidate__user=self.request.user)
            .select_related(
                'application__requisition',
                'interview_plan_stage',
            )
            .order_by('-scheduled_start')
        )


class CandidateInterviewConfirmView(APIView):
    """
    POST /api/v1/interviews/{pk}/confirm/

    Allows a candidate to confirm their attendance for a scheduled interview.
    Only valid for interviews in 'scheduled' or 'rescheduled' status.
    """

    permission_classes = [IsAuthenticated, IsCandidate]

    def post(self, request, pk):
        try:
            interview = Interview.objects.select_related(
                'application__requisition',
                'interview_plan_stage',
            ).get(pk=pk, application__candidate__user=request.user)
        except Interview.DoesNotExist:
            return Response({'detail': 'Interview not found.'}, status=status.HTTP_404_NOT_FOUND)

        if interview.status not in ('scheduled', 'rescheduled'):
            return Response(
                {'detail': f'Cannot confirm an interview with status "{interview.status}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        interview.status = 'confirmed'
        interview.save(update_fields=['status', 'updated_at'])

        return Response(
            CandidateInterviewSerializer(interview).data,
            status=status.HTTP_200_OK,
        )

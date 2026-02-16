"""Views for accounts app."""

import logging

from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils import get_client_ip

logger = logging.getLogger(__name__)

from .models import (
    CandidateProfile,
    Department,
    Education,
    InternalUser,
    JobAlert,
    JobLevel,
    Location,
    Role,
    SavedSearch,
    Skill,
    Team,
    User,
    WorkExperience,
)
from .permissions import IsCandidate, IsInternalUser
from .serializers import (
    CandidateProfileSerializer,
    CandidateProfileUpdateSerializer,
    DepartmentSerializer,
    EducationSerializer,
    InternalUserSerializer,
    JobAlertSerializer,
    JobLevelSerializer,
    LocationSerializer,
    LoginSerializer,
    MeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    RoleSerializer,
    SavedSearchSerializer,
    SkillSerializer,
    TeamSerializer,
    WorkExperienceSerializer,
)
from .services import AuthService, UserService
from .candidate_services import CandidateProfileService


class RegisterView(APIView):
    """POST /api/v1/auth/register/ — Candidate registration."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = AuthService.register_candidate(serializer.validated_data)
        AuthService.login_user(request, user)

        # CRITICAL: Save session to database before returning session key
        request.session.save()

        # Return user data with session key for Next.js to store
        response_data = MeSerializer(user).data
        response_data['token'] = request.session.session_key

        return Response(
            response_data,
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """POST /api/v1/auth/login/ — Login with email/password."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        AuthService.login_user(request, user)

        # Track login IP for internal users
        if user.is_internal and hasattr(user, 'internal_profile'):
            user.internal_profile.last_login_ip = get_client_ip(request)
            user.internal_profile.save(update_fields=['last_login_ip'])

        # Ensure session is saved to cache before returning session key
        request.session.save()

        # Return user data with session key for Next.js to store
        response_data = MeSerializer(user).data
        response_data['token'] = request.session.session_key

        return Response(response_data)


class LogoutView(APIView):
    """POST /api/v1/auth/logout/ — Clear session."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        AuthService.logout_user(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(generics.RetrieveAPIView):
    """GET /api/v1/auth/me/ — Current user profile."""

    permission_classes = [IsAuthenticated]
    serializer_class = MeSerializer

    def get_object(self):
        return self.request.user


class PasswordResetRequestView(APIView):
    """POST /api/v1/auth/password-reset/ — Request password reset."""

    permission_classes = [AllowAny]

    def post(self, request):
        from django.conf import settings
        from apps.communications.services import EmailService

        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        # Always return success to prevent email enumeration
        try:
            user = User.objects.get(email=email, is_active=True)
            token_data = AuthService.generate_password_reset_token(user)

            # Construct reset link for the appropriate frontend
            # Internal users go to internal dashboard, candidates to public site
            if user.is_internal:
                frontend_url = settings.INTERNAL_DASHBOARD_URL
            else:
                frontend_url = settings.PUBLIC_CAREERS_URL

            # Combine uid and token for the URL
            reset_token = f"{token_data['uid']}:{token_data['token']}"
            reset_link = f"{frontend_url}/reset-password?token={reset_token}"

            # Send password reset email
            EmailService.send_templated_email(
                template_name='Password Reset',
                recipient=user.email,
                context={
                    'user_name': user.get_full_name() or user.email,
                    'reset_link': reset_link,
                    'expiry_hours': 24,  # Django default token expiry
                },
            )
        except User.DoesNotExist:
            pass

        return Response({'detail': 'If the email exists, a reset link has been sent.'})


class PasswordResetConfirmView(APIView):
    """POST /api/v1/auth/password-reset/confirm/ — Confirm password reset."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService.reset_password(
            token=serializer.validated_data['token'],
            new_password=serializer.validated_data['new_password'],
        )
        return Response({'detail': 'Password has been reset successfully.'})


# --- Candidate views ---

class CandidateProfileView(generics.RetrieveUpdateAPIView):
    """GET/PUT /api/v1/candidates/profile/ — Own candidate profile."""

    permission_classes = [IsAuthenticated, IsCandidate]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return CandidateProfileUpdateSerializer
        return CandidateProfileSerializer

    def get_object(self):
        return CandidateProfile.objects.select_related('user').prefetch_related(
            'experiences', 'education', 'skills'
        ).get(user=self.request.user)


class ResumeUploadView(APIView):
    """POST /api/v1/candidates/resume/ — Upload and parse resume."""

    permission_classes = [IsAuthenticated, IsCandidate]

    def post(self, request):
        resume_file = request.FILES.get('resume')
        if not resume_file:
            return Response(
                {'detail': 'No resume file provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate file type
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt']
        file_ext = resume_file.name.lower().split('.')[-1]
        if f'.{file_ext}' not in allowed_extensions:
            return Response(
                {'detail': f'File type not supported. Allowed: {", ".join(allowed_extensions)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if resume_file.size > max_size:
            return Response(
                {'detail': 'File too large. Maximum size is 5MB.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        candidate = CandidateProfile.objects.get(user=request.user)
        auto_populate = request.data.get('auto_populate', 'true').lower() == 'true'

        # Upload and parse
        candidate = CandidateProfileService.upload_and_parse_resume(
            candidate=candidate,
            resume_file=resume_file,
            auto_populate=auto_populate
        )

        # If auto_populate is enabled, create records from parsed data
        if auto_populate:
            counts = CandidateProfileService.auto_populate_from_resume(candidate)
            return Response({
                'detail': 'Resume uploaded and parsed successfully.',
                'resume_url': candidate.resume_file.url if candidate.resume_file else None,
                'parsed_data': candidate.resume_parsed,
                'populated': counts,
            })

        return Response({
            'detail': 'Resume uploaded successfully.',
            'resume_url': candidate.resume_file.url if candidate.resume_file else None,
            'parsed_data': candidate.resume_parsed,
        })


class JobRecommendationsView(generics.ListAPIView):
    """
    Get personalized job recommendations for the authenticated candidate.
    Returns jobs scored and ranked based on profile match.
    """

    permission_classes = [IsAuthenticated, IsCandidate]

    def get(self, request):
        from .recommendation import JobRecommendationService
        from apps.jobs.serializers import PublicJobListSerializer

        try:
            candidate = CandidateProfile.objects.get(user=request.user)
        except CandidateProfile.DoesNotExist:
            return Response({
                'detail': 'Candidate profile not found.',
                'recommendations': [],
            }, status=status.HTTP_404_NOT_FOUND)

        # Get limit from query params (default 10, max 20)
        limit = int(request.query_params.get('limit', 10))
        limit = min(limit, 20)

        recommendations = JobRecommendationService.get_recommendations(
            candidate, limit=limit
        )

        # Serialize the results
        results = []
        for rec in recommendations:
            job_data = PublicJobListSerializer(rec['job']).data
            job_data['match_score'] = rec['score']
            job_data['match_reasons'] = rec['reasons']
            results.append(job_data)

        return Response({
            'count': len(results),
            'recommendations': results,
        })


class CandidateAnalyticsView(generics.GenericAPIView):
    """
    Comprehensive analytics dashboard for candidates.

    Returns:
    - Application statistics (total, active, success rate)
    - Application timeline data
    - Profile engagement metrics
    - Interview statistics
    - Insights and recommendations
    """
    permission_classes = [IsAuthenticated, IsCandidate]

    def get(self, request):
        from django.db.models import Count, Avg, Q
        from django.utils import timezone
        from datetime import timedelta
        from apps.applications.models import Application
        from apps.interviews.models import Interview

        candidate = CandidateProfile.objects.get(user=request.user)

        # Application Statistics
        applications = Application.objects.filter(candidate=candidate).exclude(status='draft')
        total_applications = applications.count()

        active_applications = applications.filter(
            status__in=['applied', 'screening', 'interview', 'assessment', 'offer']
        ).count()

        offers = applications.filter(status='offer').count()
        hired = applications.filter(status='hired').count()
        rejected = applications.filter(status='rejected').count()

        success_rate = round((hired / total_applications * 100), 1) if total_applications > 0 else 0
        offer_rate = round(((offers + hired) / total_applications * 100), 1) if total_applications > 0 else 0

        # Application Timeline (last 6 months)
        six_months_ago = timezone.now() - timedelta(days=180)
        timeline_data = []

        for i in range(6):
            month_start = timezone.now() - timedelta(days=30 * (5 - i))
            month_end = timezone.now() - timedelta(days=30 * (4 - i)) if i < 5 else timezone.now()

            month_applications = applications.filter(
                applied_at__gte=month_start,
                applied_at__lt=month_end
            ).count()

            timeline_data.append({
                'month': month_start.strftime('%b %Y'),
                'applications': month_applications
            })

        # Recent Activity (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_applications = applications.filter(applied_at__gte=thirty_days_ago).count()

        # Interview Statistics
        interviews = Interview.objects.filter(
            application__candidate=candidate
        )
        total_interviews = interviews.count()
        completed_interviews = interviews.filter(status='completed').count()
        upcoming_interviews = interviews.filter(
            status='scheduled',
            scheduled_start__gte=timezone.now()
        ).count()

        # Status Breakdown
        status_breakdown = []
        for status, label in Application.STATUS_CHOICES:
            if status == 'draft':
                continue
            count = applications.filter(status=status).count()
            if count > 0:
                status_breakdown.append({
                    'status': status,
                    'label': label,
                    'count': count,
                    'percentage': round((count / total_applications * 100), 1) if total_applications > 0 else 0
                })

        # Average Time in Process (days from applied to current status)
        applications_with_time = applications.exclude(status__in=['draft', 'withdrawn'])
        avg_days_in_process = 0
        if applications_with_time.exists():
            total_days = 0
            for app in applications_with_time:
                days = (timezone.now() - app.applied_at).days
                total_days += days
            avg_days_in_process = round(total_days / applications_with_time.count(), 1)

        # Profile Completeness
        profile_completion = candidate.calculate_completeness()

        # Insights and Recommendations
        insights = []

        if profile_completion < 70:
            insights.append({
                'type': 'warning',
                'title': 'Complete Your Profile',
                'message': f'Your profile is {profile_completion}% complete. Candidates with 80%+ complete profiles get 3x more interview invites.',
                'action': 'Complete Profile',
                'action_link': '/dashboard/profile'
            })

        if total_applications == 0:
            insights.append({
                'type': 'info',
                'title': 'Start Applying',
                'message': 'You haven\'t applied to any positions yet. Browse open roles to get started!',
                'action': 'Browse Jobs',
                'action_link': '/jobs'
            })
        elif recent_applications == 0 and total_applications > 0:
            insights.append({
                'type': 'info',
                'title': 'Stay Active',
                'message': 'You haven\'t applied to any positions in the last 30 days. Check out new openings!',
                'action': 'Browse Jobs',
                'action_link': '/jobs'
            })

        if offer_rate > 0 and offer_rate < 20 and total_applications > 5:
            insights.append({
                'type': 'tip',
                'title': 'Improve Your Success Rate',
                'message': 'Consider tailoring your applications more closely to job requirements to increase your offer rate.',
                'action': None,
                'action_link': None
            })

        if total_interviews > 0 and completed_interviews > 0:
            interview_to_offer_rate = round(((offers + hired) / completed_interviews * 100), 1) if completed_interviews > 0 else 0
            if interview_to_offer_rate > 50:
                insights.append({
                    'type': 'success',
                    'title': 'Strong Interview Performance',
                    'message': f'You\'re converting {interview_to_offer_rate}% of interviews to offers. Keep it up!',
                    'action': None,
                    'action_link': None
                })

        return Response({
            'overview': {
                'total_applications': total_applications,
                'active_applications': active_applications,
                'offers_received': offers + hired,
                'success_rate': success_rate,
                'offer_rate': offer_rate,
                'profile_completion': profile_completion,
            },
            'timeline': timeline_data,
            'recent_activity': {
                'applications_last_30_days': recent_applications,
                'avg_days_in_process': avg_days_in_process,
            },
            'interviews': {
                'total': total_interviews,
                'completed': completed_interviews,
                'upcoming': upcoming_interviews,
            },
            'status_breakdown': status_breakdown,
            'insights': insights,
        })


class WorkExperienceViewSet(viewsets.ModelViewSet):
    """CRUD for candidate work experience."""

    permission_classes = [IsAuthenticated, IsCandidate]
    serializer_class = WorkExperienceSerializer

    def get_queryset(self):
        """Return only the authenticated candidate's work experiences."""
        return WorkExperience.objects.filter(
            candidate__user=self.request.user
        ).order_by('-start_date')

    def perform_create(self, serializer):
        """Automatically associate with the authenticated candidate."""
        candidate = CandidateProfile.objects.get(user=self.request.user)
        serializer.save(candidate=candidate)


class EducationViewSet(viewsets.ModelViewSet):
    """CRUD for candidate education."""

    permission_classes = [IsAuthenticated, IsCandidate]
    serializer_class = EducationSerializer

    def get_queryset(self):
        """Return only the authenticated candidate's education records."""
        return Education.objects.filter(
            candidate__user=self.request.user
        ).order_by('-start_date')

    def perform_create(self, serializer):
        """Automatically associate with the authenticated candidate."""
        candidate = CandidateProfile.objects.get(user=self.request.user)
        serializer.save(candidate=candidate)


class SkillViewSet(viewsets.ModelViewSet):
    """CRUD for candidate skills."""

    permission_classes = [IsAuthenticated, IsCandidate]
    serializer_class = SkillSerializer

    def get_queryset(self):
        """Return only the authenticated candidate's skills."""
        return Skill.objects.filter(
            candidate__user=self.request.user
        ).order_by('name')

    def perform_create(self, serializer):
        """Automatically associate with the authenticated candidate."""
        candidate = CandidateProfile.objects.get(user=self.request.user)
        serializer.save(candidate=candidate)


# --- Internal admin views ---

class InternalUserViewSet(viewsets.ModelViewSet):
    """CRUD for internal users (admin only)."""

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = InternalUserSerializer

    def get_queryset(self):
        return InternalUser.objects.select_related(
            'user', 'department', 'team', 'manager__user'
        ).prefetch_related('roles__permissions')

    def perform_create(self, serializer):
        data = serializer.validated_data
        UserService.create_internal_user(
            email=self.request.data.get('email'),
            first_name=self.request.data.get('first_name'),
            last_name=self.request.data.get('last_name'),
            password=self.request.data.get('password'),
            employee_id=data['employee_id'],
            title=data['title'],
            department=data.get('department'),
            team=data.get('team'),
            manager=data.get('manager'),
            role_ids=[r.id for r in data.get('roles', [])],
            sso_id=data.get('sso_id', ''),
        )

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        internal_user = self.get_object()
        UserService.deactivate_user(internal_user)
        return Response({'detail': 'User deactivated.'})


class DepartmentViewSet(viewsets.ModelViewSet):
    """CRUD for departments."""

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = DepartmentSerializer
    queryset = Department.objects.select_related('parent', 'head__user')


class TeamViewSet(viewsets.ModelViewSet):
    """CRUD for teams."""

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = TeamSerializer
    queryset = Team.objects.select_related('department', 'lead__user')


class LocationViewSet(viewsets.ModelViewSet):
    """CRUD for locations."""

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = LocationSerializer
    queryset = Location.objects.all()


class JobLevelViewSet(viewsets.ModelViewSet):
    """CRUD for job levels."""

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = JobLevelSerializer
    queryset = JobLevel.objects.all()


class RoleViewSet(viewsets.ModelViewSet):
    """CRUD for roles."""

    permission_classes = [IsAuthenticated, IsInternalUser]
    serializer_class = RoleSerializer
    queryset = Role.objects.prefetch_related('permissions')

    def perform_destroy(self, instance):
        if instance.is_system:
            from apps.core.exceptions import BusinessValidationError
            raise BusinessValidationError('System roles cannot be deleted.')
        instance.delete()


class CandidateSearchView(generics.GenericAPIView):
    """Search candidates using Elasticsearch with database fallback."""

    permission_classes = [IsAuthenticated, IsInternalUser]

    def get(self, request):
        """
        Search candidates with filters.

        Query params:
        - q: Search query (name, email, skills, resume)
        - skills: Comma-separated list of skills
        - location_city: City filter
        - location_country: Country filter
        - experience_min: Minimum years of experience
        - experience_max: Maximum years of experience
        - work_authorization: Work authorization status
        - source: Candidate source
        - salary_max: Maximum salary budget
        - limit: Results limit (default 100)
        """
        from .search import CandidateSearchService

        query = request.query_params.get('q', '')
        skills_str = request.query_params.get('skills', '')
        skills = [s.strip() for s in skills_str.split(',') if s.strip()] if skills_str else None

        candidates = CandidateSearchService.search(
            query=query,
            skills=skills,
            location_city=request.query_params.get('location_city'),
            location_country=request.query_params.get('location_country'),
            experience_min=int(request.query_params.get('experience_min')) if request.query_params.get('experience_min') else None,
            experience_max=int(request.query_params.get('experience_max')) if request.query_params.get('experience_max') else None,
            work_authorization=request.query_params.get('work_authorization'),
            source=request.query_params.get('source'),
            salary_max=int(request.query_params.get('salary_max')) if request.query_params.get('salary_max') else None,
            limit=int(request.query_params.get('limit', 100)),
        )

        serializer = CandidateProfileSerializer(candidates, many=True)
        return Response({
            'count': len(candidates),
            'results': serializer.data,
        })


class SavedSearchViewSet(viewsets.ModelViewSet):
    """
    ViewSet for candidate saved job searches.

    Candidates can save search criteria and optionally receive email alerts.
    """

    serializer_class = SavedSearchSerializer
    permission_classes = [IsAuthenticated, IsCandidate]

    def get_queryset(self):
        """Return only the current candidate's saved searches."""
        if not hasattr(self.request.user, 'candidate_profile'):
            return SavedSearch.objects.none()
        return SavedSearch.objects.filter(
            candidate=self.request.user.candidate_profile
        ).order_by('-created_at')

    def perform_create(self, serializer):
        """Automatically associate with current candidate."""
        serializer.save(candidate=self.request.user.candidate_profile)

    @action(detail=True, methods=['get'])
    def matches(self, request, pk=None):
        """
        GET /api/v1/candidates/saved-searches/{id}/matches/

        Returns jobs matching this saved search.
        """
        saved_search = self.get_object()
        from apps.jobs.models import Requisition
        from apps.jobs.serializers import PublicJobSerializer

        # Build queryset based on search_params
        queryset = Requisition.objects.filter(status='open', is_published=True)
        params = saved_search.search_params

        if params.get('keywords'):
            from django.db.models import Q
            queryset = queryset.filter(
                Q(title__icontains=params['keywords']) |
                Q(description__icontains=params['keywords'])
            )

        if params.get('department'):
            queryset = queryset.filter(department__name__icontains=params['department'])

        if params.get('location_city'):
            queryset = queryset.filter(location__city__icontains=params['location_city'])

        if params.get('location_country'):
            queryset = queryset.filter(location__country=params['location_country'])

        if params.get('employment_type'):
            queryset = queryset.filter(employment_type=params['employment_type'])

        if params.get('remote_policy'):
            queryset = queryset.filter(remote_policy=params['remote_policy'])

        if params.get('level'):
            queryset = queryset.filter(level__name=params['level'])

        if params.get('salary_min'):
            queryset = queryset.filter(salary_max__gte=params['salary_min'])

        if params.get('salary_max'):
            queryset = queryset.filter(salary_min__lte=params['salary_max'])

        # Update match count
        saved_search.match_count = queryset.count()
        saved_search.save(update_fields=['match_count'])

        # Paginate results
        queryset = queryset.select_related('department', 'location')[:20]
        serializer = PublicJobSerializer(queryset, many=True)

        return Response({
            'count': saved_search.match_count,
            'results': serializer.data,
        })

    @action(detail=True, methods=['post'])
    def toggle_alerts(self, request, pk=None):
        """
        POST /api/v1/candidates/saved-searches/{id}/toggle-alerts/

        Toggle email alerts on/off for this saved search.
        """
        saved_search = self.get_object()
        saved_search.is_active = not saved_search.is_active
        saved_search.save(update_fields=['is_active', 'updated_at'])

        return Response({
            'is_active': saved_search.is_active,
            'message': 'Alerts enabled' if saved_search.is_active else 'Alerts disabled',
        })


class JobAlertViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing job alerts sent to the candidate.

    Read-only: candidates can view their alert history but not create/modify.
    """

    serializer_class = JobAlertSerializer
    permission_classes = [IsAuthenticated, IsCandidate]

    def get_queryset(self):
        """Return only alerts for the current candidate's saved searches."""
        if not hasattr(self.request.user, 'candidate_profile'):
            return JobAlert.objects.none()

        return JobAlert.objects.filter(
            saved_search__candidate=self.request.user.candidate_profile
        ).select_related(
            'saved_search',
            'requisition',
        ).order_by('-sent_at')

    @action(detail=True, methods=['post'])
    def mark_clicked(self, request, pk=None):
        """
        POST /api/v1/candidates/job-alerts/{id}/mark-clicked/

        Mark that the candidate clicked through to view the job.
        """
        alert = self.get_object()
        alert.was_clicked = True
        alert.save(update_fields=['was_clicked'])

        return Response({'status': 'marked as clicked'})

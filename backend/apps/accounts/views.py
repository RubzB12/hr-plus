"""Views for accounts app."""

from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils import get_client_ip

from .models import (
    CandidateProfile,
    Department,
    Education,
    InternalUser,
    JobLevel,
    Location,
    Role,
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
    JobLevelSerializer,
    LocationSerializer,
    LoginSerializer,
    MeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    RoleSerializer,
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
        return Response(
            MeSerializer(user).data,
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

        return Response(MeSerializer(user).data)


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
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        # Always return success to prevent email enumeration
        try:
            user = User.objects.get(email=email, is_active=True)
            token_data = AuthService.generate_password_reset_token(user)
            # TODO: Send email with reset link containing token_data
            _ = token_data
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

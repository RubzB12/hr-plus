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
    InternalUser,
    JobLevel,
    Location,
    Role,
    Team,
    User,
)
from .permissions import IsCandidate, IsInternalUser
from .serializers import (
    CandidateProfileSerializer,
    CandidateProfileUpdateSerializer,
    DepartmentSerializer,
    InternalUserSerializer,
    JobLevelSerializer,
    LocationSerializer,
    LoginSerializer,
    MeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    RoleSerializer,
    TeamSerializer,
)
from .services import AuthService, UserService


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
        return CandidateProfile.objects.select_related('user').get(
            user=self.request.user
        )


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

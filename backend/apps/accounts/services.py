"""Service layer for accounts app."""

import logging

from django.contrib.auth import login, logout
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.utils.crypto import get_random_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from apps.core.exceptions import BusinessValidationError, DuplicateError
from apps.core.services import BaseService

from .models import CandidateProfile, Department, InternalUser, Role, User

logger = logging.getLogger(__name__)


class AuthService(BaseService):
    """Handles registration, login, logout, and password reset."""

    @staticmethod
    @transaction.atomic
    def register_candidate(validated_data: dict) -> User:
        """
        Register a new candidate user and create their profile.

        Args:
            validated_data: Dict with email, password, first_name, last_name.

        Returns:
            The created User instance.

        Raises:
            DuplicateError: If a user with this email already exists.
        """
        email = validated_data['email']
        if User.objects.filter(email=email).exists():
            raise DuplicateError('A user with this email already exists.')

        user = User.objects.create_user(
            username=email,
            email=email,
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            is_internal=False,
        )

        CandidateProfile.objects.create(
            user=user,
            source=validated_data.get('source', 'direct'),
        )

        logger.info('Candidate registered: %s', user.email)
        return user

    @staticmethod
    def login_user(request, user: User) -> None:
        """
        Log in a user and create a session.

        Args:
            request: The HTTP request object.
            user: The authenticated User instance.
        """
        login(request, user)
        logger.info('User logged in: %s', user.email)

    @staticmethod
    def logout_user(request) -> None:
        """
        Log out the current user and clear the session.

        Args:
            request: The HTTP request object.
        """
        logger.info('User logged out: %s', request.user.email)
        logout(request)

    @staticmethod
    def generate_password_reset_token(user: User) -> dict:
        """
        Generate a password reset token for the given user.

        Returns:
            Dict with uid and token strings.
        """
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        return {'uid': uid, 'token': token}

    @staticmethod
    def reset_password(token: str, new_password: str) -> bool:
        """
        Reset a user's password using a token.

        The token format is 'uid:token' where uid is base64-encoded.

        Args:
            token: Combined uid:token string.
            new_password: The new password.

        Returns:
            True if password was reset successfully.

        Raises:
            BusinessValidationError: If the token is invalid or expired.
        """
        try:
            uid_str, reset_token = token.split(':', 1)
            uid = force_str(urlsafe_base64_decode(uid_str))
            user = User.objects.get(pk=uid)
        except (ValueError, User.DoesNotExist) as err:
            raise BusinessValidationError('Invalid password reset token.') from err

        if not default_token_generator.check_token(user, reset_token):
            raise BusinessValidationError('Password reset token has expired.')

        user.set_password(new_password)
        user.save(update_fields=['password'])
        logger.info('Password reset for: %s', user.email)
        return True


class UserService(BaseService):
    """CRUD operations for internal users and role assignment."""

    @staticmethod
    @transaction.atomic
    def create_internal_user(
        email: str,
        first_name: str,
        last_name: str,
        employee_id: str,
        title: str,
        password: str | None = None,
        department=None,
        team=None,
        manager=None,
        role_ids: list | None = None,
        sso_id: str = '',
    ) -> InternalUser:
        """
        Create a new internal user with associated User and InternalUser profile.

        Args:
            email: User email address.
            first_name: First name.
            last_name: Last name.
            employee_id: Unique employee identifier.
            title: Job title.
            password: Optional password (can be set later for SSO users).
            department: Department instance or None.
            team: Team instance or None.
            manager: InternalUser instance or None.
            role_ids: List of Role IDs to assign.
            sso_id: External SSO identifier.

        Returns:
            The created InternalUser instance.
        """
        if User.objects.filter(email=email).exists():
            raise DuplicateError('A user with this email already exists.')

        if InternalUser.objects.filter(employee_id=employee_id).exists():
            raise DuplicateError('An employee with this ID already exists.')

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password or get_random_string(32),
            first_name=first_name,
            last_name=last_name,
            is_internal=True,
            is_staff=True,
        )

        internal_user = InternalUser.objects.create(
            user=user,
            employee_id=employee_id,
            department=department,
            team=team,
            title=title,
            manager=manager,
            sso_id=sso_id,
        )

        if role_ids:
            roles = Role.objects.filter(id__in=role_ids)
            internal_user.roles.set(roles)

        logger.info('Internal user created: %s (%s)', user.email, employee_id)
        return internal_user

    @staticmethod
    @transaction.atomic
    def update_internal_user(internal_user: InternalUser, validated_data: dict) -> InternalUser:
        """
        Update an internal user's profile.

        Args:
            internal_user: The InternalUser instance to update.
            validated_data: Dict of fields to update.

        Returns:
            The updated InternalUser instance.
        """
        role_ids = validated_data.pop('roles', None)

        for field, value in validated_data.items():
            setattr(internal_user, field, value)
        internal_user.save()

        if role_ids is not None:
            internal_user.roles.set(role_ids)

        logger.info('Internal user updated: %s', internal_user.user.email)
        return internal_user

    @staticmethod
    def assign_roles(internal_user: InternalUser, roles: list[Role]) -> None:
        """Assign roles to an internal user (replaces existing roles)."""
        internal_user.roles.set(roles)
        logger.info(
            'Roles updated for %s: %s',
            internal_user.user.email,
            [r.name for r in roles],
        )

    @staticmethod
    def deactivate_user(internal_user: InternalUser) -> None:
        """Deactivate an internal user."""
        internal_user.is_active = False
        internal_user.save(update_fields=['is_active'])
        internal_user.user.is_active = False
        internal_user.user.save(update_fields=['is_active'])
        logger.info('Internal user deactivated: %s', internal_user.user.email)


class DepartmentService(BaseService):
    """Handles department hierarchy management."""

    @staticmethod
    def get_department_tree() -> list[dict]:
        """
        Return all departments as a nested tree structure.

        Returns:
            List of top-level departments, each with a 'children' key.
        """
        departments = Department.objects.select_related('parent', 'head__user').filter(
            is_active=True
        )
        dept_map = {dept.id: {'department': dept, 'children': []} for dept in departments}

        roots = []
        for dept in departments:
            node = dept_map[dept.id]
            if dept.parent_id and dept.parent_id in dept_map:
                dept_map[dept.parent_id]['children'].append(node)
            else:
                roots.append(node)

        return roots

    @staticmethod
    def get_ancestors(department: Department) -> list[Department]:
        """Return list of ancestors from root to immediate parent."""
        ancestors = []
        current = department.parent
        while current is not None:
            ancestors.append(current)
            current = current.parent
        ancestors.reverse()
        return ancestors

    @staticmethod
    def validate_parent(department: Department, new_parent: Department | None) -> None:
        """
        Validate that setting new_parent won't create a cycle.

        Raises:
            BusinessValidationError: If the parent would create a circular reference.
        """
        if new_parent is None:
            return
        if new_parent.id == department.id:
            raise BusinessValidationError('A department cannot be its own parent.')

        current = new_parent.parent
        while current is not None:
            if current.id == department.id:
                raise BusinessValidationError(
                    'Setting this parent would create a circular reference.'
                )
            current = current.parent

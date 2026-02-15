from rest_framework.permissions import BasePermission


class IsInternalUser(BasePermission):
    """
    Permission class to check if user is an internal user (has InternalUserProfile).
    """

    def has_permission(self, request, view):
        """Check if user is internal user."""
        if not request.user or not request.user.is_authenticated:
            return False

        return hasattr(request.user, 'internal_profile')


class IsComplianceAdmin(BasePermission):
    """
    Permission class to check if user has compliance admin permissions.
    """

    def has_permission(self, request, view):
        """Check if user is compliance admin."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Check for specific compliance permissions
        return request.user.has_perm('compliance.view_auditlog') or request.user.is_superuser


class HasPermission(BasePermission):
    """
    DRF permission class that checks if user has a specific permission.

    Usage:
        permission_classes = [IsAuthenticated, HasPermission('applications.view_application')]

    The permission string should be in Django's format: 'app_label.codename'
    """

    def __init__(self, permission_codename):
        """
        Initialize with the required permission codename.

        Args:
            permission_codename: Permission string (e.g., 'applications.view_application')
        """
        self.permission_codename = permission_codename

    def has_permission(self, request, view):
        """
        Check if the authenticated user has the required permission.

        Args:
            request: DRF request object
            view: DRF view instance

        Returns:
            bool: True if user has permission, False otherwise
        """
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.has_perm(self.permission_codename)

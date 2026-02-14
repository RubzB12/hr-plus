"""Permission classes for accounts app."""

from rest_framework.permissions import BasePermission


class IsCandidate(BasePermission):
    """Allow access only to candidate (non-internal) users."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return not request.user.is_internal


class IsInternalUser(BasePermission):
    """Allow access only to internal staff users."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_internal


class HasModulePermission(BasePermission):
    """
    Check if internal user has a specific module permission via RBAC roles.

    Usage:
        permission_classes = [IsAuthenticated, HasModulePermission('applications', 'view')]
    """

    def __init__(self, module: str, action: str):
        self.module = module
        self.action = action

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if not request.user.is_internal:
            return False
        if not hasattr(request.user, 'internal_profile'):
            return False
        return request.user.internal_profile.has_module_permission(
            self.module, self.action
        )

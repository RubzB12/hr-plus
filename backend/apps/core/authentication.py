"""Custom authentication classes for HR-Plus."""

import logging
from importlib import import_module

from django.conf import settings
from rest_framework import authentication
from rest_framework import exceptions

logger = logging.getLogger(__name__)


class SessionKeyAuthentication(authentication.BaseAuthentication):
    """
    Authenticate using session key from Authorization Bearer header.

    This allows Next.js to send the Django session key via Bearer token
    while still using Django's session framework for state management.
    Works with any session backend (cache, db, file, etc.).
    """

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header.startswith('Bearer '):
            return None

        session_key = auth_header.replace('Bearer ', '').strip()

        if not session_key:
            return None

        try:
            from apps.accounts.models import User

            # Use the configured session engine (cache, db, etc.)
            engine = import_module(settings.SESSION_ENGINE)
            session = engine.SessionStore(session_key=session_key)

            # Check if session exists and has data
            if not session.exists(session_key):
                raise exceptions.AuthenticationFailed('Invalid session')

            # Load session data
            user_id = session.get('_auth_user_id')

            if not user_id:
                raise exceptions.AuthenticationFailed('Invalid session')

            # Get the user
            user = User.objects.get(pk=user_id)

            if not user.is_active:
                raise exceptions.AuthenticationFailed('User account is disabled')

            return (user, session_key)

        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')

    def authenticate_header(self, request):
        return 'Bearer'

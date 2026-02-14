from .utils import get_client_ip


class AuditLogMiddleware:
    """
    Middleware to log all API requests for audit and compliance purposes.
    Logs actor, IP address, action, resource, and metadata.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Log all API requests (except health checks)
        if request.path.startswith('/api/') and request.path != '/api/health/':
            try:
                # Import here to avoid circular dependency and allow models to not exist yet
                from apps.compliance.models import AuditLog

                AuditLog.objects.create(
                    actor=request.user if request.user.is_authenticated else None,
                    actor_ip=get_client_ip(request),
                    action=request.method,
                    resource_type='api',
                    resource_id=request.path,
                    metadata={
                        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                        'status_code': response.status_code,
                    }
                )
            except Exception:  # noqa: S110
                # Silently fail if AuditLog model doesn't exist yet or other errors
                # This allows the middleware to be loaded before migrations are run
                pass

        return response

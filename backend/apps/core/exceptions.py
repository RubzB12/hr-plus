from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler as drf_exception_handler


class BusinessValidationError(APIException):
    """
    Exception for business rule validation failures.
    Returns 400 Bad Request.
    """
    status_code = 400
    default_detail = 'Business validation failed'
    default_code = 'business_validation_error'


class DuplicateError(BusinessValidationError):
    """
    Exception for duplicate resource attempts.
    Returns 400 Bad Request.
    """
    default_detail = 'Resource already exists'
    default_code = 'duplicate_error'


class InsufficientPermissionError(APIException):
    """
    Exception for permission/authorization failures.
    Returns 403 Forbidden.
    """
    status_code = 403
    default_detail = 'You do not have permission to perform this action'
    default_code = 'insufficient_permission'


def custom_exception_handler(exc, context):
    """
    Custom exception handler that extends DRF's default exception handler.

    This allows us to:
    - Add custom logging for exceptions
    - Standardize error response format
    - Add additional context to error responses

    Args:
        exc: The exception instance
        context: Context dict with 'view' and 'request' keys

    Returns:
        Response object or None
    """
    # Call DRF's default exception handler first to get the standard error response
    response = drf_exception_handler(exc, context)

    if response is not None:
        # Customize the response data format if needed
        # For example, you could add a timestamp, request ID, etc.
        # response.data['timestamp'] = timezone.now().isoformat()
        pass

    return response

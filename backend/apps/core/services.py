class BaseService:
    """
    Base class for service layer objects.

    Services encapsulate business logic and complex operations.
    All business logic should live in service classes, not in views,
    serializers, or models.

    Usage:
        class ApplicationService(BaseService):
            @staticmethod
            @transaction.atomic
            def create_application(validated_data, user):
                # Business logic here
                pass
    """
    pass

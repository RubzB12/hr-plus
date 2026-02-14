import uuid

from django.db import models


class TimestampedModel(models.Model):
    """
    Abstract base model providing automatic timestamp tracking.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """
    Abstract base model providing UUID primary key.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimestampedModel):
    """
    Abstract base model combining UUID primary key and timestamp tracking.
    This is the recommended base for most models in the application.
    """

    class Meta:
        abstract = True

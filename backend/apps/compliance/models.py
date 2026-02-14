"""Compliance and audit models for HR-Plus."""

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """
    Immutable audit log for tracking all system actions.
    Append-only — records should never be updated or deleted.
    """

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    actor_ip = models.GenericIPAddressField(null=True, blank=True)
    action = models.CharField(max_length=50)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=255)
    changes = models.JSONField(
        null=True,
        blank=True,
        help_text='Before/after snapshot for update operations.',
    )
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'compliance_audit_log'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['actor', '-timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
        permissions = [
            ('export_auditlog', 'Can export audit logs'),
        ]

    def __str__(self):
        actor_str = self.actor.email if self.actor else 'anonymous'
        return f'{actor_str} {self.action} {self.resource_type}/{self.resource_id}'

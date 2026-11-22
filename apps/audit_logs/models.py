
"""
Audit log model for tracking all system actions.
"""

import uuid

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from core.constants import AuditAction


class AuditLog(models.Model):
    """
    Append-only audit log for tracking all meaningful actions.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        help_text='User who performed the action'
    )

    action = models.CharField(
        max_length=20,
        choices=AuditAction.CHOICES,
        db_index=True,
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    object_id = models.UUIDField(null=True, blank=True)

    content_object = GenericForeignKey(
        'content_type',
        'object_id'
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional action metadata'
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of the actor'
    )

    user_agent = models.TextField(
        blank=True,
        default='',
        help_text='User agent string'
    )

    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['actor', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        actor_name = self.actor.username if self.actor else 'System'
        return f"{actor_name} - {self.get_action_display()} at {self.timestamp}"

    def save(self, *args, **kwargs):
        """Allow new audit logs but prevent existing logs from being modified."""

        if not self._state.adding:
            raise ValueError("Audit logs cannot be modified")

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deletion of audit logs."""

        raise ValueError("Audit logs cannot be deleted")

    @classmethod
    def log(cls, actor, action, content_object=None, metadata=None, request=None):
        """
        Create a new audit log entry.
        """

        log_data = {
            'actor': actor,
            'action': action,
            'metadata': metadata or {},
        }

        if content_object:
            log_data['content_object'] = content_object

        if request:
            log_data['ip_address'] = cls._get_client_ip(request)
            log_data['user_agent'] = request.META.get(
                'HTTP_USER_AGENT', ''
            )

        return cls.objects.create(**log_data)

    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request."""

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')

        return ip

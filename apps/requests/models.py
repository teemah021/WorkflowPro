"""
Request model with state machine logic.
"""
import uuid
from django.db import models
from django.conf import settings
from core.constants import RequestState
from core.exceptions import InvalidStateTransitionError


class Request(models.Model):
    """
    Request model representing user requests that go through approval workflow.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    title = models.CharField(
        max_length=255,
        help_text='Request title'
    )
    
    description = models.TextField(
        help_text='Detailed description of the request'
    )
    
    status = models.CharField(
        max_length=20,
        choices=RequestState.CHOICES,
        default=RequestState.DRAFT,
        db_index=True,
    )
    
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_requests',
        help_text='User who created this request'
    )
    
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_requests',
        help_text='Manager assigned to review this request'
    )
    
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_requests',
        help_text='User who approved/rejected this request'
    )
    
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the request was reviewed'
    )
    
    rejection_reason = models.TextField(
        blank=True,
        default='',
        help_text='Reason for rejection'
    )
    
    is_deleted = models.BooleanField(
        default=False,
        help_text='Soft delete flag'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['creator']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['is_deleted']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    def can_transition_to(self, new_status):
        """
        Check if the request can transition to the new status.
        """
        allowed_transitions = RequestState.TRANSITIONS.get(self.status, [])
        return new_status in allowed_transitions
    
    def transition_to(self, new_status, user=None):
        """
        Transition the request to a new status.
        Enforces state machine rules.
        """
        if not self.can_transition_to(new_status):
            raise InvalidStateTransitionError(
                f"Cannot transition from {self.status} to {new_status}"
            )
        
        old_status = self.status
        self.status = new_status
        
        # Update reviewed fields if approved or rejected
        if new_status in [RequestState.APPROVED, RequestState.REJECTED]:
            from django.utils import timezone
            self.reviewed_by = user
            self.reviewed_at = timezone.now()
        
        self.save()
        return old_status, new_status
    
    def submit(self):
        """Submit the request for approval"""
        return self.transition_to(RequestState.SUBMITTED)
    
    def approve(self, user):
        """Approve the request"""
        return self.transition_to(RequestState.APPROVED, user)
    
    def reject(self, user, reason=''):
        """Reject the request"""
        self.rejection_reason = reason
        return self.transition_to(RequestState.REJECTED, user)
    
    def is_editable(self):
        """Check if request can be edited"""
        return self.status == RequestState.DRAFT
    
    def is_terminal_state(self):
        """Check if request is in a terminal state"""
        return self.status in [RequestState.APPROVED, RequestState.REJECTED]
    
    def delete(self, using=None, keep_parents=False):
        """Soft delete instead of hard delete"""
        self.is_deleted = True
        self.save()

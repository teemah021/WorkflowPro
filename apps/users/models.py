"""
Custom user model with role-based authentication.
"""
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from core.constants import UserRole


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Uses UUID as primary key for better security and scalability.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    role = models.CharField(
        max_length=20,
        choices=UserRole.CHOICES,
        default=UserRole.USER,
        db_index=True,
    )
    
    is_deleted = models.BooleanField(
        default=False,
        help_text='Soft delete flag'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['is_deleted']),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN
    
    @property
    def is_manager(self):
        return self.role == UserRole.MANAGER
    
    @property
    def is_regular_user(self):
        return self.role == UserRole.USER
    
    def can_approve_requests(self):
        """Check if user can approve requests"""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    def delete(self, using=None, keep_parents=False):
        """Soft delete instead of hard delete"""
        self.is_deleted = True
        self.save()

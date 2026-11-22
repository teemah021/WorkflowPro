"""
Centralized permission classes for the approval system.
"""
from rest_framework import permissions
from core.constants import UserRole


class IsAdmin(permissions.BasePermission):
    """
    Permission class for admin-only access.
    """
    def has_permission(self, request, view) -> bool:
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == UserRole.ADMIN
        )


class IsManager(permissions.BasePermission):
    """
    Permission class for manager-level access.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role in [UserRole.ADMIN, UserRole.MANAGER]
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners to edit.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for owner
        return bool(obj.creator == request.user)


class CanApproveRequest(permissions.BasePermission):
    """
    Permission to approve requests (managers and admins only).
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.can_approve_requests()
        )
    
    def has_object_permission(self, request, view, obj):
        # Managers can only approve requests assigned to them
        if request.user.role == UserRole.MANAGER:
            return bool(obj.assigned_to == request.user)
        
        # Admins can approve any request
        return bool(request.user.role == UserRole.ADMIN)


class CanViewOwnRequests(permissions.BasePermission):
    """
    Users can only view their own requests unless they are managers/admins.
    """
    def has_object_permission(self, request, view, obj):
        # Admins and managers can see all requests
        if request.user.role in [UserRole.ADMIN, UserRole.MANAGER]:
            return True
        
        # Users can only see their own requests
        return bool(obj.creator == request.user)

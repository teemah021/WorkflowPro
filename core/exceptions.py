"""
Custom exceptions for the approval system.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from .constants import ErrorCode


class ApprovalSystemException(Exception):
    """Base exception for the approval system"""
    pass


class InvalidStateTransitionError(ApprovalSystemException):
    """Raised when an invalid state transition is attempted"""
    pass


class PermissionDeniedError(ApprovalSystemException):
    """Raised when user doesn't have permission for an action"""
    pass


class ValidationError(ApprovalSystemException):
    """Raised when validation fails"""
    pass


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF that returns consistent error format.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Standard DRF exception
        return response
    
    # Handle custom exceptions
    if isinstance(exc, PermissionDeniedError):
        return Response(
            {
                'error': ErrorCode.PERMISSION_DENIED,
                'message': str(exc)
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    if isinstance(exc, InvalidStateTransitionError):
        return Response(
            {
                'error': ErrorCode.INVALID_STATE_TRANSITION,
                'message': str(exc)
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if isinstance(exc, ValidationError):
        return Response(
            {
                'error': ErrorCode.VALIDATION_ERROR,
                'message': str(exc)
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # For unhandled exceptions in production, don't expose details
    return Response(
        {
            'error': 'SERVER_ERROR',
            'message': 'An unexpected error occurred'
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

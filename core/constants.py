"""
Core constants for the approval system.
"""

# User Roles
class UserRole:
    ADMIN = 'admin'
    MANAGER = 'manager'
    USER = 'user'
    
    CHOICES = [
        (ADMIN, 'Admin'),
        (MANAGER, 'Manager'),
        (USER, 'User'),
    ]


# Request States
class RequestState:
    DRAFT = 'draft'
    SUBMITTED = 'submitted'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    
    CHOICES = [
        (DRAFT, 'Draft'),
        (SUBMITTED, 'Submitted'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]
    
    # Valid state transitions
    TRANSITIONS = {
        DRAFT: [SUBMITTED],
        SUBMITTED: [APPROVED, REJECTED],
        APPROVED: [],  # Terminal state
        REJECTED: [],  # Terminal state
    }


# Audit Action Types
class AuditAction:
    CREATE = 'create'
    UPDATE = 'update'
    DELETE = 'delete'
    APPROVE = 'approve'
    REJECT = 'reject'
    SUBMIT = 'submit'
    
    CHOICES = [
        (CREATE, 'Create'),
        (UPDATE, 'Update'),
        (DELETE, 'Delete'),
        (APPROVE, 'Approve'),
        (REJECT, 'Reject'),
        (SUBMIT, 'Submit'),
    ]


# Error codes
class ErrorCode:
    PERMISSION_DENIED = 'PERMISSION_DENIED'
    INVALID_STATE_TRANSITION = 'INVALID_STATE_TRANSITION'
    NOT_FOUND = 'NOT_FOUND'
    VALIDATION_ERROR = 'VALIDATION_ERROR'
    AUTHENTICATION_FAILED = 'AUTHENTICATION_FAILED'

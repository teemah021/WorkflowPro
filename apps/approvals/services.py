"""
Service layer for request approval workflow.
"""
from django.db import transaction
from apps.audit_logs.models import AuditLog
from apps.requests.models import Request
from core.constants import AuditAction, RequestState
from core.exceptions import InvalidStateTransitionError, PermissionDeniedError
from apps.notifications.services import NotificationService
from apps.users.models import User
from core.constants import UserRole



class RequestService:
    """
    Service class for managing request workflows.
    All business logic should go through this service.
    """

    @staticmethod
    @transaction.atomic
    def create_request(user, title, description):
        """
        Create a new request and assign an available manager.
        """

        # Find an active manager
        manager = User.objects.filter(
            role=UserRole.MANAGER,
            is_active=True,
            is_deleted=False
        ).first()

        # Create the request
        request_obj = Request.objects.create(
            title=title,
            description=description,
            creator=user,
            assigned_to=manager,
            status=RequestState.DRAFT
        )

        # Log the action
        AuditLog.log(
            actor=user,
            action=AuditAction.CREATE,
            content_object=request_obj,
            metadata={'title': title}
        )

        return request_obj

    @staticmethod
    @transaction.atomic
    def submit_request(request_obj, user):
        """
        Submit a request for approval.
        Only the creator can submit.
        """
        # Check permission
        if request_obj.creator != user:
            raise PermissionDeniedError("Only the creator can submit this request")
        
        # Check state
        if not request_obj.can_transition_to(RequestState.SUBMITTED):
            raise InvalidStateTransitionError(
                f"Cannot submit request in {request_obj.status} state"
            )
        
        old_status, new_status = request_obj.submit()
        
        # Log the action
        AuditLog.log(
            actor=user,
            action=AuditAction.SUBMIT,
            content_object=request_obj,
            metadata={
                'old_status': old_status,
                'new_status': new_status
            }
        )
        # Notify the assigned manager
        NotificationService.notify_request_submitted(request_obj)
        
        return request_obj
    
    
    
    
    @staticmethod
    @transaction.atomic
    def approve_request(request_obj, user, http_request=None):
        """
        Approve a request.
        Only managers/admins can approve.
        """
        # Check permission
        if not user.can_approve_requests():
            raise PermissionDeniedError("You don't have permission to approve requests")
        
        # Managers can only approve assigned requests
        if user.role == 'manager' and request_obj.assigned_to != user:
            raise PermissionDeniedError("You can only approve requests assigned to you")
        
        # Check state
        if not request_obj.can_transition_to(RequestState.APPROVED):
            raise InvalidStateTransitionError(
                f"Cannot approve request in {request_obj.status} state"
            )
        
        old_status, new_status = request_obj.approve(user)
        
        # Log the action
        AuditLog.log(
            actor=user,
            action=AuditAction.APPROVE,
            content_object=request_obj,
            metadata={
                'old_status': old_status,
                'new_status': new_status,
                'request_title': request_obj.title
            },
            request=http_request
        )
        
        # Create notification
        NotificationService.notify_request_approved(request_obj)
        
        return request_obj
    
    @staticmethod
    @transaction.atomic
    def reject_request(request_obj, user, reason='', http_request=None):
        """
        Reject a request.
        Only managers/admins can reject.
        """
        # Check permission
        if not user.can_approve_requests():
            raise PermissionDeniedError("You don't have permission to reject requests")
        
        # Managers can only reject assigned requests
        if user.role == 'manager' and request_obj.assigned_to != user:
            raise PermissionDeniedError("You can only reject requests assigned to you")
        
        # Check state
        if not request_obj.can_transition_to(RequestState.REJECTED):
            raise InvalidStateTransitionError(
                f"Cannot reject request in {request_obj.status} state"
            )
        
        old_status, new_status = request_obj.reject(user, reason)
        
        # Log the action
        AuditLog.log(
            actor=user,
            action=AuditAction.REJECT,
            content_object=request_obj,
            metadata={
                'old_status': old_status,
                'new_status': new_status,
                'reason': reason,
                'request_title': request_obj.title
            },
            request=http_request
        )
        NotificationService.notify_request_rejected(request_obj)
        
        return request_obj
    
    @staticmethod
    @transaction.atomic
    def update_request(request_obj, user, **updates):
        """
        Update a request (only in draft state).
        """
        # Check permission
        if request_obj.creator != user:
            raise PermissionDeniedError("Only the creator can update this request")
        
        # Check if editable
        if not request_obj.is_editable():
            raise InvalidStateTransitionError("Request can only be edited in draft state")
        
        # Update allowed fields
        allowed_fields = ['title', 'description']
        changed_fields = {}
        
        for field, value in updates.items():
            if field in allowed_fields:
                old_value = getattr(request_obj, field)
                setattr(request_obj, field, value)
                changed_fields[field] = {'old': old_value, 'new': value}
        
        request_obj.save()
        
        # Log the action
        AuditLog.log(
            actor=user,
            action=AuditAction.UPDATE,
            content_object=request_obj,
            metadata={'changes': changed_fields}
        )
        
        return request_obj
    
    @staticmethod
    @transaction.atomic
    def delete_request(request_obj, user):
        """
        Soft delete a request (only in draft state).
        """
        # Check permission
        if request_obj.creator != user and not user.is_admin:
            raise PermissionDeniedError("Only the creator or admin can delete this request")
        
        # Check if deletable
        if not request_obj.is_editable() and not user.is_admin:
            raise InvalidStateTransitionError("Only draft requests can be deleted")
        
        request_obj.delete()
        
        # Log the action
        AuditLog.log(
            actor=user,
            action=AuditAction.DELETE,
            content_object=request_obj,
            metadata={'title': request_obj.title}
        )
        
        return request_obj
    
    @staticmethod
    def get_user_requests(user):
        """
        Get requests visible to a user based on their role.
        """
        from django.db import models
        
        if user.is_admin:
            # Admins see all requests
            return Request.objects.filter(is_deleted=False)
        elif user.is_manager:
            # Managers see their own and assigned requests
            return Request.objects.filter(
                models.Q(creator=user) | models.Q(assigned_to=user),
                is_deleted=False
            )
        else:
            # Regular users see only their own requests
            return Request.objects.filter(creator=user, is_deleted=False)

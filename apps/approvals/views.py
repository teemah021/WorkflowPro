"""
API views for the approval system.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import models

from apps.requests.models import Request
from apps.users.models import User
from apps.audit_logs.models import AuditLog
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    RequestSerializer,
    RequestCreateSerializer,
    RequestUpdateSerializer,
    RequestApproveSerializer,
    RequestRejectSerializer,
    AuditLogSerializer
)
from .services import RequestService
from core.permissions import (
    IsAdmin,
    IsManager,
    CanApproveRequest,
    CanViewOwnRequests
)
from core.exceptions import (
    InvalidStateTransitionError,
    PermissionDeniedError
)
from core.constants import ErrorCode


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users.
    """
    queryset = User.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    def get_permissions(self):
        """Only admins can create, update, or delete users"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user information"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class RequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing requests.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter requests based on user role"""
        user = self.request.user
        
        if user.is_admin:
            return Request.objects.filter(is_deleted=False)
        elif user.is_manager:
            return Request.objects.filter(
                models.Q(creator=user) | models.Q(assigned_to=user),
                is_deleted=False
            )
        else:
            return Request.objects.filter(creator=user, is_deleted=False)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RequestCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return RequestUpdateSerializer
        elif self.action == 'approve':
            return RequestApproveSerializer
        elif self.action == 'reject':
            return RequestRejectSerializer
        return RequestSerializer
    
    def create(self, request):
        """Create a new request"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            request_obj = RequestService.create_request(
                user=request.user,
                title=serializer.validated_data['title'],
                description=serializer.validated_data['description']
            )
            
            response_serializer = RequestSerializer(request_obj)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': ErrorCode.VALIDATION_ERROR, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def update(self, request, pk=None):
        """Update a request (only in draft state)"""
        request_obj = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            updated_request = RequestService.update_request(
                request_obj=request_obj,
                user=request.user,
                **serializer.validated_data
            )
            
            response_serializer = RequestSerializer(updated_request)
            return Response(response_serializer.data)
        except PermissionDeniedError as e:
            return Response(
                {'error': ErrorCode.PERMISSION_DENIED, 'message': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except InvalidStateTransitionError as e:
            return Response(
                {'error': ErrorCode.INVALID_STATE_TRANSITION, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def destroy(self, request, pk=None):
        """Soft delete a request"""
        request_obj = self.get_object()
        
        try:
            RequestService.delete_request(request_obj, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PermissionDeniedError as e:
            return Response(
                {'error': ErrorCode.PERMISSION_DENIED, 'message': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanApproveRequest])
    def submit(self, request, pk=None):
        """Submit a request for approval"""
        request_obj = self.get_object()
        
        try:
            submitted_request = RequestService.submit_request(request_obj, request.user)
            serializer = RequestSerializer(submitted_request)
            return Response(serializer.data)
        except PermissionDeniedError as e:
            return Response(
                {'error': ErrorCode.PERMISSION_DENIED, 'message': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except InvalidStateTransitionError as e:
            return Response(
                {'error': ErrorCode.INVALID_STATE_TRANSITION, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanApproveRequest])
    def approve(self, request, pk=None):
        """Approve a request"""
        request_obj = self.get_object()
        
        try:
            approved_request = RequestService.approve_request(
                request_obj,
                request.user,
                request
            )
            serializer = RequestSerializer(approved_request)
            return Response(serializer.data)
        except PermissionDeniedError as e:
            return Response(
                {'error': ErrorCode.PERMISSION_DENIED, 'message': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except InvalidStateTransitionError as e:
            return Response(
                {'error': ErrorCode.INVALID_STATE_TRANSITION, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanApproveRequest])
    def reject(self, request, pk=None):
        """Reject a request"""
        request_obj = self.get_object()
        serializer = RequestRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            rejected_request = RequestService.reject_request(
                request_obj,
                request.user,
                reason=serializer.validated_data.get('reason', ''),
                http_request=request
            )
            response_serializer = RequestSerializer(rejected_request)
            return Response(response_serializer.data)
        except PermissionDeniedError as e:
            return Response(
                {'error': ErrorCode.PERMISSION_DENIED, 'message': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except InvalidStateTransitionError as e:
            return Response(
                {'error': ErrorCode.INVALID_STATE_TRANSITION, 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for audit logs.
    """
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsManager]
    
    def get_queryset(self):
        """Filter audit logs based on user role"""
        user = self.request.user
        
        if user.is_admin:
            # Admins see all logs
            return AuditLog.objects.all()
        elif user.is_manager:
            # Managers see logs related to their requests
            from django.contrib.contenttypes.models import ContentType
            request_ct = ContentType.objects.get_for_model(Request)
            
            # Get request IDs where manager is involved
            request_ids = Request.objects.filter(
                models.Q(creator=user) | models.Q(assigned_to=user)
            ).values_list('id', flat=True)
            
            return AuditLog.objects.filter(
                content_type=request_ct,
                object_id__in=request_ids
            )
        else:
            # Regular users don't have access
            return AuditLog.objects.none()

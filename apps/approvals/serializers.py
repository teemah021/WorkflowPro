"""
Serializers for the approval system API.
"""
from rest_framework import serializers
from apps.users.models import User
from apps.requests.models import Request
from apps.audit_logs.models import AuditLog


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'is_active',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating users"""
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
            'role'
        ]
    
    def create(self, validated_data):
        """Create user with hashed password"""
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class RequestSerializer(serializers.ModelSerializer):
    """Serializer for Request model"""
    creator = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    reviewed_by = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Request
        fields = [
            'id',
            'title',
            'description',
            'status',
            'status_display',
            'creator',
            'assigned_to',
            'reviewed_by',
            'reviewed_at',
            'rejection_reason',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'status',
            'creator',
            'assigned_to',
            'reviewed_by',
            'reviewed_at',
            'rejection_reason',
            'created_at',
            'updated_at'
        ]


class RequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating requests"""
    
    class Meta:
        model = Request
        fields = ['title', 'description']
    
    def validate_title(self, value):
        """Validate title is not empty"""
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value


class RequestUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating requests"""
    
    class Meta:
        model = Request
        fields = ['title', 'description']


class RequestApproveSerializer(serializers.Serializer):
    """Serializer for approving requests"""
    pass  # No additional fields needed


class RequestRejectSerializer(serializers.Serializer):
    """Serializer for rejecting requests"""
    reason = serializers.CharField(required=False, allow_blank=True, max_length=1000)


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog model"""
    actor = UserSerializer(read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id',
            'actor',
            'action',
            'action_display',
            'content_type',
            'object_id',
            'metadata',
            'ip_address',
            'timestamp'
        ]
        read_only_fields = '__all__'

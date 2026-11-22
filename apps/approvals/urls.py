"""
URL configuration for API endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.approvals.views import UserViewSet, RequestViewSet, AuditLogViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'requests', RequestViewSet, basename='request')
router.register(r'audit-logs', AuditLogViewSet, basename='auditlog')

urlpatterns = [
    path('v1/', include(router.urls)),
]

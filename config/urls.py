
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

from core.views import (
    dashboard,
    request_create,
    my_requests,
    approvals,
    approve_request_view,
    reject_request_view,
    audit_logs,
    request_detail,
    request_edit,
    request_delete,
    notifications,
    mark_notification_read,
    export_audit_logs,
    register,
)

urlpatterns = [
    # Custom Authentication
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='login.html'),
        name='login'
    ),
    path(
        'register/',
        register,
        name='register'
    ),
    # Password Reset
path(
    'password-reset/',
    auth_views.PasswordResetView.as_view(
        template_name='password_reset.html'
    ),
    name='password_reset'
),
path(
    'password-reset/done/',
    auth_views.PasswordResetDoneView.as_view(
        template_name='password_reset_done.html'
    ),
    name='password_reset_done'
),
path(
    'reset/<uidb64>/<token>/',
    auth_views.PasswordResetConfirmView.as_view(
        template_name='password_reset_confirm.html'
    ),
    name='password_reset_confirm'
),
path(
    'reset/done/',
    auth_views.PasswordResetCompleteView.as_view(
        template_name='password_reset_complete.html'
    ),
    name='password_reset_complete'
),
    
    # Dashboard
    path('', dashboard, name='dashboard'),

    # Request pages
    path('requests/create/', request_create, name='request_create'),
    
    path('requests/', my_requests, name='my_requests'),
    path('requests/<uuid:request_id>/edit/', request_edit, name='request_edit'),
    path('requests/<uuid:request_id>/delete/', request_delete, name='request_delete'),
    path('notifications/', notifications, name='notifications'),
    path(
    'notifications/<uuid:notification_id>/read/',
    mark_notification_read,
    name='mark_notification_read'
),

    # Approval page
    path('approvals/', approvals, name='approvals'),
    path(
    'requests/<uuid:request_id>/approve/',
    approve_request_view,
    name='approve_request'
),

    path(
        'requests/<uuid:request_id>/reject/',
        reject_request_view,
        name='reject_request'
    ),
    path('audit-logs/', audit_logs, name='audit_logs'),
    path(
    'audit-logs/export/',
    export_audit_logs,
    name='export_audit_logs'
),
    path('requests/<uuid:request_id>/', request_detail, name='request_detail'),
    path(
    'logout/',
    auth_views.LogoutView.as_view(),
    name='logout'
),

    # Django administration
    path('admin/', admin.site.urls),

    # API routes
    path('api/', include('apps.approvals.urls')),
    path('api-auth/', include('rest_framework.urls')),
]

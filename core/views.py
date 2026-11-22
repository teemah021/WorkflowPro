
from django.shortcuts import render, redirect
from apps.audit_logs.models import AuditLog
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.db import transaction
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from apps.approvals.services import RequestService
from core.exceptions import PermissionDeniedError, InvalidStateTransitionError
from apps.notifications.models import Notification
from django.db.models import Q
from django.core.paginator import Paginator
import csv
from django.http import HttpResponse
from apps.users.forms import UserRegistrationForm


from apps.requests.models import Request
from core.constants import UserRole, RequestState


@login_required
def dashboard(request):

    # Get requests based on the logged-in user's role
    if request.user.role == UserRole.ADMIN:
        requests = Request.objects.filter(is_deleted=False)

    elif request.user.role == UserRole.MANAGER:
        requests = Request.objects.filter(
            assigned_to=request.user,
            is_deleted=False
        )

    else:
        requests = Request.objects.filter(
            creator=request.user,
            is_deleted=False
        )

    # Calculate dashboard statistics
    total_requests = requests.count()

    pending_approvals = requests.filter(
        status=RequestState.SUBMITTED
    ).count()

    completed_requests = requests.filter(
        status__in=[
            RequestState.APPROVED,
            RequestState.REJECTED
        ]
    ).count()

    # Get the latest five requests
    recent_requests = requests.order_by('-created_at')[:5]

    context = {
        'total_requests': total_requests,
        'pending_approvals': pending_approvals,
        'completed_requests': completed_requests,
        'recent_requests': recent_requests,
    }

    return render(request, 'dashboard.html', context)



@login_required
@require_http_methods(["GET", "POST"])
def request_create(request):
    errors = []
    title_value = ""
    description_value = ""

    if request.method == "POST":
        title_value = request.POST.get("title", "").strip()
        description_value = request.POST.get("description", "").strip()
        action = request.POST.get("action", "draft")

        if not title_value:
            errors.append("Please enter a request title.")

        if not description_value:
            errors.append("Please enter a description.")

        if action not in ["draft", "submit"]:
            errors.append("Invalid request action.")

        if not errors:
            with transaction.atomic():

                new_request = RequestService.create_request(
                    user=request.user,
                    title=title_value,
                    description=description_value
                )

                if action == "submit":
                    RequestService.submit_request(
                        request_obj=new_request,
                        user=request.user
                    )

            return redirect("dashboard")

    context = {
        "errors": errors,
        "title_value": title_value,
        "description_value": description_value,
    }

    return render(request, "request_form.html", context)





@login_required
def my_requests(request):

    # Get requests based on the logged-in user's role
    if request.user.role == UserRole.ADMIN:
        requests = Request.objects.filter(is_deleted=False)

    elif request.user.role == UserRole.MANAGER:
        requests = Request.objects.filter(
            assigned_to=request.user,
            is_deleted=False
        )

    else:
        requests = Request.objects.filter(
            creator=request.user,
            is_deleted=False
        )

    # Search requests by title
    search_query = request.GET.get("search", "").strip()

    if search_query:
        requests = requests.filter(
            title__icontains=search_query
        )

    # Filter requests by status
    status_filter = request.GET.get("status", "").strip()

    valid_statuses = [
        RequestState.DRAFT,
        RequestState.SUBMITTED,
        RequestState.APPROVED,
        RequestState.REJECTED,
    ]

    if status_filter in valid_statuses:
        requests = requests.filter(status=status_filter)

    # Calculate statistics from all visible requests
    if request.user.role == UserRole.ADMIN:
        all_requests = Request.objects.filter(is_deleted=False)

    elif request.user.role == UserRole.MANAGER:
        all_requests = Request.objects.filter(
            assigned_to=request.user,
            is_deleted=False
        )

    else:
        all_requests = Request.objects.filter(
            creator=request.user,
            is_deleted=False
        )

    total_requests = all_requests.count()

    pending_requests = all_requests.filter(
        status=RequestState.SUBMITTED
    ).count()

    completed_requests = all_requests.filter(
        status__in=[
            RequestState.APPROVED,
            RequestState.REJECTED
        ]
    ).count()

    context = {
        "requests": requests.order_by("-created_at"),
        "total_requests": total_requests,
        "pending_requests": pending_requests,
        "completed_requests": completed_requests,
        "search_query": search_query,
        "status_filter": status_filter,
    }

    return render(request, "my_requests.html", context)


@login_required
def approvals(request):

    # Only admins and managers can access this page
    if not request.user.can_approve_requests():
        raise PermissionDenied

    # Get submitted requests
    if request.user.is_admin:
        pending_requests = Request.objects.filter(
            status=RequestState.SUBMITTED,
            is_deleted=False
        )

    else:
        pending_requests = Request.objects.filter(
            assigned_to=request.user,
            status=RequestState.SUBMITTED,
            is_deleted=False
        )

    context = {
        "pending_requests": pending_requests.order_by("-created_at"),
        "total_pending": pending_requests.count(),
    }

    return render(request, "approvals.html", context)



@login_required
@require_POST
def approve_request_view(request, request_id):
    if not request.user.can_approve_requests():
        raise PermissionDenied

    request_obj = get_object_or_404(
        Request,
        id=request_id,
        is_deleted=False
    )

    try:
        RequestService.approve_request(
            request_obj,
            request.user,
            http_request=request
        )
        messages.success(request, "Request approved successfully.")

    except (PermissionDeniedError, InvalidStateTransitionError) as error:
        messages.error(request, str(error))

    return redirect("approvals")


@login_required
@require_POST
def reject_request_view(request, request_id):
    if not request.user.can_approve_requests():
        raise PermissionDenied

    request_obj = get_object_or_404(
        Request,
        id=request_id,
        is_deleted=False
    )

    reason = request.POST.get("reason", "").strip()

    if not reason:
        messages.error(request, "Please provide a reason for rejecting this request.")
        return redirect("approvals")

    try:
        RequestService.reject_request(
            request_obj,
            request.user,
            reason=reason,
            http_request=request
        )
        messages.success(request, "Request rejected successfully.")

    except (PermissionDeniedError, InvalidStateTransitionError) as error:
        messages.error(request, str(error))

    return redirect("approvals")
approve_request_view,
reject_request_view,



@login_required
def audit_logs(request):
    # Only administrators and managers can access audit logs
    if not request.user.can_approve_requests():
        raise PermissionDenied

    logs = AuditLog.objects.select_related(
        'actor',
        'content_type'
    ).order_by('-timestamp')

    # Search by username or action
    search_query = request.GET.get('search', '').strip()

    if search_query:
        logs = logs.filter(
            Q(actor__username__icontains=search_query) |
            Q(action__icontains=search_query)
        )

    # Filter by action
    action_filter = request.GET.get('action', '')

    if action_filter:
        logs = logs.filter(action=action_filter)

    # Pagination: 10 logs per page
    paginator = Paginator(logs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'logs': page_obj,
        'page_obj': page_obj,
        'total_logs': paginator.count,
        'search_query': search_query,
        'action_filter': action_filter,
        'action_choices': AuditLog._meta.get_field('action').choices,
    }

    return render(request, 'audit_logs.html', context)



@login_required
def export_audit_logs(request):
    # Only administrators and managers can export audit logs
    if not request.user.can_approve_requests():
        raise PermissionDenied

    logs = AuditLog.objects.select_related(
        'actor',
        'content_type'
    ).order_by('-timestamp')

    # Apply the same search filter
    search_query = request.GET.get('search', '').strip()

    if search_query:
        logs = logs.filter(
            Q(actor__username__icontains=search_query) |
            Q(action__icontains=search_query)
        )

    # Apply the same action filter
    action_filter = request.GET.get('action', '')

    if action_filter:
        logs = logs.filter(action=action_filter)

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        'attachment; filename="audit_logs.csv"'
    )

    writer = csv.writer(response)

    # CSV headings
    writer.writerow([
        'User',
        'Action',
        'Related Object',
        'Date',
        'Time',
    ])

    # CSV records
    for log in logs:
        writer.writerow([
            log.actor.username if log.actor else 'System',
            log.get_action_display(),
            str(log.content_object) if log.content_object else 'No related object',
            log.timestamp.strftime('%d %b %Y'),
            log.timestamp.strftime('%I:%M %p'),
        ])

    return response

@login_required
def request_detail(request, request_id):
    request_obj = get_object_or_404(
        RequestService.get_user_requests(request.user).filter(is_deleted=False),
        id=request_id
    )

    context = {
        "item": request_obj,
    }

    return render(request, "request_detail.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def request_edit(request, request_id):
    request_obj = get_object_or_404(
        Request,
        id=request_id,
        is_deleted=False
    )

    errors = []

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()

        if not title:
            errors.append("Please enter a request title.")

        if not description:
            errors.append("Please enter a description.")

        if not errors:
            try:
                RequestService.update_request(
                    request_obj=request_obj,
                    user=request.user,
                    title=title,
                    description=description
                )

                messages.success(
                    request,
                    "Request updated successfully."
                )

                return redirect("my_requests")

            except PermissionDeniedError:
                raise PermissionDenied

            except InvalidStateTransitionError as error:
                messages.error(request, str(error))
                return redirect("my_requests")

    context = {
        "item": request_obj,
        "errors": errors,
    }

    return render(request, "request_edit.html", context)


@login_required
@require_POST
def request_delete(request, request_id):
    request_obj = get_object_or_404(
        Request,
        id=request_id,
        is_deleted=False
    )

    try:
        RequestService.delete_request(
            request_obj=request_obj,
            user=request.user
        )

        messages.success(
            request,
            "Request deleted successfully."
        )

    except PermissionDeniedError:
        raise PermissionDenied

    except InvalidStateTransitionError as error:
        messages.error(request, str(error))

    return redirect("my_requests")



@login_required
def notifications(request):
    user_notifications = Notification.objects.filter(
        recipient=request.user
    )

    context = {
        'notifications': user_notifications,
        'unread_count': user_notifications.filter(is_read=False).count(),
    }

    return render(request, 'notifications.html', context)


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )

    notification.is_read = True
    notification.save(update_fields=['is_read'])

    messages.success(request, "Notification marked as read.")

    return redirect('notifications')



def register(request):
    # Redirect authenticated users to the dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()

            messages.success(
                request,
                "Your account has been created successfully. You can now log in."
            )

            return redirect('login')

    else:
        form = UserRegistrationForm()

    context = {
        'form': form,
    }

    return render(request, 'register.html', context)
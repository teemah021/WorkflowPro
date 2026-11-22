
"""
Service layer for managing user notifications.
"""

from apps.notifications.models import Notification


class NotificationService:

    @staticmethod
    def create_notification(
        recipient,
        title,
        message,
        notification_type='general',
        related_request=None
    ):
        """
        Create a notification for a user.
        """

        return Notification.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            related_request=related_request
        )

    @staticmethod
    def notify_request_submitted(request_obj):
        """
        Notify the assigned manager when a request is submitted.
        """

        if request_obj.assigned_to:
            return NotificationService.create_notification(
                recipient=request_obj.assigned_to,
                title="New Request Submitted",
                message=(
                    f"{request_obj.creator.username} submitted "
                    f"'{request_obj.title}' for approval."
                ),
                notification_type='submitted',
                related_request=request_obj
            )

        return None

    @staticmethod
    def notify_request_approved(request_obj):
        """
        Notify the request creator when their request is approved.
        """

        return NotificationService.create_notification(
            recipient=request_obj.creator,
            title="Request Approved",
            message=(
                f"Your request '{request_obj.title}' has been approved."
            ),
            notification_type='approved',
            related_request=request_obj
        )

    @staticmethod
    def notify_request_rejected(request_obj):
        """
        Notify the request creator when their request is rejected.
        """

        return NotificationService.create_notification(
            recipient=request_obj.creator,
            title="Request Rejected",
            message=(
                f"Your request '{request_obj.title}' was rejected. "
                f"Reason: {request_obj.rejection_reason}"
            ),
            notification_type='rejected',
            related_request=request_obj
        )

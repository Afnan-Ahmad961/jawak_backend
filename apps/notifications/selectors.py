"""Read-only queries for notifications."""

from apps.notifications.models import Notification


def notifications_for_user(*, user, unread_only=False):
    qs = Notification.objects.filter(recipient=user)
    if unread_only:
        qs = qs.filter(is_read=False)
    return qs


def notification_get(*, notification_id, user):
    return Notification.objects.get(id=notification_id, recipient=user)

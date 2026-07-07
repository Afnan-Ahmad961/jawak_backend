"""Write operations for notifications.

`notify` / `notify_many` are called explicitly from other apps' services at
the points where something noteworthy happens, keeping the notification flow
traceable rather than hidden behind signals.
"""

from django.contrib.contenttypes.models import ContentType

from apps.notifications.models import Notification


def _target_fields(target):
    if target is None:
        return None, None
    return ContentType.objects.get_for_model(target.__class__), target.pk


def notify(*, recipient, notification_type, message, target=None):
    content_type, object_id = _target_fields(target)
    return Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        message=message,
        content_type=content_type,
        object_id=object_id,
    )


def notify_many(*, recipients, notification_type, message, target=None):
    content_type, object_id = _target_fields(target)
    notifications = [
        Notification(
            recipient=recipient,
            notification_type=notification_type,
            message=message,
            content_type=content_type,
            object_id=object_id,
        )
        for recipient in recipients
    ]
    if not notifications:
        return []
    return Notification.objects.bulk_create(notifications)


def notification_mark_read(*, notification):
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=['is_read'])
    return notification


def notifications_mark_all_read(*, user):
    return Notification.objects.filter(recipient=user, is_read=False).update(
        is_read=True
    )

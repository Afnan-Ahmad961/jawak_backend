from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Notification(models.Model):
    """An in-app notification for a user.

    Delivery is DB-only and synchronous for now; email/push/WebSocket
    channels can layer on later. The optional generic relation
    (`content_type` + `object_id`) points at whatever the notification is
    about (a bid, order, request, review, dispute, message) without this app
    holding a foreign key to every other app.
    """

    class Type(models.TextChoices):
        MATCHING_REQUEST = 'matching_request', 'Matching request'
        NEW_BID = 'new_bid', 'New bid'
        BID_ACCEPTED = 'bid_accepted', 'Bid accepted'
        PRODUCTION_UPDATE = 'production_update', 'Production update'
        NEW_REVIEW = 'new_review', 'New review'
        NEW_MESSAGE = 'new_message', 'New message'
        DISPUTE_OPENED = 'dispute_opened', 'Dispute opened'
        DISPUTE_RESOLVED = 'dispute_resolved', 'Dispute resolved'

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    notification_type = models.CharField(max_length=32, choices=Type.choices)
    message = models.CharField(max_length=255)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True
    )
    object_id = models.PositiveBigIntegerField(null=True, blank=True)
    target = GenericForeignKey('content_type', 'object_id')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
        ]

    def __str__(self):
        return f'{self.get_notification_type_display()} -> {self.recipient_id}'

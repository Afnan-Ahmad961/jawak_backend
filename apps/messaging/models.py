from django.conf import settings
from django.db import models

from apps.design_requests.models import DesignRequest
from apps.vendors.models import VendorProfile


class Conversation(models.Model):
    """A negotiation thread between a request's client and one vendor.

    Keyed on (design_request, vendor): the two participants are the request's
    client and the vendor's user. One thread per client-vendor pair per request.
    """

    design_request = models.ForeignKey(
        DesignRequest, on_delete=models.CASCADE, related_name='conversations'
    )
    vendor = models.ForeignKey(
        VendorProfile, on_delete=models.CASCADE, related_name='conversations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['design_request', 'vendor'],
                name='unique_conversation_per_request_vendor',
            )
        ]

    def __str__(self):
        return f'Conversation #{self.pk} on request {self.design_request_id}'


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
    )
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Message #{self.pk} in conversation {self.conversation_id}'

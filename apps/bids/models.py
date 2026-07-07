from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.design_requests.models import DesignRequest
from apps.vendors.models import VendorProfile


class Bid(models.Model):
    """A vendor's proposal (price + timeline) on a design request."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'
        WITHDRAWN = 'withdrawn', 'Withdrawn'

    design_request = models.ForeignKey(
        DesignRequest,
        on_delete=models.CASCADE,
        related_name='bids',
    )
    vendor = models.ForeignKey(
        VendorProfile,
        on_delete=models.CASCADE,
        related_name='bids',
    )
    proposed_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    delivery_days = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    message = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['design_request', 'vendor'],
                name='unique_bid_per_vendor_per_request',
            )
        ]

    def __str__(self):
        return f'Bid #{self.pk} on request {self.design_request_id}'

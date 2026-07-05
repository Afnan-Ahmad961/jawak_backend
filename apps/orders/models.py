from django.conf import settings
from django.db import models

from apps.bids.models import Bid
from apps.common.validators import IMAGE_VALIDATORS
from apps.design_requests.models import DesignRequest
from apps.vendors.models import VendorProfile


class Order(models.Model):
    """An active contract created when a client accepts a bid.

    Snapshots the awarded price so later edits to the bid can't rewrite
    history, and tracks the manufacturing progress via `current_stage`
    (the latest `ProductionUpdate`).
    """

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        DISPUTED = 'disputed', 'Disputed'

    class Stage(models.TextChoices):
        SOURCING = 'sourcing', 'Fabric Sourced'
        CUTTING = 'cutting', 'Cutting'
        SEWING = 'sewing', 'Sewing'
        QUALITY_CHECK = 'quality_check', 'Quality Check'
        SHIPPED = 'shipped', 'Shipped'
        DELIVERED = 'delivered', 'Delivered'

    # Order in which production stages may be advanced. Used to enforce
    # forward-only transitions.
    STAGE_ORDER = [
        Stage.SOURCING,
        Stage.CUTTING,
        Stage.SEWING,
        Stage.QUALITY_CHECK,
        Stage.SHIPPED,
        Stage.DELIVERED,
    ]

    bid = models.OneToOneField(Bid, on_delete=models.PROTECT, related_name='order')
    design_request = models.ForeignKey(
        DesignRequest, on_delete=models.PROTECT, related_name='orders'
    )
    vendor = models.ForeignKey(
        VendorProfile, on_delete=models.PROTECT, related_name='orders'
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='orders'
    )
    final_price = models.DecimalField(max_digits=12, decimal_places=2)
    deadline = models.DateField(null=True, blank=True)
    current_stage = models.CharField(
        max_length=20, choices=Stage.choices, default=Stage.SOURCING
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order #{self.pk} ({self.get_status_display()})'


class ProductionUpdate(models.Model):
    """A vendor-posted milestone update on an order's manufacturing progress."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='production_updates'
    )
    stage = models.CharField(max_length=20, choices=Order.Stage.choices)
    note = models.TextField(blank=True)
    image = models.ImageField(
        upload_to='production_updates/',
        null=True,
        blank=True,
        validators=IMAGE_VALIDATORS,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='production_updates',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_stage_display()} on order {self.order_id}'

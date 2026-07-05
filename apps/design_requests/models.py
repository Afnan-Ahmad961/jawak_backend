from django.conf import settings
from django.db import models

from apps.common.validators import IMAGE_VALIDATORS


class DesignRequest(models.Model):
    """A client's custom-apparel job posting that vendors bid on."""

    class ApparelType(models.TextChoices):
        HOODIE = 'hoodie', 'Hoodie'
        JACKET = 'jacket', 'Jacket'
        TSHIRT = 'tshirt', 'T-Shirt'
        FOOTBALL_KIT = 'football_kit', 'Football Kit'
        OTHER = 'other', 'Other'

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'            # accepting bids
        AWARDED = 'awarded', 'Awarded'   # a bid was accepted
        CLOSED = 'closed', 'Closed'
        CANCELLED = 'cancelled', 'Cancelled'

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='design_requests',
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    apparel_type = models.CharField(max_length=20, choices=ApparelType.choices)
    quantity = models.PositiveIntegerField()
    material = models.CharField(max_length=255, blank=True)
    # Structured spec: list of size/quantity breakdowns,
    # e.g. [{"size": "M", "quantity": 20}, {"size": "L", "quantity": 30}].
    sizes = models.JSONField(default=list, blank=True)
    color_preferences = models.CharField(max_length=255, blank=True)
    deadline = models.DateField(null=True, blank=True)
    # Uploaded to cloud storage (S3 in production, local media in dev);
    # `.url` yields the storage URL.
    design_image = models.ImageField(
        upload_to='design_requests/',
        null=True,
        blank=True,
        validators=IMAGE_VALIDATORS,
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.get_apparel_type_display()})'


class DesignReferenceImage(models.Model):
    """An artwork/logo/graphic element to be applied to the article.

    A request can carry several of these (the emblem, sponsor logos, a print
    to place on the back, etc.) alongside the main `design_image` mockup.
    """

    design_request = models.ForeignKey(
        DesignRequest,
        on_delete=models.CASCADE,
        related_name='reference_images',
    )
    image = models.ImageField(
        upload_to='design_requests/references/',
        validators=IMAGE_VALIDATORS,
    )
    label = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.label or f'Reference image #{self.pk}'

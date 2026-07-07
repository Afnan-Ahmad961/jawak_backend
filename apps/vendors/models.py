from django.conf import settings
from django.db import models

from apps.common.validators import IMAGE_VALIDATORS


class VendorProfile(models.Model):
    """Manufacturer profile attached to a vendor user.

    Holds the factory-facing details clients compare when reviewing bids:
    what the vendor makes, where they are, and how much they can produce.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vendor_profile',
    )
    company_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)
    # e.g. ["hoodies", "jackets", "football kits"]
    specialties = models.JSONField(default=list, blank=True)
    # Approximate production capacity (units per month).
    capacity = models.PositiveIntegerField(null=True, blank=True)
    # Denormalized rating aggregates, recomputed when a review lands (see
    # apps.reviews.services). Kept here so the vendor comparison board can
    # sort/filter without aggregating reviews on every request.
    avg_rating = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True
    )
    review_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['company_name']

    def __str__(self):
        return self.company_name


class PortfolioItem(models.Model):
    """A past-work sample showcased on a vendor's profile."""

    vendor = models.ForeignKey(
        VendorProfile, on_delete=models.CASCADE, related_name='portfolio_items'
    )
    image = models.ImageField(
        upload_to='portfolio/', validators=IMAGE_VALIDATORS
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

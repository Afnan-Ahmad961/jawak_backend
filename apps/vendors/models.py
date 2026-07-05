from django.conf import settings
from django.db import models


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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['company_name']

    def __str__(self):
        return self.company_name

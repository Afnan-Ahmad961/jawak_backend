from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.orders.models import Order


class Review(models.Model):
    """Feedback left by one party on the other after a completed order.

    Both directions are allowed (client rates vendor, vendor rates client),
    one per reviewer per order.
    """

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='reviews'
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_written',
    )
    reviewee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_received',
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'reviewer'],
                name='unique_review_per_reviewer_per_order',
            )
        ]

    def __str__(self):
        return f'Review {self.rating}/5 on order {self.order_id}'

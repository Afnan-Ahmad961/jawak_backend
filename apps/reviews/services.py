"""Write operations (business logic) for reviews."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Avg, Count

from apps.orders.models import Order
from apps.reviews.models import Review
from apps.vendors.models import VendorProfile


def _recompute_vendor_rating(*, vendor):
    """Refresh a vendor's denormalized rating aggregates from its reviews."""
    stats = Review.objects.filter(reviewee=vendor.user).aggregate(
        avg=Avg('rating'), count=Count('id')
    )
    avg = stats['avg']
    vendor.avg_rating = (
        Decimal(avg).quantize(Decimal('0.01')) if avg is not None else None
    )
    vendor.review_count = stats['count']
    vendor.save(update_fields=['avg_rating', 'review_count', 'updated_at'])


@transaction.atomic
def review_create(*, order, reviewer, rating, comment=''):
    if order.status != Order.Status.COMPLETED:
        raise ValidationError('You can only review a completed order.')

    if reviewer.id == order.client_id:
        reviewee = order.vendor.user
    elif reviewer.id == order.vendor.user_id:
        reviewee = order.client
    else:
        raise ValidationError('Only the order participants can leave a review.')

    review = Review(
        order=order, reviewer=reviewer, reviewee=reviewee, rating=rating, comment=comment
    )
    # full_clean enforces the one-review-per-reviewer-per-order constraint.
    review.full_clean()
    review.save()

    # If the vendor was reviewed, refresh their profile aggregates.
    vendor = VendorProfile.objects.filter(user=reviewee).first()
    if vendor is not None:
        _recompute_vendor_rating(vendor=vendor)

    from apps.notifications.services import notify

    notify(
        recipient=reviewee,
        notification_type='new_review',
        message=f'You received a {rating}/5 review on order #{order.pk}.',
        target=review,
    )
    return review

"""Read-only queries for reviews."""

from apps.reviews.models import Review


def reviews_list(*, vendor=None, order=None, reviewee=None):
    qs = Review.objects.select_related('reviewer', 'reviewee', 'order').all()
    if vendor is not None:
        qs = qs.filter(reviewee=vendor.user)
    if order is not None:
        qs = qs.filter(order=order)
    if reviewee is not None:
        qs = qs.filter(reviewee=reviewee)
    return qs

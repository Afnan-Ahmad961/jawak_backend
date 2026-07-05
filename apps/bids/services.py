"""Write operations (business logic) for bids."""

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.bids.models import Bid
from apps.design_requests.models import DesignRequest


def bid_place(*, vendor, design_request, proposed_price, delivery_days, message=''):
    if design_request.status != DesignRequest.Status.OPEN:
        raise ValidationError('This request is not open for bidding.')

    bid = Bid(
        vendor=vendor,
        design_request=design_request,
        proposed_price=proposed_price,
        delivery_days=delivery_days,
        message=message,
    )
    # full_clean enforces the one-bid-per-vendor-per-request constraint.
    bid.full_clean()
    bid.save()
    return bid


@transaction.atomic
def bid_accept(*, bid):
    """Accept a bid: award the request, and reject all sibling bids."""
    design_request = bid.design_request
    if design_request.status != DesignRequest.Status.OPEN:
        raise ValidationError('This request is no longer open.')

    bid.status = Bid.Status.ACCEPTED
    bid.save(update_fields=['status', 'updated_at'])

    Bid.objects.filter(design_request=design_request).exclude(id=bid.id).update(
        status=Bid.Status.REJECTED
    )

    design_request.status = DesignRequest.Status.AWARDED
    design_request.save(update_fields=['status', 'updated_at'])
    return bid


def bid_reject(*, bid):
    bid.status = Bid.Status.REJECTED
    bid.save(update_fields=['status', 'updated_at'])
    return bid

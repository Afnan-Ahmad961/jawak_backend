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

    # Notify the client that a new bid arrived on their request.
    from apps.notifications.services import notify

    notify(
        recipient=design_request.client,
        notification_type='new_bid',
        message=f'New bid on "{design_request.title}".',
        target=bid,
    )
    return bid


@transaction.atomic
def bid_accept(*, bid):
    """Accept a bid: award the request, reject siblings, and open an order.

    Re-reads the request row with ``select_for_update`` so two concurrent
    accepts can't both pass the OPEN check and produce two awarded bids /
    two orders.
    """
    from apps.orders.services import order_create_from_bid

    design_request = DesignRequest.objects.select_for_update().get(
        id=bid.design_request_id
    )
    if design_request.status != DesignRequest.Status.OPEN:
        raise ValidationError('This request is no longer open.')

    bid.status = Bid.Status.ACCEPTED
    bid.save(update_fields=['status', 'updated_at'])

    Bid.objects.filter(design_request=design_request).exclude(id=bid.id).update(
        status=Bid.Status.REJECTED
    )

    design_request.status = DesignRequest.Status.AWARDED
    design_request.save(update_fields=['status', 'updated_at'])

    order_create_from_bid(bid=bid)
    return bid


def bid_reject(*, bid):
    bid.status = Bid.Status.REJECTED
    bid.save(update_fields=['status', 'updated_at'])
    return bid


def bid_withdraw(*, bid):
    """Withdraw a pending bid (vendor-initiated)."""
    if bid.status != Bid.Status.PENDING:
        raise ValidationError('Only a pending bid can be withdrawn.')
    bid.status = Bid.Status.WITHDRAWN
    bid.save(update_fields=['status', 'updated_at'])
    return bid

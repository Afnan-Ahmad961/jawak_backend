"""Write operations (business logic) for orders and production tracking."""

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.orders.models import Order, ProductionUpdate


def order_create_from_bid(*, bid):
    """Create the order for an accepted bid.

    Called from within `bids.services.bid_accept` (inside its transaction),
    so this must not be invoked for a bid that isn't actually accepted.
    """
    design_request = bid.design_request
    deadline = timezone.now().date() + timedelta(days=bid.delivery_days)

    order = Order(
        bid=bid,
        design_request=design_request,
        vendor=bid.vendor,
        client=design_request.client,
        final_price=bid.proposed_price,
        deadline=deadline,
    )
    order.full_clean(exclude=['current_stage', 'status'])
    order.save()

    # Let the vendor know they won the job.
    from apps.notifications.services import notify

    notify(
        recipient=bid.vendor.user,
        notification_type='bid_accepted',
        message=f'Your bid on "{design_request.title}" was accepted.',
        target=order,
    )
    return order


@transaction.atomic
def production_update_add(*, order, stage, user, note='', image=None):
    """Post a production update, advancing the order's current stage.

    Enforces forward-only stage transitions: the new stage must be at or
    after the order's current stage in `Order.STAGE_ORDER`.
    """
    if order.status != Order.Status.ACTIVE:
        raise ValidationError('Production updates are only allowed on active orders.')

    stage_order = Order.STAGE_ORDER
    if stage not in stage_order:
        raise ValidationError('Unknown production stage.')
    if stage_order.index(stage) < stage_order.index(order.current_stage):
        raise ValidationError('Production stage cannot move backwards.')

    update = ProductionUpdate(
        order=order, stage=stage, note=note, image=image, created_by=user
    )
    update.full_clean()
    update.save()

    order.current_stage = stage
    order.save(update_fields=['current_stage', 'updated_at'])

    from apps.notifications.services import notify

    notify(
        recipient=order.client,
        notification_type='production_update',
        message=f'Order #{order.pk}: {update.get_stage_display()}.',
        target=order,
    )
    return update


def order_confirm_delivery(*, order):
    """Client confirms the delivered order, completing it and unlocking reviews."""
    if order.status != Order.Status.ACTIVE:
        raise ValidationError('Only an active order can be confirmed.')
    if order.current_stage != Order.Stage.DELIVERED:
        raise ValidationError('The order has not been marked delivered yet.')

    order.status = Order.Status.COMPLETED
    order.save(update_fields=['status', 'updated_at'])
    return order

"""Write operations (business logic) for disputes."""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q

from apps.disputes.models import Dispute
from apps.orders.models import Order

User = get_user_model()


def _admin_users():
    return User.objects.filter(Q(role=User.Role.ADMIN) | Q(is_staff=True))


@transaction.atomic
def dispute_open(*, order, raised_by, reason, description=''):
    if raised_by.id not in (order.client_id, order.vendor.user_id):
        raise ValidationError('Only the order participants can raise a dispute.')
    if order.status not in (Order.Status.ACTIVE, Order.Status.COMPLETED):
        raise ValidationError('This order cannot be disputed in its current state.')

    dispute = Dispute(
        order=order, raised_by=raised_by, reason=reason, description=description
    )
    dispute.full_clean()
    dispute.save()

    order.status = Order.Status.DISPUTED
    order.save(update_fields=['status', 'updated_at'])

    from apps.notifications.services import notify_many

    notify_many(
        recipients=list(_admin_users()),
        notification_type='dispute_opened',
        message=f'Dispute opened on order #{order.pk}: {reason}.',
        target=dispute,
    )
    return dispute


@transaction.atomic
def dispute_resolve(*, dispute, admin, status, resolution=''):
    if status not in (Dispute.Status.RESOLVED, Dispute.Status.REJECTED):
        raise ValidationError('A dispute must be resolved or rejected.')

    dispute.status = status
    dispute.resolution = resolution
    dispute.resolved_by = admin
    dispute.full_clean()
    dispute.save()

    # Closing the dispute returns the order to active so its flow can continue.
    order = dispute.order
    if order.status == Order.Status.DISPUTED:
        order.status = Order.Status.ACTIVE
        order.save(update_fields=['status', 'updated_at'])

    from apps.notifications.services import notify

    notify(
        recipient=dispute.raised_by,
        notification_type='dispute_resolved',
        message=f'Your dispute on order #{order.pk} was {status}.',
        target=dispute,
    )
    return dispute

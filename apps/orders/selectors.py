"""Read-only queries for orders."""

from django.db.models import Q

from apps.orders.models import Order


def _base_qs():
    return Order.objects.select_related(
        'design_request', 'vendor', 'vendor__user', 'client', 'bid'
    ).prefetch_related('production_updates')


def orders_for_user(*, user):
    """Orders the user participates in, as either the client or the vendor."""
    return _base_qs().filter(Q(client=user) | Q(vendor__user=user)).distinct()


def order_get(*, order_id):
    return _base_qs().get(id=order_id)


def order_is_participant(*, order, user):
    return order.client_id == user.id or order.vendor.user_id == user.id

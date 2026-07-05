"""Read-only queries for disputes."""

from django.db.models import Q

from apps.disputes.models import Dispute


def _base_qs():
    return Dispute.objects.select_related(
        'order', 'raised_by', 'resolved_by'
    )


def disputes_for_user(*, user):
    """Admins see everything; participants see disputes on their own orders."""
    qs = _base_qs()
    if user.is_staff or user.role == user.Role.ADMIN:
        return qs
    return qs.filter(
        Q(order__client=user) | Q(order__vendor__user=user)
    ).distinct()


def dispute_get(*, dispute_id):
    return _base_qs().get(id=dispute_id)

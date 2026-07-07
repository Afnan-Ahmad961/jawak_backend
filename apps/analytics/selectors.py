"""Read-only aggregate queries powering the admin analytics dashboard."""

from django.db.models import Avg, Count, Q

from apps.bids.models import Bid
from apps.design_requests.models import DesignRequest
from apps.disputes.models import Dispute
from apps.orders.models import Order
from apps.vendors.models import VendorProfile


def requests_by_apparel_type():
    return list(
        DesignRequest.objects.values('apparel_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )


def orders_by_status():
    return list(
        Order.objects.values('status').annotate(count=Count('id')).order_by('-count')
    )


def top_vendors(*, limit=10):
    return list(
        VendorProfile.objects.annotate(
            completed_orders=Count(
                'orders', filter=Q(orders__status=Order.Status.COMPLETED)
            )
        )
        .values(
            'id',
            'company_name',
            'avg_rating',
            'review_count',
            'completed_orders',
        )
        .order_by('-avg_rating', '-review_count')[:limit]
    )


def overview():
    total_requests = DesignRequest.objects.count()
    total_bids = Bid.objects.count()
    total_orders = Order.objects.count()
    total_disputes = Dispute.objects.count()
    avg_bid = Bid.objects.aggregate(avg=Avg('proposed_price'))['avg']

    return {
        'totals': {
            'requests': total_requests,
            'bids': total_bids,
            'orders': total_orders,
            'vendors': VendorProfile.objects.count(),
            'disputes': total_disputes,
        },
        'avg_bid_amount': float(avg_bid) if avg_bid is not None else None,
        'bids_per_request': (
            round(total_bids / total_requests, 2) if total_requests else 0
        ),
        'dispute_rate': (
            round(total_disputes / total_orders, 3) if total_orders else 0
        ),
        'requests_by_apparel_type': requests_by_apparel_type(),
        'orders_by_status': orders_by_status(),
        'top_vendors': top_vendors(),
    }

"""Read-only queries for bids."""

from apps.bids.models import Bid


def bids_for_request(*, design_request):
    return (
        Bid.objects.select_related('vendor', 'vendor__user', 'design_request')
        .filter(design_request=design_request)
    )


def bids_for_vendor(*, vendor):
    return Bid.objects.select_related('design_request').filter(vendor=vendor)


def bid_get(*, bid_id):
    return (
        Bid.objects.select_related(
            'design_request', 'design_request__client', 'vendor', 'vendor__user'
        ).get(id=bid_id)
    )
